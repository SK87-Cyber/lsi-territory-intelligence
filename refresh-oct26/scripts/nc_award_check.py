#!/usr/bin/env python3
"""Search a pdftotext dump of an NCDOT Board document for a contract's award.

Usage: python3 -I nc_award_check.py <board_doc.txt> <contract_id>

Finds the Item C page for the contract, prints the page's letting date, the
bidder block, and whether the literal text AWARDED appears between the
contract's bidder list and the next page header. Also prints any narrative
award statement lines ("awarded by the Secretary", "Award of Highway
Construction Contracts").
"""
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()
cid = sys.argv[2]
lines = text.splitlines()

for i, ln in enumerate(lines):
    if re.search(r"awarded by the Secretary|Award of Highway Construction Contracts", ln):
        ctx = " ".join(l.strip() for l in lines[i:i + 2]).strip()
        print(f"NARRATIVE line {i + 1}: {ctx}")

hits = [i for i, ln in enumerate(lines) if ln.strip() == cid]
if not hits:
    print(f"{cid}: NOT FOUND in {sys.argv[1]}")
    sys.exit(1)
for i in hits:
    # scan forward to the next HIGHWAY LETTING page header or EOF
    end = len(lines)
    for j in range(i + 1, len(lines)):
        if "HIGHWAY LETTING" in lines[j]:
            end = j
            break
    block = lines[i:end]
    awarded = any(ln.strip() == "AWARDED" for ln in block)
    date = next((ln.strip() for ln in lines[max(0, i - 12):i]
                 if re.match(r"^[A-Z]+ \d{1,2}, \d{4}$", ln.strip())), "?")
    print(f"\n{cid} at line {i + 1}, letting date on page: {date}, "
          f"AWARDED text present: {awarded}")
    for ln in block:
        if re.search(r"[\d,]+\.\d{2}\s+[+-]", ln) or ln.strip() == "AWARDED":
            print("   ", ln.strip())
