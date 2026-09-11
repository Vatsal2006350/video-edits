# Shared filter for putting a STILL on a video frame without distorting it.
#
# The old filter was `scale=W2:-1,zoompan=...:s=WxH`, which is wrong: zoompan's `s` forces
# the output size, so a 4:3 photo pushed into 9:16 gets stretched vertically. It squashed
# every YC-sign card in the batch. Cropping to 9:16 instead would be undistorted but cuts
# people out of a wide group shot, so: letterbox the real photo over a blurred, darkened
# copy of itself. Nothing is stretched and nothing is lost.
#
#   still_vf <out_w> <out_h> [zoom_rate] [zoom_max]
still_vf () {
  local w="${1:?w}" h="${2:?h}" rate="${3:-0.0012}" zmax="${4:-1.14}"
  printf '%s' "split=2[bg][fg];\
[bg]scale=${w}:${h}:force_original_aspect_ratio=increase,crop=${w}:${h},gblur=sigma=40,eq=brightness=-0.12:saturation=0.60[b];\
[fg]scale=${w}:${h}:force_original_aspect_ratio=decrease[f];\
[b][f]overlay=(W-w)/2:(H-h)/2,\
zoompan=z='min(1.0+${rate}*on,${zmax})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=${w}x${h}:fps=30,fps=30"
}

# Cover-crop variant: fills the box, trims the overflow, never distorts. Use it when the
# subject is a single face that should fill the frame (childhood portraits, diptych halves)
# and losing the edges costs nothing. Use still_vf instead when the whole image matters --
# a group shot, a screenshot, a sign.
#
#   still_cover_vf <out_w> <out_h> [zoom_rate] [zoom_max]
still_cover_vf () {
  local w="${1:?w}" h="${2:?h}" rate="${3:-0.0014}" zmax="${4:-1.16}"
  printf '%s' "scale=$((w*2)):$((h*2)):force_original_aspect_ratio=increase,crop=$((w*2)):$((h*2)),\
zoompan=z='min(1.0+${rate}*on,${zmax})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=${w}x${h}:fps=30,fps=30"
}

# Plain black bars instead of the blurred-copy backdrop. Vatsal on the YC photo: "even in
# the background it shows them, don't do that" -- the blur reads as a ghost of the same
# image. Black is cleaner whenever the photo is the whole point.
#
#   still_black_vf <out_w> <out_h> [zoom_rate] [zoom_max]
still_black_vf () {
  local w="${1:?w}" h="${2:?h}" rate="${3:-0.0012}" zmax="${4:-1.14}"
  printf '%s' "scale=${w}:${h}:force_original_aspect_ratio=decrease,\
pad=${w}:${h}:(ow-iw)/2:(oh-ih)/2:black,\
zoompan=z='min(1.0+${rate}*on,${zmax})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=${w}x${h}:fps=30,fps=30"
}
