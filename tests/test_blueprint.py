"""Run: python tests/test_blueprint.py — lint and guard cases against copies of tests/fixtures/blueprint/shop."""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PLUGIN = HERE.parent / "plugins" / "blueprint"
LINT = PLUGIN / "skills" / "blueprint" / "scripts" / "blueprint_lint.py"
GUARD = PLUGIN / "hooks" / "blueprint_guard.py"
FIXTURE = HERE / "fixtures" / "blueprint" / "shop"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="bp-"))
fails = 0


def fresh():
    root = tmp / "docs" / "blueprint" / "shop"
    shutil.rmtree(root, ignore_errors=True)
    shutil.copytree(FIXTURE, root)
    return root


def edit(root, name, old, new):
    p = root / name
    text = p.read_text(encoding="utf-8")
    assert old in text, f"{name}: '{old}' not in fixture"
    p.write_bytes(text.replace(old, new, 1).encode("utf-8"))


def lint(root, *args):
    p = subprocess.run([sys.executable, str(LINT), str(root), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout


def guard(event, tool, inp):
    p = subprocess.run([sys.executable, str(GUARD)], capture_output=True, text=True, encoding="utf-8",
                       input=json.dumps({"hook_event_name": event, "tool_name": tool, "tool_input": inp}))
    if p.stderr.strip():
        return "ERR " + p.stderr.strip()[-300:]
    if not p.stdout.strip():
        return "pass"
    out = json.loads(p.stdout)["hookSpecificOutput"]
    return out.get("permissionDecision") or out.get("additionalContext", "")


def t(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {detail[:600]}"))
    fails += 0 if ok else 1


def expect_code(name, code, mutate):
    root = fresh()
    mutate(root)
    rc, out = lint(root)
    t(name, rc == 1 and f" {code} " in out, out)


try:
    rc, out = lint(fresh())
    t("clean fixture passes", rc == 0 and "0 errors" in out, out)
    expect_code("done-when misses an AC", "task-done-ac",
                lambda r: edit(r, "BACKLOG.md", "- AC-F01-2 → test `Foreign_order_403_AC_F01_2` passes\n", ""))
    expect_code("XL task", "task-xl", lambda r: edit(r, "BACKLOG.md", "| M | agent-ready |", "| XL | agent-ready |"))
    expect_code("screen field not in data model", "field-missing",
                lambda r: edit(r, "DESIGN.md", "E-Order.total", "E-Order.discount"))
    expect_code("dependency cycle", "dependency-cycle",
                lambda r: edit(r, "BACKLOG.md", "| S | human | — | — | — |", "| S | human | — | — | T-01.1.1 |"))
    expect_code("dangling decision", "dangling-ref", lambda r: edit(r, "BACKLOG.md", "· D-01", "· D-09"))
    expect_code("pack section missing", "task-pack", lambda r: edit(r, "BACKLOG.md", "- Out of scope: discounts.\n", ""))
    expect_code("AC without task", "ac-uncovered",
                lambda r: edit(r, "PRODUCT.md", "**Entities:** E-Order", "- AC-F01-3 · Given x, when y, then z.\n**Entities:** E-Order"))
    expect_code("entity without fields", "entity-no-fields",
                lambda r: edit(r, "PRODUCT.md", "| E-Order | an order | shop |", "| E-Order | an order | shop |\n| E-Invoice | invoice | shop |"))
    expect_code("MVP feature without screen", "feature-no-screen", lambda r: edit(r, "DESIGN.md", "— F-01 ·", "— ·"))

    root = fresh()
    edit(root, "PRODUCT.md", "version: 2", "version: 3")
    edit(root, "PRODUCT.md", "· changed: F-01\n", "· changed: F-01\n- v3 · 2026-09-06 · order total rule · changed: E-Order\n")
    rc, out = lint(root)
    t("cascade lists stale items", "STALE stale" in out and "revisit: E-Order" in out, out)

    root = fresh()
    ap = subprocess.run([sys.executable, str(LINT), "--approve", str(root / "PRODUCT.md")], capture_output=True, text=True, encoding="utf-8")
    t("approve records hash", "approved PRODUCT.md v2" in ap.stdout, ap.stdout + ap.stderr)
    rc, out = lint(root, "--quick")
    t("approved doc lints clean", rc == 0, out)
    edit(root, "PRODUCT.md", "success = 30%", "success = 40%")
    rc, out = lint(root, "--quick")
    t("approved doc edited without bump fails", "approved-changed" in out, out)
    edit(root, "PRODUCT.md", "success = 40%", "success = 30%")

    p = str(root / "PRODUCT.md")
    t("guard: edit approved without bump denied", guard("PreToolUse", "Edit", {"file_path": p, "old_string": "30%", "new_string": "40%"}) == "deny")
    text = (root / "PRODUCT.md").read_text(encoding="utf-8")
    t("approve keeps LF endings and no trailing spaces", "\r\n" not in (root / "PRODUCT.md").read_bytes().decode()
      and "status: approved\n" in text)

    def bump(extra):
        return re.sub(r"(?m)^version: 2", "version: 3", text).replace("status: approved", "status: draft").replace(
            "· changed: F-01\n", "· changed: F-01\n" + extra)
    t("guard: write with bump passes",
      guard("PreToolUse", "Write", {"file_path": p, "content": bump("- v3 · 2026-09-06 · wording · changed: none\n")}) == "pass")
    t("guard: bump without changelog line denied", guard("PreToolUse", "Write", {"file_path": p, "content": bump("")}) == "deny")
    t("guard: status-only edit on approved denied",
      guard("PreToolUse", "Edit", {"file_path": p, "old_string": "status: approved", "new_string": "status: draft"}) == "deny")
    t("guard: lowercase file name still gated",
      guard("PreToolUse", "Edit", {"file_path": p.replace("PRODUCT.md", "product.md"), "old_string": "30%", "new_string": "40%"}) == "deny")
    t("guard: hand approval denied", guard("PreToolUse", "Edit", {"file_path": str(root / "TECHNICAL.md"),
                                                               "old_string": "status: draft", "new_string": "status: approved"}) == "deny")
    t("guard: hand approved_version denied", guard("PreToolUse", "Edit", {"file_path": str(root / "DESIGN.md"),
                                                                        "old_string": "approved_version: null", "new_string": "approved_version: 1"}) == "deny")
    t("guard: new doc from template passes", guard("PreToolUse", "Write", {"file_path": str(tmp / "docs" / "blueprint" / "new" / "PRODUCT.md"),
                                                                        "content": "---\ndoc: product\nversion: 1\nstatus: draft\napproved_version: null\n---\n# x\n"}) == "pass")
    t("guard: backlog before technical approved denied",
      guard("PreToolUse", "Edit", {"file_path": str(root / "BACKLOG.md"), "old_string": "Shop", "new_string": "Shop"}) == "deny")
    t("guard: design before technical approved denied",
      guard("PreToolUse", "Edit", {"file_path": str(root / "DESIGN.md"), "old_string": "Shop", "new_string": "Shop"}) == "deny")
    subprocess.run([sys.executable, str(LINT), "--approve", str(root / "TECHNICAL.md")], capture_output=True)
    t("guard: design after technical approved passes",
      guard("PreToolUse", "Edit", {"file_path": str(root / "DESIGN.md"), "old_string": "Shop", "new_string": "Shop"}) == "pass")
    t("guard: backlog with design draft denied",
      guard("PreToolUse", "Edit", {"file_path": str(root / "BACKLOG.md"), "old_string": "Shop", "new_string": "Shop"}) == "deny")
    edit(root, "DESIGN.md", "status: draft", "status: skipped")
    edit(root, "DESIGN.md", "skip_reason: null", "skip_reason: API only")
    t("guard: backlog with design skipped passes",
      guard("PreToolUse", "Edit", {"file_path": str(root / "BACKLOG.md"), "old_string": "Shop", "new_string": "Shop"}) == "pass")
    merge = bump("- v3 · 2026-09-07 · promo · merged: evolutions/promo · changed: F-02\n")
    t("guard: merge into base asks", guard("PreToolUse", "Write", {"file_path": p, "content": merge}) == "ask")
    proj = tmp / "docs" / "blueprint" / "blueprint"
    shutil.copytree(root, proj)
    t("guard: project named blueprint still gated",
      guard("PreToolUse", "Edit", {"file_path": str(proj / "PRODUCT.md"), "old_string": "30%", "new_string": "40%"}) == "deny")
    t("guard: outside docs/blueprint passes", guard("PreToolUse", "Write", {"file_path": str(tmp / "PRODUCT.md"), "content": "x"}) == "pass")

    tech = str(root / "TECHNICAL.md")
    (root / "PRODUCT.md").write_bytes(bump("- v3 · 2026-09-06 · wording · changed: none\n").encode("utf-8"))

    def move(a, b):
        return guard("PreToolUse", "Edit", {"file_path": tech, "old_string": f"based_on_product_version: {a}",
                                            "new_string": f"based_on_product_version: {b}"})
    t("guard: based_on-only edit on approved doc passes", move(2, 3) == "pass")
    t("guard: based_on past the upstream version denied", move(2, 99) == "deny")
    t("guard: unresolvable edit gets no exemption", move(7, 3) == "deny")
    edit(root, "PRODUCT.md", "version: 3", "version: 4")
    edit(root, "PRODUCT.md", "· changed: none\n", "· changed: none\n- v4 · 2026-09-07 · 403 rule · changed: AC-F01-2\n")
    t("guard: based_on move over a stale item denied", move(2, 4) == "deny")
    rc, out = lint(root)
    t("cascade catches a table row citing a changed id", "STALE" in out and "TECHNICAL.md" in out and "AC-F01-2" in out, out)

    edit(root, "TECHNICAL.md", "## 2. Decisions", "## 2. Decisions\n### F-01 · dup")
    post = guard("PostToolUse", "Edit", {"file_path": str(root / "TECHNICAL.md")})
    t("post hook reports quick lint errors", "duplicate-id" in post, post)

    evo = root / "evolutions" / "promo"
    evo.mkdir(parents=True)
    (evo / "PRODUCT.md").write_text((FIXTURE / "PRODUCT.md").read_text(encoding="utf-8")
                                    .replace("base: null", "base: ../..").replace("mode: new", "mode: evolution"), encoding="utf-8")
    rc, out = lint(evo, "--quick")
    t("evolution redefining base id without (changed) fails", "base-collision" in out, out)
    delta = """---\ndoc: product\nproject: shop\nmode: evolution\nbase: ../..\nversion: 1\nstatus: draft\n---\n# Promo
## 4. MVP and phases\n| Feature | Priority (MoSCoW) | Phase |\n|---|---|---|\n| F-02 | Must | MVP |
## 5. Features\n### F-02 · Promo codes\n- AC-F02-1 · Given a code, when I pay, then E-Order total drops.\n"""
    (evo / "PRODUCT.md").write_text(delta, encoding="utf-8")
    rc, out = lint(evo)
    t("evolution delta full lint ignores base features", rc == 0 and "F-01" not in out, out)

    root = fresh()
    edit(root, "PRODUCT.md", "version: 2", "version: 3")
    edit(root, "PRODUCT.md", "· changed: F-01\n", "· changed: F-01\n- v3 · 2026-09-06 · typo · changed: none\n")
    rc, out = lint(root)
    t("changed: none is a warning, not stale", rc == 0 and "STALE" not in out and "WARN behind" in out, out)

    root = fresh()
    subprocess.run([sys.executable, str(LINT), "--approve", str(root / "PRODUCT.md")], capture_output=True)
    edit(root, "PRODUCT.md", "then I get 403", "then I get 404")
    ap = subprocess.run([sys.executable, str(LINT), "--approve", str(root / "PRODUCT.md")], capture_output=True, text=True, encoding="utf-8")
    t("approve refuses to re-stamp an approved doc edited in place", ap.returncode == 1 and "approved-changed" in ap.stdout, ap.stdout)
    edit(root, "PRODUCT.md", "then I get 404", "then I get 403")
    tp = root / "TECHNICAL.md"
    subprocess.run([sys.executable, str(LINT), "--approve", str(tp)], capture_output=True)
    tp.write_bytes(b"\xef\xbb\xbf" + tp.read_bytes())
    t("guard: approved doc with BOM still gated",
      guard("PreToolUse", "Edit", {"file_path": str(tp), "old_string": "PostgreSQL", "new_string": "MySQL"}) == "deny")

    evo2 = fresh() / "evolutions" / "more"
    evo2.mkdir(parents=True)
    (evo2 / "PRODUCT.md").write_text("---\ndoc: product\nproject: shop\nmode: evolution\nbase: ../..\nversion: 1\nstatus: draft\n---\n# More\n"
                                     "## 4. MVP and phases\n| Feature | Priority (MoSCoW) | Phase |\n|---|---|---|\n| F-01 | Must | MVP |\n"
                                     "## 5. Features\n### F-01 · Place order (changed)\n- AC-F01-3 · Given a gift, when I order, then no price shows.\n",
                                     encoding="utf-8")
    (evo2 / "BACKLOG.md").write_text("---\ndoc: backlog\nproject: shop\nmode: evolution\nbase: ../..\nversion: 1\nstatus: draft\n---\n# More\n"
                                     "#### US-01.2 · Gift · S · MVP\nCovers: F-01 · AC-F01-3\n##### T-01.2.1 · Hide price\n"
                                     "| Size | Executor | Agent / entry | Repo / area | Depends on |\n|---|---|---|---|---|\n| S | human | — | web | — |\n"
                                     "Covers: US-01.2 · AC-F01-3\n**Done when**\n- AC-F01-3 → test `Gift_AC_F01_3`\n", encoding="utf-8")
    rc, out = lint(evo2)
    t("evolution needs only its own criteria covered", "ac-uncovered" not in out, out)

    root = fresh()
    for n in ("BACKLOG.md", "TECHNICAL.md", "PRODUCT.md"):
        p2 = root / n
        p2.write_text(p2.read_text(encoding="utf-8").replace("|---|---|---|---|---|", "| --- | --- | --- | --- | --- |")
                      .replace("| F-01 | Must |", "| F-01    | Must |").replace("| E-Order | an order |", "| E-Order   | an order |"), encoding="utf-8")
    edit(root, "BACKLOG.md", "- Facts: E-Order", "- Facts: **E-Order**")
    (root / "DECISIONS.md").write_text("---\ndoc: decisions\n---\n| Q-01 | 2026-09-01 | scope | Drop F-09? | yes | no | PRODUCT · F-09 |\n", encoding="utf-8")
    edit(root, "DESIGN.md", "### S-01 ·", "## S-02 · Receipt — F-01\n**States:** success\n### S-01 ·")
    rc, out = lint(root)
    t("spacing variants, bold in pack, DECISIONS history, ## screen", rc == 0, out)

    root = fresh()
    edit(root, "BACKLOG.md", "| M | agent-ready |", "| XL | agent-ready |")
    ap = subprocess.run([sys.executable, str(LINT), "--approve", str(root / "PRODUCT.md")], capture_output=True, text=True, encoding="utf-8")
    t("approve refused while the folder has errors", ap.returncode == 1 and "refused" in ap.stdout, ap.stdout)

    tpl = tmp / "docs" / "blueprint" / "tpl"
    tpl.mkdir(parents=True)
    for rel in ("blueprint-scope/templates/PRODUCT.md", "blueprint-tech/templates/TECHNICAL.md",
                "blueprint-design/templates/DESIGN.md", "blueprint-backlog/templates/BACKLOG.md"):
        shutil.copy(PLUGIN / "skills" / rel, tpl)
    rc, out = lint(tpl)
    codes = sorted({l.split()[1] for l in out.splitlines() if l.startswith("ERROR")})
    t("templates lint only on their placeholders", codes == ["decision-unchosen", "no-failure-behaviour"], out)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("FAILED", fails)
sys.exit(1 if fails else 0)
