#!/usr/bin/env python3
"""Visual energy pass on a finished 1080x1920 reel: whip-pan transitions + punch-in zooms (+ optional B&W flash).

  python3 bin/energy-pass.py in.mp4 out.mp4 --whips 5.10,11.18 --punches 4.03,22.45 [--bw 9.0:0.6] [--audio mix.wav]

whip   : last 0.10 s before the cut slides out left with horizontal motion blur, the new shot slides in from the right
         over 0.12 s with the blur settling (pair with sfx-auto "whips"/"cuts").
punch  : snap zoom to 1.10x on the beat, eases back to 1.0 over ~0.35 s (pair with pops/slams).
bw     : black-and-white flash start:duration (the reference's "as a YOUNG" beat).
Base zoom is 1.04 so slides never show an edge; the IG safe box (59px side margin) still holds.
Never overwrites; writes a new file.
"""
import os, subprocess, sys

args = sys.argv[1:]
src, out = args[0], args[1]
opt = lambda k: args[args.index(k) + 1] if k in args else ''
whips = [float(x) for x in opt('--whips').split(',') if x]
punch = [float(x) for x in opt('--punches').split(',') if x]
bws = [tuple(map(float, x.split(':'))) for x in opt('--bw').split(',') if x]
audio = opt('--audio')
if os.path.exists(out): sys.exit(f'refusing to overwrite {out}')

PRE, POST, SHIFT = 0.10, 0.12, 170          # whip window and max slide (px)
# zoom(t): base 1.04 + punches
zt = '1.04' + ''.join(f'+0.10*exp(-(t-{p:.3f})/0.16)*gte(t,{p:.3f})' for p in punch)
# horizontal slide for whips
sh = ''.join(f"+if(between(t,{w-PRE:.3f},{w:.3f}),-{SHIFT}*pow((t-{w-PRE:.3f})/{PRE},2),0)"
             f"+if(between(t,{w:.3f},{w+POST:.3f}),{SHIFT}*pow(1-(t-{w:.3f})/{POST},2),0)" for w in whips) or '+0'
blur_en = '+'.join(f'between(t,{w-PRE:.3f},{w+POST*0.8:.3f})' for w in whips) or '0'
bw_en = '+'.join(f'between(t,{a:.3f},{a+d:.3f})' for a, d in bws) or '0'
vf = (f"scale=w='1080*({zt})':h=-2:eval=frame:flags=bicubic,"
      f"crop=1080:1920:x='max(0,min(iw-1080,(iw-1080)/2{sh}))':y='(ih-1920)/2',"
      f"avgblur=sizeX=46:sizeY=1:enable='{blur_en}',"
      f"hue=s=0:enable='{bw_en}',setsar=1,format=yuv420p")
cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', src]
if audio: cmd += ['-i', audio]
cmd += ['-vf', vf, '-map', '0:v', '-map', '1:a' if audio else '0:a?', '-c:v', 'libx264', '-crf', '15', '-preset', 'slow',
        '-pix_fmt', 'yuv420p', '-r', '30', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
        '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode: sys.exit(r.stderr[-1500:])
print(out, f'whips={len(whips)} punches={len(punch)} bw={len(bws)}')
