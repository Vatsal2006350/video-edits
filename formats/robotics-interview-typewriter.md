# Michigan interview: typed questions

Builder: `videos/october-new-reels/revise-professor.py`. Preserves the accepted 61.933s source edit in `06_michigan-robotics-full-interview/base.mp4`; never silently rebuilds the cut map. Output suffix `-v2` preserves the previous master.

- DM Serif Display headings: maize `#FFCB05`, navy `#00274C` 2px keyline, no shadow. Opening size58, y310, two lines; name Montserrat44 at475. Transparent Block M enters at555 via 0.55s cubic ease, scale80–100%, opacity0–100%.
- During the actual questions, replace the heading with verbatim character-by-character type. Existing `typed-hook.py` now accepts `character_reveal`, `fill`, `stroke`, and `stroke_fill`; existing defaults are unchanged. Word starts/ends come from original alignment and the accepted source-to-timeline map. Full text is pre-laid out so partial words never reflow. Question size57, max680, center485, line pitch67. Cream card x185–895, y320–680, 3px maize edge. No simultaneous duplicate question rail.
- Lower rail: Montserrat58, warm cream with3px navy outline, no shadow; preserve original speech and correct name to Damen. The real guest is Managing Director Damen Provost, not the department chair. Check official profile before authoring titles.
- NASA retroreflector insert retained18.2–26.1s. Michigan Apollo15 panorama12–18.2s; round-trip laser diagram28–36.47s. All above faces, not arbitrary unrelated robot footage.
- Music: one continuous downloaded vocal-free “The Good Part” passage18–79.933s. Speech stays primary, bed target-31LUFS with sidechain ratio6, 12ms attack/240ms release, 0.6s closing fade. The speech-led cut map is not snapped to beats.
- Validate alpha bboxes for graphic layers and actual subtitle render; safe x59–918/y278–1536, centered max724. Review question padding, particularly the fifth line of Q1. Every result needs master, `export-ig.sh` upload copy, phone preview, `ig-safe.py view`, and independent story QA.
