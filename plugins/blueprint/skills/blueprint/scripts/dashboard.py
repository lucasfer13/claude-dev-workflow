"""Render the read-only blueprint dashboard (HTML body for the Artifact tool) from a blueprint folder.

  dashboard.py <root> <out.html> [--lang es|en]
"""
import html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from blueprint_lint import ID_RE, Lint  # noqa: E402

T = {
    "en": dict(product="Product", technical="Technical", design="Design", backlog="Backlog", mvp="MVP",
               lint="Lint", errors="errors", warnings="warnings", stale="stale", progress="Progress",
               done="done", tasks="tasks", trace="Traceability", feature="Feature", criteria="Criteria",
               screens="Screens", stories="Stories", tested="With named test", sprints="Sprints",
               findings="Open findings", none="None", missing="not started", noprogress="No task closed yet",
               goal="Goal", items="Items", appr="approved"),
    "es": dict(product="Producto", technical="Técnico", design="Diseño", backlog="Backlog", mvp="MVP",
               lint="Lint", errors="errores", warnings="avisos", stale="obsoletos", progress="Progreso",
               done="hechas", tasks="tareas", trace="Trazabilidad", feature="Funcionalidad", criteria="Criterios",
               screens="Pantallas", stories="Historias", tested="Con test nombrado", sprints="Sprints",
               findings="Hallazgos abiertos", none="Ninguno", missing="sin empezar", noprogress="Ninguna tarea cerrada aún",
               goal="Objetivo", items="Elementos", appr="aprob."),
}

CSS = """
:root{--paper:#f5f7fa;--surface:#fff;--ink:#1c2330;--muted:#5b6678;--line:#d8dee8;--accent:#2451b7;
--accent-soft:#e3eafb;--ok:#2e7d4f;--warn:#a86a12;--crit:#b83227;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0f141d;--surface:#161d2a;--ink:#e3e8f1;
--muted:#9aa6ba;--line:#2a3447;--accent:#82a6ff;--accent-soft:#1d2a47;--ok:#5cc58a;--warn:#e0a84a;--crit:#f07a6e;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#0f141d;--surface:#161d2a;--ink:#e3e8f1;--muted:#9aa6ba;--line:#2a3447;--accent:#82a6ff;
--accent-soft:#1d2a47;--ok:#5cc58a;--warn:#e0a84a;--crit:#f07a6e;color-scheme:dark}
body{background:var(--paper);color:var(--ink);font:15px/1.5 "IBM Plex Sans",system-ui,sans-serif;padding:0 16px}
main{max-width:1180px;margin:0 auto;padding-block:28px 48px;display:grid;gap:28px}
h1,h2{font-family:"IBM Plex Sans Condensed","Arial Narrow",sans-serif;text-wrap:balance;margin:0}
h1{font-size:30px;font-weight:600}h2{font-size:19px;font-weight:600}
.eyebrow{font:500 12px/1 "IBM Plex Mono",ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.sub{color:var(--muted)}
.phases{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.phase{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:14px 16px;display:grid;gap:6px}
.phase b{font-family:"IBM Plex Sans Condensed",sans-serif;font-size:17px}
.pill{display:inline-block;font:500 12px/1.6 "IBM Plex Mono",monospace;padding:0 8px;border-radius:99px;border:1px solid currentColor;width:max-content}
.approved{color:var(--ok)}.draft{color:var(--warn)}.skipped,.missing{color:var(--muted)}.crit{color:var(--crit)}
.strip{display:flex;flex-wrap:wrap;gap:8px 20px;font-variant-numeric:tabular-nums}
.bar{height:10px;background:var(--accent-soft);border-radius:99px;overflow:hidden}.bar i{display:block;height:100%;background:var(--accent)}
.scroll{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font:500 12px "IBM Plex Mono",monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
tr:last-child td{border-bottom:0}
code,.id{font:13px "IBM Plex Mono",ui-monospace,monospace}
.chips{display:flex;flex-wrap:wrap;gap:4px}.chip{font:12px "IBM Plex Mono",monospace;padding:1px 6px;border-radius:4px;background:var(--accent-soft);color:var(--ink)}
.chip.done{background:var(--ok);color:var(--surface)}.chip.in-progress{outline:1px solid var(--accent)}.chip.blocked{background:var(--crit);color:var(--surface)}
svg text{fill:var(--muted);font:11px "IBM Plex Mono",monospace}
section{display:grid;gap:12px}
"""


def esc(s):
    return html.escape(str(s if s is not None else ""))


def table_rows(path, first):
    if not path.exists():
        return []
    rows = []
    for l in path.read_text(encoding="utf-8").splitlines():
        if re.match(rf"^\| ?{first}", l):
            rows.append([c.strip() for c in l.strip().strip("|").split("|")])
    return rows


def burnup(root, total, t):
    pts = {}
    for r in table_rows(root / "PROGRESS.md", r"T-"):
        if len(r) >= 6 and r[1] == "done" and re.match(r"\d{4}-\d{2}-\d{2}", r[5]):
            pts[r[5]] = pts.get(r[5], 0) + 1
    if not pts or not total:
        return f'<p class="sub">{t["noprogress"]}</p>'
    dates, acc, cum = sorted(pts), 0, []
    for d in dates:
        acc += pts[d]
        cum.append(acc)
    w, h, pad = 640, 160, 34
    x = lambda i: pad + (w - 2 * pad) * (i / max(len(dates) - 1, 1))
    y = lambda v: h - pad + 8 - (h - pad) * v / total
    line = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(cum))
    area = f"{x(0):.1f},{y(0):.1f} {line} {x(len(cum) - 1):.1f},{y(0):.1f}"
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="burn-up" style="width:100%;max-width:{w}px">'
            f'<line x1="{pad}" x2="{w - pad}" y1="{y(total):.1f}" y2="{y(total):.1f}" stroke="var(--line)" stroke-dasharray="4 4"/>'
            f'<text x="{w - pad}" y="{y(total) - 6:.1f}" text-anchor="end">{total}</text>'
            f'<polygon points="{area}" fill="var(--accent-soft)"/>'
            f'<polyline points="{line}" fill="none" stroke="var(--accent)" stroke-width="2"/>'
            f'<circle cx="{x(len(cum) - 1):.1f}" cy="{y(cum[-1]):.1f}" r="4" fill="var(--accent)"/>'
            f'<text x="{pad}" y="{h - 4}">{esc(dates[0])}</text><text x="{w - pad}" y="{h - 4}" text-anchor="end">{esc(dates[-1])}</text>'
            f'</svg>')


def render(root, lang):
    t = T.get(lang, T["en"])
    lint = Lint(root)
    lint.run()
    m = lint.model()
    root = pathlib.Path(root)
    project = next((d.fm.get("project") for d in lint.docs if d.fm.get("project")), root.name)
    mode = next((d.fm.get("mode") for d in lint.docs if d.fm.get("mode")), "new")
    tasks = sorted(i for i in m["items"] if i.startswith("T-"))
    prog = m["progress"]
    done = sum(1 for x in tasks if prog.get(x) == "done")
    phases = ""
    for key, name in (("product", "PRODUCT.md"), ("technical", "TECHNICAL.md"), ("design", "DESIGN.md"), ("backlog", "BACKLOG.md")):
        d = m["docs"].get(name)
        st = d["status"] if d else "missing"
        label = t["missing"] if not d else st
        ver = f'v{esc(d["version"])}' + (f' · {t["appr"]} v{esc(d["approved_version"])}' if d and d["approved_version"] not in (None, "null") else "") if d else ""
        phases += f'<div class="phase"><b>{t[key]}</b><span class="pill {esc(st)}">{esc(label)}</span><span class="sub id">{ver}</span></div>'
    counts = {k: sum(1 for f in m["findings"] if f["level"] == k) for k in ("ERROR", "WARN", "STALE")}
    tests = set()
    for d in lint.docs:
        if d.name == "BACKLOG.md":
            tests |= set(re.findall(r"(AC-F\d+-\d+)\s*(?:→|->)\s*test", d.body))
    rows = ""
    feats = sorted(i for i in m["items"] if re.fullmatch(r"F-\d+", i))
    for f in feats:
        acs = [a for a in sorted(lint.defs) if a.startswith(f"AC-{f.replace('-', '')}-")]
        scr = sorted(i for i, v in m["items"].items() if i.startswith("S-") and f in v["cites"])
        us = sorted(i for i in m["items"] if i.startswith(f"US-{f[2:]}."))
        ts = [x for x in tasks if x.startswith(f"T-{f[2:]}.")]
        chips = "".join(f'<span class="chip {esc(prog.get(x, ""))}" title="{esc(m["titles"].get(x, ""))}">{esc(x)}</span>' for x in ts)
        mvp = f' <span class="pill approved">{t["mvp"]}</span>' if f in m["mvp"] else ""
        rows += (f'<tr><td><span class="id">{esc(f)}</span>{mvp}<br>{esc(m["titles"].get(f, ""))}</td>'
                 f'<td class="id">{len(acs)}</td><td class="id">{sum(1 for a in acs if a in tests)}/{len(acs)}</td>'
                 f'<td class="id">{esc(", ".join(scr)) or "—"}</td><td class="id">{esc(", ".join(us)) or "—"}</td>'
                 f'<td><div class="chips">{chips or "—"}</div></td></tr>')
    sprint_rows = "".join(f'<tr><td class="id">{esc(r[0])}</td><td>{esc(r[1])}</td><td class="id">{esc(r[2])}</td></tr>'
                          for r in table_rows(root / "BACKLOG.md", r"S\d") if len(r) >= 3)
    open_f = [r for r in table_rows(root / "REVIEW.md", r"RV-") if len(r) >= 7 and r[6].startswith("open")]
    find_rows = "".join(f'<tr><td class="id">{esc(r[0])}</td><td class="{"crit" if r[1] == "BLOCKER" else "draft"}">{esc(r[1])}</td>'
                        f'<td class="id">{esc(r[2])}</td><td>{esc(r[3])}</td></tr>' for r in open_f)
    pct = int(100 * done / len(tasks)) if tasks else 0
    return f"""<title>{esc(project)} blueprint</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>{CSS}</style>
<main>
<header style="display:grid;gap:6px"><span class="eyebrow">blueprint · {esc(mode)}</span><h1>{esc(project)}</h1>
<div class="strip sub"><span>{t["lint"]}: <b class="{"crit" if counts["ERROR"] else "approved"}">{counts["ERROR"]} {t["errors"]}</b></span>
<span>{counts["WARN"]} {t["warnings"]}</span><span>{counts["STALE"]} {t["stale"]}</span></div></header>
<div class="phases">{phases}</div>
<section><h2>{t["progress"]}</h2><div class="strip"><span class="id">{done}/{len(tasks)} {t["tasks"]} {t["done"]} · {pct}%</span></div>
<div class="bar"><i style="width:{pct}%"></i></div>{burnup(root, len(tasks), t)}</section>
<section><h2>{t["trace"]}</h2><div class="scroll"><table><thead><tr><th>{t["feature"]}</th><th>{t["criteria"]}</th><th>{t["tested"]}</th>
<th>{t["screens"]}</th><th>{t["stories"]}</th><th>{t["tasks"]}</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section><h2>{t["sprints"]}</h2><div class="scroll"><table><thead><tr><th>Sprint</th><th>{t["goal"]}</th><th>{t["items"]}</th></tr></thead>
<tbody>{sprint_rows or f'<tr><td colspan="3">{t["none"]}</td></tr>'}</tbody></table></div></section>
<section><h2>{t["findings"]}</h2><div class="scroll"><table><tbody>{find_rows or f'<tr><td>{t["none"]}</td></tr>'}</tbody></table></div></section>
</main>
"""


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    i = argv.index("--lang") if "--lang" in argv else -1
    lang = argv[i + 1] if 0 <= i < len(argv) - 1 else "en"
    out = pathlib.Path(argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(argv[0], lang), encoding="utf-8")
    print(f"dashboard: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
