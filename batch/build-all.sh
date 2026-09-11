#!/bin/bash
# Rebuild the whole reel batch, themed into folders.
#
# Theme (Vatsal, 2026-09-05): growth, YC, startups, success, learnings + teachings.
# Travel stays because it performs, but it is the supporting theme, not the spine.
#
#   bash batch/build-all.sh            # everything
#   bash batch/build-all.sh yc         # one folder only
set -uo pipefail
V="$(cd "$(dirname "$0")/.." && pwd)"
S="${VIDEO_EDITS_WORK_ROOT:-${TMPDIR:-/tmp}/video-edits}"
mkdir -p "$S"
B=$HOME/Downloads/photos-broll; C=$HOME/Downloads/content; OUT=$HOME/Downloads/reel-batch
A=$B/aura-new; T=$B/travel2; K=$B/kerala-scenic; M=$B/mumbai; BM=$B/bom; P=$B/before-jpg
YC=$HOME/Downloads/yc_announcement.JPG
LAP=$T/IMG_2627.MOV          # laptop running the product
STK=$C/IMG_7152.MOV          # laptop with the YC sticker, purple light
GTR=$C/IMG_6946.MOV
DESK=$C/IMG_8346.mov
CLOSE=$B/broll/0606_175232_IMG_1863.MOV.MOV   # looking out to sea -- the closer
WALK=$B/broll/0606_175255_IMG_1864.MOV.MOV
SUN=$B/broll/0523_185029_IMG_1003.MOV.MOV
ONLY="${1:-all}"
want () { [ "$ONLY" = all ] || [ "$ONLY" = "$1" ]; }

for d in 1-yc-startups 2-lessons 3-success-glowup 4-travel 5-talking-head; do
  mkdir -p "$OUT/$d" "$OUT/phone/$d"
done

# Skip anything already rendered so the script is cheap to re-run after adding reels.
# FORCE=1 re-renders everything (that is how the still-aspect fix was rolled out).
done_already () { [ "${FORCE:-0}" != 1 ] && [ -s "$1" ] && { echo "    skip $(basename "$1")"; return 0; }; return 1; }

or_reel () { # or_reel <folder> <name> <hook> <ss> <l1> <l3> <payoffs>
  done_already "$OUT/$1/$2.mp4" && return
  OUT="$OUT/$1/$2.mp4" HOOK="$3" HOOK_SS="$4" L1="$5" L2="OR" L3="$6" \
  CUT=4.75 DUR=9.53 TARGET_W=670 CY=1105 PAYOFFS="$7" bash "$V/bin/or-reel.sh" 2>&1 | tail -1
}

# ─────────────────────────── 1. YC / startups ───────────────────────────
if want yc; then
echo "=== 1-yc-startups ==="
or_reel 1-yc-startups 01_or_degree "$C/IMG_8286.mov" 0.30 "Finish your degree" "Become a YC founder" \
"$YC|0|6.502|Became a YC founder at 18
$LAP|1.0|7.848|
$GTR|7.30|9.53|"
or_reel 1-yc-startups 02_or_job "$C/IMG_8286.mov" 0.30 "Take the safe job" "Build your own thing" \
"$LAP|1.0|6.502|Shipping it at 18
$STK|0.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 03_or_permission "$C/IMG_8286.mov" 0.30 "Wait for permission" "Just start building" \
"$STK|0.5|6.502|Nobody said yes first
$LAP|1.0|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 04_or_comfort "$C/IMG_8286.mov" 0.30 "Stay comfortable" "Go build something" \
"$YC|0|6.502|18 and in YC
$T/IMG_4881.MOV|1.0|7.848|
$T/IMG_4910.MOV|1.0|9.53|"
or_reel 1-yc-startups 05_or_grades "$C/IMG_8286.mov" 0.30 "Chase a 4.0 GPA" "Chase something real" \
"$YC|0|6.502|Y Combinator at 18
$LAP|1.0|7.848|
$STK|0.5|9.53|"
or_reel 1-yc-startups 06_or_someday "$C/IMG_8286.mov" 0.30 "Someday when I'm ready" "Today" \
"$LAP|1.0|6.502|Started at 17
$YC|0|7.848|
$GTR|7.30|9.53|"
or_reel 1-yc-startups 07_or_ship "$C/IMG_8346.mov" 0.40 "Coast through college" "Ship something real" \
"$YC|0|6.502|YC at 18
$GTR|0.30|7.848|
$GTR|7.30|9.53|"
or_reel 1-yc-startups 08_or_startnow "$B/purple/IMG_8454.MOV" 1.20 "Wait till you're ready" "Start before you are" \
"$YC|0|6.502|18 and funded
$LAP|1.0|7.848|
$STK|0.5|9.53|"
or_reel 1-yc-startups 09_or_quietly "$C/IMG_8286.mov" 0.30 "Post about the plan" "Build it quietly" \
"$LAP|60.5|6.502|Two years, no posts
$STK|0.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 10_or_blame "$B/purple/IMG_8456.MOV" 2.0 "Blame the system" "Out-work it" \
"$LAP|60.5|6.502|Nobody is coming
$STK|0.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 11_or_perfect "$B/purple/IMG_8449.MOV" 1.5 "Wait for the perfect idea" "Ship the ugly one" \
"$DESK|1.0|6.502|Version one was bad
$LAP|60.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 12_or_later "$C/IMG_8346.mov" 1.0 "Do it after graduation" "Do it this semester" \
"$YC|0|6.502|Did it at 18
$T/IMG_4910.MOV|1.0|7.848|
$CLOSE|3.6|9.53|"
or_reel 1-yc-startups 13_or_opinion "$B/purple/IMG_8459.MOV" 1.0 "Ask them what they think" "Ask them in two years" \
"$LAP|60.5|6.502|They stopped asking
$STK|0.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 14_or_backup "$C/IMG_8286.mov" 0.30 "Keep a backup plan" "Make the plan work" \
"$YC|0|6.502|No plan B at 18
$T/IMG_4910.MOV|1.0|7.848|
$CLOSE|3.6|9.53|"
or_reel 1-yc-startups 15_or_ivy "$T/IMG_6646.MOV" 20.0 "Get into the ivy" "Build the thing" \
"$LAP|60.5|6.502|One of them still matters
$STK|0.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 16_or_users "$B/purple/IMG_8456.MOV" 2.0 "Wait for the perfect market" "Talk to ten users" \
"$LAP|60.5|6.502|Ten users beat a plan
$STK|0.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 17_or_resume "$B/purple/IMG_8449.MOV" 1.5 "Polish the resume" "Build something to point at" \
"$LAP|60.5|6.502|One line beat the whole page
$STK|0.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 18_or_audience "$B/purple/IMG_8454.MOV" 1.2 "Build an audience first" "Build the thing first" \
"$LAP|60.5|6.502|The thing made the audience
$STK|0.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 19_or_cofounder "$C/IMG_8286.mov" 0.30 "Wait for a co-founder" "Start and let them find you" \
"$YC|0|6.502|They found me building
$LAP|60.5|7.848|
$STK|0.5|9.53|"

# receipts -- SILENT, attach trending audio in the IG composer
receipts () { # receipts <name> <manifest-heredoc-file>
  done_already "$OUT/1-yc-startups/$1.mp4" && return
  bash "$V/bin/receipt-reel.sh" "$2" "$OUT/1-yc-startups/$1.mp4" 10.912 2>&1 | tail -1
}
cat > $S/_r1 <<EOF
video|$B/purple/IMG_8454.MOV|center|"you're 18, what do you\nactually know"|1.2
video|$LAP|center||60.5
video|$STK|center||0.5
photo|$YC|center||0
video|$A/0618_140349_IMG_2447.MOV.MOV|center||1.0
EOF
receipts 20_receipts_know $S/_r1
cat > $S/_r2 <<EOF
video|$B/purple/IMG_8456.MOV|center|"you should focus\non your degree"|2.0
video|$DESK|center||1.0
video|$LAP|center||60.5
photo|$YC|center||0
video|$STK|center||0.5
EOF
receipts 21_receipts_degree $S/_r2
cat > $S/_r3 <<EOF
video|$B/purple/IMG_8449.MOV|center|"you just got lucky"|1.5
video|$DESK|center||1.0
video|$A/0610_214419_od_video-6222_singular_display.mov.mov|center||3.5
video|$LAP|center||60.5
photo|$YC|center||0
EOF
receipts 22_receipts_lucky $S/_r3
cat > $S/_r4 <<EOF
video|$B/purple/IMG_8459.MOV|center|"why not just\nget a normal job"|1.0
video|$LAP|center||60.5
video|$STK|center||0.5
video|$T/IMG_4910.MOV|center||1.0
photo|$YC|center||0
EOF
receipts 23_receipts_job $S/_r4
or_reel 1-yc-startups 24_or_internship "$C/IMG_8286.mov" 0.30 "Optimise for the internship" "Optimise for the skill" \
"$LAP|60.5|6.502|One of them compounds
$STK|0.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 25_or_pay "$B/purple/IMG_8454.MOV" 1.2 "Ask if it's a good idea" "Ask if anyone will pay" \
"$LAP|60.5|6.502|Only one answer is data
$DESK|1.0|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 26_or_learn "$B/purple/IMG_8449.MOV" 1.5 "Learn everything first" "Learn what you need next" \
"$DESK|1.0|6.502|You will never feel ready
$LAP|60.5|7.848|
$STK|0.5|9.53|"
or_reel 1-yc-startups 27_or_network "$C/IMG_8346.mov" 1.0 "Work the whole room" "Email the one person" \
"$LAP|60.5|6.502|One of them gets read
$STK|0.5|7.848|
$YC|0|9.53|"
or_reel 1-yc-startups 28_or_credentials "$B/purple/IMG_8459.MOV" 1.0 "Collect the credentials" "Collect the users" \
"$LAP|60.5|6.502|Users don't check your age
$STK|0.5|7.848|
$YC|0|9.53|"

cat > $S/_r5 <<EOF
video|$B/purple/IMG_8454.MOV|center|"no business will buy\nfrom an 18 year old"|1.2
video|$LAP|center||60.5
video|$DESK|center||1.0
video|$STK|center||0.5
photo|$YC|center||0
EOF
receipts 24_receipts_buy $S/_r5
cat > $S/_r6 <<EOF
video|$B/purple/IMG_8456.MOV|center|"it's just a wrapper"|2.0
video|$LAP|center||60.5
video|$LAP|center||20.0
video|$STK|center||0.5
photo|$YC|center||0
EOF
receipts 25_receipts_wrapper $S/_r6
fi

# ─────────────────────────── 2. lessons / teachings ───────────────────────────
card () { # card <folder> <name> <top> <audio> <audio_ss> <cards>
  done_already "$OUT/$1/$2.mp4" && return
  OUT="$OUT/$1/$2.mp4" TOP="$3" AUDIO="$HOME/Downloads/music-good/$4.mp3" AUDIO_SS="$5" CARDS="$6" \
    bash "$V/bin/card-reel.sh" 2>&1 | tail -1
}
if want lessons; then
echo "=== 2-lessons ==="
card 2-lessons 01_three_things 1140 trend_36267 0 \
"$T/IMG_4805.MOV|36.0|2.60|3 things i wish|someone told me at 16
$LAP|60.5|5.10|1. nobody is|checking your gpa
$STK|0.5|7.60|2. start before|you feel ready
$A/0618_140349_IMG_2447.MOV.MOV|1.0|10.10|3. the ones who|doubt you are busy
$CLOSE|3.6|13.00|none of it|was about talent"
card 2-lessons 02_quiet_years 1250 wishes 34.3 \
"$A/0610_214419_od_video-6222_singular_display.mov.mov|2.0|2.60|nobody saw|the two years
$DESK|1.0|5.10|they saw|the announcement
$LAP|60.5|7.60|the announcement|took one day
$STK|0.5|10.10|the two years|took two years
$YC|0|13.00|do the two years|"
card 2-lessons 03_boring_answer 1250 trend_21977 0.4 \
"$DESK|1.0|2.60|people ask how|i got into yc at 18
$LAP|60.5|5.10|the answer is|boring
$STK|0.5|7.60|i built the thing|every single day
$A/0610_214419_od_video-6222_singular_display.mov.mov|2.0|10.10|for two years|before anyone looked
$YC|0|13.00|that is the whole|secret"
card 2-lessons 04_rejection 1250 dont_tell_dreams 26.0 \
"$T/IMG_6646.MOV|20.0|2.60|i have a folder|of rejections
$DESK|1.0|5.10|schools|internships
$A/0610_214419_od_video-6222_singular_display.mov.mov|2.0|7.60|every one of them|felt final
$LAP|60.5|10.10|none of them|changed anything
$YC|0|13.00|i just kept|building"
card 2-lessons 05_boring_reps 1250 trend_7985 0 \
"$DESK|1.0|2.60|discipline is not|a personality
$A/0610_214419_od_video-6222_singular_display.mov.mov|2.0|5.10|it is doing|the boring rep
$LAP|60.5|7.60|on the day|you do not want to
$STK|0.5|10.10|nobody is|watching that day
$YC|0|13.00|that is the day|that counts"
card 2-lessons 06_no_connections 1250 dont_tell_dreams 26.0 \
"$BM/IMG_4943.MOV|6.0|2.60|i had zero|connections at 17
$DESK|1.0|5.10|no warm intros|no family in tech
$LAP|60.5|7.60|so i shipped|and posted the link
$STK|0.5|10.10|the work|was the intro
$YC|0|13.00|it still is|"
card 2-lessons 07_the_timeline 1250 wishes 34.3 \
"$M/IMG_4935.MOV|2.0|2.60|the timeline|nobody posts
$DESK|1.0|5.10|month 1 to 18|nothing works
$A/0610_214419_od_video-6222_singular_display.mov.mov|2.0|7.60|month 19|something does
$LAP|60.5|10.10|everyone sees|month 19
$YC|0|13.00|the other 18|are the job"
card 2-lessons 08_do_differently 1250 trend_7985 0 \
"$DESK|1.0|2.60|what i'd do|differently at 16
$LAP|60.5|5.10|ship in public|from day one
$STK|0.5|7.60|stop optimising|for permission
$K/0820_171934_IMG_4332.MOV.MOV|15.0|10.10|take the trip|earlier
$CLOSE|3.6|13.00|that's the list|"
card 2-lessons 09_turning_18 1140 trend_36267 0 \
"$M/IMG_4935.MOV|2.0|2.60|nothing magic|happens at 18
$BM/IMG_4943.MOV|6.0|5.10|you just run out|of people to blame
$LAP|60.5|7.60|that's the whole|difference
$K/0820_171934_IMG_4332.MOV.MOV|15.0|10.10|it's not|confidence
$CLOSE|3.6|13.00|it's just|starting"
card 2-lessons 10_if_youre_17 1140 trend_21977 0.4 \
"$K/0820_181056_IMG_4382.MOV.MOV|1.6|2.60|if you're 17|and reading this
$T/IMG_4910.MOV|1.0|5.10|you are not|behind
$K/0820_171934_IMG_4332.MOV.MOV|15.0|7.60|you are just|early
$T/IMG_4968.MOV|25.4|10.10|and early|feels the same
$CLOSE|3.6|13.00|keep going|"
card 2-lessons 11_work_hard 1140 trend_29085 0 \
"$A/0610_214419_od_video-6222_singular_display.mov.mov|3.5|3.40|work hard until|the flights feel short
$A/0610_214835_od_video-6230_singular_display.mov.mov|5.0|6.80|until the 3am|is a choice
$STK|0.5|10.20|until nobody|asks what you do
$LAP|60.5|13.50|they just know|"
card 2-lessons 13_cold_email 1250 trend_7985 0 \
"$DESK|1.0|2.60|how to email someone|who does not know you
$LAP|60.5|5.10|one specific line|about their work
$STK|0.5|7.60|one sentence|on what you built
$A/0610_214419_od_video-6222_singular_display.mov.mov|2.0|10.10|then stop typing|
$YC|0|13.00|that is the email|"
card 2-lessons 14_demo_30s 1250 trend_21977 0.4 \
"$LAP|60.5|2.60|your demo has|30 seconds
$LAP|20.0|5.10|do not explain|the architecture
$STK|0.5|7.60|show the thing|working once
$DESK|1.0|10.10|then be quiet|
$YC|0|13.00|that is the demo|"
card 2-lessons 15_no_cofounder 1140 dont_tell_dreams 26.0 \
"$DESK|1.0|2.60|you do not need|a co-founder to start
$LAP|60.5|5.10|you need|one working thing
$STK|0.5|7.60|the right people|find working things
$A/0618_140349_IMG_2447.MOV.MOV|1.0|10.10|not pitch decks|
$YC|0|13.00|build first|"
card 2-lessons 16_look_serious 1250 trend_36267 0 \
"$B/purple/IMG_8454.MOV|1.2|2.60|the fastest way|to be taken seriously
$LAP|60.5|5.10|is not|a better bio
$STK|0.5|7.60|it is a link|to something running
$DESK|1.0|10.10|age stops mattering|the moment you have one
$YC|0|13.00|go get the link|"
fi

# ─────────────────────────── 3. success / glow-up ───────────────────────────
glow () { # glow <name> <audio> <audio_ss> <capy> <l1> <l2> <stills> <motion> <payoff>
  done_already "$OUT/3-success-glowup/$1.mp4" && return
  OUT="$OUT/3-success-glowup/$1.mp4" AUDIO="$HOME/Downloads/music-good/$2.mp3" AUDIO_SS="$3" \
  CAPY="$4" L1="$5" L2="$6" STILLS="$7" MOTION="$8" PAYOFF="$9" \
    bash "$V/bin/glowup-reel.sh" 2>&1 | tail -1
}
dip () { # dip <name> <audio> <audio_ss> <top_t> <bot_t> <l1> <l2> <pairs>
  done_already "$OUT/3-success-glowup/$1.mp4" && return
  OUT="$OUT/3-success-glowup/$1.mp4" AUDIO="$HOME/Downloads/music-good/$2.mp3" AUDIO_SS="$3" \
  TOP_T="$4" BOT_T="$5" L1="$6" L2="$7" PAIRS="$8" \
    bash "$V/bin/diptych-reel.sh" 2>&1 | tail -1
}
if want success; then
echo "=== 3-success-glowup ==="
glow 01_glowup_yc phonk-hard 0 1400 "nobody was betting" "on that kid" \
"$P/20180409_204014_IMG_2101.jpg|1.579
$P/20180419_203302_IMG_2326.jpg|2.531
$P/20180427_153228_IMG_2464.jpg|3.019
$P/20180615_175346_IMG_3160.jpg|3.506
$P/20180622_212013_IMG_3194.jpg|3.831
$P/20180503_191633_IMG_2637.jpg|4.458" \
"$B/purple/IMG_8454.MOV|1.2|5.573
$BM/IMG_4943.MOV|6.0|6.385
$LAP|60.5|7.012" \
"$YC|9.567|YC founder at 18"
glow 02_glowup_name phonk-brazilian 0 1460 "they had a name" "for me in school" \
"$P/20180419_203306_IMG_2328.jpg|1.416
$P/20180427_153234_IMG_2466.jpg|1.904
$P/20180427_153231_IMG_2465.jpg|2.392
$P/20180615_175413_IMG_3161.jpg|2.856
$P/20180615_180529_IMG_3171.jpg|3.344" \
"$B/purple/IMG_8456.MOV|2.0|4.783
$LAP|60.5|5.503
$A/0618_140349_IMG_2447.MOV.MOV|1.0|6.200
$T/IMG_4910.MOV|1.0|7.175" \
"$YC|9.079|they use my full name now"
glow 03_glowup_slowest phonk-gym 0 1460 "i was the slowest kid" "in every race" \
"$P/20180415_171327_IMG_2168.jpg|1.277
$P/20180419_203304_IMG_2327.jpg|1.533
$P/20180421_160613_8A4FD91A-90AD-4A8E-9EA9-86B1AB283CD0.JPG.JPG.jpg|2.067
$P/20180427_154951_IMG_2472.jpg|2.833
$P/20180615_180001_IMG_3165.jpg|3.344" \
"$B/purple/IMG_8449.MOV|1.5|4.133
$LAP|60.5|4.899
$T/IMG_4968.MOV|25.4|5.689
$A/0618_140349_IMG_2447.MOV.MOV|1.0|6.594" \
"$YC|9.056|still running"
glow 04_glowup_discipline phonk-gym 0 1460 "i changed my body" "the same way" \
"$P/20180427_154931_IMG_2470.jpg|1.277
$P/20180615_175426_IMG_3162.jpg|2.067
$P/20180419_203306_IMG_2328.jpg|2.833
$P/20180615_180529_IMG_3171.jpg|3.344
$P/20180622_212046_IMG_3196.jpg|3.878" \
"$B/purple/IMG_8454.MOV|1.2|4.899
$DESK|1.0|5.689
$LAP|60.5|6.594
$WALK|2.0|7.500" \
"$YC|9.056|boring reps, every day"
glow 05_glowup_winner winner_is 0 1400 "for the kid who" "got picked last" \
"$P/20180409_204014_IMG_2101.jpg|2.4
$P/20180419_203304_IMG_2327.jpg|3.6
$P/20180427_154951_IMG_2472.jpg|4.7
$P/20180615_180116_IMG_3168.jpg|5.8
$P/20180622_212046_IMG_3196.jpg|6.9" \
"$B/purple/IMG_8454.MOV|1.2|8.4
$T/IMG_4958.MOV|0.2|9.6
$A/0618_140349_IMG_2447.MOV.MOV|1.0|10.8" \
"$YC|13.6|you made it out"
glow 06_glowup_plane phonk-dark 5.5 1400 "this kid had never" "been on a plane" \
"$P/20180415_171327_IMG_2168.jpg|1.28
$P/20180421_152622_IMG_2375.jpg|2.05
$P/20180427_154940_IMG_2471.jpg|2.72
$P/20180615_180049_IMG_3167.jpg|3.30
$P/20180622_212028_IMG_3195.jpg|3.90" \
"$T/IMG_4958.MOV|0.2|4.80
$T/IMG_4910.MOV|1.0|5.60
$T/IMG_4968.MOV|25.4|6.40
$A/0618_140349_IMG_2447.MOV.MOV|1.0|7.20" \
"$CLOSE|9.40|8000 miles from home"
glow 07_glowup_hometown phonk-gym 0 1400 "that kid never left" "his hometown" \
"$P/20180419_203302_IMG_2326.jpg|1.277
$P/20180421_152619_IMG_2374.jpg|2.067
$P/20180427_154931_IMG_2470.jpg|2.833
$P/20180615_180001_IMG_3165.jpg|3.344
$P/20180615_180529_IMG_3171.jpg|3.878" \
"$BM/IMG_4943.MOV|6.0|4.899
$K/0820_171934_IMG_4332.MOV.MOV|15.0|5.689
$T/IMG_4910.MOV|1.0|6.594
$A/0618_140349_IMG_2447.MOV.MOV|1.0|7.500" \
"$CLOSE|9.056|4 countries at 18"

dip 08_then_now phonk-hard 0 "2018" "2026" "same kid" "different room" \
"$P/20180409_204014_IMG_2101.jpg|$B/purple/IMG_8454.MOV|1.2|2.531
$P/20180427_153228_IMG_2464.jpg|$DESK|1.0|3.831
$P/20180615_175346_IMG_3160.jpg|$LAP|60.5|5.108
$P/20180622_212013_IMG_3194.jpg|$T/IMG_4910.MOV|1.0|6.385
$P/20180503_191633_IMG_2637.jpg|$A/0618_140349_IMG_2447.MOV.MOV|1.0|7.663
$P/20180419_203302_IMG_2326.jpg|$CLOSE|3.6|9.567"
dip 09_then_now_asked phonk-hard 0 "asked for advice" "stopped asking" "" "" \
"$P/20180415_171327_IMG_2168.jpg|$DESK|1.0|2.531
$P/20180427_153228_IMG_2464.jpg|$LAP|60.5|3.831
$P/20180427_154951_IMG_2472.jpg|$STK|0.5|5.108
$P/20180622_212028_IMG_3195.jpg|$T/IMG_4910.MOV|1.0|6.385
$P/20180419_203304_IMG_2327.jpg|$A/0618_140349_IMG_2447.MOV.MOV|1.0|7.663
$P/20180409_204014_IMG_2101.jpg|$YC|0|9.567"
dip 10_then_now_build phonk-brazilian 0 "wanted to build" "building" "" "" \
"$P/20180427_154931_IMG_2470.jpg|$DESK|1.0|1.904
$P/20180615_175426_IMG_3162.jpg|$LAP|60.5|2.856
$P/20180419_203306_IMG_2328.jpg|$STK|0.5|4.296
$P/20180615_180529_IMG_3171.jpg|$B/purple/IMG_8454.MOV|1.2|5.503
$P/20180421_152619_IMG_2374.jpg|$A/0610_214419_od_video-6222_singular_display.mov.mov|2.0|6.687
$P/20180409_204014_IMG_2101.jpg|$YC|0|9.079"
dip 11_then_now_quiet phonk-gym 0 "no one asked" "everyone asks" "" "" \
"$P/20180419_203304_IMG_2327.jpg|$DESK|1.0|2.322
$P/20180427_154951_IMG_2472.jpg|$LAP|60.5|3.344
$P/20180615_180116_IMG_3168.jpg|$STK|0.5|4.528
$P/20180622_212046_IMG_3196.jpg|$A/0618_140349_IMG_2447.MOV.MOV|1.9|5.689
$P/20180409_204014_IMG_2101.jpg|$YC|0|8.011"
dip 12_then_now_far phonk-dark 5.5 "his whole world" "one year later" "" "" \
"$P/20180427_153228_IMG_2464.jpg|$T/IMG_4910.MOV|1.0|2.345
$P/20180615_175346_IMG_3160.jpg|$T/IMG_4968.MOV|25.4|3.200
$P/20180622_212013_IMG_3194.jpg|$K/0820_171934_IMG_4332.MOV.MOV|15.0|4.100
$P/20180419_203302_IMG_2326.jpg|$A/0618_140349_IMG_2447.MOV.MOV|1.0|5.000
$P/20180409_204014_IMG_2101.jpg|$CLOSE|3.6|6.400"
dip 13_then_now_travel phonk-gym 0 "never left home" "4 countries later" "" "" \
"$P/20180415_171327_IMG_2168.jpg|$BM/IMG_4943.MOV|6.0|2.322
$P/20180419_203302_IMG_2326.jpg|$T/IMG_4958.MOV|0.2|3.344
$P/20180427_153228_IMG_2464.jpg|$T/IMG_4910.MOV|1.0|4.528
$P/20180615_175346_IMG_3160.jpg|$K/0820_171934_IMG_4332.MOV.MOV|2.0|5.689
$P/20180622_212013_IMG_3194.jpg|$K/0820_182523_IMG_4391.MOV.MOV|1.6|6.989
$P/20180503_191633_IMG_2637.jpg|$A/0618_140349_IMG_2447.MOV.MOV|1.0|8.266
$P/20180409_204014_IMG_2101.jpg|$CLOSE|3.6|9.500"
fi

# ─────────────────────────── 4. travel (supporting theme) ───────────────────────────
# Long tracks need a seek or the reel opens on a quiet intro and the drop never lands.
# Values from bin/music-map.py: seek = drop_time - ~6s.
audio_seek () { case "$1" in
    wishes) echo 34.3 ;; dont_tell_dreams) echo 26.0 ;; winner_is) echo 13.0 ;;
    trend_21977) echo 0.4 ;; trend_29894) echo 1.6 ;; *) echo 0 ;; esac; }

trav () { # trav <name> <audio> <l1> <l2> <e1> <e2> <open> <dur> <shots>
  done_already "$OUT/4-travel/$1.mp4" && return
  OUT="$OUT/4-travel/$1.mp4" AUDIO="$HOME/Downloads/music-good/$2.mp3" AUDIO_SS="$(audio_seek "$2")" \
  L1="$3" L2="$4" E1="$5" E2="$6" OPEN="$7" OPEN_D=2.50 DUR="$8" SHOTS="$9" \
    bash "$V/bin/travel-story-reel.sh" 2>&1 | tail -1
}
if want travel; then
echo "=== 4-travel ==="
trav 01_ladakh travel_trend "two years ago i had never" "left my city alone" "the world is smaller" "than they told you" \
"$T/IMG_4805.MOV|36.0" 14.05 \
"$T/IMG_4881.MOV|13.2|3.181|1
$T/IMG_4910.MOV|1.0|4.040|1
$T/IMG_4929.MOV|17.4|5.364|1
$T/IMG_4968.MOV|25.4|5.921|0
$T/IMG_4974.MOV|34.6|6.780|1
$T/IMG_4965.MOV|3.4|8.057|1
$T/IMG_4853.MOV|6.0|8.777|0
$T/IMG_4805.MOV|10.0|9.752|0
$T/IMG_4887.MOV|8.0|10.704|1
$T/IMG_4958.MOV|0.2|11.587|0
$T/IMG_2447.MOV|2.1|12.446|0
$CLOSE|3.6|14.05|0"
trav 02_from_the_air trend_21977 "i said yes before" "i checked the map" "best decision" "i never planned" \
"$T/IMG_9323.MOV|52.0" 14.05 \
"$T/IMG_9765.MOV|2.8|3.181|1
$T/IMG_9482.MOV|2.6|4.040|1
$T/IMG_4881.MOV|13.2|5.364|1
$T/IMG_5014.MOV|33.0|5.921|1
$T/IMG_4910.MOV|1.0|6.780|1
$T/IMG_4929.MOV|17.4|8.057|1
$T/IMG_4968.MOV|25.4|8.777|0
$T/IMG_4974.MOV|34.6|9.752|1
$T/IMG_4965.MOV|3.4|10.704|1
$T/IMG_4853.MOV|6.0|11.587|0
$T/IMG_9323.MOV|53.0|12.446|0
$CLOSE|3.6|14.05|0"
trav 03_dubai_nights wishes "the city i was in" "when everything started" "i still miss" "those drives" \
"$T/IMG_2637.MOV|4.0" 14.05 \
"$A/0610_214419_od_video-6222_singular_display.mov.mov|3.5|3.181|0
$A/0610_214835_od_video-6230_singular_display.mov.mov|5.0|4.040|0
$T/IMG_2637.MOV|8.0|5.364|0
$STK|0.5|5.921|0
$A/0611_214647_IMG_2135.MOV.MOV|2.0|6.780|0
$T/IMG_1867.MOV|2.5|8.057|0
$T/IMG_1770.MOV|13.8|8.777|0
$T/IMG_1898.MOV|2.6|9.752|0
$T/IMG_1521.MOV|133.0|10.704|0
$A/0610_214419_od_video-6222_singular_display.mov.mov|7.2|11.587|0
$LAP|60.5|12.446|0
$CLOSE|3.6|14.05|0"
trav 04_full_arc trend_36267 "one year, four countries" "one company" "say yes" "then figure it out" \
"$M/IMG_4935.MOV|2.0" 14.05 \
"$M/IMG_4568.MOV|3.0|3.181|0
$B/broll/0523_191247_od_video-4539_singular_display.mov.mov|1.5|4.040|0
$BM/IMG_4943.MOV|6.0|5.364|0
$T/IMG_4958.MOV|0.2|5.921|0
$A/0610_214835_od_video-6230_singular_display.mov.mov|3.0|6.780|0
$A/0618_140154_IMG_2442.MOV.MOV|1.0|8.057|0
$A/0614_120534_video-6838_singular_display.mov.mov|1.2|8.777|0
$T/IMG_4910.MOV|1.0|9.752|1
$T/IMG_4968.MOV|25.4|10.704|0
$K/0820_171934_IMG_4332.MOV.MOV|15.0|11.587|0
$LAP|60.5|12.446|0
$CLOSE|3.6|14.05|0"
trav 05_where_im_from trend_36267 "everyone here wanted" "the safe life for me" "i wanted" "to build something" \
"$M/IMG_4935.MOV|2.0" 14.05 \
"$B/broll/0523_191247_od_video-4539_singular_display.mov.mov|1.5|3.181|0
$M/IMG_4568.MOV|3.0|4.040|0
$M/IMG_4578.MOV|4.0|5.364|0
$M/IMG_4590.MOV|2.0|5.921|0
$T/IMG_3681.MOV|0.5|6.780|1
$M/IMG_4988.MOV|3.0|8.057|0
$T/IMG_3748.MOV|1.0|8.777|1
$M/IMG_4935.MOV|10.0|9.752|0
$BM/IMG_4943.MOV|6.0|10.704|0
$T/IMG_4958.MOV|0.2|11.587|0
$A/0618_140349_IMG_2447.MOV.MOV|1.0|12.446|0
$LAP|60.5|14.05|0"
trav 06_departure_bom dont_tell_dreams "leaving home" "never gets easier" "see you" "in a few months" \
"$BM/IMG_4940.MOV|1.5" 14.05 \
"$BM/IMG_4942.MOV|1.5|3.181|0
$BM/IMG_4942.MOV|3.4|4.040|0
$BM/IMG_4943.MOV|10.0|5.364|0
$BM/IMG_4947.MOV|8.5|5.921|0
$BM/IMG_4958.MOV|0.7|6.780|0
$BM/IMG_4959.MOV|4.4|8.057|0
$BM/IMG_4960.MOV|1.4|8.777|0
$BM/IMG_4961.MOV|7.2|9.752|0
$BM/IMG_4949.MOV|19.0|10.704|0
$T/IMG_4958.MOV|0.2|11.587|0
$A/0618_140349_IMG_2447.MOV.MOV|1.9|12.446|0
$CLOSE|3.6|14.05|0"
trav 07_us_year wishes "i landed here with" "two suitcases" "give it two years" "you won't recognise it" \
"$T/IMG_4958.MOV|0.2" 14.05 \
"$A/0618_140154_IMG_2442.MOV.MOV|1.0|3.181|0
$A/0618_140349_IMG_2447.MOV.MOV|1.0|4.040|0
$A/0618_140410_IMG_2452.MOV.MOV|1.5|5.364|0
$T/IMG_3331.MOV|3.0|5.921|1
$A/0614_113007_video-6811_singular_display.mov.mov|2.0|6.780|0
$A/0614_120534_video-6838_singular_display.mov.mov|1.2|8.057|0
$A/0614_122917_video-6832_singular_display.mov.mov|4.0|8.777|0
$A/0611_085357_video-6314_singular_display.mov.mov|2.0|9.752|0
$B/broll/0522_192342_video-4382_singular_display.mov.mov|6.0|10.704|0
$B/broll/0523_182630_video-4501_singular_display.mov.mov|2.0|11.587|0
$LAP|60.5|12.446|0
$SUN|3.0|14.05|0"
trav 08_kerala trend_21977 "three weeks in kerala" "still thinking about it" "go before" "you're ready" \
"$K/0820_181056_IMG_4382.MOV.MOV|1.6" 14.05 \
"$K/0819_151621_IMG_4230.MOV.MOV|1.2|3.181|0
$K/0819_151855_IMG_4232.MOV.MOV|8.5|4.040|0
$K/0820_171934_IMG_4332.MOV.MOV|15.0|5.364|0
$K/0820_171934_IMG_4332.MOV.MOV|20.0|5.921|0
$K/0820_182543_IMG_4392.MOV.MOV|5.0|6.780|0
$K/0820_174214_IMG_4367.MOV.MOV|6.0|8.057|0
$K/0820_181056_IMG_4382.MOV.MOV|3.0|8.777|0
$T/IMG_4853.MOV|6.0|9.752|0
$K/0819_151855_IMG_4232.MOV.MOV|11.0|10.704|0
$SUN|3.0|11.587|0
$WALK|2.0|12.446|0
$CLOSE|3.6|14.05|0"
trav 09_quiet_part travel_trend "i built for two years" "without telling anyone" "the quiet part" "is the whole part" \
"$K/0820_181056_IMG_4382.MOV.MOV|1.6" 14.05 \
"$K/0820_182543_IMG_4392.MOV.MOV|5.0|3.181|0
$K/0819_151621_IMG_4230.MOV.MOV|1.2|4.040|0
$K/0819_151855_IMG_4232.MOV.MOV|8.5|5.364|0
$K/0820_171934_IMG_4332.MOV.MOV|15.0|5.921|0
$K/0820_171934_IMG_4332.MOV.MOV|20.0|6.780|0
$T/IMG_4853.MOV|6.0|8.057|0
$K/0820_174214_IMG_4367.MOV.MOV|6.0|8.777|0
$T/IMG_4805.MOV|36.0|9.752|0
$T/IMG_4910.MOV|1.0|10.704|1
$SUN|3.0|11.587|0
$WALK|2.0|12.446|0
$CLOSE|3.6|14.05|0"
trav 10_go_alone trend_21977 "i stopped waiting for" "someone to come with me" "go alone" "go now" \
"$K/0820_182543_IMG_4392.MOV.MOV|5.0" 14.05 \
"$K/0819_151621_IMG_4230.MOV.MOV|1.2|3.181|0
$K/0819_151855_IMG_4232.MOV.MOV|8.5|4.040|0
$K/0820_181056_IMG_4382.MOV.MOV|1.6|5.364|0
$K/0820_171934_IMG_4332.MOV.MOV|15.0|5.921|0
$K/0820_171934_IMG_4332.MOV.MOV|20.0|6.780|0
$K/0820_174214_IMG_4367.MOV.MOV|6.0|8.057|0
$K/0819_151855_IMG_4232.MOV.MOV|11.0|8.777|0
$T/IMG_4853.MOV|6.0|9.752|0
$K/0820_181056_IMG_4382.MOV.MOV|3.0|10.704|0
$SUN|3.0|11.587|0
$WALK|2.0|12.446|0
$CLOSE|3.6|14.05|0"
trav 11_night_to_mountain trend_29085 "the year i stopped" "asking for permission" "look where" "it went" \
"$A/0610_214419_od_video-6222_singular_display.mov.mov|2.0" 12.60 \
"$A/0610_214835_od_video-6230_singular_display.mov.mov|3.0|2.902|0
$STK|0.5|3.460|0
$LAP|60.5|4.017|0
$BM/IMG_4943.MOV|6.0|4.574|0
$T/IMG_4958.MOV|0.2|5.132|0
$T/IMG_4881.MOV|13.2|5.689|1
$T/IMG_4910.MOV|1.0|6.223|1
$T/IMG_4968.MOV|25.4|6.780|0
$T/IMG_4974.MOV|34.6|7.338|1
$A/0618_140349_IMG_2447.MOV.MOV|1.0|8.500|0
$SUN|3.0|10.000|0
$CLOSE|3.6|12.60|0"
fi

echo
echo "=== phone previews ==="
for d in 1-yc-startups 2-lessons 3-success-glowup 4-travel 5-talking-head; do
  for f in "$OUT/$d"/*.mp4; do
    [ -f "$f" ] || continue
    n=$(basename "$f")
    [ "$OUT/phone/$d/$n" -nt "$f" ] 2>/dev/null && continue
    ffmpeg -nostdin -v error -i "$f" -vf "scale=608:1080" -c:v libx264 -crf 26 -preset veryfast \
      -c:a aac -b:a 128k -movflags +faststart "$OUT/phone/$d/$n" -y 2>/dev/null \
      || ffmpeg -nostdin -v error -i "$f" -vf "scale=608:1080" -c:v libx264 -crf 26 -preset veryfast \
         -an -movflags +faststart "$OUT/phone/$d/$n" -y
  done
  echo "  $d: $(ls "$OUT/$d"/*.mp4 2>/dev/null | wc -l | tr -d ' ')"
done
