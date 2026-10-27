#!/usr/bin/env python3
"""Parse an NCDOT Item C (award of contracts) pdftotext -layout dump into JSON.

Usage: python3 -I nc_itemc.py <itemc.txt> <out.json>

One contract per page. Captures id, wbs, federal-aid/funding line, county,
TIP, division (from the page header), RPN, bidder count, estimate, type of
work, location, proposal length, every bidder with amount and % diff, and the
printed ESTIMATE TOTAL / LETTING TOTAL lines when present.
"""
import json
import re
import sys

AMT = re.compile(r"([\d,]+\.\d{2})\s+([+-]\s?\d+\.\d)\s*$")

# City names seen in NCDOT bidder lines ("NAME CITY, ST"); longest match is
# stripped from the tail of the name. Extend as new bidders appear.
CITIES = [
    "ROCKY MOUNT", "NEW BERN", "SNEADS FERRY", "WALLACE", "RALEIGH",
    "ROANOKE", "SNOW HILL", "WILSON", "CHARLOTTE", "GREENSBORO",
    "BURLINGTON", "ARCHDALE", "ALBEMARLE", "CHARLOTTESVILLE", "JEFFERSON",
    "CLAREMONT", "MOUNT AIRY", "WEST JEFFERSON", "WILMINGTON", "EDISON",
    "MONROE", "LIBERTY", "NASHVILLE", "HENDERSONVILLE", "CLIFFSIDE",
    "ASHEVILLE", "SAN ANTONIO", "PITTSBURGH", "GREAT FALLS",
    "ALEXANDRIA", "TEMPE", "LIVONIA", "JEFFERSONVILLE", "BENICIA",
    "CASTLE HAYNE", "STATESVILLE", "MOORESVILLE", "ORLANDO",
    "LUMBERTON", "CHARLESTON",
]


def split_name_city(raw):
    """'BARNHILL CONTRACTING CO ROCKY MOUNT, NC' -> (name, 'ROCKY MOUNT, NC')."""
    m = re.search(r",\s*([A-Z]{2})$", raw)
    if not m:
        return raw.strip(), ""
    state = m.group(1)
    head = raw[: m.start()].strip()
    for city in sorted(CITIES, key=len, reverse=True):
        if head.endswith(" " + city):
            return head[: -len(city) - 1].strip(), f"{city}, {state}"
    return head, state  # city not recognised; keep name intact


def parse(path):
    text = open(path, encoding="utf-8").read()
    pages = re.split(r"\n?\s*HIGHWAY LETTING\s+PAGE: \d+ of \d+\n", text)
    pages = [p for p in pages if p.strip()]
    out = {"contracts": [], "estimateTotal": None, "lettingTotal": None,
           "lettingTotalPctDiff": None, "date": None}
    for page in pages:
        lines = page.splitlines()
        div = None
        date = None
        idx = None
        for i, ln in enumerate(lines):
            s = ln.strip()
            m = re.match(r"DIVISION (\d+)$", s)
            if m:
                div = int(m.group(1))
            if re.match(r"^[A-Z]+ \d{1,2}, \d{4}$", s):
                date = s
            if re.match(r"^C\d{6}$", s):
                idx = i
                break
        if date and not out["date"]:
            out["date"] = date
        # letting totals can sit on the last page after the bidders
        for ln in lines:
            m = re.search(r"ESTIMATE TOTAL\s+([\d,]+\.\d{2})", ln)
            if m:
                out["estimateTotal"] = float(m.group(1).replace(",", ""))
            m = re.search(r"LETTING TOTAL\s+([\d,]+\.\d{2})\s*([+-]\s?\d+\.\d)?", ln)
            if m:
                out["lettingTotal"] = float(m.group(1).replace(",", ""))
                if m.group(2):
                    out["lettingTotalPctDiff"] = float(m.group(2).replace(" ", ""))
        if idx is None:
            continue
        c = {"id": lines[idx].strip(), "div": div}
        # header lines until PROPOSAL LENGTH: wbs, funding, county[, tip]
        hdr = []
        j = idx + 1
        while j < len(lines) and "PROPOSAL LENGTH" not in lines[j]:
            if lines[j].strip():
                hdr.append(lines[j].strip())
            j += 1
        if hdr:
            c["wbs"] = hdr[0]
        if len(hdr) > 1:
            c["funding"] = hdr[1]
        if len(hdr) > 2:
            c["county"] = hdr[2].title()
        c["tip"] = hdr[3] if len(hdr) > 3 else ""
        body = "\n".join(lines[j:])
        m = re.search(r"PROPOSAL LENGTH\s+([\d.]+)\s+MILES", body)
        if m:
            c["lengthMiles"] = float(m.group(1))
        m = re.search(r"TYPE OF WORK\s+(.+)", body)
        if m:
            c["typeOfWork"] = m.group(1).strip()
        m = re.search(r"LOCATION\s+(.+?)(?:\n\s{10,}(\S.*?))?\n\s*\n", body)
        if m:
            loc = m.group(1).strip()
            if m.group(2) and "EST CONST" not in m.group(2):
                loc += " " + m.group(2).strip()
            c["location"] = loc
        m = re.search(r"RPN (\d+)\s+(\d+) BIDDER", body)
        if m:
            c["rpn"] = m.group(1)
            c["nBidders"] = int(m.group(2))
        m = re.search(r"ESTIMATE\s+([\d,]+\.\d{2})", body)
        if m:
            c["estimate"] = float(m.group(1).replace(",", ""))
        # bidders: after "$ TOTALS"
        bidders = []
        started = False
        for ln in lines[j:]:
            s = ln.strip()
            if "$ TOTALS" in s:
                started = True
                continue
            if not started or not s:
                continue
            if "ESTIMATE TOTAL" in s or "LETTING TOTAL" in s or "AWARDED" in s:
                break
            m = AMT.search(s)
            if m:
                raw = s[: m.start()].strip()
                bidders.append({"raw": raw,
                                "amt": float(m.group(1).replace(",", "")),
                                "pctDiff": float(m.group(2).replace(" ", ""))})
            elif bidders and re.match(r"^[A-Z ,&.'-]+$", s):
                bidders[-1]["raw"] += " " + s  # wrapped name tail
        for b in bidders:
            name, city = split_name_city(b["raw"])
            b["name"], b["city"] = name, city
            del b["raw"]
        c["bidders"] = bidders
        if bidders:
            c["low"] = bidders[0]["name"]
            c["lowAmt"] = bidders[0]["amt"]
        out["contracts"].append(c)
    return out


if __name__ == "__main__":
    res = parse(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    for c in res["contracts"]:
        listed = len(c["bidders"])
        flag = "" if listed == c.get("nBidders") else f"  !! RPN says {c.get('nBidders')} bidders, parsed {listed}"
        print(f"{c['id']} div{c['div']} {c.get('county','?')} {c.get('nBidders')} bidders"
              f" low={c.get('low')} {c.get('lowAmt')}{flag}")
    print("lettingTotal:", res["lettingTotal"], " estimateTotal:", res["estimateTotal"],
          " sum(low):", round(sum(c.get("lowAmt", 0) for c in res["contracts"]), 2))
