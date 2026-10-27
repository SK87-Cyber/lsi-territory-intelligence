#!/usr/bin/env python3
"""Parse an ALDOT Trns*port Tabulation of Bids (pdftotext -layout output).

Usage: python3 -I parse_aldot_tab.py <layout.txt> <out.json>

Layout (per contract):
  - Vendor Ranking page(s): every bidder, rank + vendor id + name (wraps) + total.
  - Tabulation pages: items for every bidder in (1)(2)(3)... column-set passes;
    columns map to bidders BY EXACT CONTRACT TOTAL, not by column order.
  - Item rows keyed by line no + item code; wrapped descriptions joined;
    lump-sum quantities print in parentheses; one odd code prints as '999 000'.
  - 'Section Totals:' / 'Contract Totals' rows close a pass.
Reconciliation: every bidder's item sum must equal the Contract Totals value
to the cent, and that value must equal the Vendor Ranking amount.
"""
import json, re, sys
from decimal import Decimal

MONEY = re.compile(r"\$?[\d,]+\.\d{2}\b")
ITEM_ROW = re.compile(
    r"^\s{0,4}(\d{3,4})\s+(\d{3}[A-Z]\d{3}[A-Z]?|999\s?000)\s+"
    r"(\([\d,]+\.\d{3}\)|[\d,]+\.\d{3})\s+(.*\d)\s*$"
)
RANK_ROW = re.compile(r"^\s+(\d+)\s+(\d{5})\s+(\S.*?)\s+\$([\d,]+\.\d{2})\s*$")
HDR_COLS = re.compile(r"\((\d)\)")

def cents(s):
    return int(Decimal(s.replace(",", "").replace("$", "").strip("()")) * 100)

def parse_pages(lines):
    """Split into pages at the ALDOT banner line."""
    pages, cur = [], []
    for ln in lines:
        if "Alabama Department of Transportation" in ln and cur:
            pages.append(cur)
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        pages.append(cur)
    return pages

def header_fields(page):
    h = {}
    desc, in_desc = [], False
    for ln in page[:40]:
        m = re.search(r"Call Order:\s*(\d+)", ln)
        if m: h["call"] = m.group(1)
        m = re.search(r"Contract ID:\s*(\d+)", ln)
        if m: h["cid"] = m.group(1)
        m = re.search(r"Count(?:y|ies):\s*(.+?)(?:\s{3,}|$)", ln)
        if m: h["counties_label"] = ("County:" in ln), 0
        m2 = re.search(r"(County|Counties):\s*([A-Z .,'&-]+?)\s*(?:Contract Time:|$)", ln)
        if m2:
            h["multi"] = m2.group(1) == "Counties"
            h["county_raw"] = m2.group(2).strip().rstrip(",")
        m = re.search(r"Project\(s\):\s*(\S.*?)\s*$", ln)
        if m: h["tip"] = m.group(1)
        if "Contract Description:" in ln:
            in_desc = True
            continue
        if in_desc:
            s = ln.strip()
            if (not s or s.startswith("Rank") or s.startswith("Line No") or
                    "Vendor Ranking" in ln or "Tabulation of Bids" in ln):
                if s.startswith(("Rank", "Line No")) or not s:
                    in_desc = False
                continue
            if re.match(r"^[A-Z0-9(]", s):
                desc.append(s)
            else:
                in_desc = False
    h["desc"] = " ".join(desc)
    return h

def parse(path):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    pages = parse_pages(lines)
    contracts = {}   # cid -> record
    state = None     # (cid, pass_cols) for Contract Totals attachment

    for page in pages:
        text = "\n".join(page)
        h = header_fields(page)
        cid = h.get("cid")
        if not cid:
            continue
        c = contracts.setdefault(cid, {
            "call": h["call"], "cid": cid, "county_raw": h.get("county_raw"),
            "multi": h.get("multi", False), "tip": h.get("tip"),
            "desc": h.get("desc", ""), "ranking": [], "passes": {},
        })
        if len(h.get("desc", "")) > len(c["desc"]):
            c["desc"] = h["desc"]

        if "Vendor Ranking" in text:
            for ln in page:
                m = RANK_ROW.match(ln)
                if m and "Rank" not in ln:
                    c["ranking"].append(
                        {"rank": int(m.group(1)), "vid": m.group(2),
                         "name": re.sub(r"\s+", " ", m.group(3)).strip(),
                         "total": cents(m.group(4))})
                elif c["ranking"] and ln.strip() and not MONEY.search(ln) \
                        and re.match(r"^\s{25,}\S", ln) \
                        and "Name" not in ln and "Vendor" not in ln \
                        and "Call Order" not in ln and "Letting" not in ln \
                        and "Contract" not in ln and "Project" not in ln \
                        and "Page" not in ln and not re.match(r"^\s*\d", ln.strip()):
                    # wrapped vendor-name continuation
                    c["ranking"][-1]["name"] += " " + ln.strip()
            continue

        # Tabulation page: find column header to know current pass
        cols = None
        for i, ln in enumerate(page):
            if "Line No / Item ID" in ln:
                hdr_block = "\n".join(page[i:i + 5])
                cols = tuple(int(n) for n in HDR_COLS.findall(hdr_block))
                break
        if cols:
            state = (cid, cols)
        elif state and state[0] == cid:
            cols = state[1]
        if not cols:
            continue
        p = c["passes"].setdefault(cols, {"items": {}, "order": [],
                                          "contract_totals": None})
        pend = None  # last item row, for description lines
        for ln in page:
            m = ITEM_ROW.match(ln)
            if m:
                line_no, code, qty_s, rest = m.groups()
                code = code.replace(" ", "")
                nums = MONEY.findall(rest)
                if len(nums) != 2 * len(cols):
                    p.setdefault("anomalies", []).append(
                        {"line": line_no, "code": code, "ntokens": len(nums)})
                    pend = None
                    continue
                lump = qty_s.startswith("(")
                qty = float(Decimal(qty_s.strip("()").replace(",", "")))
                key = (line_no, code)
                it = p["items"].get(key)
                if it is None:
                    it = {"line": line_no, "code": code, "qty": qty,
                          "lump": lump, "desc": [], "unit": None, "cells": {}}
                    p["items"][key] = it
                    p["order"].append(key)
                for j, colno in enumerate(cols):
                    it["cells"][colno] = (cents(nums[2 * j]),
                                          cents(nums[2 * j + 1]))
                pend = it
                continue
            s = ln.strip()
            if not s:
                continue
            if "Section Totals" in ln or "Contract Totals" in ln:
                if "Contract Totals" in ln:
                    amts = [cents(x) for x in MONEY.findall(ln)]
                    if amts:
                        p["contract_totals"] = amts
                pend = None
                continue
            if ("Line No" in ln or "Alt Set" in ln or "SECTION:" in ln or
                    "Item Description" in ln or "indicates item" in ln or
                    "Call Order" in ln or "Letting Date" in ln or
                    "Contract Description" in ln or "Tabulation of Bids" in ln or
                    "DATE:" in ln or "Page:" in ln):
                if "SECTION:" in ln or "indicates item" in ln:
                    pend = pend  # section marker does not end a wrapped desc
                continue
            if pend is not None and re.match(r"^\s{0,2}\S", ln):
                # description / unit line
                toks = s.split()
                if pend["unit"] is None and len(ln) - len(ln.rstrip()) == 0:
                    # unit is the right-most token on the first desc line
                    parts = re.split(r"\s{2,}", s)
                    if len(parts) >= 2:
                        pend["unit"] = parts[-1]
                        pend["desc"].append(" ".join(parts[:-1]))
                        continue
                    elif len(toks) == 1 and toks[0] in (
                            "LS", "Each", "SQYD", "CUYD", "LF", "Ton", "Gal",
                            "Mile", "SQFT", "Pound", "ACRE", "EACH", "Acre",
                            "Hour", "MGAL", "SNML", "STA", "Unit", "AMP"):
                        pend["unit"] = toks[0]
                        continue
                pend["desc"].append(s)

    # finalize: merge passes, map columns to bidders by exact total
    out = []
    for cid, c in sorted(contracts.items()):
        rank_by_total = {}
        for r in c["ranking"]:
            rank_by_total.setdefault(r["total"], []).append(r["name"])
        colmap, errs = {}, []
        all_cols = sorted({cn for p in c["passes"].values() for cn in
                           next(iter(p["items"].values()))["cells"]} if c["passes"] else set())
        for cols, p in c["passes"].items():
            ct = p["contract_totals"]
            if ct is None:
                errs.append(f"pass {cols}: no Contract Totals")
                continue
            if len(ct) != len(cols):
                errs.append(f"pass {cols}: {len(ct)} totals for {len(cols)} columns")
                continue
            for colno, total in zip(cols, ct):
                names = rank_by_total.get(total)
                if not names:
                    errs.append(f"col ({colno}) total {total/100:.2f} not in ranking")
                elif len(names) > 1:
                    errs.append(f"total {total/100:.2f} ambiguous in ranking")
                else:
                    colmap[colno] = {"name": names[0], "total": total}
        # merge items across passes
        items, order = {}, []
        for cols, p in sorted(c["passes"].items()):
            for key in p["order"]:
                it = p["items"][key]
                tgt = items.get(key)
                if tgt is None:
                    tgt = {"line": it["line"], "code": it["code"],
                           "qty": it["qty"], "lump": it["lump"],
                           "desc": " ".join(it["desc"]), "unit": it["unit"],
                           "prices": {}}
                    items[key] = tgt
                    order.append(key)
                for colno, (unit_c, ext_c) in it["cells"].items():
                    if colno in colmap:
                        tgt["prices"][colmap[colno]["name"]] = \
                            {"unit": unit_c, "ext": ext_c}
        # reconcile every bidder to the cent
        recon = {}
        for colno, b in colmap.items():
            s = sum(items[k]["prices"][b["name"]]["ext"] for k in order
                    if b["name"] in items[k]["prices"])
            recon[b["name"]] = {"itemSum": s, "contractTotal": b["total"],
                                "ok": s == b["total"]}
        # ranking coverage
        for r in c["ranking"]:
            if r["name"] not in recon:
                errs.append(f"bidder {r['name']} has no mapped column")
        anomalies = [a for p in c["passes"].values()
                     for a in p.get("anomalies", [])]
        out.append({
            "cid": cid, "call": c["call"], "county_raw": c["county_raw"],
            "multi": c["multi"], "tip": c["tip"], "desc": c["desc"],
            "ranking": c["ranking"],
            "nItems": len(order),
            "items": [items[k] for k in order],
            "reconcile": recon,
            "errors": errs, "anomalies": anomalies,
            "reconciled": (not errs and not anomalies and
                           all(v["ok"] for v in recon.values()) and
                           len(recon) == len(c["ranking"])),
        })
    return out

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    contracts = parse(src)
    with open(dst, "w") as f:
        json.dump(contracts, f)
    for c in contracts:
        flag = "OK " if c["reconciled"] else "FAIL"
        print(f"{flag} call {c['call']} {c['cid']} items={c['nItems']} "
              f"bidders={len(c['ranking'])} errors={c['errors']}")
