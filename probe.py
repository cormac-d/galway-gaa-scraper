"""Sweep below the known seasons to see how far back the archive goes.

The first sweep covered seasonid 2900-4100 and found four football seasons:
3070 (2023), 3642 (2024), 3831 (2025), 3976 (2026). 2022 would sit below
3070, outside that range. This looks lower, and dates anything it finds from
real match dates rather than assuming the numbering is regular.
"""
import os, re, json, time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

BASE = "https://www.galwaygaa.ie"
AJAX = f"{BASE}/wp-admin/admin-ajax.php"
FOOTBALL = "6929"
HEAD = {"User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
        "Referer": f"{BASE}/competitions/"}
s = requests.Session(); s.headers.update(HEAD)
out = []


def comps(sid):
    try:
        r = s.post(AJAX, data={"action": "Get_competition_data",
                               "value": FOOTBALL, "seasonid": str(sid)},
                   headers={"X-Requested-With": "XMLHttpRequest"}, timeout=25)
        html = r.json().get("competition", "") or ""
    except Exception:
        return {}
    d = {}
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        m = re.search(r"/league/(\d+)", a["href"])
        if m:
            d[int(m.group(1))] = a.get_text(" ", strip=True)
    return d


def years(cid):
    try:
        r = s.get(f"{BASE}/league/{cid}", timeout=25)
    except Exception:
        return []
    ds = [e.get("data-date") for e in BeautifulSoup(r.text, "html.parser")
          .select("[data-date]") if e.get("data-date")]
    return sorted({int(m.group()) for d in ds
                   for m in [re.search(r"(?:19|20)\d\d", d)] if m})


def main():
    os.makedirs("data", exist_ok=True)
    found = {}
    for sid in range(1500, 3100):
        c = comps(sid)
        time.sleep(0.08)
        if not c:
            continue
        found[sid] = c
        print(f"seasonid {sid}: {len(c)} competitions")
    out.append("# How far back the archive goes\n")
    out.append(f"Run {datetime.utcnow():%Y-%m-%d %H:%M} UTC\n")
    out.append(f"Swept seasonid 1500-3099. Football seasons found: {len(found)}\n")
    out.append("| seasonid | competitions | match years | sample |")
    out.append("|---|---|---|---|")
    for sid in sorted(found):
        ids = sorted(found[sid])
        ys = []
        for cid in ids[:4]:
            ys = years(cid)
            time.sleep(0.08)
            if ys:
                break
        out.append(f"| {sid} | {len(ids)} | {','.join(map(str, ys)) or '—'} | "
                   f"{found[sid][ids[0]][:60]} |")
    open("data/archive_depth.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
