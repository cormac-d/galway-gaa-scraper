"""Is the 2022 senior championship an UNLISTED competition?

The season list for 2849 serves 139 competitions and none of them is the SFC
group stage, though its relegation group (id 176667) is there. Competition ids
are global and a /league/<id> page renders whether or not the id appears in any
season list, so an orphaned competition is still readable.

2022's listed ids run 168776 to 177745. This walks that range, keeps any page
whose matches are dated 2022, and reports the ones we do not already hold.
"""
import re, time, json, os
import requests
from bs4 import BeautifulSoup

BASE = "https://www.galwaygaa.ie"
HEAD = {"User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
        "Referer": f"{BASE}/competitions/"}
s = requests.Session(); s.headers.update(HEAD)

LO, HI = 168700, 177800
STEP = 1
INTERESTING = re.compile(r'senior|intermediate|championship|\bsfc\b|\bifc\b', re.I)


def page(cid):
    try:
        r = s.get(f"{BASE}/league/{cid}", timeout=20)
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
    yrs = sorted({int(m.group()) for d in dates for m in [re.search(r"(?:19|20)\d\d", d)] if m})
    teams = sorted({e.get("data-hometeam", "") for e in els})[:4]
    return dict(n=len(els), names=sorted(n for n in names if n), years=yrs, teams=teams)


def main():
    os.makedirs("data", exist_ok=True)
    found, checked, hits = [], 0, 0
    for cid in range(LO, HI, STEP):
        d = page(cid)
        checked += 1
        time.sleep(0.03)
        if not d or 2022 not in d["years"]:
            continue
        hits += 1
        nm = " / ".join(d["names"]) or "(unnamed)"
        if INTERESTING.search(nm):
            found.append(dict(id=cid, name=nm, n=d["n"], years=d["years"],
                              teams=d["teams"]))
        if checked % 1000 == 0:
            print(f"  {checked} ids checked, {hits} with 2022 matches, "
                  f"{len(found)} championship-named")
    out = ["# Unlisted 2022 competitions", "",
           f"Walked ids {LO}-{HI}. {hits} pages carry 2022 matches; "
           f"{len(found)} are championship-named.", ""]
    for f in found:
        out.append(f"- **{f['id']}** {f['name']} — {f['n']} matches, "
                   f"years {f['years']}, e.g. {', '.join(f['teams'][:3])}")
    open("data/probe2022.md", "w").write("\n".join(out) + "\n")
    json.dump(found, open("data/unlisted_2022.json", "w"), indent=1)
    print("\n".join(out[:60]))


if __name__ == "__main__":
    main()
