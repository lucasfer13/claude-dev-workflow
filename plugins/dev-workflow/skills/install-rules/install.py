"""Install or update the dev-workflow rules into ~/.claude (CLAUDE.md block, references, scripts, config).

Usage: python install.py [--dry-run]
"""
import datetime
import pathlib
import shutil
import sys

PLUGIN = pathlib.Path(__file__).resolve().parents[2]
RULES = PLUGIN / "rules"
CLAUDE = pathlib.Path.home() / ".claude"
TARGET = CLAUDE / "dev-workflow"
START, END = "<!-- dev-workflow:start -->", "<!-- dev-workflow:end -->"


def block():
    text = (RULES / "CLAUDE.md").read_text(encoding="utf-8")
    i, j = text.index(START), text.index(END) + len(END)
    return text[i:j]


def main(dry):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    md = CLAUDE / "CLAUDE.md"
    current = md.read_text(encoding="utf-8") if md.exists() else ""
    new_block = block()
    if START in current and END in current:
        i, j = current.index(START), current.index(END) + len(END)
        updated, action = current[:i] + new_block + current[j:], "replaced"
    else:
        updated, action = (current.rstrip() + "\n\n" if current.strip() else "") + new_block + "\n", "appended"
    print(f"CLAUDE.md: rules block {action} ({len(new_block.encode())} bytes)")
    if not dry:
        CLAUDE.mkdir(parents=True, exist_ok=True)
        if md.exists():
            shutil.copy2(md, CLAUDE / f"CLAUDE.md.bak.{stamp}")
            print(f"  backup: CLAUDE.md.bak.{stamp}")
        md.write_text(updated, encoding="utf-8")

    for sub in ("reference", "scripts"):
        for f in sorted((RULES / sub).glob("*")):
            print(f"{sub}/{f.name} -> {TARGET / sub / f.name}")
            if not dry:
                (TARGET / sub).mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, TARGET / sub / f.name)

    cfg = CLAUDE / "dev-workflow.json"
    if cfg.exists():
        print("dev-workflow.json: kept (already exists)")
    else:
        print("dev-workflow.json: created from config.example.json — edit it")
        if not dry:
            shutil.copy2(PLUGIN / "config.example.json", cfg)


if __name__ == "__main__":
    main("--dry-run" in sys.argv)
