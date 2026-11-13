#!/usr/bin/env python3
"""Fill the generated gallery blocks in README.md from gallery/*.json.

Edit the JSON, then run `python3 bin/build-readme.py`. The README text outside the
<!-- x:start --> / <!-- x:end --> markers is hand-written and is left alone.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
GALLERY = ROOT / "gallery"
COLS = 4


def load(name, key="items"):
    data = json.loads((GALLERY / name).read_text(encoding="utf-8"))
    return data[key] if key else data


def esc(text):
    return html.escape(str(text), quote=True)


def reels_block(reels, folder_url=None):
    live = [dict(r, watch_url=r.get("watch_url") or folder_url) for r in reels]
    live = [r for r in live if r["watch_url"]]
    if not live:
        return "<!-- no reels published yet: set watch_url in gallery/reels.json -->"
    rows = []
    for i in range(0, len(live), 3):
        cells = []
        for r in live[i:i + 3]:
            cells.append(
                f'<td width="33%" valign="top"><a href="{esc(r["watch_url"])}">'
                f'<img src="{esc(r["thumb"])}" alt="{esc(r["title"])}" width="100%"></a><br>'
                f'<a href="{esc(r["watch_url"])}"><b>{esc(r["title"])}</b></a><br>'
                f'<sub>{esc(r["look"])} · {r["duration_s"]:.0f}s</sub></td>'
            )
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def looks_block(looks):
    cells = []
    for lk in looks:
        tool = lk.get("tool", "").split(" ")[0] if lk.get("tool") else ""
        badge = "runs here" if lk.get("runs_here") else "preview"
        cells.append(
            f'<td width="25%" valign="top"><a href="{esc(lk["clip"])}">'
            f'<img src="{esc(lk["poster"])}" alt="{esc(lk["name"])}" width="100%"></a><br>'
            f'<b>{esc(lk["name"])}</b><br>'
            f'<sub>{esc(lk["kind"])} · {badge}{(" · " + esc(tool)) if tool else ""}</sub></td>'
        )
    rows = []
    for i in range(0, len(cells), COLS):
        rows.append("<tr>" + "".join(cells[i:i + COLS]) + "</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def replace_block(text, name, body):
    pattern = re.compile(rf"(<!-- {name}:start -->)(.*?)(<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"README is missing the {name} markers")
    return pattern.sub(lambda m: m.group(1) + "\n" + body + "\n" + m.group(3), text)


def main():
    looks = load("looks.json")
    reels_doc = load("reels.json", key=None)
    reels = reels_doc["items"]
    text = README.read_text(encoding="utf-8")
    text = replace_block(text, "reels", reels_block(reels, reels_doc.get("folder_url")))
    text = replace_block(text, "looks", looks_block(looks))
    text = re.sub(r"\d+ looks", f"{len(looks)} looks", text)
    README.write_text(text, encoding="utf-8")
    live = sum(1 for r in reels if r.get("watch_url"))
    print(f"README updated: {len(looks)} looks, {live}/{len(reels)} reels with a watch link")


if __name__ == "__main__":
    main()
