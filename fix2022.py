"""Scrape the Galway football competitions that the season lists do not serve.

What the id walk found
----------------------
Competition ids are global across the whole GAA platform, and a /league/<id>
page renders whether or not that id appears in any season list. Walking ids
168700-177800 turned up 404 pages that carry 2022 matches and a Galway club,
against the 138 competitions the 2022 football season list serves. Most of the
difference is soccer, hurling, camogie, schools and other counties sharing the
platform, but a real remainder is Galway club football the list omits:

    SFC - Group 1 / 2 / 3        45 appearances   the senior championship
    Senior FC Knockout Stages     9               group stage and knockout
    IFC - Group 1 / 2 / 3 / 4    24
    Intermediate C'ship Knockout 10
    U14 League Fixtures Div 1-7  ~197             a second set of county
    U16 League Fixtures Div 1-7  ~155             leagues, named differently
    Adult League Fixtures 1-10   ~113

So 2022's senior championship was never missing from the archive, only from
the index - exactly as suspected. This script fetches those pages and appends
their matches to season_2022.csv in scraper.py's schema.

It then asks the same question of 2023-2026: walk each season's own id range
and report any Galway football competition the list does not serve. If those
seasons are short too, every comparison in the review rests on partial data.
"""
import csv
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE = "https://www.galwaygaa.ie"
AJAX = f"{BASE}/wp-admin/admin-ajax.php"
FOOTBALL = "6929"
HEAD = {"User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
        "Referer": f"{BASE}/competitions/"}

SEASONS = {1617: 2016, 1745: 2017, 1891: 2018, 2063: 2019, 2266: 2020,
           2588: 2021, 2849: 2022, 3070: 2023, 3642: 2024, 3831: 2025,
           3976: 2026}
AUDIT_YEARS = [2023, 2024, 2025, 2026]
WORKERS = 10
TIMEOUT = 8

# Everything on the platform that is not Galway club football. The season list
# is already filtered to football, so these only matter for pages found by id.
SOCCER = re.compile(r'\bgfa\b|western hygiene|sfai|\bfai\b|connacht cup|connacht shield|'
                    r'national (?:cup|trophy)|\butd\b|rovers|celtic|athletic|dynamo|'
                    r'developmental league|\bbu1\d\b|\bgu1\d\b|premier cup|boys|girls', re.I)
HURL = re.compile(r'hurl|\bhc\b|\bihc\b|camog|iomán|iomanaiocht|roinn|\bcup\b.*\b(?:athenry|'
                  r'carnmore|turloughmore|kilconieron|sarsfields)\b', re.I)
RUGBY = re.compile(r'\brfc\b|cawley|1st xv', re.I)
SCHOOL = re.compile(r'school|college|\bpps\b|post.?primary|\bcc\b|\bcbs\b|coláiste|colaiste|'
                    r'comprehensive|university|fresher|sigerson|pinergy|bunscol', re.I)
LADIES = re.compile(r'ladies|\blgfa\b|dlgfa|\bgirls\b|camogie', re.I)
OTHERCO = re.compile(r'rebel og|gorey|wexford|go.?ahead|fingallians|st james gaels|westmeath|'
                     r'new ross|forth mountain|county football league|bon secours|'
                     r'courtyard ferns|milltownpass|castledaly|justin cheevers|toddie byrne|'
                     r'\bdemo\b|\btest comp\b', re.I)

# Galway club names, to tell a Galway page from another county's.
GALWAY_CLUBS = (
    'maigh cuilinn', 'mhaigh cuilinn', 'moycullen', 'corofin', 'salthill',
    'knocknacarra', 'mountbellew', 'annaghdown', 'claregalway', 'killannin',
    'oranmore', 'tuam stars', 'dunmore machales', 'dunmore mchales',
    'caherlistrane', 'an spidéal', 'an spideal', 'bearna', 'bhearna',
    'cheathrú rua', 'cheathru rua', 'breathnach', 'athenry', 'cortoon',
    'kilkerrin', 'monivea', 'barna', 'killererin', 'headford', 'caltra',
    'glenamaddy', 'kilconly', 'naomh mhuire', 'gráinne mhaols', 'grainne mhaols',
    'carna caiseal', 'loughrea', 'ballinasloe', 'st. gabriels', 'st gabriels',
    'milltown', 'st james', 'sylane', 'clifden', 'abbeyknockmoy', 'castlegar',
)

local = threading.local()
lock = threading.Lock()
count = dict(n=0)


def session():
    if not hasattr(local, "s"):
        local.s = requests.Session()
        local.s.headers.update(HEAD)
        local.s.mount(BASE, requests.adapters.HTTPAdapter(
            pool_connections=1, pool_maxsize=2, max_retries=1))
    return local.s


def is_galway(teams):
    t = ' '.join(teams).lower()
    return any(c in t for c in GALWAY_CLUBS)


def is_galway_football(name, teams):
    """Galway club football, as opposed to the other sports and counties that
    share the platform. Judged on the competition name and the team names."""
    if not is_galway(teams):
        return False
    for rx in (SOCCER, HURL, RUGBY, SCHOOL, LADIES, OTHERCO):
        if rx.search(name):
            return False
    return True


def matches(cid):
    """Every match on a competition page, with the fields scraper.py writes."""
    try:
        r = session().get(f"{BASE}/league/{cid}", timeout=TIMEOUT)
    except Exception:
        return None
    with lock:
        count['n'] += 1
        if count['n'] % 500 == 0:
            print(f"    {count['n']} pages fetched", flush=True)
    if r.status_code != 200:
        return None
    els = BeautifulSoup(r.text, "html.parser").select("[data-hometeam]")
    if not els:
        return None
    out = []
    for e in els:
        out.append(dict(
            Date=e.get("data-date", "").strip(),
            Time=e.get("data-time", "00:00").strip(),
            Competition=e.get("data-compname", "").strip(),
            Home_Team=e.get("data-hometeam", "").strip(),
            Home_Score=e.get("data-homescore", "").strip(),
            Away_Score=e.get("data-awayscore", "").strip(),
            Away_Team=e.get("data-awayteam", "").strip(),
            Venue=e.get("data-venue", "").strip(),
            Referee=e.get("data-referee", "").strip(),
            Match_Status=e.get("data-status", "").strip(),
        ))
    return dict(id=cid, rows=out,
                name=out[0]["Competition"] if out else "",
                teams=sorted({m["Home_Team"] for m in out}),
                years=sorted({int(m.group()) for r_ in out
                              for m in [re.search(r"(?:19|20)\d\d", r_["Date"])] if m}))


def season_ids(key):
    """The competition ids the season list serves, via the AJAX endpoint."""
    try:
        r = requests.post(AJAX, headers=HEAD, timeout=30,
                          data={"action": "Get_competition_data",
                                "value": FOOTBALL, "seasonid": str(key)})
        j = r.json()
    except Exception as e:
        print(f"  season {key}: list unavailable ({e})", flush=True)
        return []
    # The JSON escapes slashes, so parse it before looking for hrefs.
    html = j.get("competition", "") if isinstance(j, dict) else ""
    return sorted({int(m) for m in re.findall(r"/league/(\d+)", html)})


def fetch_many(ids, label):
    print(f"  {label}: fetching {len(ids)} ids on {WORKERS} threads", flush=True)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return [r for r in pool.map(matches, ids) if r]


def fix_2022():
    """Append the unlisted 2022 Galway football competitions to season_2022.csv."""
    miss = json.load(open("data/missing_2022_football.json"))
    got = fetch_many([r["id"] for r in miss], "2022 unlisted")

    keep, skipped = [], []
    for g in got:
        if 2022 not in g["years"]:
            skipped.append((g["id"], g["name"], "no 2022 matches"))
        elif not is_galway_football(g["name"], g["teams"]):
            skipped.append((g["id"], g["name"], "not Galway club football"))
        else:
            keep.append(g)

    path = "data/season_2022.csv"
    existing = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    cols = list(existing[0].keys())
    # A match already held is identified by its competition, date and teams.
    seen = {(r["Competition"], r["Date"], r["Home_Team"], r["Away_Team"])
            for r in existing}
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    added = 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        for g in keep:
            for m in g["rows"]:
                k = (m["Competition"], m["Date"], m["Home_Team"], m["Away_Team"])
                if k in seen:
                    continue
                seen.add(k)
                row = {c: "" for c in cols}
                row.update({c: v for c, v in m.items() if c in cols})
                row["Scraped_At"] = stamp
                w.writerow(row)
                added += 1

    rep = [f"# 2022: the competitions the season list does not serve", "",
           f"Fetched {len(got)} of {len(miss)} candidate pages. "
           f"{len(keep)} are Galway club football; {added} new match rows appended "
           f"to season_2022.csv (was {len(existing)} rows).", "",
           "## Added", ""]
    for g in sorted(keep, key=lambda x: -len(x["rows"])):
        rep.append(f"- **{g['id']}** {g['name']} — {len(g['rows'])} appearances, "
                   f"e.g. {', '.join(g['teams'][:3])}")
    rep += ["", "## Skipped", ""]
    for cid, nm, why in sorted(skipped, key=lambda x: x[2]):
        rep.append(f"- {cid} {nm} — {why}")
    open("data/fix2022_report.md", "w").write("\n".join(rep) + "\n")
    print("\n".join(rep[:40]), flush=True)
    return added


def audit():
    """Ask of 2023-2026 the question 2022 failed: is the season list complete?"""
    keys = {y: k for k, y in SEASONS.items() if y in AUDIT_YEARS}
    rep = ["# Are the other season lists complete?", "",
           "For each season, the competitions its list serves against the Galway",
           "club football competitions reachable inside its own id range.", ""]
    summary = {}

    for y in AUDIT_YEARS:
        listed = season_ids(keys[y])
        if not listed:
            rep.append(f"## {y}\n\nSeason list unavailable; skipped.\n")
            continue
        lo, hi = min(listed), max(listed)
        print(f"\n=== {y}: {len(listed)} listed, range {lo}-{hi} ===", flush=True)
        got = fetch_many(range(lo, hi + 1), f"{y} range")

        inyear = [g for g in got if y in g["years"]]
        foot = [g for g in inyear if is_galway_football(g["name"], g["teams"])]
        lset = set(listed)
        unlisted = [g for g in foot if g["id"] not in lset]

        summary[y] = dict(listed=len(listed), pages=len(got), inyear=len(inyear),
                          football=len(foot), unlisted=len(unlisted),
                          unlisted_matches=sum(len(g["rows"]) for g in unlisted))
        rep += [f"## {y}", "",
                f"- list serves **{len(listed)}** competitions (ids {lo}-{hi})",
                f"- {len(got)} pages render in that range; {len(inyear)} carry {y} matches",
                f"- {len(foot)} of those are Galway club football",
                f"- **{len(unlisted)}** are not in the season list "
                f"({sum(len(g['rows']) for g in unlisted)} appearances)", ""]
        for g in sorted(unlisted, key=lambda x: -len(x["rows"]))[:60]:
            rep.append(f"  - {g['id']} {g['name']} — {len(g['rows'])} app., "
                       f"e.g. {', '.join(g['teams'][:3])}")
        rep.append("")
        json.dump([dict(id=g["id"], name=g["name"], n=len(g["rows"]),
                        teams=g["teams"], rows=g["rows"]) for g in unlisted],
                  open(f"data/unlisted_{y}.json", "w"), indent=1)

    rep += ["## Summary", "",
            "| season | listed | Galway football found | not listed | appearances |",
            "|---|---|---|---|---|"]
    for y, s in sorted(summary.items()):
        rep.append(f"| {y} | {s['listed']} | {s['football']} | "
                   f"{s['unlisted']} | {s['unlisted_matches']} |")
    open("data/season_completeness.md", "w").write("\n".join(rep) + "\n")
    print("\n".join(rep[-12:]), flush=True)


def main():
    os.makedirs("data", exist_ok=True)
    print("=== STEP 1: 2022 ===", flush=True)
    added = fix_2022()
    print(f"\n2022: {added} rows added\n", flush=True)
    print("=== STEP 2: completeness of 2023-2026 ===", flush=True)
    audit()
    print("\nDONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
