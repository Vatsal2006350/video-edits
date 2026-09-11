# Reel font repo

Everything here is either open-licence (Google Fonts, OFL) or a macOS system face
instanced to a static weight. Safe to burn into reels.

## IMPACT / DISPLAY — hooks, big statements
Anton · Bebas Neue · Archivo Black · Kanit Black · Oswald SemiBold · Teko Bold
Fjalla One · Staatliches · Passion One · Chivo Black · Barlow Condensed Bold · Rubik ExtraBold

## FUN / CHUNKY — playful, meme energy
Titan One · Bungee · Bowlby One · Alfa Slab One · Righteous

## SERIF DISPLAY — elegant openers (the "I got a ___" look)
Playfair Display Italic · Instrument Serif (+Italic) · DM Serif Display (+Italic)
Abril Fatface · Bodoni Moda Bold · Lora Italic

## CAPTION SANS — body / subtitles
Poppins SemiBold + Bold · Inter SemiBold + Bold · Figtree Bold · Plus Jakarta Bold
Sora SemiBold · Outfit SemiBold · Manrope Bold · Space Grotesk Bold
Avenir Next Regular + Medium · Montserrat (Bold / SemiBold / ExtraBold)

## House defaults
- Openers: Playfair Display Italic lead-in + Poppins Bold payoff line
- Captions: Poppins SemiBold/Bold, active word in maize `&H0005CBFF&`
- Cinematic behind-subject type: Avenir Next Regular (see bin/hero-type.py)

## Effects
- `bin/glow-text.py` — the gold-glow look: stacked blurred copies of the glyphs behind
  the fill. Best on dark footage; on bright footage raise `spread` or switch the fill
  to white with a dark keyline. Params: font, size, glow, fill, passes, radius, spread.
- `bin/hero-type.py` — stacked light-weight reveal, auto-shrinks to fit the frame.
- `bin/make-captions.py` — ASS captions from forced-aligned words.

## Variable fonts
`*-VF.ttf` are variable; ffmpeg/libass render them at the DEFAULT weight (usually
Regular), which silently loses the weight you wanted. Always instance first:
`uvx --from fonttools fonttools varLib.instancer X-VF.ttf wght=700 -o X-Bold.ttf`
