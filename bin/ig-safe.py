#!/usr/bin/env python3
"""Instagram Reels safe-area viewer and checker.

IG draws its own chrome over the reel: status bar and header at the top, the
like/comment/share rail down the right, and username + caption + audio + nav along the
bottom. Anything you burn into those bands is either covered or fights with it.

  ig-safe.py zones                           -> the safe box + the build defaults that fit it
  ig-safe.py view   <reel.mp4> <out.jpg> [t] -> contact sheet with the zones drawn on

Zones are fractions of the 1080x1920 frame, measured against a real posted-reel
screenshot (the "Trial reels" header is what pushed TOP down to 0.14).
"""
import sys, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- safe area, as fractions of the frame -------------------------------------
TOP    = 0.145   # status bar + header ("Reels"/"Trial reels", back arrow, camera)
BOTTOM = 0.200   # username, caption, audio ticker, tab bar
RIGHT  = 0.150   # like / comment / share / more rail
LEFT   = 0.055   # rounded corner + edge margin

W, H = 1080, 1920
def bands():
    return dict(top=int(TOP*H), bottom=int(H-BOTTOM*H), right=int(W-RIGHT*W), left=int(LEFT*W))

FONTS = "/Users/vatsalshah/Code/video-edits/fonts"

def frames(path, times):
    out = []
    for t in times:
        p = subprocess.run(['ffmpeg','-nostdin','-v','error','-ss',str(t),'-i',path,
                            '-frames:v','1','-vf',f'scale={W}:{H}','-f','image2pipe',
                            '-vcodec','png','-'], capture_output=True)
        if p.stdout:
            import io
            out.append((t, Image.open(io.BytesIO(p.stdout)).convert('RGB')))
    return out

def zones():
    """Print the safe box. This is the authoritative check: because we control where
    text is placed, validating the PLACEMENT is exact, whereas detecting burned text
    from pixels alone is not -- white type on a light wall and a blown-out window are
    not separable by any threshold I trust. Use `view` to eyeball, and keep build
    params inside these numbers.
    """
    b = bands()
    print(f"IG safe box on {W}x{H}:")
    print(f"  y {b['top']} .. {b['bottom']}     (top {int(TOP*100)}% = status bar + header,"
          f" bottom {int(BOTTOM*100)}% = username/caption/audio/tabs)")
    print(f"  x {b['left']} .. {b['right']}     (right {int(RIGHT*100)}% = like/comment/share rail)")
    print()
    print("  build defaults that respect it:")
    print("    hook / mid-reel hero text : y 1000..1400  (chest band, below the face)")
    print("    burned captions           : margin_v 500  (baseline ~y1420)")
    print("    overlay cards             : x 690..1040, y 134..745")
    print("    full-width glow type      : keep the BLOOM inside x59..918 (text <= ~690px)")

def view(path, out, times):
    b = bands()
    tiles = []
    lf = ImageFont.truetype(f"{FONTS}/Montserrat-Bold.ttf", 30)
    for t, im in frames(path, times):
        ov = im.convert('RGBA')
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(sh)
        d.rectangle([0, 0, W, b['top']],            fill=(255, 60, 60, 80))
        d.rectangle([0, b['bottom'], W, H],         fill=(255, 60, 60, 80))
        d.rectangle([b['right'], b['top'], W, b['bottom']], fill=(255, 170, 0, 80))
        d.rectangle([0, b['top'], b['left'], b['bottom']],  fill=(255, 170, 0, 60))
        d.rectangle([b['left'], b['top'], b['right'], b['bottom']], outline=(60, 255, 120, 230), width=5)
        # mock the chrome so the collision is obvious
        d.rounded_rectangle([W//2-120, 40, W//2+120, 96], 12, fill=(255,255,255,190))
        for i, cy in enumerate(range(int(H*0.55), int(H*0.80), 108)):
            d.ellipse([W-116, cy, W-56, cy+60], outline=(255,255,255,200), width=5)
        d.rectangle([46, int(H*0.845), 700, int(H*0.885)], fill=(255,255,255,150))
        d.rectangle([46, int(H*0.895), 860, int(H*0.925)], fill=(255,255,255,120))
        ov = Image.alpha_composite(ov, sh)
        dd = ImageDraw.Draw(ov)
        dd.text((18, b['top']+10), "SAFE", font=lf, fill=(60,255,120,255))
        dd.text((18, 12), f"{t:.1f}s  IG header", font=lf, fill=(255,255,255,255))
        tiles.append(ov.convert('RGB').resize((330, 587)))
    cols = min(4, len(tiles)); rows = (len(tiles)+cols-1)//cols
    sheet = Image.new('RGB', (330*cols, 587*rows), (18, 18, 18))
    for i, tl in enumerate(tiles):
        sheet.paste(tl, ((i % cols)*330, (i//cols)*587))
    sheet.save(out, quality=93)
    print(f"wrote {out}")

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'zones':
        zones()
    elif mode == 'view':
        path, out = sys.argv[2], sys.argv[3]
        ts = [float(x) for x in sys.argv[4:]] or [1.5, 5, 26, 45]
        view(path, out, ts)
