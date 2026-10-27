#!/usr/bin/env python3
"""Parse an ALDOT Low Bid Sheet (pdftotext -layout output) into a census JSON.

Usage: python3 -I parse_lowbid.py <layout.txt> <letting-iso> <letting-label> \
                <county_div_AL.json> <out.json>

The Low Bid Sheet lists AT MOST the three lowest bidders per contract — a cap,
not the full bidder list. Bids are opened but awards are pending (no tabulation
posted), so this is census-level only: NOT a year-record entry, no award facts.
"""
import json, re, sys

CALL = re.compile(r"^\s{1,5}(\d{3})\.\s+(\S.*?)\s*$")
BIDDER = re.compile(r"^\s{0,5}([1-3])\.\s+(\S.*?)\s+\$([\d,]+\.\d{2})\s*$")
COUNTY = re.compile(r"^Count(?:y|ies):\s+(.+?)\s*$")
PAGENO = re.compile(r"^\s*\d+\s*$")

LIGHT_HINT = re.compile(r"\bLIGHTING\b")

def main(src, iso, label, cdiv_p, out_p):
    cdiv = json.load(open(cdiv_p))
    by_upper = {k.upper(): (k, v) for k, v in cdiv.items()}
    lines = open(src, encoding="utf-8", errors="replace").read().splitlines()

    contracts, cur = [], None
    for ln in lines:
        if ("Alabama Department of Transportation" in ln or
                "Low Bid Sheet" in ln or "Letting Date:" in ln or
                PAGENO.match(ln)):
            continue
        m = CALL.match(ln)
        if m and not BIDDER.match(ln):
            cur = {"call": m.group(1), "project": m.group(2),
                   "county": None, "div": None, "desc": [],
                   "lowBidders": [], "biddersCapped": False,
                   "status": "low bids opened — award pending"}
            contracts.append(cur)
            continue
        if cur is None:
            continue
        m = COUNTY.match(ln)
        if m:
            names, divs = [], []
            for part in m.group(1).split(","):
                part = part.strip()
                if not part:
                    continue
                hit = by_upper.get(part.upper())
                names.append(hit[0] if hit else part.title())
                divs.append(hit[1] if hit else None)
            cur["county"] = ", ".join(names)
            cur["div"] = divs[0] if divs else None
            continue
        if "WITHDRAWN FROM THE LETTING" in ln:
            cur["status"] = "withdrawn from the letting"
            continue
        m = BIDDER.match(ln)
        if m:
            cur["lowBidders"].append(
                [re.sub(r"\s+", " ", m.group(2)), float(m.group(3).replace(",", ""))])
            continue
        s = ln.strip()
        if not s:
            continue
        if cur["lowBidders"]:
            continue  # address lines under a bidder
        if re.match(r"^[A-Z0-9(]", s):
            cur["desc"].append(s)

    for c in contracts:
        c["desc"] = " ".join(c["desc"])
        c["biddersCapped"] = len(c["lowBidders"]) >= 3
        if LIGHT_HINT.search(c["desc"]):
            c["lightingFlag"] = ("description mentions lighting — possible "
                                 "Section 750 content; flag only, no dollars "
                                 "claimed until the tabulation posts")

    with_bids = [c for c in contracts if c["lowBidders"]]
    withdrawn = [c for c in contracts if "withdrawn" in c["status"]]
    out = {
        "letting": {
            "id": "L" + iso[2:4] + iso[5:7] + iso[8:10], "date": label,
            "iso": iso,
            "status": ("bids opened, awards pending — no Tabulation of Bids "
                       "posted as of Oct 26, 2026, so nothing here is an award"),
            "contracts": len(contracts), "withBids": len(with_bids),
            "withdrawn": len(withdrawn),
            "lowBidRows": sum(len(c["lowBidders"]) for c in contracts),
            "apparentLowSum": round(sum(c["lowBidders"][0][1]
                                        for c in with_bids), 2),
            "apparentLowSumNote": ("sum of the #1 (apparent low) bids on the "
                                   "Low Bid Sheet — not awards"),
        },
        "census": True,
        "biddersCap": ("ALDOT's Low Bid Sheet lists at most the three lowest "
                       "bidders per contract — a cap, not the full bidder "
                       "list; biddersCapped=true means more bidders may exist"),
        "contracts": contracts,
    }
    with open(out_p, "w") as f:
        json.dump(out, f, indent=1)
    flagged = [c["call"] for c in contracts if "lightingFlag" in c]
    print(f"{label}: contracts={len(contracts)} withBids={len(with_bids)} "
          f"withdrawn={len(withdrawn)} lowBidRows={out['letting']['lowBidRows']} "
          f"lightingFlags={flagged}")

if __name__ == "__main__":
    main(*sys.argv[1:6])
