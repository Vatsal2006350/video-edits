#!/usr/bin/env python3
"""Scenario simulation for YC reel tests; not an Instagram prediction API."""
from __future__ import annotations

import json
import math
import random
import statistics
from pathlib import Path

SEED = 20260911
RUNS = 100_000
random.seed(SEED)

# Account evidence: recent receipt-led winners had 124,563 / 137,168 / 318,999
# views. The mixture also includes a weak-test state because those three winners
# are not a representative sample of every upload.
states = (
    (0.47, 24_000, 0.72),
    (0.43, 130_000, 0.43),
    (0.10, 319_000, 0.34),
)
variants = {
    "professional-outdoor": 1.15,
    "bad-dream-origin": 1.10,
    "opportunity-calls": 1.02,
    "college-tradeoff": 0.98,
}

def sample_views(score: float) -> int:
    r = random.random()
    acc = 0.0
    for weight, median, sigma in states:
        acc += weight
        if r <= acc:
            # Clamp outlandish tails; actual reach can still exceed this model.
            return round(min(1_500_000, random.lognormvariate(math.log(median), sigma) * score))
    raise AssertionError

def quantile(xs: list[int], q: float) -> int:
    return sorted(xs)[round((len(xs) - 1) * q)]

samples = {name: [sample_views(score) for _ in range(RUNS)] for name, score in variants.items()}
batch_totals = [sum(samples[name][i] for name in variants) for i in range(RUNS)]
batch_max = [max(samples[name][i] for name in variants) for i in range(RUNS)]

# Observed follows/view across the three supplied top reels: 0.302%-0.477%.
# This triangular draw is conditional on a clear follow CTA/profile conversion.
batch_follows = [round(v * random.triangular(.00302, .00477, .00346)) for v in batch_totals]
gap = 1_828
result = {
    "model": "three-state Monte Carlo scenario model (not a platform forecast)",
    "seed": SEED,
    "runs": RUNS,
    "inputs": {
        "known_top_reel_views": [318999, 137168, 124563],
        "known_follow_per_view_range": [0.00302, 0.00477],
        "follower_gap": gap,
    },
    "variants": {},
    "batch": {
        "views_p10_p50_p90": [quantile(batch_totals, q) for q in (.1, .5, .9)],
        "max_reel_p50": quantile(batch_max, .5),
        "chance_total_views_at_least_528k": sum(v >= 528000 for v in batch_totals) / RUNS,
        "follows_p10_p50_p90": [quantile(batch_follows, q) for q in (.1, .5, .9)],
        "chance_closes_1828_follower_gap": sum(v >= gap for v in batch_follows) / RUNS,
    },
    "limitations": [
        "Only three first-party winning-reel view counts were available; non-winner history is approximated.",
        "Audio popularity, retention, posting time, distribution, and creative quality are not available from an Instagram prediction API.",
        "Use Trial Reel retention and follows/view to replace these priors after each post.",
    ],
}
for name, xs in samples.items():
    result["variants"][name] = {
        "views_p10_p50_p90": [quantile(xs, q) for q in (.1, .5, .9)],
        "chance_over_100k": sum(v >= 100000 for v in xs) / RUNS,
        "chance_over_300k": sum(v >= 300000 for v in xs) / RUNS,
    }

out = Path("analytics/yc-trend-pack-simulation.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
