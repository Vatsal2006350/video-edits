#!/usr/bin/env bash
# fetch-epic-fonts.sh -- the premium "epic / luxury" type set used by
# bin/cinema-flex-reel.py. All OFL (Google Fonts). fonts/*.ttf is gitignored,
# so this script is how a fresh clone gets them. Variable fonts are instanced
# to static weights because ffmpeg/libass/PIL render a VF at its default weight.
set -euo pipefail
cd "$(dirname "$0")/../fonts"
B=https://raw.githubusercontent.com/google/fonts/main/ofl
get() { [ -s "$2" ] || curl -sfL -o "$2" "$B/$1" || { echo "failed: $1" >&2; exit 1; }; }
get "cinzel/Cinzel%5Bwght%5D.ttf" Cinzel-VF.ttf
get "cinzel/OFL.txt" OFL-Cinzel.txt
get "cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf" CormorantGaramond-VF.ttf
get "cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf" CormorantGaramond-Italic-VF.ttf
get "cormorantgaramond/OFL.txt" OFL-CormorantGaramond.txt
get "tenorsans/TenorSans-Regular.ttf" TenorSans-Regular.ttf
get "tenorsans/OFL.txt" OFL-TenorSans.txt
get "italiana/Italiana-Regular.ttf" Italiana-Regular.ttf
get "italiana/OFL.txt" OFL-Italiana.txt
get "cinzeldecorative/CinzelDecorative-Bold.ttf" CinzelDecorative-Bold.ttf
inst() { [ -s "$3" ] || uvx --from fonttools fonttools varLib.instancer "$1" "wght=$2" -q -o "$3"; }
inst Cinzel-VF.ttf 600 Cinzel-SemiBold.ttf
inst Cinzel-VF.ttf 400 Cinzel-Regular.ttf
inst CormorantGaramond-Italic-VF.ttf 500 CormorantGaramond-MediumItalic.ttf
inst CormorantGaramond-Italic-VF.ttf 400 CormorantGaramond-Italic.ttf
inst CormorantGaramond-VF.ttf 500 CormorantGaramond-Medium.ttf
echo "[fetch-epic-fonts] ok: Cinzel, Cormorant Garamond, Tenor Sans, Italiana, Cinzel Decorative"
