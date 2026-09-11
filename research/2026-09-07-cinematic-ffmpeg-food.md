# Cinematic phone-food techniques in ffmpeg (agent research, 2026-09-07) -- condensed, tested syntax noted where used

HDR first: `ffprobe ... color_transfer`; arib-std-b67 = HLG -> tonemap before grading:
`zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p`.
Grade A (warm, skin-safe): eq=contrast=1.06:saturation=1.05, colorbalance rs=.03 bs=-.05 rm=.05 bm=-.04 rh=.03 bh=-.02 pl=1,
selectivecolor reds='-0.10 0 0.05 0' yellows='0 0 0.10 0', vibrance=intensity=0.25:rbal=1.3:bbal=0.7, curves m='0/0 0.25/0.22
0.5/0.52 0.75/0.79 1/1', vignette=angle=PI/5.5. Never eq=saturation>1.2 on faces; selectivecolor |values| <= 0.15.
Grade B (film): lifted blacks curves m='0/0.035 ...', halation = lutyuv threshold>200 -> gblur sigma 22 -> colorchannelmixer
rr=1 gg=.45 bb=.30 -> blend screen 0.30, then noise=c0s=7:c0f=t+u (luma-only temporal grain, LAST), vignette.
Grade C: lut3d (free .cube: Luttie "Faded Kodak", Presetpro Portra 800) with split/blend opacity as strength.
Slow-mo: setpts alone only for 60/120fps sources (2x/4x); 30fps needs minterpolate mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,
cap at 2x, mb_size=8 for steam, scd=none inside one shot; diffuse steam -> mi_mode=blend. Ramp = trim segments at 1.5x / 0.4x /
1.5x concat, or a single eased setpts expression + minterpolate.
Push-in: upscale 3x first then zoompan z='min(1+0.0009*on,1.12)' d=1 s=1080x1920 (aspect must match); or per-frame crop with a
smoothstep. Stabilise: vidstabdetect shakiness=6 -> vidstabtransform smoothing=15 optzoom=1 zoomspeed=0.25 (iPhone already OIS;
smoothing>20 goes floaty); stabilise BEFORE zoompan.
Sound: freesound (CC0 / CC BY / CC BY-NC per file), Pixabay (no credit, commercial OK), Mixkit (check "Restricted"). Levels:
master -14 LUFS / -1 dBTP; dialogue -6..-12 dBFS; sizzle/ambience beds -16..-20; hits -8..-12 for 100-300ms; music 12-14 dB under
voice with ducking; anything under -24 dBFS vanishes on phone speakers. adelay=ms:all=1, amix normalize=0, sidechaincompress.
Lower third: serif title 64-80px (Playfair / DM Serif Display / Instrument Serif / Fraunces) + light sans 30-36px caps sub-line
(DM Sans / Inter / Montserrat Light), white, 2px soft shadow, no box; title baseline y 1380-1440, sub y 1460-1500, x 80, nothing
right of x 918; rise 28px over 0.4s smoothstep + alpha fade (drawtext alpha expr, or PNG + overlay for tracking).
Transitions that survive IG's 2-5 Mbps re-encode: hard cuts on the beat, 0.15-0.3s high-contrast moves (xfade hblur 0.25s,
zoomin 0.2s, tmix=frames=5 smear before an hblur), fast bright light leak via blend screen 0.3s; NOT slow dissolves over dark
plates. xfade needs identical size/pix_fmt/fps/timebase (fps=30,settb=AVTB,format=yuv420p first). Final: H.264 High, crf 18,
maxrate 12M, yuv420p, 30fps, g=60, AAC 192k 48k.
