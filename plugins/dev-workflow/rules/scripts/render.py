"""Render a development trace (<id>.trace.md) into a self-contained HTML page for an Artifact.

Usage: python render.py <trace.md> <out.html>
"""
import datetime
import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
MARKS = {"✔": "ok", "✘": "fail", "⚠": "warn", "–": "na", "-": "na"}
HEAD = re.compile(r"^##\s+(?:(?P<time>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2})\s*·\s*)?(?P<from>.+?)\s*→\s*(?P<to>[^·]+?)\s*(?:·.*)?$")
FIELD = re.compile(r"^(?P<k>[A-Za-zÁÉÍÓÚáéíóúñ ]{2,20}):\s*(?P<v>.*)$")
KEYS = {"hecho": "done", "agente": "agent", "intentos": "attempts", "siguiente": "next",
        "done": "done", "agent": "agent", "attempts": "attempts", "next": "next"}
CRITERIA = {"criterios", "criteria"}
REVIEW = {"para revisar", "review"}


def parse(text):
    meta, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            for line in text[3:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
            body = text[end + 4:]
    blocks, cur, section = [], None, None
    for raw in body.splitlines():
        line = raw.rstrip()
        m = HEAD.match(line)
        if m:
            cur = {"time": m["time"] or "", "from": m["from"].strip(), "to": m["to"].strip().upper(),
                   "agent": "", "done": "", "criteria": [], "attempts": "", "review": [], "next": "", "extra": []}
            blocks.append(cur)
            section = None
            continue
        if cur is None or not line.strip():
            continue
        item = re.match(r"^\s*[-*]\s+(.*)$", line)
        if item and section in ("criteria", "review"):
            t = item[1].strip()
            if section == "criteria":
                state = MARKS.get(t[:1], "warn")
                t = t[1:].strip() if t[:1] in MARKS else t
                cur["criteria"].append({"state": state, "text": t})
            else:
                cur["review"].append(t)
            continue
        f = FIELD.match(line.strip())
        if f:
            k, v = f["k"].strip().lower(), f["v"].strip()
            if k in CRITERIA:
                section = "criteria"
            elif k in REVIEW:
                section = "review"
                if v:
                    cur["review"].append(v)
            elif k in KEYS:
                section = None
                cur[KEYS[k]] = v
            else:
                section = None
                cur["extra"].append({"k": f["k"].strip(), "v": v})
    return meta, blocks


def main(src, out):
    src_path = pathlib.Path(src)
    meta, blocks = parse(src_path.read_text(encoding="utf-8"))
    meta["source"] = src_path.name
    data = {"meta": meta, "blocks": blocks,
            "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    title = "Trace " + meta.get("development_id", src_path.stem.replace(".trace", ""))
    page = (HERE / "template.html").read_text(encoding="utf-8")
    page = page.replace("__TITLE__", html.escape(title)).replace("__DATA__", payload)
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(out).write_text(page, encoding="utf-8")
    print(f"{out} · {len(blocks)} blocks")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
