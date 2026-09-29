"""Blueprint hooks (contract §2): PreToolUse gates edits to blueprint docs, PostToolUse runs the quick lint.

Reads the hook payload on stdin. Escape hatch for a real exception: the user edits the file themselves.
"""
import json
import pathlib
import re
import subprocess
import sys

GATED = {"PRODUCT.md", "TECHNICAL.md", "DESIGN.md", "BACKLOG.md"}
NEEDS = {"TECHNICAL.md": ["PRODUCT.md"], "DESIGN.md": ["TECHNICAL.md"], "BACKLOG.md": ["TECHNICAL.md", "DESIGN.md"]}
LINT = pathlib.Path(__file__).resolve().parent.parent / "skills" / "blueprint" / "scripts" / "blueprint_lint.py"


def pre(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def frontmatter(text):
    text = (text or "").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}
    fm = {}
    for line in text[4:text.find("\n---", 3)].splitlines():
        if ":" in line and not line.startswith((" ", "#")):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.split(" #")[0].strip().strip('"')
    return fm


def body(text):
    text = (text or "").replace("\r\n", "\n")
    end = text.find("\n---", 3) if text.startswith("---\n") else -1
    return text[end + 4:].strip() if end >= 0 else text.strip()


def read(p):
    try:
        return p.read_text(encoding="utf-8-sig")
    except OSError:
        return None


def locate(fp):
    """(blueprint root, logical doc name, file) for a path inside docs/blueprint, else None."""
    p = pathlib.Path(fp)
    parts = [x.lower() for x in p.parts]
    if p.suffix.lower() != ".md" or not any(parts[i:i + 2] == ["docs", "blueprint"] for i in range(len(parts))):
        return None
    if p.parent.name.lower() == "backlog" and re.match(r"EP-\d+", p.name, re.I):
        return p.parent.parent, "BACKLOG.md", p
    return p.parent, p.name.upper().replace(".MD", ".md"), p


def after_edit(inp, current):
    if "content" in inp:
        return inp["content"]
    text = current or ""
    for e in inp.get("edits") or [inp]:
        old, new = e.get("old_string", ""), e.get("new_string", "")
        text = text.replace(old, new) if e.get("replace_all") else text.replace(old, new, 1)
    return text


def val(v):
    return None if v in (None, "", "null") else v


def num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def based_on_ok(root, owner, new_fm):
    """A based_on_* move is harmless only up to the upstream version and when nothing cited went stale."""
    for k, v in new_fm.items():
        m = re.match(r"based_on_(\w+)_version$", k)
        if m and val(v) is not None:
            up = frontmatter(read(root / f"{m.group(1).upper()}.md"))
            if num(v) > num(up.get("version")):
                return False
    sys.path.insert(0, str(LINT.parent))
    try:
        from blueprint_lint import Lint
        lint = Lint(root)
        lint.cascade()
    except Exception:
        return False
    return not any(f[0] == "STALE" and pathlib.Path(f[2].rsplit(":", 1)[0]).name == owner.name for f in lint.out)


def check_pre(inp):
    fp = inp.get("file_path")
    loc = locate(fp) if fp else None
    if not loc:
        return
    root, name, path = loc
    if name not in GATED:
        return
    current = read(path)
    new = after_edit(inp, current)
    is_owner = path.parent == root
    owner = path if is_owner else root / name
    cur_fm = frontmatter(current if is_owner else read(owner))
    new_fm = frontmatter(new) if is_owner else cur_fm
    if is_owner:
        for k in ("approved_version", "approved_hash"):
            if val(new_fm.get(k)) != val(cur_fm.get(k)):
                pre("deny", f"{k} is set only by `blueprint_lint.py --approve` after the user approves at the gate.")
        if new_fm.get("status") == "approved" and cur_fm.get("status") != "approved":
            pre("deny", "Approval is recorded only by `blueprint_lint.py --approve` after the user approves at the gate.")
    if cur_fm.get("status") == "approved":
        v = num(cur_fm.get("version")) + 1
        only_based_on = is_owner and new != current and body(new) == body(current) and all(
            new_fm.get(k) == cur_fm.get(k) for k in set(new_fm) | set(cur_fm) if not k.startswith("based_on_")) \
            and based_on_ok(root, owner, new_fm)
        bumped = new_fm.get("status") == "draft" and num(new_fm.get("version")) > num(cur_fm.get("version"))
        logged = re.search(rf"(?m)^- v{num(new_fm.get('version'))} · ", new or "")
        if not only_based_on and not (bumped and logged):
            pre("deny", f"{name} is approved (v{cur_fm.get('version')}). In ONE edit (Write or MultiEdit) set status: draft, "
                        f"version: {v} and add the changelog line '- v{v} · <date> · <what> · changed: <ids>'; "
                        f"the change then goes back to its gate.")
    for up in NEEDS.get(name, []):
        up_fm = frontmatter(read(root / up))
        ok = up_fm.get("approved_version") not in (None, "", "null") or (up == "DESIGN.md" and up_fm.get("status") == "skipped")
        if not ok:
            hint = " or record it as skipped (status: skipped + skip_reason)" if up == "DESIGN.md" else ""
            pre("deny", f"{name} needs {up} approved first{hint}.")
    if is_owner and "evolutions" not in [x.lower() for x in root.parts]:
        added = set(new.splitlines()) - set((current or "").splitlines())
        if any(re.match(r"^- v\d+ · .*merged: ", l) for l in added):
            pre("ask", f"This merges an evolution into the base {name}. Approved by the user?")


def check_post(inp):
    fp = inp.get("file_path")
    loc = locate(fp) if fp else None
    if not loc or not LINT.exists():
        return
    res = subprocess.run([sys.executable, str(LINT), str(loc[0]), "--quick"], capture_output=True, text=True,
                         encoding="utf-8", timeout=15)
    errors = [l for l in res.stdout.splitlines() if l.startswith("ERROR")]
    if errors:
        msg = "blueprint lint (quick):\n" + "\n".join(errors[:15])
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


def main():
    try:
        payload = json.load(sys.stdin.buffer)
    except Exception:
        return
    if payload.get("tool_name") not in ("Edit", "Write", "MultiEdit"):
        return
    inp = payload.get("tool_input") or {}
    if payload.get("hook_event_name") == "PostToolUse":
        check_post(inp)
    else:
        check_pre(inp)


if __name__ == "__main__":
    main()
