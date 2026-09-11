# Food / restaurant reel (Farmyard, Adimali -- 25_kerala_food v6, 2026-09-07)

Built on the research in `research/2026-09-07-food-reel-craft.md` + `...-cinematic-ffmpeg-food.md`. Vatsal's brief: b-roll with the
owner's voice as VO ("important bits he says, the famous dishes"), cinematic like the popular food creators, kitchen footage used.

Structure (Plan A): open on the PAYOFF, never on the intro or the wide.
0-2.0 leaf slapped down (60fps source, 2x slow via setpts, slap SFX at 0.3, bed silent) + lower third "Kerala's fish thali / Rs 200-400 a head"
2.0-4.4 rice on the leaf (slow) -> owner VO starts under plating/stove: "we have a variety of fish... dishes and food"
-> "you should try all the fish Pollichathu, very authentic... comes with a banana leaf... steamed... delicious" under chef at the
   stove (sizzle SFX -14 dB), leaf laid, rice served + lower third "Meen Pollichathu / steamed in a banana leaf"
-> owner ON CAMERA for exactly one line ("we have opened this restaurant from 2017") + "Farmyard, Adimali / since 2017"
-> Vatsal's intro line on camera as the verdict beat -> first bite, second bite -> overhead thali plating = the reveal (whoosh
   SFX) + "Fish curry meal / Rs 200-400" -> restaurant wide + "Kochi-Madurai road, Adimali / 7:30-22:00", cut dead. 42s.
Facts on screen are from public listings (restaurant-guru / FavHiker: address, Rs 200-400, 7:30-22:00); "since 2017" is the owner's word.

Builder features it uses (all in `bin/build-story-reel.sh`): HEAD (b-roll before speech; voice/captions/hook shift), CUTS as one
contiguous block under the owner, TAIL, MIDTEXT lower thirds (DM Serif Italic 84/64, x 88, top 960/1000), SFX cues mixed with the
bed and ducked under voice, BROLL_VF gentle food grade (colorbalance warm mids, selectivecolor reds/yellows <= 0.06, vibrance 0.15,
soft S-curve, vignette PI/5.5 -- the stronger research chain went orange on skin and papadum), WORDFIX (Fram Yard->Farmyard,
which->Pollichathu, uh dropped), TONEMAP=auto.

**TONEMAP finding (big):** every clip from this trip is iPhone HLG 10-bit (`arib-std-b67`, `yuv420p10le`, 60fps). Encoding it
straight to yuv420p gives the flat, hazy look the reviewer kept flagging. `zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,
tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p` first restores contrast and saturation (measured: sat 0.17 -> 0.27,
blacks 18 -> 10). The builder now detects `color_transfer` per source and tonemaps automatically; 60fps sources give clean 2x slow-mo
with setpts alone.
Sound: bed Arz Kiya Hai @20 at 0.17 (ducked), sizzle -14, slap -6, whoosh -12; master via the IG export (-14 LUFS, -2 dBTP).
