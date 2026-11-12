"""Why does 2022 have no county senior championship?

Three possibilities, tested here:
  1. The competition exists under seasonid 2849 but our list missed it.
  2. 2022 has a SECOND season key (Galway sometimes files a championship
     under its own key, e.g. "2022/23"), so sweep ids around 2849.
  3. The championship sits under a different competition "value" code than
     6929 (football) / 44 (hurling), so sweep plausible codes.
"""
import re, time, json
import requests
from bs4 import BeautifulSoup

BASE = "https://www.galwaygaa.ie"
AJAX = f"{BASE}/wp-admin/admin-ajax.php"
HEAD = {"User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
        "Referer": f"{BASE}/competitions/"}
s = requests.Session(); s.headers.update(HEAD)
out = []


def comps(sid, value="6929"):
    try:
        r = s.post(AJAX, data={"action": "Get_competition_data", "value": value,
                               "seasonid": str(sid)},
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


def years_and_sample(cid):
    try:
        r = s.get(f"{BASE}/league/{cid}", timeout=25)
    except Exception:
        return [], []
    soup = BeautifulSoup(r.text, "html.parser")
    ds = [e.get("data-date") for e in soup.select("[data-date]") if e.get("data-date")]
    yrs = sorted({int(m.group()) for d in ds for m in [re.search(r"(?:19|20)\d\d", d)] if m})
    teams = [e.get("data-hometeam") for e in soup.select("[data-hometeam]")][:4]
    return yrs, teams


def main():
    # 1. full 2022 list
    c = comps(2849)
    out.append(f"## seasonid 2849 (2022): {len(c)} competitions\n")
    sen = {k: v for k, v in c.items() if re.search(r'senior|sfc|intermediate|championship', v, re.I)}
    out.append(f"championship-named: {len(sen)}\n")
    for k, v in sorted(sen.items(), key=lambda x: x[1]):
        out.append(f"- {k}: {v}")
    out.append("\nALL names:\n")
    for k, v in sorted(c.items(), key=lambda x: x[1]):
        out.append(f"- {v}")

    # 2. neighbouring season keys
    out.append("\n## sweeping seasonid 2700-3069 for other 2022 keys\n")
    for sid in range(2700, 3070):
        if sid == 2849:
            continue
        d = comps(sid)
        time.sleep(0.05)
        if not d:
            continue
        ids = sorted(d)
        yrs, teams = [], []
        for cid in ids[:3]:
            yrs, teams = years_and_sample(cid)
            time.sleep(0.05)
            if yrs:
                break
        out.append(f"- seasonid {sid}: {len(d)} comps, years {yrs}, sample '{d[ids[0]]}'")

    # 3. other competition codes for 2022
    out.append("\n## other 'value' codes under seasonid 2849\n")
    for val in ["6929", "44", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                "6930", "6928", "45", "43", "6931", "6927"]:
        d = comps(2849, val)
        time.sleep(0.05)
        if d:
            out.append(f"- value {val}: {len(d)} comps, sample '{d[sorted(d)[0]]}'")

    open("data/probe2022.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out[:80]))


if __name__ == "__main__":
    main()
