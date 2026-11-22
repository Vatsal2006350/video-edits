# Cinema flex reel (luxury night out, joke hook, gold title, DM CTA)

Built 2026-11-23 for the Ramayana re-watch in the VOX Mall of the Emirates IMAX THEATRE pods.
Tool: `bin/cinema-flex-reel.py <spec.json>` (stills first with `--frames t1,t2,...`).
Fonts: `bash bin/fetch-epic-fonts.sh` (Cinzel, Cormorant Garamond, Tenor Sans; all OFL).
Example spec: `projects/ramayana-imax-pod/spec.template.json`.

## Structure (about 15s)
| time | beat | type |
|---|---|---|
| 0.25 to 2.75 | the joke setup, first person ("I was worried Ramayana wouldn't make back its ₹4,000 crore budget") | `whisper` |
| 2.9 to 4.75 | the turn ("so I went to watch it again") | `whisper` |
| 4.9 to 6.95 | the escalation ("in the most expensive seat in the city") | `whisper` |
| 7.05 to 10.35 | PAYOFF on the drop: widest glamour shot + gold title, hairline rule, kicker fact | `title` + `rule` + `kicker` |
| 10.4 to 12.6 | fast glamour cuts, one deadpan callback ("doing my part for the box office") | `whisper` low (cy 1180) |
| 12.75 to 15.6 | CTA end card: `COMMENT "POD"` + "and I'll send you where this is", fade out | `rule` + `cta` |

## Measured type (1080x1920)
- whisper: Cormorant Garamond Medium Italic 80px (auto-fits to 724px), ivory #F6EEE0, pitch 1.12,
  soft shadow 0.55, blur-in 9px to 0 and 26px rise over 0.75s, lines staggered 0.2s.
- title: Cinzel SemiBold 104px, engraved gold gradient (#FCF0C8 > #E2BE6E > #B0843A > #ECCC84),
  warm bloom (#E8B256, blur 0.22 em), tracking breathes 0.16 em to 0.24 em across the hold.
- kicker: Tenor Sans 34px caps, tracking 0.36 em, champagne #F0DEB2.
- rule: 2px gold hairline with a centre diamond, draws out from the centre over 0.9s.
- every text block gets a soft dark scrim pool (0.34) so it holds on bright, busy shots.
- all type measured inside x 178 to 901, y 635 to 1231 on the stand-in render (IG safe box x 59 to 918, y 278 to 1536).

## Grade `imax-gold`
Contrast 1.07, saturation 0.9, cool lifted shadows, warm gold highlights, filmic shoulder curve,
vignette PI/4.6, highlight halation (screen blend of a thresholded gblur 22 at 0.3), luma grain 6,
eased 4 to 7 percent push-in per shot. iPhone HLG is tonemapped per shot before the grade.
`velvet-noir` is the redder, deeper alternative for velvet interiors.

## Shot rules
- Show the EXPERIENCE (pod exterior, reclining in the pod, blanket, food arriving, the room from the
  pod, the lounge, the IMAX logo wall). Keep the actual film on screen to brief, wide, out-of-focus
  glimpses: the Ramayana makers warned of legal action against recording and sharing film footage.
- Payoff shot (7.05s) is the single widest, most "wow" frame; it must land on the music drop.
- Montage cuts 1.0 to 1.2s, last shot holds 3s under the CTA with a 0.6s fade.

## Audio
Upload copy stays silent; attach the song in the Instagram composer (reach + licensing).
Pick the segment in the composer so the swell hits the title at about 7s.
Tracks used: AR Rahman's Ramayana songs "Mangal Rang" (wedding song, warm) or "Jai Jai Ram"
(devotional build). Set `audio.src` to a local copy only for the `_preview.mp4`.

## Engagement
- Hook is a joke riding the live ₹4,000 crore budget discourse; the location is withheld on purpose.
- CTA keyword "POD" turns the location into a comment-to-DM (comments are the strongest signal).
- Pin a reply with the second-best joke so the comment section starts warm.
