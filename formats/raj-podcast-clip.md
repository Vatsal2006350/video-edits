# Podcast clip — all-yellow POV serif captions

Talking-head treatment with one concise, speech-grounded POV headline from frame one, followed by all-caps running dialogue captions. Use a bold Anton condensed headline in maize yellow with a dark keyline. Keep it visible for about 2.8 seconds, then fade it out. Do not fade the opener in; its first frame must already be readable.

Dialogue captions use Bodoni Moda, maize only (`&H0005CBFF&`), a dark outline and soft shadow. Keep the captions centered in the lower safe region. Word timings remain tied to the transcript, with a small 110% active-word pop over 100 ms. `CAP_FILL` and `CAP_HIGHLIGHT` should use the same yellow so every caption stays one color. Use `CAPS_LOCK=1`.

## Build settings
Use `bin/build-story-reel.sh` with `CAPFONT='Bodoni Moda'`, `CAPSIZE=86`, `CAPOUTLINE=5`, `CAP_SHADOW=1`, `CAP_MARGIN_V=530`, `CAPS_LOCK=1`, `CAP_FILL='&H0005CBFF&'`, and `CAP_HIGHLIGHT='&H0005CBFF&'`. Render the POV PNG with `bin/druk-inspired-title.py`, yellow line fill only and a dark keyline; overlay from time 0 with no entrance fade. Verify its alpha bounds with the tool and inspect master, IG and phone exports using `bin/ig-safe.py view`.

Normalize instrumental beds consistently before mixing. Use a moderate music level with gentle side-chain ducking, and keep audio in phone previews so the user can hear the mix. Verify the final IG encode's stereo 44.1 kHz AAC, edit-list count and true peak.

Keep the speaker's meaning intact. Editorial hooks can be provocative, but phrase numerical, product-performance and market statements as the speaker's claims. The exact typeface used by Raj Shamani is not publicly documented; this is a visual reference treatment, not a claim that it uses his proprietary font.
