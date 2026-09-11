
Built 2026-09-02 at `~/Code/video-edits/fonts/` (61 files, 12MB, all OFL or macOS faces instanced to static weights). `fonts/README.md` lists them grouped by the job they do: **impact/display** (Anton, Bebas Neue, Archivo Black, Kanit Black, Oswald, Teko, Chivo Black, Rubik ExtraBold...), **fun/chunky** (Titan One, Bungee, Bowlby One, Alfa Slab, Righteous), **serif display** for elegant openers (Playfair Italic, Instrument Serif, DM Serif, Abril Fatface, Bodoni Moda, Lora Italic), and **caption sans** (Poppins, Inter, Figtree, Plus Jakarta, Sora, Outfit, Manrope, Space Grotesk).

`bin/glow-text.py` renders the **gold-glow** look Vatsal asked for (from @rj.mahvash): stacked blurred copies of the glyphs behind the fill, so it blooms instead of reading as a soft outline. **Anton + gold glow** is the pick. It needs dark footage — on his yellow-shirt talking-head frames the yellow glow disappears, so use a white fill with a dark keyline there instead.

**Why:** he asked for "a solid repo of these type of strong bold useful catchy fonts for reels" rather than one-off downloads, so future reels pick from a named set instead of restarting the search.

**How to apply:** the trap worth remembering is that `*-VF.ttf` variable fonts render at their DEFAULT weight in ffmpeg/libass — Playfair Display silently came out Regular instead of Black. Always instance first with `fonttools varLib.instancer`. House defaults are recorded in the README. See [[reel-typography-standard]] and [[cinematic-hero-type]].
