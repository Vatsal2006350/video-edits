#!/usr/bin/env python3
"""Forced alignment of whisper output against the audio (wav2vec2 phoneme alignment).

Whisper derives word times from decoder cross-attention, which jitters by up to ~0.3s.
Forced alignment matches the known transcript to the waveform frame by frame, so the
timings land on the actual attack of each word. Run with the whisperx venv's python.

  force-align.py <audio.wav> <whisper.json> <out.json>
"""
import json, sys, warnings
warnings.filterwarnings('ignore')
import whisperx

audio_path, wjson, out = sys.argv[1], sys.argv[2], sys.argv[3]
device = "cpu"

d = json.load(open(wjson))
segments = [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in d["segments"]]

audio = whisperx.load_audio(audio_path)
model_a, meta = whisperx.load_align_model(language_code="en", device=device)
res = whisperx.align(segments, model_a, meta, audio, device, return_char_alignments=False)

words = []
for s in res["segments"]:
    for w in s.get("words", []):
        if "start" in w and "end" in w:
            words.append({"word": w["word"], "start": float(w["start"]), "end": float(w["end"])})
json.dump({"segments": [{"words": words}]}, open(out, "w"))
print(f"aligned {len(words)} words -> {out}")
