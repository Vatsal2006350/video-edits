# Diwali abroad: quiet street time cards

Reference: [Instagram reel DfeB4VihL3t](https://www.instagram.com/reel/DfeB4VihL3t/).
The user-requested remake keeps the continuous 17.208s reference audio, the
"Diwali celebration abroad 🥺" title, and five static local-time cards. Cuts land
on the spoken cue boundaries at 3.26, 5.72, 9.36, and 11.66s. Cards are
`8:00 AM`, `11:45 AM`, `2:45 PM`, `7:45 PM`, and `10:45 PM`.

## Type and placement

- Montserrat Bold, 49px title + 48px color emoji, 50px time card, 3px black outline.
- Text center x=540; title y=815, time y=870.
- Rendered title layer alpha bbox: x=181..898, y=815..923; strict-white bbox
  x=185..886, y=818..919. The centered line is 720px, within the 724px limit
  and the Instagram safe box.
- Keep the background and card positions fixed; only update the time line at
  the measured phrase boundaries.

## Picture and sound

- Each card uses a distinct Michigan source: a morning street, an empty campus plaza,
  a pedestrian bridge, a dusk path, and a snowy night street. The final street
  footage was recorded in Ann Arbor at about 8:56 PM.
- The times and voice follow the reference and do not claim the clips were recorded
  at those exact hours or on one day.
- HLG is tonemapped to Rec.709 before a slight contrast/saturation adjustment.
- Use the downloaded reference audio continuously from 0.0 to 17.208s; do not
  replace, loop, or remix it. Master audio correlation against the downloaded
  reference is 0.99999 at zero offset.
- Build with `python3 videos/diwali-street-remake/build.py`. It creates a master,
  an IG export through `bin/export-ig.sh`, and a 608x1080 phone preview under
  `~/Downloads/reel-batch/diwali-abroad-michigan/`.

## Latest render evidence (r04)

- Master and IG copy: 1080x1920, 30fps, H.264 High. IG is level 4.0, Rec.709,
  stereo 44.1kHz AAC, -14.0 LUFS, -2.2 dBTP, with no `elst` atom.
- Phone preview: 608x1080, 30fps, CRF 26.
- Safe-area sheets: `.work/dfeB4VihL3t/master-r04-safe.jpg`,
  `.work/dfeB4VihL3t/IG-r04-safe.jpg`, and `.work/dfeB4VihL3t/phone-r04-safe.jpg`.
