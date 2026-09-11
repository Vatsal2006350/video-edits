# Receipt-reel format (decoded from vatsal.returns virals, 2026-08-27)

Both reference reels are the SAME 10.912s template = one exact segment of
"Wishes" — Hasan Raheem, Umair, Talwiinder (IG audio id 838040817866845).
Reel A (scenic hook opener): 488 likes. Reel B (desk webcam opener): 3,693
likes on a ~490-follower account. Same receipts, same text, same audio —
ONLY the opener changed. Conclusion: relatable authentic-desk opener >>
pretty scenery for the hook.

## Structure (4 scenes x 2.728s, hard cuts, no transitions)
1. HOOK — authentic lo-fi clip of you (webcam desk shot, Ray-Ban Meta POV,
   phone selfie). Meme-relatable line in bold white: "Studying till she replies"
2-4. RECEIPTS — flex escalation, one bold line each:
   letterboxed photo on black (text in top bar) or full-bleed video clip.
   e.g. "Became a YC founder at 18\nand raised $500k" -> "Worked at 3
   startups" -> "Met Sam Altman"
Caption: 1-2 line motivational + #fyp #yc #startup/#growth #tech.
Audio: attach IN THE COMPOSER (trending graph) — never burn into the file.
Cuts land on beats automatically because scene length matches the template.

## Production
bin/receipt-reel.sh <manifest> <out.mp4>   # silent 1080x1920, 10.912s
manifest lines: type|src|focus|text   (video/photo, focus=left|center|right,
\n = line break). Font: Montserrat SemiBold, white, soft shadow; hook at 54%
height on video, receipts at 16% in the top black bar of letterboxed photos.
Photos can be HEIC (auto-converted). Reference build: receipts/sample1.manifest

## Hook-line bank (rotate; meme-relatable, lowercase-adjacent tone)
Studying till she replies · Replying to her at 2am · Waiting for her text ·
POV: your friends are partying · They said drop out · GPA says I'm failing ·
Mom thinks I'm wasting my time

## Audio bank (2026-08 research)
Confirmed in-niche:
- "Wishes" — Hasan Raheem, Umair, Talwiinder (IG audio 838040817866845; the 10.912s template segment). Both virals used it.
- Adjacent desi artists whose tracks trend in the same feeds: NDS, AP Dhillon, Yashraj, Shubh, Abdul Hannan ("Bikhra"), Anuv Jain ("Afsos").
Trending broadly for motivational/milestone reels (Aug 2026):
- "Don't Tell Your Dreams" — STOSLIV (business milestones, cinematic)
- "Oh Yeah" — Steve Lacy (discipline/progress edits)
Classic reveal-DROP candidates for the "small college → MIT" flip format
(verify in-app by tapping the audio on a trend reel; original sounds dominate):
- "Kerosene" — Crystal Castles · "Neon Blade" — MoonDeity ·
  "METAMORPHOSIS" — INTERWORLD · "Close Eyes" — DVRST
Vatsal's own YC-reveal post (DcaOGyMhNBC) has the trend track BURNED IN as
"Original audio" — the source file lives in his CapCut project; transcribe
lyrics from that export to identify the exact song when he shares it.
Rule: attach audio in the composer, never burn it in (trend graph + reach).

Gotcha: finished CapCut exports (e.g. 0820/source.mp4) have overlays BURNED
IN (YC logo 0-3s, book photo 4-7s, IG screenshots 10.3s+). When reusing that
footage for hooks, cut ONLY from verified-clean windows (walking segment
~30-39s) — or better, use raw camera clips. Always frame-check a hook window
before shipping a draft.

## Holy-airball (Soul Survivor) trend research — 2026-08-27
Audio "Soul Survivor" — Young Jeezy ft. Akon (id 415458279040894): 31,218
reels use it. The format on the audio page, across every niche (trucks, MMA,
nails, dirt bikes, students), is IDENTICAL to what we built:
  setup text ("Me: I'm a psychology student") → 🔊 quote page reaction
  ("Them: oh so you must be good at managing stress") → BEAT DROP flex reveal
  ("HOLY FCKN AIRBALL 😅😄").
Top view counts seen: 60.8K, 27.5K, 26.5K, 14.7K. A comment on one:
"Please do soul survivor next" = live demand. Our two-page + drop structure
matches the winners exactly; the founder angle (YC/Sam Altman) is an
untapped niche on this sound — mostly generic flex/sport reels so far.
Takeaways to apply:
- Setup line is FIRST-PERSON identity ("Me: I'm a ___"), reaction is the
  dismissive quote, drop is the flex that contradicts it. Ours already does this.
- Keep the burned setup/quote text; attach the sound in-app (never burned).

## 2026-09-06 viral: "Forget her / or / Become a YC founder" (Dc8vZ0gOMF5, 5.4k likes)
Same 10.912s Wishes template -- the segment is `wishes.mp3` @ **114.707s** (second drop, lands at 8.80), NOT the 31.56 first-drop cut; identify by cross-correlating the reel audio against the song, never by ear. Hook = 3-line OR over a Ladakh snow POV (feet), then YC sign photo ("Became a YC founder at 18
and raised $500k"), stage clip IMG_6946 @0.5 ("Scaled 3 startups"), laptop Zoom clip IMG_3773 @44 ("Met Sam Altman").
Caption "Priorities are set" #trend #fyp #yc. The "her vs the work" thread keeps working (studying-till-she-replies -> this).
Variations shipped 2026-09-07 as reels 37-39 (receipts/her1-3.manifest): rotate hook line + hook footage + receipt order so
IG sees new content; keep the YC sign + Sam Altman as anchors. White hook text needs darker ground (snow/rocks, lake, desk);
over bright sand it disappears (shadow only, no scrim).

Measured text (viral, YC-sign scene): 'Became a YC founder at 18' spans x 117-963 (846px), block top y=406 in the top
black bar, ~11px stems -> Montserrat Bold 61px, line pitch ~73, white, shadow 0/3 @0.6, NO box. Photo fitted to width on
black (band 656-1263). Hook text centred at 42% height over video. All of this is the default in `bin/receipt-reel2.sh`;
Vatsal's rule: after the hook, beat 2 is ALWAYS the YC sign photo; other YC receipts come after it.
