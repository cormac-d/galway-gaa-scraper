"""Backfill earlier Galway football seasons by season and competition id.

Why the results page could not do this
--------------------------------------
scraper.py drives fdate/tdate on /results/. That page has no season control,
so it answers for the live season whatever dates you give it - which is why
asking it for 2022-2025 returned nothing. It was the wrong door, not a bug.

The competitions page uses a different route:

    POST /wp-admin/admin-ajax.php
        action   = Get_competition_data
        value    = 6929        (football; 44 is hurling)
        seasonid = <season key>

Sweeping seasonid found four seasons still served, each confirmed from match
dates on its own competition pages:

    3070 -> 2023 (209 competitions)
    3642 -> 2024 (343)
    3831 -> 2025 (262)
    3976 -> 2026 (205)

What a competition page actually serves
---------------------------------------
Only the standings table is server-rendered: Team, Pld, W, D, L, PF, PA, PD,
Pts. The match list is loaded client-side, which is why the first attempt at
this found nothing.

Standings are still most of what the review needs - games played, won and
lost, scores for and against, and final position, per club per competition per
season. So this takes them, and at the same time dumps the page's AJAX wiring
so the match-level endpoint can be found next.
"""

import os
import re
import csv
import json
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE = "https://www.galwaygaa.ie"
AJAX = f"{BASE}/wp-admin/admin-ajax.php"
FOOTBALL = "6929"

SEASONS = {3070: 2023, 3642: 2024, 3831: 2025, 3976: 2026}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
    "Referer": f"{BASE}/competitions/",
}
PAUSE = 0.2
TIMEOUT = 30

FIELDS = ["Season", "Competition_Id", "Competition", "Position", "Team",
          "Played", "Won", "Drawn", "Lost", "Points_For", "Points_Against",
          "Difference", "League_Points", "Scraped_At"]

session = requests.Session()
session.headers.update(HEADERS)
recon = []


def competitions_for(seasonid):
    """Competition ids and names in one season."""
    try:
        r = session.post(
            AJAX,
            data={"action": "Get_competition_data", "value": FOOTBALL,
                  "seasonid": str(seasonid)},
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=TIMEOUT,
        )
    except Exception as exc:
        print(f"  seasonid {seasonid}: {type(exc).__name__}")
        return {}, ""
    if r.status_code != 200:
        print(f"  seasonid {seasonid}: http {r.status_code}")
        return {}, ""

    blob = r.text
    names = {}
    # Try to pair ids with names out of whatever JSON shape comes back.
    try:
        data = r.json()
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                cid = node.get("competition_id") or node.get("id")
                nm = (node.get("name") or node.get("competition_name")
                      or node.get("title"))
                if cid and str(cid).isdigit() and nm:
                    names[int(cid)] = str(nm).strip()
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    except Exception:
        pass

    ids = {int(i) for i in re.findall(
        r'"?(?:competition_?id|id)"?\s*[:=]\s*"?(\d{5,7})"?', blob)}
    if not ids:
        ids = {int(i) for i in re.findall(r"/league/(\d+)", blob)}
    for i in ids:
        names.setdefault(i, "")
    return names, blob[:1500]


HDR = ("team", "pld", "w", "d", "l")


def standings_and_recon(cid):
    """Standings rows from a competition page, plus its AJAX wiring."""
    try:
        r = session.get(f"{BASE}/league/{cid}", timeout=TIMEOUT)
    except Exception:
        return [], None, []
    if r.status_code != 200:
        return [], None, []
    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    # Competition name: the <title> is more specific than any heading here.
    title = ""
    if soup.title and soup.title.get_text(strip=True):
        title = re.sub(r"\s*[-|]\s*(Galway GAA|GAA).*$", "",
                       soup.title.get_text(strip=True)).strip()
    if not title or title.lower() in ("league", "competition"):
        for sel in ("h1", "h2", ".comp-name"):
            el = soup.select_one(sel)
            t = el.get_text(strip=True) if el else ""
            if t and t.lower() not in ("league", "fixtures", "results"):
                title = t
                break

    rows = []
    for table in soup.find_all("table"):
        trs = table.find_all("tr")
        if len(trs) < 2:
            continue
        head = [c.get_text(strip=True).lower()
                for c in trs[0].find_all(["th", "td"])]
        if len(head) < 5 or not head[0].startswith("team"):
            continue
        for pos, tr in enumerate(trs[1:], 1):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 9 or not cells[0]:
                continue
            rows.append({
                "Competition_Id": cid,
                "Competition": title,
                "Position": pos,
                "Team": cells[0],
                "Played": cells[1], "Won": cells[2], "Drawn": cells[3],
                "Lost": cells[4], "Points_For": cells[5],
                "Points_Against": cells[6], "Difference": cells[7],
                "League_Points": cells[8],
            })

    # Recon: what AJAX actions does this page use? One of them loads matches.
    actions = sorted(set(re.findall(r'action\s*:\s*["\']([A-Za-z_]{4,40})["\']', html)))
    return rows, title, actions


def main():
    os.makedirs("data", exist_ok=True)
    wanted = {int(y) for y in
              os.environ.get("BACKFILL_YEARS", "2023 2024 2025").split()
              if y.isdigit()}

    summary, all_actions, sample_payload = [], set(), ""

    for seasonid, year in sorted(SEASONS.items()):
        if year not in wanted:
            continue
        print(f"\n=== season {year} (seasonid {seasonid}) ===")
        names, payload = competitions_for(seasonid)
        if year == min(wanted):
            sample_payload = payload
        print(f"  {len(names)} competitions")
        time.sleep(PAUSE)

        rows = []
        for n, cid in enumerate(sorted(names), 1):
            srows, title, actions = standings_and_recon(cid)
            all_actions.update(actions)
            time.sleep(PAUSE)
            if not srows:
                continue
            name = (title or names.get(cid) or "").lower()
            if "hurling" in name or "camogie" in name:
                continue
            for r in srows:
                r["Season"] = year
                r["Competition"] = r["Competition"] or names.get(cid, "")
                r["Scraped_At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows.extend(srows)
            if n % 50 == 0:
                print(f"  {n}/{len(names)}, {len(rows)} standings rows")

        if not rows:
            summary.append(f"- **{year}**: nothing returned")
            continue
        path = f"data/standings_{year}.csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        comps = len({r["Competition_Id"] for r in rows})
        teams = len({r["Team"] for r in rows})
        mc = [r for r in rows if "Mhaigh Cuilinn" in r["Team"]
              or "Maigh Cuilinn" in r["Team"] or "Moycullen" in r["Team"]]
        summary.append(
            f"- **{year}**: {len(rows)} standings rows, {comps} competitions, "
            f"{teams} teams — {len(mc)} Moycullen entries"
        )
        print(f"  wrote {path}")

    with open("data/backfill_report.md", "w", encoding="utf-8") as fh:
        fh.write("# Backfill — standings by season\n\n")
        fh.write(f"Run {datetime.utcnow():%Y-%m-%d %H:%M} UTC\n\n")
        fh.write("Competition pages server-render only the standings table; "
                 "the match list loads client-side. Standings still give "
                 "played, won, lost, scores for and against and final "
                 "position per club per competition per season.\n\n")
        fh.write("\n".join(summary) + "\n\n")
        fh.write("## Recon for match-level data\n\n")
        fh.write("AJAX actions seen on competition pages:\n\n")
        for a in sorted(all_actions):
            fh.write(f"- `{a}`\n")
        fh.write("\n## Sample competition-list payload\n\n```\n")
        fh.write((sample_payload or "(none)")[:1200])
        fh.write("\n```\n")
    print("\n" + "\n".join(summary))
    print("actions:", sorted(all_actions))


if __name__ == "__main__":
    main()
