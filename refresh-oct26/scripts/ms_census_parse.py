#!/usr/bin/env python3
"""Parse an MDOT CheckedBidResults pdftotext(-layout) dump into JSON calls.

Usage: python3 -I ms_census_parse.py <census.txt> <county_div_MS.json> <out.json>
Input is untrusted data; nothing from it is executed.
"""
import json, re, sys

BIDDER = re.compile(
    r"^\s*(\d+)\s+(.+?) - ([A-Za-z .'-]+), ([A-Z]{2})\s+(?:A\+C = ([\d,.]+)\s+)?\$\s*([\d,]+\.\d{2})\s*$"
)
CALLHDR = re.compile(r"^\s{0,2}(\d{1,2})\s+([A-Z]{1,6}-\d{3,4}.*)$")
AMOUNT = re.compile(r"\$\s*([\d,]+\.\d{2})")


def num(s):
    return float(s.replace(",", ""))


def main(txt_path, county_path, out_path):
    counties = json.load(open(county_path))
    cnames = {c.lower(): c for c in counties}
    lines = open(txt_path).read().splitlines()

    # letting date from the banner
    date = None
    for ln in lines[:5]:
        m = re.search(r"Checked Bid Results\s+(.*?) Letting", ln)
        if m:
            date = m.group(1).strip()
            break

    calls = []
    cur = None
    state = None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if ("Unofficial Document" in s or s.startswith("Checked Bid Results")
                or re.match(r"^\d{1,2}/\d{1,2}/\d{4}", s)):
            continue
        m = CALLHDR.match(ln)
        if m and (cur is None or state != "hdr"):
            cur = {"call": m.group(1).zfill(2), "hdr": [m.group(2).strip()],
                   "desc": [], "bidders": [], "estimate": None,
                   "estDir": None, "estPct": None, "withdrawn": False}
            calls.append(cur)
            state = "hdr"
            continue
        if cur is None:
            continue
        mb = BIDDER.match(ln)
        if mb and state in ("desc", "bidders", "hdr"):
            cur["bidders"].append({
                "rank": int(mb.group(1)),
                "name": mb.group(2).strip(),
                "city": mb.group(3).strip(),
                "st": mb.group(4),
                "ac": num(mb.group(5)) if mb.group(5) else None,
                "amount": num(mb.group(6)),
            })
            state = "bidders"
            continue
        if "STATE ESTIMATE" in s:
            m2 = re.search(r"(UNDER|OVER) STATE ESTIMATE\s+([\d.]+)%", s)
            if m2:
                cur["estDir"], cur["estPct"] = m2.group(1), float(m2.group(2))
            state = "est"
            ma = AMOUNT.search(s)
            if ma:
                cur["estimate"] = num(ma.group(1))
            continue
        if state == "est":
            ma = AMOUNT.search(s)
            m2 = re.search(r"(UNDER|OVER) STATE ESTIMATE\s+([\d.]+)%", s)
            if ma and cur["estimate"] is None:
                cur["estimate"] = num(ma.group(1))
            elif m2:
                cur["estDir"], cur["estPct"] = m2.group(1), float(m2.group(2))
            else:
                state = None
            continue
        if "Withdrawn from Letting" in s:
            cur["withdrawn"] = True
            state = None
            continue
        if state == "hdr" and (re.search(r"\d{9}", s) or re.match(r"^[A-Z]{1,6}-\d{3,4}", s)):
            cur["hdr"].append(s)
            continue
        if state in ("hdr", "desc"):
            cur["desc"].append(s)
            state = "desc"
            continue

    out = []
    for c in calls:
        hdr = " ".join(c["hdr"])
        # peel county names (joined by &) off the end of the header text
        tail = []
        work = hdr
        while True:
            work = work.rstrip().rstrip("&").rstrip()
            words = work.split()
            got = None
            for k in (2, 1):
                if len(words) >= k:
                    cand = " ".join(words[-k:]).lower()
                    if cand in cnames:
                        got = cnames[cand]
                        work = " ".join(words[:-k])
                        break
            if got:
                tail.insert(0, got)
            else:
                break
        tip = work.rstrip().rstrip("&").rstrip()
        county_disp = " & ".join(c2 for c2 in tail)
        # keep the census spelling for display, but map division via canonical
        divs = sorted({counties[t] for t in tail})
        # proposal id: first 9-digit number in the tip
        mprop = re.search(r"(\d{9})", tip)
        out.append({
            "call": c["call"],
            "tip": tip,
            "county": county_disp,
            "countyRaw": tail,
            "div": divs[0] if len(divs) == 1 else divs,
            "proposal": mprop.group(1) if mprop else None,
            "desc": " ".join(c["desc"]),
            "bidders": c["bidders"],
            "estimate": c["estimate"],
            "estDir": c["estDir"],
            "estPct": c["estPct"],
            "withdrawn": c["withdrawn"],
        })
    res = {"letting": date, "calls": out}
    with open(out_path, "w") as f:
        json.dump(res, f, indent=1)
    for c in out:
        print(c["call"], c["proposal"], c["county"], "div", c["div"],
              "bids", len(c["bidders"]), "est", c["estimate"],
              "WITHDRAWN" if c["withdrawn"] else "")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
