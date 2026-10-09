"""Run: python tests/test_guard.py — feeds hook payloads to guard.py against a throwaway git repo."""
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

GUARD = pathlib.Path(__file__).resolve().parents[1] / "plugins" / "dev-workflow" / "hooks" / "guard.py"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="dw-guard-"))
repo = tmp / "repo"
repo.mkdir()
cfg = tmp / "dev-workflow.json"
cfg.write_text(json.dumps({
    "work_item": {"prefix": "PROJ", "mcp_server": "tracker", "ascii_only": True},
    "review_request": {"tool": "mcp", "mcp_server": "reviews", "title_format": "{id} - {subject}",
                       "sections": ["Summary", "QA", "Tests"]},
    "forbidden_models": ["expensive-model"],
}))
env = {**os.environ, "DEV_WORKFLOW_CONFIG": str(cfg)}


def sh(*a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)


sh("init", "-q", "-b", "main"); sh("config", "user.email", "t@t"); sh("config", "user.name", "t")
(repo / "A.cs").write_text("class A {}\n"); sh("add", "."); sh("commit", "-qm", "init")


def run(tool, inp):
    p = subprocess.run([sys.executable, str(GUARD)], input=json.dumps({"tool_name": tool, "tool_input": inp, "cwd": str(repo)}),
                       capture_output=True, text=True, encoding="utf-8", env=env)
    if p.stderr.strip():
        return "ERR " + p.stderr.strip()[-300:]
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout.strip() else "pass"


fails = 0


def t(name, want, tool, inp):
    global fails
    got = run(tool, inp)
    fails += got != want
    print(("ok   " if got == want else "FAIL ") + f"{name}: want {want}, got {got}")


B = "Bash"
t("force push", "deny", B, {"command": "git push --force origin main"})
t("normal push", "pass", B, {"command": "git push -u origin feat/PROJ-1"})
t("reset hard", "deny", B, {"command": "git reset --hard HEAD~1"})
t("clean -fd", "deny", B, {"command": "git clean -fd"})
t("checkout -b", "pass", B, {"command": "git checkout -b feat/x"})
t("checkout -- .", "ask", B, {"command": "git checkout -- ."})
t("attribution trailer", "deny", B, {"command": "git commit -m \"x\n\nCo-Authored-By: Bot <b@b>\""})
(repo / "A.cs").write_text("class A {\n  // PROJ-123 hack\n  int x;\n}\n"); sh("add", "A.cs")
t("work-item id in comment", "deny", B, {"command": "git commit -m fix"})
(repo / "A.cs").write_text("class A {\n  /// a\n  /// b\n  /// c\n  /// d\n  /// e\n  int x;\n  int y;\n}\n"); sh("add", "A.cs")
t("comment density", "deny", B, {"command": "git commit -m fix"})
(repo / "A.cs").write_text("class A {\n  // why\n  int x;\n  int y;\n  int z;\n}\n")
t("clean commit", "pass", B, {"command": "git add A.cs && git commit -m fix"})
sh("add", "A.cs"); sh("commit", "-qm", "c2")
t("amend unpushed", "pass", B, {"command": "git commit --amend -m y"})
t("gh pr bad title", "deny", B, {"command": "gh pr create --title 'fix stuff' --body '## Summary\n## QA\n## Tests'"})
t("gh pr ok", "pass", B, {"command": "gh pr create --title 'PROJ-7 - Fix totals' --body '## Summary\ns\n## QA\nq\n## Tests\nt'"})
t("glab mr missing sections", "deny", B, {"command": "glab mr create -t 'PROJ-7 - Fix' -d 'just a body'"})
t("tracker non-ascii", "deny", "mcp__tracker__add_note", {"issue_id": 1, "note": "done ✔"})
t("tracker ascii", "pass", "mcp__tracker__add_note", {"issue_id": 1, "note": "done"})
t("tracker read accents", "pass", "mcp__tracker__search", {"query": "café"})
t("mcp review bad order", "deny", "mcp__reviews__create", {"title": "PROJ-1 - x", "description": "## Summary\n## Tests\n## QA\n"})
t("mcp review signature", "deny", "mcp__reviews__create", {"title": "PROJ-1 - x", "description": "## Summary\n## QA\n## Tests\nGenerated with Claude Code"})
t("mcp review ok", "pass", "mcp__reviews__create", {"title": "PROJ-1 - x", "description": "## Summary\ns\n## QA\nq\n## Tests\nt"})
words = lambda n: " ".join(["word"] * n)
t("pr section over word limit", "deny", B, {"command": f"gh pr create --title 'PROJ-7 - Fix' --body '## Summary\n{words(201)}\n## QA\nq\n## Tests\nt'"})
t("pr sections at word limit", "pass", B, {"command": f"gh pr create --title 'PROJ-7 - Fix' --body '## Summary\n{words(200)}\n## QA\n{words(200)}\n## Tests\nt'"})
t("pr banned opener", "deny", B, {"command": "gh pr create --title 'PROJ-7 - Fix' --body '## Summary\nThis PR introduces totals.\n## QA\nq\n## Tests\nt'"})
t("forbidden model", "deny", "Agent", {"prompt": "x", "description": "x", "model": "expensive-model"})
t("allowed model", "pass", "Agent", {"prompt": "x", "description": "x", "model": "sonnet"})

state = pathlib.Path.home() / ".claude" / "dev-state" / "_dw_guard_test"
state.mkdir(parents=True, exist_ok=True)
cp = state / "PROJ-1.md"
now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
fm = (f"---\nschema_version: 1\ndevelopment_id: PROJ-1\nrepo_root: {repo}\nstatus: active\ntask_class: STANDARD\n"
      f"plan_approved: false\ndevelopment_branch: main\nbranch_status: pending\nlast_updated: \"{now}+00:00\"\n---\n")
try:
    cp.write_text(fm)
    t("edit before approval", "ask", "Write", {"file_path": str(repo / "A.cs"), "content": "x"})
    t("edit outside repo", "pass", "Write", {"file_path": str(tmp / "note.md"), "content": "x"})
    cp.write_text(fm.replace("plan_approved: false", "plan_approved: true"))
    t("edit after approval", "pass", "Write", {"file_path": str(repo / "A.cs"), "content": "x"})
    cp.unlink()

    cfg.write_text(json.dumps({"work_item": {"prefix": "#", "tool": "gh"}, "review_request": {"tool": "gh"}}))
    (repo / "b.py").write_text("# 3 retries, then give up\nx = 1\ny = 2\nz = 3\nw = 4\n"); sh("add", "b.py")
    t("gh: hash comment with number", "pass", B, {"command": "git commit -m fix"})
    (repo / "b.py").write_text("# workaround for #12\nx = 1\ny = 2\nz = 3\nw = 4\n"); sh("add", "b.py")
    t("gh: issue ref in comment", "deny", B, {"command": "git commit -m fix"})
    (repo / "b.py").write_text("x = 1\ny = 2\nz = 3\nw = 4\n"); sh("add", "b.py")
    t("gh: Fixes #12 in commit message", "pass", B, {"command": "git commit -m 'Fix totals\n\nFixes #12'"})
    t("gh: pr title ok", "pass", B, {"command": "gh pr create --title '#12 - Fix totals' --body '## Summary\nCloses #12\n## QA\nq\n## Tests\nt'"})
    t("gh: pr title spaced id", "deny", B, {"command": "gh pr create --title '# 12 - Fix totals' --body '## Summary\ns\n## QA\nq\n## Tests\nt'"})

    cfg.write_text(json.dumps({"review_request": {"title_format": "{subject}", "max_section_words": 20, "banned_phrases": []}}))
    t("configured word limit", "deny", B, {"command": f"gh pr create --title 'Fix' --body '## Summary\n{words(21)}\n## QA\nq\n## Tests\nt'"})
    t("banned phrases disabled", "pass", B, {"command": "gh pr create --title 'Fix' --body '## Summary\nThis PR introduces totals.\n## QA\nq\n## Tests\nt'"})
finally:
    shutil.rmtree(state, ignore_errors=True)
    shutil.rmtree(tmp, ignore_errors=True)
print("FAILED", fails)
sys.exit(1 if fails else 0)
