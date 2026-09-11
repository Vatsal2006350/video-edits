
Vatsal's rule for montages: **more views, less him — once in Kerala, once in Maldives, looking outward, no mic.** Six reels shipped breaking it because I trusted directory names.

`~/Downloads/photos-broll/maldives-sunset/` is not scenery at all: all 7 clips are one take of him centre-frame, facing camera, holding a mic. Cropping to the sea side does not rescue them (an arm intrudes at anything wider than ~28% of frame width). `kerala-scenic/` is roughly half unusable too — a restaurant interior, a chocolate shop, dark motion blur, and two clips where he is on camera the whole time. `broll/` is Dubai and India, not the US, despite being used as US footage in a first pass.

The Maldives shot he actually wants is `broll/0606_175232_IMG_1863.MOV.MOV` @3.6 — standing, looking out to sea, no mic. It is the closer for nearly every travel reel.

**How to apply:** the per-clip verified seek list lives in `~/Code/video-edits/FOOTAGE.md` — read it before building a montage and add to it when new footage lands. Before putting any unlisted clip in a reel, pull a frame at the exact seek you intend (`ffmpeg -ss <t> -i <clip> -frames:v 1`) and look at it. A clip is not "scenery" because its folder says so, and it is not clean at 6s because it was clean at 2s. Contact-sheet a whole folder at two timestamps per clip when meeting it for the first time. Same discipline as [[verify-rendered-not-intermediate]]; see also [[clip-stability-scanning]] for picking the steadiest window once a clip is known good.
