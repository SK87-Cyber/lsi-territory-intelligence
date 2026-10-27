#!/usr/bin/env python3
"""Parse an MDOT Commission Bid Awards pdftotext dump into JSON actions.

Usage: python3 -I ms_awards_parse.py <awards.txt> <out.json>
Untrusted input; nothing from it is executed.
"""
import json, re, sys

PROJ = re.compile(r"[A-Z]{1,6}-\d{3,4}-\d{2}\(\d+\)\s*/\s*(\d{9})")
AMT = re.compile(r"\$([\d,]+\.\d{2})\s*$")
AMT_NOCENTS = re.compile(r"\$([\d,]{4,})\s*$")


def main(txt_path, out_path):
    lines = open(txt_path).read().splitlines()
    action_date = None
    for ln in lines[:6]:
        m = re.search(r"^\s*([A-Z][a-z]+ \d{1,2}, \d{4})\s*$", ln)
        if m:
            action_date = m.group(1)
            break
    section = None
    entries = []
    cur = None

    def close():
        nonlocal cur
        if cur and cur["proposals"]:
            entries.append(cur)
        cur = None

    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("AWARDED") and "TOTAL" not in s:
            close(); section = "awarded"; continue
        if s.startswith("POSTPONED"):
            close(); section = "pwr"; continue
        if "TOTAL AWARDED" in s or s.startswith("BY:") or "CONTRACT ADMINISTRATION" in s \
           or "Original Signed" in s or "NEAL DOUGHERTY" in s or "***NONE***" in s \
           or "GRAND TOTAL" in s or "BROUGHT FORWARD" in s:
            close(); continue
        if section is None:
            continue
        props = PROJ.findall(s)
        starts_entry = props and not s[0].islower() and (s == s.upper() or re.match(r"^[A-Z]{1,6}-\d", s))
        if starts_entry and (cur is None or cur.get("_seen_body")):
            close()
            cur = {"section": section, "proposals": props, "projLine": [s],
                   "county": None, "projDesc": [], "contractor": None, "amount": None,
                   "_seen_body": False}
            if s.rstrip().endswith("&"):
                cur["_hdr_open"] = True
            continue
        if cur is None:
            continue
        if cur.get("_hdr_open"):
            cur["proposals"] += PROJ.findall(s)
            cur["projLine"].append(s)
            cur.pop("_hdr_open")
            continue
        mc = re.match(r"^([A-Z .&'-]+?) COUNT(?:Y|IES) - (.*)$", s)
        if mc and cur["county"] is None:
            cur["county"] = mc.group(1).title()
            cur["projDesc"].append(mc.group(2))
            cur["_seen_body"] = True
            continue
        ma = AMT.search(s)
        if ma:
            cur["amount"] = float(ma.group(1).replace(",", ""))
            cur["_seen_body"] = True
            # strip the amount off; the rest may be an address fragment
            s = AMT.sub("", s).strip()
            if not s:
                continue
        if section == "awarded" and cur["contractor"] is None and s == s.upper() \
           and not re.search(r"\d{5}", s) and not re.match(r"^(PO BOX|\d)", s) and cur["county"]:
            cur["contractor"] = s
            cur["_seen_body"] = True
            continue
        cur["_seen_body"] = True
        # otherwise: address lines / wrapped description — keep description
        if cur["contractor"] is None and cur["county"] is not None and s != s.upper():
            cur["projDesc"].append(s)
    close()

    for e in entries:
        e.pop("_seen_body", None)
        e["projDesc"] = " ".join(e["projDesc"])
        e["projLine"] = " ".join(e["projLine"])
    out = {"actionDate": action_date, "entries": entries}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    for e in entries:
        print(e["section"], e["proposals"], e["contractor"], e["amount"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
