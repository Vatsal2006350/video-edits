#!/usr/bin/env python3
"""Read-only Instagram account audit: what is driving follows, and what is not.

    python3 bin/ig-audit.py pull      # Graph API -> analytics/ig-audit-<date>.json (never publishes)
    python3 bin/ig-audit.py report    # newest pull -> tables on stdout + analytics/ig-audit-<date>.md

Same token/keychain as trial-reel-learning.py. Every figure printed is from the API response;
nothing is extrapolated except the rows explicitly labelled "projection".
Metric names drift between Graph versions, so `pull` probes one reel and keeps what the API accepts.
"""
import datetime as dt, importlib.util, json, re, statistics, sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trl", ROOT / "bin/trial-reel-learning.py")
trl = importlib.util.module_from_spec(spec); spec.loader.exec_module(trl)
TZ = ZoneInfo("America/Detroit")
OUT = ROOT / "analytics"
REEL_METRICS = ["views", "reach", "likes", "comments", "saved", "shares", "total_interactions",
                "ig_reels_avg_watch_time", "ig_reels_video_view_total_time", "reels_skip_rate",
                "reposts", "follows", "profile_visits"]
ACCOUNT_TOTALS = ["views", "reach", "accounts_engaged", "total_interactions", "profile_views",
                  "follows_and_unfollows", "likes", "comments", "shares", "saves", "profile_links_taps"]


def try_get(path, **params):
    try:
        return trl.get(path, **params), None
    except RuntimeError as e:
        return None, str(e)


def pull():
    now = dt.datetime.now(dt.timezone.utc)
    data = {"pulled_at": now.isoformat(), "errors": {}}
    prof, err = try_get(trl.USER_ID, fields="username,followers_count,follows_count,media_count,biography,name")
    data["profile"] = prof or {}
    if err: data["errors"]["profile"] = err

    # media list
    media, after = [], None
    while True:
        params = dict(fields="id,timestamp,media_type,media_product_type,caption,permalink,like_count,comments_count", limit=50)
        if after: params["after"] = after
        page = trl.get(f"{trl.USER_ID}/media", **params)
        media += page.get("data", [])
        after = page.get("paging", {}).get("cursors", {}).get("after")
        if not after or not page.get("paging", {}).get("next"): break
    reels = [m for m in media if m.get("media_product_type") == "REELS"]

    # probe which reel metrics this API version accepts
    ok = []
    if reels:
        probe = reels[min(5, len(reels) - 1)]["id"]
        for name in REEL_METRICS:
            r, e = try_get(f"{probe}/insights", metric=name)
            if r is not None: ok.append(name)
            else: data["errors"][f"reel_metric:{name}"] = e
    data["reel_metrics_accepted"] = ok
    for i, m in enumerate(reels):
        r, e = try_get(f"{m['id']}/insights", metric=",".join(ok))
        m["insights"] = {d["name"]: d["values"][0]["value"] for d in (r or {}).get("data", [])}
        if e: m["insights_error"] = e
        if i % 40 == 0: print(f"  reels {i}/{len(reels)}", file=sys.stderr)
    data["media"] = media

    # account totals, 3 windows
    data["account"] = {}
    for days in (7, 30, 90):
        since = int((now - dt.timedelta(days=days)).timestamp()); until = int(now.timestamp())
        win = {}
        for name in ACCOUNT_TOTALS:
            r, e = try_get(f"{trl.USER_ID}/insights", metric=name, period="day", metric_type="total_value",
                           since=since, until=until)
            if r and r.get("data"):
                win[name] = r["data"][0].get("total_value", {}).get("value")
            elif days == 30 and e: data["errors"][f"account:{name}"] = e
        data["account"][f"last_{days}d"] = win
    # follow type breakdown + views by follower/non-follower, 30d
    since = int((now - dt.timedelta(days=30)).timestamp()); until = int(now.timestamp())
    for name, bd in (("follows_and_unfollows", "follow_type"), ("views", "follow_type"),
                     ("views", "media_product_type"), ("reach", "follow_type"), ("reach", "media_product_type")):
        r, e = try_get(f"{trl.USER_ID}/insights", metric=name, period="day", metric_type="total_value",
                       breakdown=bd, since=since, until=until)
        key = f"{name}_by_{bd}_30d"
        if r and r.get("data"):
            tv = r["data"][0].get("total_value", {})
            data["account"][key] = {"/".join(x["dimension_values"]): x["value"]
                                    for b in tv.get("breakdowns", []) for x in b.get("results", [])}
        elif e: data["errors"][key] = e
    # daily follower_count time series (API allows last 30 days)
    r, e = try_get(f"{trl.USER_ID}/insights", metric="follower_count,reach", period="day", since=since, until=until)
    if r:
        data["account"]["daily"] = {d["name"]: [(v.get("end_time"), v.get("value")) for v in d.get("values", [])]
                                    for d in r.get("data", [])}
    elif e: data["errors"]["daily"] = e
    # audience
    for metric in ("follower_demographics", "engaged_audience_demographics"):
        for bd in ("country", "city", "age", "gender"):
            r, e = try_get(f"{trl.USER_ID}/insights", metric=metric, period="lifetime", metric_type="total_value",
                           timeframe="this_month", breakdown=bd)
            key = f"{metric}_{bd}"
            if r and r.get("data"):
                tv = r["data"][0].get("total_value", {})
                rows = {"/".join(x["dimension_values"]): x["value"]
                        for b in tv.get("breakdowns", []) for x in b.get("results", [])}
                data["account"][key] = dict(sorted(rows.items(), key=lambda kv: -kv[1])[:12])
            elif e: data["errors"][key] = e
    r, e = try_get(f"{trl.USER_ID}/insights", metric="online_followers", period="lifetime")
    if r and r.get("data"): data["account"]["online_followers"] = r["data"][0].get("values", [])[-3:]

    out = OUT / f"ig-audit-{dt.date.today()}.json"
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    print(f"{len(reels)} reels, metrics {ok} -> {out}")
    if data["errors"]: print("not available:", ", ".join(sorted(data["errors"])))


THEMES = [("yc/founder", r"\byc\b|y combinator|founder|startup|interview|raise|investor|amplify"),
          ("claude/ai-edit", r"claude|\bai\b|agent|edited|skill|codex|prompt"),
          ("identity/proof", r"prove|doubt|priorit|focus|believe|nobody|no one|next move|glow|140 ?kg|weight|lost"),
          ("student/umich", r"umich|michigan|college|student|exam|ib\b|campus|class"),
          ("culture/myth", r"ramayan|mahabharat|yuga|parashu|krishna|shiva|diwali|india|desi|mumbai"),
          ("birthday/family", r"birthday|mom|mother|dad|family|cake"),
          ("travel/life", r"travel|kerala|dubai|flight|airport|trip|beach|sunset"),
          ("music", r"guitar|sing|song|cover|piano")]


def theme(caption):
    c = (caption or "").lower()
    for name, pat in THEMES:
        if re.search(pat, c): return name
    return "other"


def report():
    files = sorted(OUT.glob("ig-audit-*.json"))
    if not files: sys.exit("run `pull` first")
    d = json.loads(files[-1].read_text()); L = []
    P = lambda s="": L.append(s)
    now = dt.datetime.fromisoformat(d["pulled_at"])
    prof, acct = d.get("profile", {}), d.get("account", {})
    P(f"# Instagram audit — pulled {now.astimezone(TZ):%Y-%m-%d %H:%M} Detroit (read-only Graph API)\n")
    P(f"Followers **{prof.get('followers_count')}**, following {prof.get('follows_count')}, media {prof.get('media_count')}.")
    P(f"Bio: {prof.get('biography')!r}\n")
    P("## Account totals\n| window | " + " | ".join(ACCOUNT_TOTALS) + " |\n|---|" + "---|" * len(ACCOUNT_TOTALS))
    for w in ("last_7d", "last_30d", "last_90d"):
        P(f"| {w} | " + " | ".join(str(acct.get(w, {}).get(m, "–")) for m in ACCOUNT_TOTALS) + " |")
    for k in sorted(acct):
        if "_by_" in k or "demographics" in k: P(f"\n**{k}**: {acct[k]}")
    daily = acct.get("daily", {}).get("follower_count") or []
    if daily:
        vals = [v for _, v in daily if v is not None]
        P(f"\nNew followers per day, last {len(vals)} days: total {sum(vals)}, median {statistics.median(vals)}, "
          f"best {max(vals)}, last 7 {vals[-7:]}")

    # Fallback: a token without instagram_manage_insights still lists media. Join the newest
    # reel-timing CSV (same API, earlier pull) by media id so the report still says something,
    # and say which day those numbers are from.
    if not any(m.get("insights") for m in d["media"]):
        import csv
        csvs = sorted(OUT.glob("reel-timing-*.csv"))
        if csvs:
            old = {r["id"]: r for r in csv.DictReader(open(csvs[-1]))}
            for m in d["media"]:
                o = old.get(m["id"])
                if o: m["insights"] = dict(views=int(o["views"]), reach=int(o["reach"]), shares=int(o["shares"]),
                                           saved=int(o["saved"]), likes=m.get("like_count", int(o["likes"])),
                                           comments=m.get("comments_count", 0),
                                           ig_reels_avg_watch_time=float(o["avg_watch_s"]) * 1000)
            P(f"\n> **Insights are NOT from today.** Today's token has no `instagram_manage_insights`; per-reel "
              f"views/reach/shares/saves/watch below are from `{csvs[-1].name}`. Followers, likes and comments are live.")
    reels = []
    for m in d["media"]:
        if m.get("media_product_type") != "REELS" or not m.get("insights"): continue
        i = m["insights"]; t = dt.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00"))
        reach = i.get("reach") or 0
        reels.append(dict(t=t, age_d=(now - t).days, views=i.get("views", 0), reach=reach, shares=i.get("shares", 0),
                          saved=i.get("saved", 0), likes=i.get("likes", m.get("like_count", 0)), comments=i.get("comments", 0),
                          watch=(i.get("ig_reels_avg_watch_time") or 0) / 1000, skip=i.get("reels_skip_rate"),
                          follows=i.get("follows"), cap=(m.get("caption") or "").replace("\n", " "),
                          url=m.get("permalink"), theme=theme(m.get("caption")),
                          sr=100 * i.get("shares", 0) / reach if reach else 0, sv=100 * i.get("saved", 0) / reach if reach else 0))
    settled = [r for r in reels if r["age_d"] >= 3]
    tot = sum(r["views"] for r in reels)
    if not tot:
        print("\n".join(L)); sys.exit("no reel insights available (token lacks instagram_manage_insights and no reel-timing CSV)")
    top = sorted(reels, key=lambda r: -r["views"])
    P(f"\n## Reels: {len(reels)} with insights, {tot:,} lifetime views")
    P(f"Top 3 = {100 * sum(r['views'] for r in top[:3]) / tot:.1f}% of views, top 10 = {100 * sum(r['views'] for r in top[:10]) / tot:.1f}%. "
      f"Median reel {statistics.median(r['views'] for r in settled):,.0f} views; "
      f"{sum(1 for r in settled if r['views'] < 1000)} of {len(settled)} settled reels under 1K, "
      f"{sum(1 for r in settled if r['views'] >= 10000)} over 10K.")
    P("\n### Top 12 by views\n| date | views | reach | shares/reach | saves/reach | avg watch s | skip | caption |\n|---|---|---|---|---|---|---|---|")
    for r in top[:12]:
        P(f"| {r['t'].astimezone(TZ):%m-%d} | {r['views']:,} | {r['reach']:,} | {r['sr']:.2f}% | {r['sv']:.2f}% | {r['watch']:.1f} | {r['skip'] if r['skip'] is not None else '–'} | {r['cap'][:60]} |")
    P("\n### Sequel seeds: high intent, low reach (reach 500+, not top 12, ranked by shares+saves per reach)\n| date | views | shares/reach | saves/reach | avg watch s | caption |\n|---|---|---|---|---|---|")
    seeds = sorted([r for r in settled if r["reach"] >= 500 and r not in top[:12]], key=lambda r: -(r["sr"] + r["sv"]))
    for r in seeds[:10]:
        P(f"| {r['t'].astimezone(TZ):%m-%d} | {r['views']:,} | {r['sr']:.2f}% | {r['sv']:.2f}% | {r['watch']:.1f} | {r['cap'][:70]} |")
    P("\n### By month\n| month | reels | total views | median views | reels ≥10K | median shares/reach |\n|---|---|---|---|---|---|")
    for mo in sorted({r["t"].astimezone(TZ).strftime("%Y-%m") for r in reels}):
        g = [r for r in reels if r["t"].astimezone(TZ).strftime("%Y-%m") == mo]
        P(f"| {mo} | {len(g)} | {sum(r['views'] for r in g):,} | {statistics.median(r['views'] for r in g):,.0f} | "
          f"{sum(1 for r in g if r['views'] >= 10000)} | {statistics.median(r['sr'] for r in g):.2f}% |")
    P("\n### By theme (caption keywords, directional; settled reels)\n| theme | reels | median views | best | ≥10K | median shares/reach | median saves/reach | median watch s |\n|---|---|---|---|---|---|---|---|")
    for th in sorted({r["theme"] for r in settled}, key=lambda th: -statistics.median(r["views"] for r in settled if r["theme"] == th)):
        g = [r for r in settled if r["theme"] == th]
        P(f"| {th} | {len(g)} | {statistics.median(r['views'] for r in g):,.0f} | {max(r['views'] for r in g):,} | "
          f"{sum(1 for r in g if r['views'] >= 10000)} | {statistics.median(r['sr'] for r in g):.2f}% | "
          f"{statistics.median(r['sv'] for r in g):.2f}% | {statistics.median(r['watch'] for r in g):.1f} |")
    P("\n### Last 30 days vs before (settled)\n| period | reels | reels/day | median views | ≥10K | median watch s |\n|---|---|---|---|---|---|")
    for name, g in (("last 30d", [r for r in settled if r["age_d"] <= 30]), ("31-60d", [r for r in settled if 30 < r["age_d"] <= 60]),
                    ("older", [r for r in settled if r["age_d"] > 60])):
        if g:
            span = max(1, max(r["age_d"] for r in g) - min(r["age_d"] for r in g) + 1)
            P(f"| {name} | {len(g)} | {len(g) / span:.1f} | {statistics.median(r['views'] for r in g):,.0f} | "
              f"{sum(1 for r in g if r['views'] >= 10000)} | {statistics.median(r['watch'] for r in g):.1f} |")
    f30 = acct.get("last_30d", {}).get("follows_and_unfollows"); v30 = acct.get("last_30d", {}).get("views")
    fol = prof.get("followers_count")
    if fol:
        P(f"\n## Gap to 10K\nNeed **{10000 - fol:,}** more followers.")
        if daily:
            vals = [v for _, v in daily if v is not None]; rate = sum(vals) / max(1, len(vals))
            if rate > 0: P(f"Projection at the last-{len(vals)}-day gross follow rate ({rate:.1f}/day, unfollows not subtracted): {(10000 - fol) / rate:.0f} days.")
    if d.get("errors"): P("\n_Not available from this token/API version: " + ", ".join(sorted(d["errors"])) + "_")
    text = "\n".join(L); print(text)
    (OUT / f"ig-audit-{dt.date.today()}.md").write_text(text + "\n")


if __name__ == "__main__":
    {"pull": pull, "report": report}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
