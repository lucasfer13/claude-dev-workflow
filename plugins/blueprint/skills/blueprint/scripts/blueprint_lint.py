"""Deterministic checks for a blueprint folder (contract: ../reference/contract.md).

  blueprint_lint.py <root> [--quick] [--json]   lint; exit 1 on errors
  blueprint_lint.py --approve <doc.md>          full lint, then record the approval in the frontmatter
  blueprint_lint.py --hash <doc.md>             print the body hash
"""
import hashlib
import json
import pathlib
import re
import sys

ID = (r"AC-F\d{2,}-\d+|US-\d{2,}\.\d+|T-\d{2,}\.\d+(?:\.\d+)?|EP-\d{2,}|FL-\d{2,}|SP-\d{2,}|RV-\d{2,}|CR-\d{2,}"
      r"|F-\d{2,}|S-\d{2,}|D-\d{2,}|I-\d{2,}|Q-\d{2,}|P-\d{2,}|E-[A-Z][A-Za-z0-9]*|C-[A-Z][A-Za-z0-9]*"
      r"|G-[a-z0-9][a-z0-9-]*")
ID_RE = re.compile(rf"(?<![\w-])({ID})(?![\w-]|\.\d)")
DEF_RE = re.compile(rf"^(?:#{{2,6}} |\|\s*|- )({ID})(?= ·|\s+\||\||\s*$| \(| —)")
SEP_RE = re.compile(r"^\|\s*:?-{3,}")
PROSE_KINDS = {"E", "C", "G"}
DEF_BY = {"#": set("F FL S EP US T E".split()), "|": set("E G D I SP C Q RV P CR".split()), "-": {"AC", "Q"}}
DOCS = ["PRODUCT.md", "TECHNICAL.md", "DESIGN.md", "BACKLOG.md", "DECISIONS.md", "REVIEW.md", "CHANGES.md"]
MULTI_DOC = {"E": {"PRODUCT.md", "TECHNICAL.md"}, "Q": {"PRODUCT.md", "DECISIONS.md"}}
UPSTREAM = {"TECHNICAL.md": ["PRODUCT.md"], "DESIGN.md": ["PRODUCT.md", "TECHNICAL.md"],
            "BACKLOG.md": ["PRODUCT.md", "TECHNICAL.md", "DESIGN.md"]}
PACK = ["Goal", "Facts", "Where", "From dependencies", "Conventions", "Out of scope"]
PACK_MAX_WORDS = 400


def kind(i):
    return i.split("-", 1)[0]


def definition(line):
    m = DEF_RE.match(line)
    return m.group(1) if m and kind(m.group(1)) in DEF_BY[line[0]] else None


def split_doc(text):
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}, text, 0
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text, 0
    fm = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "#")):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.split(" #")[0].strip().strip('"')
    body = text[end + 4:].lstrip("\n")
    return fm, body, text[:len(text) - len(body)].count("\n")


def body_hash(body):
    norm = "\n".join(line.rstrip() for line in body.replace("\r\n", "\n").strip().splitlines())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def row(line, first):
    """Cells of a table row whose first cell is an id of the given pattern, else None."""
    if not re.match(rf"^\|\s*(?:{first})\s*\|", line):
        return None
    return [c.strip() for c in line.strip().strip("|").split("|")]


def num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


class Doc:
    def __init__(self, path, base=False):
        self.path = path
        self.name = path.name if path.parent.name != "backlog" else "BACKLOG.md"
        self.fm, self.body, self.offset = split_doc(path.read_text(encoding="utf-8-sig"))
        self.lines = self.body.splitlines()
        self.base = base

    def at(self, i):
        return f"{self.path.as_posix()}:{i + self.offset + 1}"


class Lint:
    def __init__(self, root, quick=False):
        self.root = pathlib.Path(root)
        self.quick = quick
        self.out = []
        self.docs = self.load(self.root)
        self.base_docs = []
        base = next((d.fm.get("base") for d in self.docs if d.fm.get("base") not in (None, "", "null")), None)
        if base is None and self.root.parent.name == "evolutions":
            base = "../.."
        if base:
            self.base_docs = self.load((self.root / base).resolve(), base=True)
        self.defs = {}
        self.refs = []

    @staticmethod
    def load(root, base=False):
        docs = [Doc(root / n, base) for n in DOCS if (root / n).exists()]
        docs += [Doc(p, base) for p in sorted((root / "backlog").glob("EP-*.md"))] if (root / "backlog").is_dir() else []
        return docs

    def add(self, level, code, where, msg):
        self.out.append((level, code, where, msg))

    def doc(self, name):
        return next((d for d in self.docs if d.name == name and d.path.name == name), None)

    # ---------- ids ----------
    def index(self):
        for d in self.base_docs:
            for i, line in enumerate(d.lines):
                if definition(line):
                    self.defs.setdefault(definition(line), []).append((d, i))
        base_ids = set(self.defs)
        for d in self.docs:
            if d.name == "DESIGN.md" and d.fm.get("status") == "skipped":
                continue
            in_code = False
            for i, line in enumerate(d.lines):
                if line.startswith("```"):
                    in_code = not in_code
                if in_code:
                    continue
                own = definition(line)
                if own:
                    if own in base_ids and "(changed" not in line:
                        self.add("ERROR", "base-collision", d.at(i), f"{own} exists in the base; mark the line '(changed)' or use a new number")
                    self.defs.setdefault(own, []).append((d, i))
                for r in ID_RE.findall(line):
                    if r != own:
                        self.refs.append((r, d, i))
        for i, places in self.defs.items():
            local = [(d, n) for d, n in places if not d.base]
            names = [d.name for d, _ in local]
            for name in set(names):
                if names.count(name) > 1:
                    d, n = next(p for p in local if p[0].name == name)
                    self.add("ERROR", "duplicate-id", d.at(n), f"{i} defined {names.count(name)} times in {name}")
            if len(set(names)) > 1 and not set(names) <= MULTI_DOC.get(kind(i), set()):
                d, n = local[0]
                self.add("ERROR", "duplicate-id", d.at(n), f"{i} defined in {', '.join(sorted(set(names)))}")

    def dangling(self):
        for r, d, i in self.refs:
            if r not in self.defs and d.name not in ("REVIEW.md", "CHANGES.md", "DECISIONS.md"):
                level = "WARN" if kind(r) in PROSE_KINDS else "ERROR"
                self.add(level, "dangling-ref", d.at(i), f"{r} is cited but defined nowhere")

    def local(self, k):
        return [i for i, ps in self.defs.items() if kind(i) == k and any(not d.base for d, _ in ps)]

    # ---------- frontmatter ----------
    def frontmatter(self):
        for d in self.docs:
            if d.name not in ("PRODUCT.md", "TECHNICAL.md", "DESIGN.md", "BACKLOG.md") or d.path.parent.name == "backlog":
                continue
            st = d.fm.get("status")
            if st not in ("draft", "approved", "skipped") or (st == "skipped" and d.name != "DESIGN.md"):
                self.add("ERROR", "frontmatter", d.at(-1), f"status '{st}' not allowed")
            if num(d.fm.get("version")) is None:
                self.add("ERROR", "frontmatter", d.at(-1), "version missing or not a number")
            if st == "skipped" and d.fm.get("skip_reason") in (None, "", "null"):
                self.add("ERROR", "frontmatter", d.at(-1), "skipped design needs skip_reason")
            if st == "approved":
                h = self.doc_hash(d)
                if d.fm.get("approved_hash") != h:
                    self.add("ERROR", "approved-changed", d.at(-1), "approved doc changed after approval: set status draft, bump version, add a changelog line")
                if d.fm.get("approved_version") != d.fm.get("version"):
                    self.add("ERROR", "approved-changed", d.at(-1), "approved_version differs from version")

    def doc_hash(self, d):
        parts = [d.body] + [p.body for p in self.docs if d.name == "BACKLOG.md" and p.path.parent.name == "backlog"]
        return body_hash("\n".join(parts))

    # ---------- versions and cascade ----------
    def cascade(self):
        for name, ups in UPSTREAM.items():
            down = self.doc(name)
            if not down or down.fm.get("status") == "skipped":
                continue
            for up_name in ups:
                up = self.doc(up_name)
                key = f"based_on_{up_name.split('.')[0].lower()}_version"
                if not up or up.fm.get("status") == "skipped":
                    continue
                have, cur = num(down.fm.get(key)), num(up.fm.get("version"))
                if have is None or cur is None or have >= cur:
                    continue
                changed = set()
                for line in up.lines:
                    m = re.match(r"^- v(\d+) · .*changed: (.*)$", line)
                    if m and int(m.group(1)) > have:
                        changed |= set(ID_RE.findall(m.group(2)))
                stale = sorted({blk for blk, ids in self.blocks(name) if ids & changed})
                loose = changed & set(ID_RE.findall("\n".join(x.body for x in self.docs if x.name == name)))
                if loose and not stale:
                    stale = [f"lines citing {', '.join(sorted(loose))}"]
                if stale:
                    self.add("STALE", "stale", down.at(-1), f"{key}={have} < {up_name} v{cur}; changed {', '.join(sorted(changed))}; revisit: {', '.join(stale)}")
                else:
                    self.add("WARN", "behind", down.at(-1), f"{key}={have} < {up_name} v{cur}; nothing cited changed: set {key}: {cur}")

    def blocks(self, name, text=False):
        """(defining id, ids cited in its block[, block text]) for every heading-defined item of a doc and its epic files."""
        for d in [x for x in self.docs if x.name == name]:
            cur, ids, lines = None, set(), []
            for line in d.lines + ["# end"]:
                own = definition(line) if line.startswith("|") else None
                if own:
                    yield (own, set(ID_RE.findall(line)), line) if text else (own, set(ID_RE.findall(line)))
                if line.startswith("#"):
                    if cur:
                        yield (cur, ids, "\n".join(lines)) if text else (cur, ids)
                    cur, ids, lines = definition(line), set(), []
                if cur:
                    ids |= set(ID_RE.findall(line))
                    lines.append(line)

    # ---------- coverage ----------
    def mvp_features(self):
        p = self.doc("PRODUCT.md")
        if not p:
            return []
        return [r[0] for l in p.lines if (r := row(l, r"F-\d+")) and any(c.upper() == "MVP" for c in r[1:])]

    def acs_of(self, f):
        acs = [i for i in self.defs if i.startswith(f"AC-{f.replace('-', '')}-")]
        return sorted(set(acs) & set(self.local("AC"))) if self.base_docs else sorted(acs)

    def product(self):
        p = self.doc("PRODUCT.md")
        if not p:
            return
        feats = self.local("F")
        phased = {r[0] for l in p.lines if (r := row(l, r"F-\d+"))}
        for f in feats:
            block = dict(self.blocks("PRODUCT.md")).get(f, set())
            where = self.where(f)
            if not self.acs_of(f):
                self.add("ERROR", "no-acceptance", where, f"{f} has no AC-{f.replace('-', '')}-n criterion")
            if f not in phased:
                self.add("ERROR", "no-priority", where, f"{f} missing from §4 MVP and phases")
            if not any(kind(i) == "E" for i in block):
                self.add("WARN", "no-entities", where, f"{f} cites no entity")
        for f in phased - set(feats):
            self.add("ERROR", "dangling-ref", p.at(0), f"{f} in §4 has no feature section")

    def technical(self):
        t, p = self.doc("TECHNICAL.md"), self.doc("PRODUCT.md")
        if not t or not p:
            return
        heads = {m.group(1) for l in t.lines if (m := re.match(r"^### (E-\w+)", l))}
        for l in p.lines:
            r = row(l, r"E-[A-Z]\w*")
            if r and r[0] not in heads:
                self.add("ERROR", "entity-no-fields", t.at(0), f"{r[0]} has no '### {r[0]}' field table")
        for i, l in enumerate(t.lines):
            d, g = row(l, r"D-\d+"), row(l, r"I-\d+")
            if d and (len(d) < 3 or d[2] in ("", "…")):
                self.add("ERROR", "decision-unchosen", t.at(i), f"{d[0]} has no chosen option")
            if g and (len(g) < 5 or g[4] in ("", "…")):
                self.add("ERROR", "no-failure-behaviour", t.at(i), f"{g[0]} has no failure behaviour")
        tested = set(ID_RE.findall("\n".join(self.section(t, "Test strategy"))))
        missing = [a for f in self.mvp_features() for a in self.acs_of(f) if a not in tested]
        if missing:
            self.add("WARN", "untested-ac", t.at(0), f"MVP criteria without a test level in §8: {', '.join(missing)}")

    def fields(self):
        t = self.doc("TECHNICAL.md")
        out, cur = {}, None
        for l in (t.lines if t else []):
            m = re.match(r"^### (E-\w+)", l)
            if m:
                cur = m.group(1)
                out[cur] = set()
            elif l.startswith("#"):
                cur = None
            elif cur and l.startswith("|") and not SEP_RE.match(l) and not re.match(r"^\|\s*Field\s*\|", l):
                out[cur].add(l.split("|")[1].strip().strip("`"))
        return out

    def design(self):
        d = self.doc("DESIGN.md")
        if not d or d.fm.get("status") == "skipped":
            return
        blocks = [b for b in self.blocks("DESIGN.md", text=True) if kind(b[0]) == "S"]
        screens = {s: ids for s, ids, _ in blocks}
        for f in self.mvp_features():
            if not any(f in ids for ids in screens.values()):
                self.add("ERROR", "feature-no-screen", d.at(0), f"MVP {f} has no screen")
        fields = self.fields()
        for i, l in enumerate(d.lines):
            for e, fld in re.findall(r"(E-[A-Z]\w*)\.([A-Za-z_]\w*)", l):
                if e in fields and fld not in fields[e]:
                    self.add("ERROR", "field-missing", d.at(i), f"{e}.{fld} is not a field in TECHNICAL {e}")
        for s, _, blk in blocks:
            if "**States:**" not in blk:
                self.add("ERROR", "screen-no-states", self.where(s), f"{s} has no States line")

    def backlog(self):
        if not self.doc("BACKLOG.md"):
            return
        tasks, deps = {}, {}
        for d in [x for x in self.docs if x.name == "BACKLOG.md"]:
            cur = None
            for i, l in enumerate(d.lines + ["#### end"]):
                m = re.match(r"^##### (T-[\d.]+)", l)
                if m or l.startswith("#"):
                    cur = None
                if m:
                    cur = m.group(1)
                    tasks[cur] = {"doc": d, "line": i, "text": []}
                elif cur:
                    tasks[cur]["text"].append(l)
        covered = set()
        for t, info in tasks.items():
            body = "\n".join(info["text"])
            where = info["doc"].at(info["line"])
            data = next((l for l in info["text"] if l.startswith("|") and not SEP_RE.match(l)
                         and not re.match(r"^\|\s*Size\s*\|", l)), "")
            cells = [c.strip() for c in data.strip().strip("|").split("|")]
            size, executor = (cells + ["", ""])[:2]
            deps[t] = set(ID_RE.findall(cells[4])) if len(cells) > 4 else set()
            cov = re.search(r"^Covers: (.*)$", body, re.M)
            cov_ids = set(ID_RE.findall(cov.group(1))) if cov else set()
            covered |= cov_ids
            if size not in ("S", "M", "L", "XL"):
                self.add("ERROR", "task-size", where, f"{t} size '{size}' not S/M/L/XL")
            if size == "XL":
                self.add("ERROR", "task-xl", where, f"{t} is XL: split it")
            if executor not in ("agent-ready", "human"):
                self.add("ERROR", "task-executor", where, f"{t} executor '{executor}' not agent-ready/human")
            if not cov:
                self.add("ERROR", "task-covers", where, f"{t} has no Covers line")
            if "**Done when**" not in body:
                self.add("ERROR", "task-done-when", where, f"{t} has no Done when")
            if executor != "agent-ready":
                continue
            if "**Context pack**" not in body:
                self.add("ERROR", "task-pack", where, f"{t} agent-ready without Context pack")
                continue
            pack = re.split(r"^\*\*(?:Ready|Done) when\*\*", body.split("**Context pack**", 1)[1], maxsplit=1, flags=re.M)[0]
            missing = [k for k in PACK if not re.search(rf"^- {re.escape(k)}:", pack, re.M)]
            if missing:
                self.add("ERROR", "task-pack", where, f"{t} pack missing: {', '.join(missing)}")
            words = len(pack.split())
            if words > PACK_MAX_WORDS:
                self.add("ERROR", "task-pack-size", where, f"{t} pack {words} words > {PACK_MAX_WORDS}")
            if re.search(r"\b(see above|ver arriba|como se dijo|as discussed)\b", pack, re.I):
                self.add("ERROR", "task-pack-selfcontained", where, f"{t} pack points outside itself")
            if "**Ready when**" not in body:
                self.add("ERROR", "task-dor", where, f"{t} has no Ready when")
            done = body.split("**Done when**", 1)[-1]
            for ac in sorted(i for i in cov_ids if kind(i) == "AC"):
                if not re.search(rf"{re.escape(ac)}\s*(→|->)", done):
                    self.add("ERROR", "task-done-ac", where, f"{t} covers {ac} but Done when has no '{ac} → test'")
        for f in self.mvp_features():
            if not any(u.startswith(f"US-{f[2:]}.") for u in self.defs):
                self.add("ERROR", "feature-no-story", self.where(f), f"MVP {f} has no story")
            for ac in self.acs_of(f):
                if ac not in covered:
                    self.add("ERROR", "ac-uncovered", self.where(ac), f"{ac} covered by no task")
        for sp in self.local("SP"):
            if sp not in covered:
                self.add("ERROR", "spike-no-task", self.where(sp), f"{sp} has no T-00.n task")
        cycle = self.find_cycle(deps)
        if cycle:
            self.add("ERROR", "dependency-cycle", self.where(cycle[0]), " → ".join(cycle))

    @staticmethod
    def find_cycle(graph):
        state = {}

        def visit(n, path):
            state[n] = 1
            for m in graph.get(n, ()):
                if state.get(m) == 1:
                    return path[path.index(m):] + [m] if m in path else [n, m]
                if not state.get(m):
                    c = visit(m, path + [m])
                    if c:
                        return c
            state[n] = 2
            return None

        for n in graph:
            if not state.get(n):
                c = visit(n, [n])
                if c:
                    return c
        return None

    def section(self, d, title):
        out, on = [], False
        for l in d.lines:
            if l.startswith("## "):
                on = title.lower() in l.lower()
            elif on:
                out.append(l)
        return out

    def where(self, i):
        places = [p for p in self.defs.get(i, []) if not p[0].base]
        return places[0][0].at(places[0][1]) if places else str(self.root)

    def run(self):
        self.index()
        self.frontmatter()
        if not self.quick:
            self.dangling()
            self.product()
            self.technical()
            self.design()
            self.backlog()
            self.cascade()
        return self.out

    def model(self):
        feats = self.mvp_features()
        prog = {}
        p = self.root / "PROGRESS.md"
        if p.exists():
            for l in p.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\|\s*(T-[\d.]+)\s*\|\s*(\w[\w-]*)\s*\|", l)
                if m:
                    prog[m.group(1)] = m.group(2)
        docs = {d.name: {k: d.fm.get(k) for k in ("version", "status", "approved_version")}
                for d in self.docs if d.path.parent.name != "backlog"}
        items = {}
        for name in ("PRODUCT.md", "TECHNICAL.md", "DESIGN.md", "BACKLOG.md"):
            for i, ids in self.blocks(name):
                items[i] = {"doc": name, "cites": sorted(ids - {i})}
        titles = {i: re.sub(r"^[#|\- ]+\S+ ·? ?", "", p[0].lines[p[1]]).strip(" |") for i, ps in self.defs.items()
                  for p in ps[:1] if not p[0].base}
        return {"root": str(self.root), "docs": docs, "mvp": feats, "items": items, "titles": titles,
                "progress": prog, "findings": [dict(zip(("level", "code", "where", "msg"), f)) for f in self.out]}


def approve(path):
    path = pathlib.Path(path).resolve()
    if path.name not in ("PRODUCT.md", "TECHNICAL.md", "DESIGN.md", "BACKLOG.md") or path.parent.name == "backlog":
        print("approve: only PRODUCT, TECHNICAL, DESIGN or BACKLOG (epic files are approved with BACKLOG.md)")
        return 2
    lint = Lint(path.parent)
    doc = next((d for d in lint.docs if d.path.resolve() == path), None)
    if not doc or not doc.fm:
        print("approve: no frontmatter")
        return 2
    errors = [f for f in lint.run() if f[0] in ("ERROR", "STALE")]
    if errors:
        report(errors)
        print("approve: refused, fix the errors above first")
        return 1
    raw = path.read_bytes().decode("utf-8-sig")
    eol = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    h = lint.doc_hash(doc)
    end = text.find("\n---", 3)
    head, rest = text[:end], text[end:]
    for k, v in (("status", "approved"), ("approved_version", doc.fm.get("version")), ("approved_hash", h)):
        if re.search(rf"(?m)^{k}:", head):
            head = re.sub(rf"(?m)^{k}:[^\n#]*?(\s+#[^\n]*)?$", lambda m: f"{k}: {v}{m.group(1) or ''}", head, count=1)
        else:
            head += f"\n{k}: {v}"
    path.write_bytes((head + rest).replace("\n", eol).encode("utf-8"))
    print(f"approved {path.name} v{doc.fm.get('version')} · hash {h}")
    return 0


def report(out):
    for level, code, where, msg in out:
        print(f"{level} {code} {where} {msg}")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) >= 2 and argv[0] == "--approve":
        return approve(argv[1])
    if len(argv) >= 2 and argv[0] == "--hash":
        p = pathlib.Path(argv[1]).resolve()
        lint = Lint(p.parent)
        doc = next((d for d in lint.docs if d.path.resolve() == p), None)
        print(lint.doc_hash(doc) if doc else body_hash(split_doc(p.read_text(encoding="utf-8-sig"))[1]))
        return 0
    roots = [a for a in argv if not a.startswith("--")]
    if not roots:
        print(__doc__)
        return 2
    lint = Lint(roots[0], quick="--quick" in argv)
    out = lint.run()
    if "--json" in argv:
        print(json.dumps(lint.model(), ensure_ascii=False, indent=1))
    else:
        report(out)
        n = {k: sum(1 for f in out if f[0] == k) for k in ("ERROR", "WARN", "STALE")}
        print(f"lint: {n['ERROR']} errors · {n['WARN']} warnings · {n['STALE']} stale")
    return 1 if any(f[0] == "ERROR" for f in out) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
