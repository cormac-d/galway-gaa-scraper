"""Enumerate the seasons the Galway results platform will still serve.

What the structure probe found
------------------------------
The results page (/results/) has no season control at all - only fdate and
tdate. That is why date-chunking across 2025 returned nothing: the endpoint is
scoped to the current season whatever dates you hand it. The backfill was never
going to work that way.

The competitions page is different. It carries:

    <select id="select_level">
      <option value=""     seasonid="">Select Code</option>
      <!-- <option value="6929" seasonid="3070">Football</option>
           <option value="44"   seasonid="3057">Hurling</option> -->
      <option value="6929" seasonid="3976">Football</option>
      <option value="44"   seasonid="3958">Hurling</option>
    </select>

and drives it with

    POST /wp-admin/admin-ajax.php
        action   = Get_competition_data
        value    = 6929 (football) | 44 (hurling)
        seasonid = <season key>

So season is a first-class parameter, 6929 is football, and 3070 is a season
they previously had live and have since commented out - almost certainly the
one before 3976.

This script sweeps seasonid, records every season that still returns football
competitions, and then dates each one by reading real match dates off one of
its competition pages. That gives a seasonid -> year map, which is all the
scraper needs to backfill properly.
"""

import os
import re
import json
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE = "https://www.galwaygaa.ie"
AJAX = f"{BASE}/wp-admin/admin-ajax.php"
FOOTBALL = "6929"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE}/competitions/",
}

# Seasons known to exist from the markup: 3976 current football, 3070 the
# commented-out older one. Sweep generously around both.
SWEEP = list(range(2900, 4100))

PAUSE = 0.12
TIMEOUT = 25

session = requests.Session()
session.headers.update(HEADERS)
out = []


def w(line=""):
    out.append(line)


def fetch_season(seasonid):
    """Ask for the football competitions in one season."""
    try:
        r = session.post(
            AJAX,
            data={"action": "Get_competition_data",
                  "value": FOOTBALL,
                  "seasonid": str(seasonid)},
            timeout=TIMEOUT,
        )
    except Exception as exc:
        return None, f"error {type(exc).__name__}"
    if r.status_code != 200:
        return None, f"http {r.status_code}"
    body = r.text.strip()
    if not body or body in ("0", "-1", "null", "[]", "{}"):
        return None, "empty"
    try:
        return r.json(), "json"
    except Exception:
        return body, "text"


def ids_and_names(payload):
    """Pull competition ids and names out of whatever shape came back."""
    blob = payload if isinstance(payload, str) else json.dumps(payload)
    ids = sorted({int(i) for i in re.findall(r'"?(?:competition_?id|id)"?\s*[:=]\s*"?(\d{5,7})"?', blob)})
    if not ids:
        ids = sorted({int(i) for i in re.findall(r"/league/(\d+)", blob)})
    names = re.findall(r'"(?:name|competition_name|title)"\s*:\s*"([^"]{4,80})"', blob)
    return ids, names[:12], len(blob)


def date_a_competition(cid):
    """Read real match dates off a competition page to pin its year."""
    try:
        r = session.get(f"{BASE}/league/{cid}", timeout=TIMEOUT,
                        headers={"Accept": "text/html"})
    except Exception:
        return None, None
    if r.status_code != 200:
        return None, None
    soup = BeautifulSoup(r.text, "html.parser")

    # Match rows carry data-date="07 Nov 2026" on this platform.
    dates = [el.get("data-date") for el in soup.select("[data-date]")
             if el.get("data-date")]
    if not dates:
        dates = re.findall(r"\b\d{1,2}\s+[A-Z][a-z]{2}\s+(?:19|20)\d\d\b", r.text)
    years = sorted({int(m.group()) for d in dates
                    for m in [re.search(r"(?:19|20)\d\d", d)] if m})

    title = None
    for sel in ("h1", "h2", ".comp-name"):
        el = soup.select_one(sel)
        if el and el.get_text(strip=True) and el.get_text(strip=True).lower() != "league":
            title = el.get_text(strip=True)
            break
    return years, (title or "")[:90]


def main():
    os.makedirs("data", exist_ok=True)
    w("# Season enumeration")
    w()
    w(f"Run {datetime.utcnow():%Y-%m-%d %H:%M} UTC")
    w()
    w("The results page has no season control, only fdate/tdate, which is why "
      "date-chunking earlier years returned nothing. The competitions page "
      "drives a `seasonid` parameter through admin-ajax.php instead. This "
      "sweeps that parameter for football (value=6929).")
    w()

    hits = {}
    for sid in SWEEP:
        payload, how = fetch_season(sid)
        time.sleep(PAUSE)
        if payload is None:
            continue
        ids, names, size = ids_and_names(payload)
        if not ids:
            continue
        hits[sid] = {"ids": ids, "names": names, "size": size, "how": how}
        print(f"seasonid {sid}: {len(ids)} competitions ({how}, {size}b)")

    w(f"## Seasons returning football competitions: {len(hits)}")
    w()
    if not hits:
        w("None. Either the parameter needs a nonce or a logged-in session, "
          "or the endpoint only answers for the live season.")
    else:
        w("| seasonid | competitions | id range | sample names |")
        w("|---|---|---|---|")
        for sid in sorted(hits):
            h = hits[sid]
            rng = f"{min(h['ids'])}-{max(h['ids'])}" if h["ids"] else "-"
            w(f"| {sid} | {len(h['ids'])} | {rng} | "
              f"{', '.join(h['names'][:3])[:70]} |")
    w()

    # ---- date each season ------------------------------------------------
    w("## Dating each season from real match dates")
    w()
    w("| seasonid | competition sampled | match years | title |")
    w("|---|---|---|---|")
    season_years = {}
    for sid in sorted(hits):
        ids = hits[sid]["ids"]
        for cid in ids[: min(3, len(ids))]:
            years, title = date_a_competition(cid)
            time.sleep(PAUSE)
            if years:
                season_years.setdefault(sid, set()).update(years)
                w(f"| {sid} | {cid} | {','.join(str(y) for y in years)} | {title} |")
                break
        else:
            w(f"| {sid} | {ids[0] if ids else '-'} | (no dates found) | |")
    w()

    w("## Verdict")
    w()
    if season_years:
        for sid in sorted(season_years):
            ys = sorted(season_years[sid])
            w(f"- seasonid **{sid}** -> {', '.join(str(y) for y in ys)}")
        w()
        w("To backfill, the scraper should request competitions for the "
          "wanted seasonid, then read each competition page by id, rather "
          "than driving fdate/tdate on the results page.")
    else:
        w("Seasons were listed but none could be dated; the competition "
          "pages may need the playwright path scraper.py already uses.")

    with open("data/season_report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    with open("data/seasons_found.json", "w", encoding="utf-8") as fh:
        json.dump({str(k): v for k, v in hits.items()}, fh, indent=1)
    print("\n".join(out[-40:]))


if __name__ == "__main__":
    main()
