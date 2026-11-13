#!/usr/bin/env python3
"""Read-only pull of every reel's post time + insights, then views by hour / weekday (America/Detroit).

    python3 bin/reel-timing.py            # writes analytics/reel-timing-<date>.csv and prints the tables

Used to choose posting slots for a schedule. Read-only Graph API (same token/keychain as
trial-reel-learning.py); it never publishes. Medians, not means: one 750K reel would own a mean.
"""
import csv, datetime as dt, importlib.util, statistics, sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trl", ROOT / "bin/trial-reel-learning.py")
trl = importlib.util.module_from_spec(spec); spec.loader.exec_module(trl)
TZ = ZoneInfo("America/Detroit")


def main():
    rows, after = [], None
    while True:
        params = dict(fields="id,timestamp,media_product_type,caption,permalink,like_count,comments_count", limit=50)
        if after: params["after"] = after
        page = trl.get(f"{trl.USER_ID}/media", **params)
        for m in page.get("data", []):
            if m.get("media_product_type") != "REELS": continue
            try:
                ins = trl.get(f"{m['id']}/insights", metric="views,reach,shares,saved,ig_reels_avg_watch_time")
                vals = {d["name"]: d["values"][0]["value"] for d in ins.get("data", [])}
            except RuntimeError:
                continue
            t = dt.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")).astimezone(TZ)
            rows.append(dict(id=m["id"], local=t.isoformat(), weekday=t.strftime("%a"), hour=t.hour,
                             views=vals.get("views", 0), reach=vals.get("reach", 0), shares=vals.get("shares", 0),
                             saved=vals.get("saved", 0), likes=m.get("like_count", 0),
                             avg_watch_s=round(vals.get("ig_reels_avg_watch_time", 0) / 1000, 2),
                             caption=(m.get("caption") or "").replace("\n", " ")[:80], permalink=m.get("permalink")))
        after = page.get("paging", {}).get("cursors", {}).get("after")
        if not after or not page.get("paging", {}).get("next"): break
    out = ROOT / f"analytics/reel-timing-{dt.date.today()}.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} reels -> {out}")
    now = dt.datetime.now(TZ)
    old = [r for r in rows if (now - dt.datetime.fromisoformat(r["local"])).days >= 3]   # settled reels only
    def table(key, order):
        print(f"\nby {key}: n, median views, median shares/reach %, share of reels over 5K views")
        for k in order:
            g = [r for r in old if r[key] == k]
            if len(g) < 3: continue
            mv = statistics.median(r["views"] for r in g)
            sr = statistics.median(100 * r["shares"] / r["reach"] if r["reach"] else 0 for r in g)
            hit = 100 * sum(1 for r in g if r["views"] >= 5000) / len(g)
            print(f"  {str(k):>4}  n={len(g):3d}  med views {mv:8.0f}  shares/reach {sr:5.2f}%  >=5K {hit:4.0f}%")
    table("hour", range(24)); table("weekday", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    def band(h): return "morning 7-11" if 7 <= h < 12 else "midday 12-16" if 12 <= h < 17 else "evening 17-22" if 17 <= h < 23 else "night 23-6"
    for r in old: r["band"] = band(r["hour"])
    table("band", ["morning 7-11", "midday 12-16", "evening 17-22", "night 23-6"])


if __name__ == "__main__":
    main()
