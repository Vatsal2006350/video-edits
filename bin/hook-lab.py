#!/usr/bin/env python3
"""Hook lab: one clip -> N versions that differ ONLY in the first seconds, for matched Trial Reels.

    bin/hook-lab.py <rec709 clip.mp4> --text "PROOF" --slug masla-proof              # stills sheet only (look first)
    bin/hook-lab.py <rec709 clip.mp4> --text "PROOF" --slug masla-proof --render     # writes the variants
    options: --variants control,halftone,neon,speed,halo,ascii,tear,vhs   --len 2.2   --date "AUG 20 2026"
             --proof <image>  (tear shows this image instead of the word)

Why: the 2026-11-12 audit (analytics/ig-audit-2026-11-12.md) showed median avg-watch 6-7 s on the
long tail vs 8.1-11.5 s on every reel over 20K, and the Sept deep dive tied that to the first frame. A hook
test is only a test when one thing changes, so every variant shares the same cut, audio, caption
and length; only the opening treatment differs. `experiment.json` records the cell for
trial-reel-learning.py. Nothing here publishes.

Output: ~/Downloads/reel-batch/hook-lab/<slug>/<slug>_hook-<variant>.mp4 (+ sheet, experiment.json).
Each variant still needs bin/export-ig.sh and ig-safe before it is queued.
"""
import argparse, json, os, shutil, subprocess, sys, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FX = str(ROOT / "bin/fx-extra.sh")


def variants(a):
    L, t = a.len, a.text
    v = {
        "control": [],
        "halftone": [dict(fx="halftone-pop", start=0, end=L, text=t)],
        "neon": [dict(fx="neon-trace", start=0, end=L)],
        "speed": [dict(fx="chroma-quake", start=0, end=0.35), dict(fx="speed-lines", start=0.05, end=min(L, 0.9))],
        "halo": [dict(fx="halo-rays", start=0, end=L)],
        "ascii": [dict(fx="ascii-room", start=0, end=L)],
        "tear": [dict(fx="paper-tear", start=0.15, end=L, at=0.66, open=0.15, **({"image": a.proof} if a.proof else {"text": t}))],
    }
    if a.date: v["vhs"] = [dict(fx="vhs-tape", start=0, end=L, text=a.date)]
    return v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clip"); ap.add_argument("--text", required=True, help="the hook word(s), | between lines; his words only")
    ap.add_argument("--slug", required=True); ap.add_argument("--variants", default="control,halftone,neon,speed,halo,tear")
    ap.add_argument("--len", type=float, default=2.2); ap.add_argument("--date", default=""); ap.add_argument("--proof", default="")
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    clip = Path(a.clip).expanduser().resolve()
    if not clip.is_file(): sys.exit(f"missing clip: {clip}")
    tr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer", "-of", "csv=p=0", str(clip)],
                        capture_output=True, text=True).stdout.strip()
    if tr in ("arib-std-b67", "smpte2084"): sys.exit("clip is HLG/PQ: run bin/color-normalize.sh raw first (CLAUDE.md rule)")
    table = variants(a); names = [n.strip() for n in a.variants.split(",") if n.strip()]
    bad = [n for n in names if n not in table]
    if bad: sys.exit(f"unknown variant(s) {bad}; have {sorted(table)}" + ("" if a.date else " (vhs needs --date)"))
    out = Path.home() / "Downloads/reel-batch/hook-lab" / a.slug; out.mkdir(parents=True, exist_ok=True)
    work = out / "plans"; work.mkdir(exist_ok=True)
    made = []
    for n in names:
        plan = work / f"{n}.json"; plan.write_text(json.dumps({"effects": table[n]}, indent=1))
        dst = out / f"{a.slug}_hook-{n}.mp4"
        if not a.render:
            if not table[n]: continue
            png = work / f"{n}.png"
            mid = ",".join(f"{t:.2f}" for t in (0.25, a.len * 0.5))
            r = subprocess.run([FX, "--plan", str(plan), str(clip), str(png), "--still", mid], capture_output=True, text=True)
            if r.returncode: sys.exit(f"{n}: {r.stderr[-600:]}")
            made.append((n, sorted(work.glob(f"{n}_*.png"))))
            continue
        if dst.exists(): print(f"keep (exists, never overwrite): {dst.name}"); made.append((n, dst)); continue
        if not table[n]:
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(clip), "-vf", "scale=1080:-2", "-c:v", "libx264", "-crf", "17",
                            "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dst)], check=True)
        else:
            r = subprocess.run([FX, "--plan", str(plan), str(clip), str(dst)], capture_output=True, text=True)
            if r.returncode: sys.exit(f"{n}: {r.stderr[-600:]}")
        made.append((n, dst)); print("rendered", dst)
    if not a.render:
        from PIL import Image, ImageDraw
        tiles = [(n, Image.open(f).convert("RGB").resize((270, 480))) for n, fs in made for f in fs]
        sheet = Image.new("RGB", (278 * len(tiles), 510), (18, 18, 18)); d = ImageDraw.Draw(sheet)
        for i, (n, im) in enumerate(tiles): sheet.paste(im, (i * 278, 30)); d.text((i * 278 + 6, 8), n, fill=(255, 255, 255))
        p = out / f"{a.slug}_hook-sheet.jpg"; sheet.save(p, quality=88)
        print(f"CHECK SHEET: {p}\nLook at it, drop weak variants with --variants, then add --render.")
        return
    exp = dict(slug=a.slug, created=dt.datetime.now().astimezone().isoformat(timespec="seconds"), source=str(clip),
               variable="opening treatment, first %.1f s" % a.len, held_constant=["cut", "audio", "caption", "length", "post slot (post within the same hour band)"],
               hook_text=a.text, cells=[dict(variant=n, file=str(f), plan=table[n]) for n, f in made],
               read_at=["24h", "72h", "7d"], gates=dict(avg_watch_s=">= 9 (every reel over 20K views sits at 8.1-11.5)",
                                                         shares_per_reach=">= 1%", saves_per_reach=">= 1% for utility"),
               note="Trial-publish manually. A cell wins only if it beats control on two gates at the same age.")
    (out / "experiment.json").write_text(json.dumps(exp, indent=1))
    print(f"{len(made)} variants -> {out}\nnext: bin/export-ig.sh each, ig-safe view, then queue as Trial Reels with experiment.json's cell in publish.json")


if __name__ == "__main__":
    main()
