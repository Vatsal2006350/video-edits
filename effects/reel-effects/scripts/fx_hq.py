"""HQ cut-out for the effect engine: RobustVideoMatting alpha + decontaminated edge colour.

Why: the engine's own matte is MediaPipe selfie_segmenter (256 px model) run on a 540-px frame and
upscaled. On a light wall that leaves a white rim round the hair whenever the room behind is
replaced or darkened (reported 2026-11-12 on ascii-room). Two fixes, both needed:
  1. alpha: RVM resnet50 at full 1080 res (bin/rvm-matte.py), strand-level hair.
  2. edge colour: a semi-transparent hair pixel still contains wall colour. Every "behind you"
     composite here uses  F*alpha + new_room*(1-alpha)  with RVM's foreground colour F, instead of
     src*alpha + new_room*(1-alpha), so no wall survives in the edge.

Use (bin/fx-extra.sh passes the environment through):
    .agents/skills/video-effects/.venv/bin/python bin/rvm-matte.py clip.mp4 clip_rvm.mov --ratio 0.5
    FX_MATTE=clip_rvm.mov [FX_MATTE_SS=<seconds into clip_rvm where this input starts>] bin/fx-extra.sh ...
The matte must be frame-aligned with the input at 30 fps. It is decoded once into a memmap cache
next to the .mov (<name>.cache.npy, delete it when the job is done).
"""
import os, subprocess, numpy as np, cv2
import fx

PATH = os.environ.get('FX_MATTE')
SS = float(os.environ.get('FX_MATTE_SS', '0') or 0)
_mm = None


def _load():
    global _mm
    if _mm is not None: return _mm
    w, h, n = [int(float(x)) for x in subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=width,height,nb_read_packets',
         '-of', 'csv=p=0', PATH], capture_output=True, text=True).stdout.strip().split(',')[:3]]
    cache = PATH.rsplit('.', 1)[0] + '.cache.npy'
    if not (os.path.exists(cache) and os.path.getsize(cache) >= n * h * w * 4):
        print(f'HQ matte: decoding {n} frames of {os.path.basename(PATH)} once...', flush=True)
        mm = np.lib.format.open_memmap(cache + '.part', 'w+', np.uint8, (n, h, w, 4))
        p = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-i', PATH, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], stdout=subprocess.PIPE)
        for i in range(n):
            b = p.stdout.read(w * h * 4)
            if len(b) < w * h * 4: break
            mm[i] = np.frombuffer(b, np.uint8).reshape(h, w, 4)
        p.wait(); mm.flush(); del mm; os.replace(cache + '.part', cache)
    _mm = np.load(cache, mmap_mode='r')
    return _mm


def _attach(c):
    if getattr(c, '_hq', False): return
    c._hq = True
    mm = _load(); i = min(len(mm) - 1, max(0, int(round((SS + c.t) * 30))))
    fr = mm[i]
    if fr.shape[1] != c.W or fr.shape[0] != c.H: fr = cv2.resize(np.ascontiguousarray(fr), (c.W, c.H), interpolation=cv2.INTER_AREA)
    c.m = fr[..., 3].astype(np.float32) / 255.0
    c.F = fr[..., :3].astype(np.float32) / 255.0


def wrap_all():
    for name, (fn, desc) in list(fx.EFFECTS.items()):
        def w(c, e, _fn=fn):
            _attach(c); return _fn(c, e)
        fx.EFFECTS[name] = (w, desc)


_orig_comp = fx.comp
def comp(c, layer, x, y, alpha=1.0, behind=False, guard=False):
    if not (behind and hasattr(c, 'F')): return _orig_comp(c, layer, x, y, alpha, behind, guard)
    L = fx.to_np(layer) if not isinstance(layer, np.ndarray) else layer
    h, w = L.shape[:2]; x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(c.W, x + w), min(c.H, y + h)
    if x1 <= x0 or y1 <= y0 or alpha <= 0: return
    L = L[y0 - y:y1 - y, x0 - x:x1 - x]
    a = L[..., 3:4] * alpha; m = c.m[y0:y1, x0:x1, None]
    dst = c.img[y0:y1, x0:x1]; F = c.F[y0:y1, x0:x1]
    dst[:] = dst * (1 - a) + F * (a * m) + L[..., :3] * (a * (1 - m))


_orig_camera = fx.camera
def camera(c, zoom, cx, cy):
    zoom = min(zoom, 2.0)
    if zoom <= 1.002: return
    if hasattr(c, 'F'):
        cw, ch = c.W / zoom, c.H / zoom
        x0 = fx.clamp(cx - cw / 2, 0, c.W - cw); y0 = fx.clamp(cy - ch / 2, 0, c.H - ch)
        M = np.float32([[zoom, 0, -x0 * zoom], [0, zoom, -y0 * zoom]])
        c.F = cv2.warpAffine(c.F, M, (c.W, c.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return _orig_camera(c, zoom, cx, cy)


def fg(c):
    """Foreground colour for matting composites: RVM's F when loaded, else the frame itself."""
    return c.F if hasattr(c, 'F') else c.img


if PATH:
    fx.comp = comp; fx.camera = camera
    # the extra packs imported these names directly; rebind them there too
    import sys
    for mod in ('fx_world', '__main__', 'fx_extra'):
        m = sys.modules.get(mod)
        if m is None: continue
        if getattr(m, 'comp', None) is _orig_comp: m.comp = comp
        if getattr(m, 'camera', None) is _orig_camera: m.camera = camera
