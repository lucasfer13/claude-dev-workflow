"""PreToolUse guard for the dev-workflow rules (§2, §7, §8, §16, §18 of rules/CLAUDE.md).

Reads the hook payload on stdin and prints a deny/ask decision, or nothing to let the call through.
Settings come from ~/.claude/dev-workflow.json. Escape hatch for a real exception: the user runs the
command with `!` in the prompt.
"""
import datetime
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys

CLAUDE = pathlib.Path.home() / ".claude"
DEV_STATE = CLAUDE / "dev-state"
CODE_EXT = {".cs", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".kt", ".kts", ".java", ".py", ".go", ".rs", ".scss", ".css"}
HASH_COMMENT_EXT = {".py"}
GENERATED = re.compile(r"\.Designer\.cs$|\.g\.cs$|\.g\.i\.cs$|ModelSnapshot\.cs$|\.min\.js$|/Migrations/|/obj/|/bin/|/dist/")
ATTRIBUTION = re.compile(r"co-authored-by|generated with \[?claude code", re.I)


def load_config():
    try:
        path = os.environ.get("DEV_WORKFLOW_CONFIG") or CLAUDE / "dev-workflow.json"
        cfg = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except Exception:
        cfg = {}
    wi = cfg.get("work_item") or {}
    rr = cfg.get("review_request") or {}
    return {
        "prefix": wi.get("prefix"),
        "tracker": wi.get("mcp_server"),
        "ascii": bool(wi.get("ascii_only")),
        "rr_server": rr.get("mcp_server"),
        "title_format": rr.get("title_format") or "{id} - {subject}",
        "sections": [s.lower() for s in (rr.get("sections") or ["Summary", "QA", "Tests"])],
        "max_words": rr.get("max_section_words") or 200,
        "banned": [p.lower() for p in rr.get("banned_phrases", ["This PR introduces", "In this PR", "This pull request"])],
        "forbidden": [m.lower() for m in (cfg.get("forbidden_models") or [])],
        "attribution": cfg.get("block_attribution", True),
    }


def ticket_regex(prefix):
    if not prefix:
        return None
    if prefix == "#":
        # GitHub refs are '#' glued to digits; a spaced hash comment, an HTML entity or word-glued '#' is not one
        return re.compile(r"(?<![\w&#])#\d+\b")
    return re.compile(rf"{re.escape(prefix)}[\s_-]?\d+", re.I)


CFG = load_config()
TICKET_ID = ticket_regex(CFG["prefix"])


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": decision,
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=15)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def winpath(p):
    m = re.match(r"^/([a-zA-Z])(/.*)?$", p)
    return f"{m[1].upper()}:{m[2] or '/'}" if m and os.name == "nt" else os.path.expanduser(p)


# ---------- review request format (§16) ----------

def title_regex():
    idp = r"#\d+" if CFG["prefix"] == "#" else rf"{re.escape(CFG['prefix'])}[- ]?\d+" if CFG["prefix"] else r"\S+"
    parts = re.split(r"(\{id\}|\{subject\})", CFG["title_format"])
    rx = "".join(idp if p == "{id}" else r"\S.*" if p == "{subject}" else re.escape(p) for p in parts)
    return re.compile("^" + rx + "$")


def check_review_request(title, body, creating):
    if title is not None and not title_regex().match(title.strip()):
        decide("deny", f"Review-request title must follow '{CFG['title_format']}' (§16).")
    if body is None:
        if creating:
            decide("deny", "Review request without a body (§16): " + " / ".join(CFG["sections"]) + ".")
        return
    heads = [h.strip().lower() for h in re.findall(r"^##\s+(.+)$", body, re.M)]
    if heads[:len(CFG["sections"])] != CFG["sections"]:
        decide("deny", f"Review-request body (§16) needs sections {CFG['sections']} in that order; found {heads}.")
    if CFG["attribution"] and (ATTRIBUTION.search(body) or "\U0001F916" in body):
        decide("deny", "The body carries an attribution signature. Remove it (§8).")
    for part in re.split(r"^##\s+", body, flags=re.M)[1:]:
        head, _, text = part.partition("\n")
        if len(text.split()) > CFG["max_words"]:
            decide("deny", f"Section '{head.strip()}' has {len(text.split())} words, over max_section_words "
                           f"{CFG['max_words']} (§16): keep what the diff cannot tell.")
    hit = next((p for p in CFG["banned"] if p in body.lower()), None)
    if hit:
        decide("deny", f"Review-request body uses the filler phrase '{hit}' (§16, review_request.banned_phrases).")


def read_file(path):
    try:
        return pathlib.Path(winpath(path)).read_text(encoding="utf-8")
    except Exception:
        decide("deny", f"Cannot read body file: {path}")


def check_cli_review(argv):
    """gh pr create|edit, glab mr create|update."""
    if len(argv) < 3 or (argv[0], argv[1]) not in (("gh", "pr"), ("glab", "mr")) or argv[2] not in ("create", "edit", "update"):
        return
    title = body = None
    i = 3
    while i < len(argv):
        a = argv[i]
        key, eq, val = a.partition("=")
        if not eq:
            val = argv[i + 1] if i + 1 < len(argv) else None
        if key in ("--title", "-t"):
            title = val
        elif key in ("--body", "-b", "--description", "-d"):
            body = val
        elif key in ("--body-file", "-F"):
            body = None if val == "-" else read_file(val)
        else:
            i += 1
            continue
        i += 1 if eq else 2
    check_review_request(title, body, creating=argv[2] == "create")


# ---------- Bash: git ----------

def segments(cmd):
    return [s.strip() for s in re.split(r"&&|\|\||;|\n|\|", cmd) if s.strip()]


def git_call(seg):
    m = re.match(r"^(?:\w+=\S+\s+)*git\s+(.*)$", seg)
    if not m:
        return None
    rest, cdir = m[1], None
    while True:
        c = re.match(r"^(-C|-c)\s+(\"[^\"]+\"|'[^']+'|\S+)\s+(.*)$", rest)
        if not c:
            break
        if c[1] == "-C":
            cdir = winpath(c[2].strip("\"'"))
        rest = c[3]
    return cdir, rest


def pushed(repo):
    out = git(repo, "branch", "-r", "--contains", "HEAD")
    return bool(out and out.strip())


def cli_review_calls(cmd):
    """Token lists of every gh/glab review-request call, parsed over the whole command (bodies span lines)."""
    for m in re.finditer(r"(?<![\w-])(gh\s+pr|glab\s+mr)\s+(create|edit|update)\b", cmd):
        lex = shlex.shlex(cmd[m.start():], posix=True, punctuation_chars=";&|")
        lex.whitespace_split = True
        tokens = []
        try:
            for tok in lex:
                if tok in (";", "&&", "||", "|", "&"):
                    break
                tokens.append(tok)
        except ValueError:
            decide("ask", "Could not parse the review-request command to check its title and body (§16). Confirm.")
        yield tokens


def check_bash(cmd, cwd):
    repo = pathlib.Path(cwd)
    for argv in cli_review_calls(cmd):
        check_cli_review(argv)
    added_in_cmd = False
    for seg in segments(cmd):
        cd = re.match(r"^cd\s+(\"[^\"]+\"|'[^']+'|\S+)$", seg)
        if cd:
            repo = pathlib.Path(winpath(cd[1].strip("\"'")))
            continue
        call = git_call(seg)
        if not call:
            continue
        cdir, rest = call
        where = pathlib.Path(cdir) if cdir else repo
        sub = rest.split()[0] if rest.split() else ""
        if sub == "push":
            if re.search(r"(^|\s)(--force(-with-lease)?(=\S+)?|-f|--mirror)(\s|$)", rest) or re.search(r"\s\+\S+", rest):
                decide("deny", "Force-push blocked (§8): correct pushed history forward with a new commit.")
            if re.search(r"(^|\s)(--delete|-d)(\s|$)|\s:\S+", rest):
                decide("ask", "This deletes a remote branch. Confirm.")
        elif sub == "reset" and "--hard" in rest:
            decide("deny", "git reset --hard blocked (§8): it destroys local work. If needed, run it yourself with `!`.")
        elif sub == "clean" and re.search(r"\s-\w*f", " " + rest):
            decide("deny", "git clean -f blocked (§8): it deletes untracked files for good.")
        elif sub in ("checkout", "restore") and (re.search(r"\s--\s", f" {rest} ") or re.search(r"\s\.(\s|$)", f" {rest} ")) and "--staged" not in rest:
            decide("ask", "This discards local working-tree changes. Confirm.")
        elif sub == "stash" and re.search(r"\s(drop|clear)(\s|$)", f" {rest} "):
            decide("ask", "This drops stash entries for good. Confirm.")
        elif sub == "branch" and re.search(r"(^|\s)-D(\s|$)", rest):
            decide("ask", "Force-deletes a local branch. Confirm.")
        elif sub == "rebase" and not re.search(r"--(abort|continue|skip|quit)", rest) and pushed(where):
            decide("deny", "Rebase of a pushed branch blocked (§8): it rewrites shared history. Merge the target instead.")
        elif sub == "add":
            added_in_cmd = True
        elif sub == "commit":
            if CFG["attribution"] and ATTRIBUTION.search(cmd):
                decide("deny", "The commit message carries an attribution trailer (Co-Authored-By / Generated with). Remove it (§8).")
            if "--amend" in rest and pushed(where):
                decide("deny", "--amend on a pushed commit blocked (§8): make a new commit.")
            check_diff(where, include_worktree=added_in_cmd or re.search(r"(^|\s)(-a|--all|-\w*a\w*)(\s|$)", rest) is not None)


def dev_base(repo):
    for ref in ("origin/develop", "origin/dev", "origin/HEAD", "origin/main", "origin/master"):
        base = git(repo, "merge-base", "HEAD", ref)
        if base and base.strip():
            return base.strip(), ref.replace("origin/", "")
    return None, None


def check_diff(repo, include_worktree):
    """Work-item ids in comments and comment density over the whole development diff (§2, §21 phase 9)."""
    if git(repo, "rev-parse", "--show-toplevel") is None:
        return
    base, target = dev_base(repo)
    if base:
        diff = git(repo, "diff", "-U0", "--no-color", base) if include_worktree else git(repo, "diff", "-U0", "--no-color", "--cached", base)
        scope = f"{target}...(staged)"
    else:
        diff = git(repo, "diff", "-U0", "--no-color", "HEAD" if include_worktree else "--cached")
        scope = "staged"
    if not diff:
        return
    code = comments = 0
    ids, in_block, path = [], False, ""
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else ""
            in_block = False
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        ext = pathlib.PurePosixPath(path).suffix.lower()
        if ext not in CODE_EXT or GENERATED.search("/" + path):
            continue
        t = line[1:].strip()
        if not t:
            continue
        is_comment = in_block or t.startswith(("//", "/*", "*")) or (ext in HASH_COMMENT_EXT and t.startswith("#"))
        if t.startswith("/*") and "*/" not in t:
            in_block = True
        elif in_block and "*/" in t:
            in_block = False
        if is_comment:
            comments += 1
            if TICKET_ID and TICKET_ID.search(re.sub(r"^(//+|/\*+|\*+|#+)", "", t)):
                ids.append(f"{path}: {t[:80]}")
        else:
            code += 1
    if ids:
        decide("deny", f"Work-item ids in comments of the diff ({scope}) — §2 / §21 phase 9, remove them:\n" + "\n".join(ids[:8]))
    if code > 0 and comments >= 4 and comments * 4 > code:
        decide("deny", f"Comment density {comments}/{code} added code lines (> 1/4) over {scope} — §2 / §21 phase 9, blocking. "
                       "Cut to one-line whys. A justified exception: tell the user; they commit with `!`.")


# ---------- MCP ----------

def check_mcp(tool, inp):
    verb = tool.rsplit("__", 1)[-1]
    if CFG["tracker"] and CFG["ascii"] and tool.startswith(f"mcp__{CFG['tracker']}__") and re.search(r"create|update|add|note|set|assign|edit|comment", verb):
        text = " ".join(str(v) for v in inp.values() if isinstance(v, str))
        bad = sorted({c for c in text if ord(c) > 127})
        if bad:
            decide("deny", "The tracker only accepts ASCII (work_item.ascii_only). Replace: " + " ".join(bad[:20]))
    if CFG["rr_server"] and tool.startswith(f"mcp__{CFG['rr_server']}__") and re.search(r"create|update|edit", verb):
        body = inp.get("description") or inp.get("body")
        f = inp.get("description_file") or inp.get("body_file")
        if f:
            body = read_file(f)
        check_review_request(inp.get("title"), body, creating="create" in verb)


def check_agent(inp):
    if str(inp.get("model", "")).lower() in CFG["forbidden"]:
        decide("deny", f"Model '{inp.get('model')}' is in forbidden_models (dev-workflow.json).")


# ---------- Edit/Write: plan approval (§7) ----------

def frontmatter(p):
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    fm = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.split("#")[0].strip().strip('"')
    return fm


def norm(p):
    return os.path.realpath(p).replace("\\", "/").rstrip("/").lower() if p else ""


def check_plan(inp):
    fp = inp.get("file_path") or inp.get("notebook_path")
    if not fp:
        return
    d = pathlib.Path(fp).parent
    while not d.exists() and d != d.parent:
        d = d.parent
    top = git(d, "rev-parse", "--show-toplevel")
    if not top:
        return
    top = norm(top.strip())
    branch = (git(top, "branch", "--show-current") or "").strip()
    now = datetime.datetime.now()
    for cp in DEV_STATE.glob("*/*.md"):
        if cp.name.endswith(".trace.md"):
            continue
        fm = frontmatter(cp)
        if norm(fm.get("repo_root", "")) != top:
            continue
        if fm.get("status") not in ("active", "waiting_user") or fm.get("plan_approved") == "true":
            continue
        if fm.get("task_class") not in ("STANDARD", "COMPLEX", "BUG"):
            continue
        try:
            if (now - datetime.datetime.fromisoformat(fm.get("last_updated", "")[:19])).days > 3:
                continue
        except ValueError:
            continue
        if branch == fm.get("working_branch") or (fm.get("branch_status") != "created" and branch == fm.get("development_branch")):
            decide("ask", f"{cp.stem} has plan_approved: false (§7). No repo edits before gate #1. Continue anyway?")


def main():
    try:
        payload = json.load(sys.stdin.buffer)
    except Exception:
        return
    tool = payload.get("tool_name", "")
    inp = payload.get("tool_input") or {}
    if tool == "Bash":
        check_bash(inp.get("command", ""), payload.get("cwd") or os.getcwd())
    elif tool in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        check_plan(inp)
    elif tool.startswith("mcp__"):
        check_mcp(tool, inp)
    elif tool in ("Agent", "Task"):
        check_agent(inp)


if __name__ == "__main__":
    main()
