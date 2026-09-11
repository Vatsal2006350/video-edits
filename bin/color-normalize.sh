#!/usr/bin/env bash
# Reusable Rec.709 color handling for the reel factory.
#
#   color-normalize.sh inspect <video>
#   color-normalize.sh raw <input> <output>
#   color-normalize.sh retag <display-ready-input> <output>
#
# `raw` tonemaps tagged HLG/PQ pixels and encodes a Rec.709 H.264 intermediate.
# `retag` changes metadata only. Use it only when the pixels were already
# tonemapped/graded for Rec.709 but inherited an incorrect HDR tag.
set -euo pipefail

MODE="${1:?usage: color-normalize.sh inspect|raw|retag <input> [output]}"
IN="${2:?usage: color-normalize.sh inspect|raw|retag <input> [output]}"
[ -f "$IN" ] || { echo "missing input: $IN" >&2; exit 1; }

inspect() {
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=codec_name,pix_fmt,color_range,color_space,color_transfer,color_primaries \
    -of default=nw=1 "$1"
}

if [ "$MODE" = inspect ]; then inspect "$IN"; exit 0; fi
OUT="${3:?usage: color-normalize.sh $MODE <input> <output>}"
[ "$IN" != "$OUT" ] || { echo "input and output must differ" >&2; exit 1; }
[ "${FORCE:-0}" = 1 ] || [ ! -e "$OUT" ] || { echo "refusing to overwrite: $OUT (set FORCE=1)" >&2; exit 1; }
mkdir -p "$(dirname "$OUT")"

tags=(-color_primaries bt709 -color_trc bt709 -colorspace bt709)
h264tag=(-bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1)

case "$MODE" in
  raw)
    # Some MOV/MP4 files expose ambient-viewing side data that makes ffprobe's
    # CSV writer append a delimiter (for example `arib-std-b67,`). Read only
    # the transfer token so HLG/PQ detection cannot silently fall through.
    transfer=$(ffprobe -v error -select_streams v:0 \
      -show_entries stream=color_transfer -of default=nw=1:nk=1 "$IN" \
      | head -n 1 | tr -d '\r,' | xargs)
    case "$transfer" in
      arib-std-b67|smpte2084)
        vf="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"
        action="tonemapped $transfer"
        ;;
      *)
        vf="format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"
        action="normalized SDR/unknown metadata"
        ;;
    esac
    ffmpeg -nostdin -y -v error -i "$IN" -map 0:v:0 -map '0:a?' -vf "$vf" \
      -c:v libx264 -crf "${CRF:-17}" -preset "${PRESET:-medium}" -pix_fmt yuv420p \
      "${tags[@]}" "${h264tag[@]}" -c:a copy -movflags +faststart "$OUT"
    echo "[color-normalize] $action -> $OUT"
    ;;
  retag)
    codec=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 "$IN")
    case "$codec" in
      h264) bsf=("${h264tag[@]}");;
      hevc) bsf=(-bsf:v hevc_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1);;
      *) echo "retag supports H.264/HEVC, got: $codec" >&2; exit 1;;
    esac
    ffmpeg -nostdin -y -v error -i "$IN" -map 0 -c copy "${tags[@]}" "${bsf[@]}" \
      -movflags +faststart+negative_cts_offsets -use_editlist 0 "$OUT"
    echo "[color-normalize] metadata-only Rec.709 retag -> $OUT"
    ;;
  *) echo "unknown mode: $MODE (expected inspect, raw, or retag)" >&2; exit 1;;
esac

inspect "$OUT"
