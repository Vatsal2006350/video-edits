#!/usr/bin/env python3
"""pick_cuts.py <beats.txt> <n_scenes> — choose n+1 beat boundaries >=1.6s apart."""
import sys
bs=[float(l) for l in open(sys.argv[1]) if l.strip()]
n=int(sys.argv[2])
picks=[bs[0]] if bs else [0.0]
for b in bs:
    if b-picks[-1] >= 1.6:
        picks.append(b)
    if len(picks) > n: break
while len(picks) <= n:
    picks.append(picks[-1]+2.0)
print('\n'.join('%.3f' % p for p in picks))
