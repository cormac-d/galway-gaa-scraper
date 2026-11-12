"""Append the 2022 competitions the county's season list omits — strictly.

The first attempt classified by keyword and let through soccer (Connacht
Junior Cup, the U21 Premier full of Celtics and Uniteds), rugby (Adult
Friendlies with Buccaneers RFC and Claremorris 1st XV) and other counties
(IFC Section A with Milltownpass, a Westmeath club). Blocklists cannot do this
job: "Athenry" is a Galway GAA club and also a soccer club, so the name alone
decides nothing.

This uses an allowlist instead. A competition is Galway GAA football only if
most of its teams are clubs that appear in volume in Galway county
competitions across the decade, and no team carries a soccer or rugby marker.
The allowlist is derived from the existing season files, not typed by hand.

Nothing is appended unless it passes on the full team list of the fetched
page, not on the four sampled names.
"""
import csv
import json
import os
import re
import sys
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup

BASE = "https://www.galwaygaa.ie"
HEAD = {"User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
        "Referer": f"{BASE}/competitions/"}
WORKERS, TIMEOUT = 8, 10

CLUBS = {c.strip() for c in open("galway_clubs.txt", encoding="utf-8") if c.strip()}

# a team name carrying any of these is not a GAA club side
NOTGAA = re.compile(r'\b(?:utd|united|celtic|rovers|athletic|wanderers|town|fc|afc|rfc|'
                    r'dynamo|hibernian|albion|1st xv|u20s|college|community school|'
                    r'secondary|vs\b|cbs|university|institute|\bitt\b|\batu\b)\b', re.I)
# competition names that are never Galway men's club football
NOTCOMP = re.compile(r'hurl|camog|iomán|iomanaiocht|ladies|lgfa|peil na mban|soccer|'
                     r'schools?\b|post.?primary|colleges?\b|\bpps\b|university|sigerson|'
                     r'fresher|higher education|\bhe \b|rugby|friendl|'
                     r'connacht junior cup|\bgfa\b|sfai|\bfai\b|london|'
                     r'mayo|roscommon|sligo|leitrim|kerry|tipperary|wexford|westmeath|'
                     r'dublin|cork|limerick|ulster|munster|leinster', re.I)

local = threading.local()


def session():
    if not hasattr(local, "s"):
        local.s = requests.Session()
        local.s.headers.update(HEAD)
        local.s.mount(BASE, requests.adapters.HTTPAdapter(
            pool_connections=1, pool_maxsize=2, max_retries=1))
    return local.s


ALIAS = {'moycullen': 'maigh cuilinn', 'mhaigh cuilinn': 'maigh cuilinn',
         'st jamess': 'st james', 'bhearna na forbacha': 'bearna na forbacha'}


def canon(t):
    """The report's own canonicaliser, copied exactly.

    A reimplementation of this missed Irish lenition — "Cumann Peil Mhaigh
    Cuilinn" did not reduce to "maigh cuilinn" — and that silently failed two
    of the three 2022 senior championship groups. Keep this in step with
    fourseason.canon.
    """
    s = unicodedata.normalize('NFKD', str(t)).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\b(cumann|peile?|iomanaiochta|clg|gaa|club)\b', ' ', s)
    s = re.sub(r"[^a-z0-9]", ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'\s+(football|hurling)$', '', s)
    s = re.sub(r'\s+[a-d]$', '', s)
    s = re.sub(r'\bmh', 'm', s)
    return ALIAS.get(s, s)


def galway_football(comp, teams):
    if NOTCOMP.search(comp):
        return False, "competition name"
    if any(NOTGAA.search(t) for t in teams):
        return False, "non-GAA team name"
    c = {canon(t) for t in teams}
    c = {x for x in c if x}
    if not c:
        return False, "no teams"
    hit = len(c & CLUBS) / len(c)
    if hit < 0.6:
        return False, f"only {hit:.0%} of teams are Galway clubs"
    return True, f"{hit:.0%} Galway clubs"


def page(cid):
    try:
        r = session().get(f"{BASE}/league/{cid}", timeout=TIMEOUT)
    except Exception:
        return None
    if r.status_code != 200:
        return None
    els = BeautifulSoup(r.text, "html.parser").select("[data-hometeam]")
    if not els:
        return None
    rows, teams, names = [], set(), set()
    for e in els:
        d = e.get("data-date", "")
        if not re.search(r"2022", d):
            continue
        h, a = e.get("data-hometeam", ""), e.get("data-awayteam", "")
        teams.update([h, a])
        names.add(e.get("data-compname", "").strip())
        rows.append([d, e.get("data-time", ""), e.get("data-compname", ""),
                     h, e.get("data-homescore", ""), e.get("data-awayscore", ""),
                     a, e.get("data-venue", ""), e.get("data-referee", ""),
                     e.get("data-status", ""), "2026-11-12"])
    if not rows:
        return None
    return dict(id=cid, name=" / ".join(sorted(n for n in names if n)) or "(unnamed)",
                teams=sorted(teams), rows=rows)


def main():
    cands = json.load(open("data/all_2022_comps.json", encoding="utf-8"))
    # shortlist on the sampled names first, so only plausible pages are fetched
    short = [c for c in cands
             if galway_football(c["name"], c.get("teams", []))[0]]
    print(f"{len(cands)} candidates, {len(short)} shortlisted", flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        got = [p for p in pool.map(lambda c: page(c["id"]), short) if p]
    print(f"{len(got)} pages fetched", flush=True)

    held = set()
    with open("data/season_2022.csv", encoding="utf-8-sig") as f:
        rd = csv.reader(f)
        next(rd)
        for r in rd:
            held.add((r[2], r[0], r[3], r[6]))

    kept, rejected, new = [], [], []
    for p in got:
        ok, why = galway_football(p["name"], p["teams"])
        if not ok:
            rejected.append((p["id"], p["name"], why))
            continue
        add = [r for r in p["rows"] if (r[2], r[0], r[3], r[6]) not in held]
        for r in add:
            held.add((r[2], r[0], r[3], r[6]))
        if add:
            kept.append((p["id"], p["name"], len(add), why))
            new.extend(add)

    if new:
        with open("data/season_2022.csv", "a", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerows(new)

    out = ["# 2022, appended under the strict club allowlist", "",
           f"{len(short)} shortlisted, {len(got)} fetched, {len(kept)} accepted, "
           f"{len(rejected)} rejected. {len(new)} new match rows appended.", "",
           "## Accepted", ""]
    for cid, nm, n, why in sorted(kept, key=lambda x: -x[2]):
        out.append(f"- **{cid}** {nm} — {n} rows ({why})")
    out += ["", "## Rejected", ""]
    for cid, nm, why in sorted(rejected)[:60]:
        out.append(f"- {cid} {nm} — {why}")
    open("data/fix2022_strict.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
