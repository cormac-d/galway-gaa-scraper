"""Is the 2022 senior championship an UNLISTED competition?

Same question as probe2022.py, asked concurrently. That version walked 9,100
ids one at a time with a 20-second timeout and had not finished in four hours.
A /league/<id> fetch is almost entirely waiting, so the walk is run on a small
thread pool with a short timeout instead. Eight workers is modest load for a
county site and finishes the range in minutes.

The season list for 2849 serves 139 competitions and none of them is the SFC
group stage, though its relegation group (id 176667) is there. Competition ids
are global and a /league/<id> page renders whether or not the id appears in any
season list, so an orphaned competition is still readable.
"""
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup

BASE = "https://www.galwaygaa.ie"
HEAD = {"User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
        "Referer": f"{BASE}/competitions/"}

LO, HI = 168700, 177800
WORKERS = 8
TIMEOUT = 8
INTERESTING = re.compile(r'senior|intermediate|championship|\bsfc\b|\bifc\b', re.I)

local = threading.local()
lock = threading.Lock()
state = dict(checked=0, hits=0)


def session():
    if not hasattr(local, "s"):
        local.s = requests.Session()
        local.s.headers.update(HEAD)
        # one pooled connection per worker, so the pool is not rebuilt per call
        local.s.mount(BASE, requests.adapters.HTTPAdapter(
            pool_connections=1, pool_maxsize=2, max_retries=1))
    return local.s


def page(cid):
    try:
        r = session().get(f"{BASE}/league/{cid}", timeout=TIMEOUT)
    except Exception:
        return None
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    els = soup.select("[data-hometeam]")
    if not els:
        return None
    names = {e.get("data-compname", "").strip() for e in els if e.get("data-compname")}
    dates = [e.get("data-date", "") for e in els]
    yrs = sorted({int(m.group()) for d in dates
                  for m in [re.search(r"(?:19|20)\d\d", d)] if m})
    teams = sorted({e.get("data-hometeam", "") for e in els})[:4]
    return dict(n=len(els), names=sorted(n for n in names if n), years=yrs, teams=teams)


def check(cid):
    d = page(cid)
    with lock:
        state["checked"] += 1
        c = state["checked"]
        if d and 2022 in d["years"]:
            state["hits"] += 1
        if c % 500 == 0:
            print(f"  {c} of {HI - LO} ids checked, {state['hits']} with 2022 matches",
                  flush=True)
    if not d or 2022 not in d["years"]:
        return None
    return dict(id=cid, name=" / ".join(d["names"]) or "(unnamed)",
                n=d["n"], years=d["years"], teams=d["teams"])


def main():
    os.makedirs("data", exist_ok=True)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        all2022 = [r for r in pool.map(check, range(LO, HI)) if r]

    champ = [r for r in all2022 if INTERESTING.search(r["name"])]
    out = ["# Unlisted 2022 competitions", "",
           f"Walked ids {LO}-{HI}. {len(all2022)} pages carry 2022 matches; "
           f"{len(champ)} are championship-named.", ""]
    for f in champ:
        out.append(f"- **{f['id']}** {f['name']} — {f['n']} matches, "
                   f"years {f['years']}, e.g. {', '.join(f['teams'][:3])}")
    out += ["", "## Every 2022 page found, named", ""]
    for f in sorted(all2022, key=lambda x: x["name"]):
        out.append(f"- {f['id']} {f['name']} ({f['n']})")

    open("data/probe2022fast.md", "w").write("\n".join(out) + "\n")
    json.dump(all2022, open("data/all_2022_comps.json", "w"), indent=1)
    print("\n".join(out), flush=True)
    print(f"\nDONE checked={state['checked']} with2022={len(all2022)} "
          f"championship={len(champ)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
