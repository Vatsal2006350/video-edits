
`scale=2160:-1,zoompan=...:s=1080x1920` looks like it crops. It does not. **`zoompan`'s `s=` forces the output size**, so a 4:3 photo gets stretched vertically into 9:16. Vatsal caught it on the YC group photo — "this yc image gets quashed" — and it was in *every* still branch of *every* builder (`or-reel`, `glowup-reel`, `card-reel`, `diptych-reel`, `receipt-reel`), so it hit the YC payoff card in all 19 OR reels plus every glow-up and diptych.

The fix lives in `~/Code/video-edits/bin/lib-still.sh`, sourced by each builder:
- `still_vf <w> <h> [rate] [zmax]` — letterboxes the real photo over a blurred, darkened copy of itself. Use when the whole image matters (a group shot, a sign, a screenshot); cropping would cut people out.
- `still_cover_vf <w> <h> [rate] [zmax]` — `force_original_aspect_ratio=increase` + crop, so it fills without distorting. Use when one face should fill the frame (childhood portraits, diptych halves) and the edges cost nothing.

**The general trap:** any ffmpeg filter that takes an explicit output size (`zoompan s=`, `scale=w:h` without `force_original_aspect_ratio`, `pad` mis-sized) will happily distort rather than refuse. Aspect correctness is never automatic — assert it by pulling a frame and looking, the same discipline as [[verify-rendered-not-intermediate]] and [[footage-folder-names-lie]].

Related: the whole batch is now reproducible from `~/Code/video-edits/batch/build-all.sh`, themed into folders — that is what made re-rendering ~70 reels against this fix a single command instead of 70 edits.
