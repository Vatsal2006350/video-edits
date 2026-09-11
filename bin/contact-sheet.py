#!/usr/bin/env python3
"""Contact-sheet a folder of clips/stills so you can SEE what is in them before building.

Folder names lie: `maldives-sunset` turned out to be seven takes of Vatsal talking to
camera with a mic, and six of the 48 "childhood" stills are his parents. Nothing goes in
a reel until it has been looked at.

  contact-sheet.py <dir> [out.jpg] [--frames N] [--cols N] [--width N]

Samples N frames spread across each clip (stills are sampled once), labels every tile with
its index, and writes an index map next to the sheet so a tile number maps back to a
filename AND the timestamp it was taken at -- that timestamp is the seek you then use.
"""
import sys, os, subprocess, glob, json
from PIL import Image, ImageDraw, ImageFont

VID = ('.mov', '.mp4', '.m4v')
IMG = ('.jpg', '.jpeg', '.png', '.heic')
FONTS = "/Users/vatsalshah/Code/video-edits/fonts/Montserrat-Bold.ttf"

def dur(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', p], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except ValueError: return 0.0

def grab(p, t, w, h, label):
    cmd = ['ffmpeg', '-nostdin', '-v', 'error']
    if t: cmd += ['-ss', f'{t:.2f}']
    cmd += ['-i', p, '-frames:v', '1', '-vf',
            f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
            f"drawtext=text='{label}':fontsize={max(18, w//6)}:fontcolor=yellow:"
            f"borderw=3:bordercolor=black:x=4:y=4",
            '-f', 'image2pipe', '-vcodec', 'png', '-']
    r = subprocess.run(cmd, capture_output=True)
    if not r.stdout: return None
    import io
    return Image.open(io.BytesIO(r.stdout)).convert('RGB')

def main():
    d = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') \
          else os.path.join(d, 'contact-sheet.jpg')
    args = sys.argv[2:]
    def opt(name, dflt):
        return int(args[args.index(name)+1]) if name in args else dflt
    nfr  = opt('--frames', 2)
    cols = opt('--cols', 10)
    w    = opt('--width', 150)
    h    = int(w * 16 / 9)

    files = sorted(f for f in glob.glob(os.path.join(d, '*'))
                   if f.lower().endswith(VID + IMG))
    tiles, index = [], []
    for i, f in enumerate(files, 1):
        if f.lower().endswith(IMG):
            im = grab(f, None, w, h, str(i))
            if im: tiles.append(im); index.append({'tile': len(tiles), 'file': os.path.basename(f), 't': None})
        else:
            D = dur(f)
            for k in range(nfr):
                t = D * (k + 1) / (nfr + 1)
                im = grab(f, t, w, h, f"{i}")
                if im:
                    tiles.append(im)
                    index.append({'tile': len(tiles), 'file': os.path.basename(f), 't': round(t, 1)})
    if not tiles:
        print(f"no readable media in {d}"); return
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (w*cols, h*rows), (16, 16, 16))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols)*w, (i // cols)*h))
    sheet.save(out, quality=88)
    ix = os.path.splitext(out)[0] + '_index.json'
    json.dump(index, open(ix, 'w'), indent=1)
    print(f"{len(files)} files -> {len(tiles)} tiles")
    print(f"  sheet {out}")
    print(f"  index {ix}   (tile -> file + the timestamp that tile was grabbed at)")

if __name__ == '__main__':
    main()
