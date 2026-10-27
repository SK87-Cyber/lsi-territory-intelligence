#!/usr/bin/env python3
"""Build an NC letting delta from a parsed Item C JSON plus (optionally) the
letting's XLS bid tab converted to .xlsx.

Usage:
  python3 -I nc_delta.py <itemc.json> <out_delta.json> [xlsx_path]

XLS layout (NCDOT legacy bid-tab export, one flat table):
  col 0 letting id, 5 contract, 14 pay-item code, 15 spec section, 16 line no,
  19 description, 20 supplemental description, 21 qty, 22/23 units,
  then up to three bidder blocks of 5 cols: name, city, unit price,
  extension, blank. Items with more bidders repeat the row with further
  bidder blocks, so rows are grouped by (contract, line no).
  The spreadsheet holds itemised prices for a SUBSET of bidders (always
  including the low bidder); contract totals and bid counts come only from
  Item C. A contract's item list counts as complete only when the low
  bidder's item extensions sum to its Item C total to the cent.

Lighting classifier (NC Division 14) and the delta gates are implemented
exactly as documented in the year record's rules.
"""
import json
import re
import sys
from decimal import Decimal

LIGHT_WORDS = re.compile(
    r"LIGHTING|LUMINAIRE|LIGHT STANDARD|HIGH MOUNT|LITE STD|LIGHT POLE"
    r"|STREET LIGHT|LITE CNTRL")
EXCLUDE_WORDS = re.compile(
    r"WZ PRESENCE LIGHTING|LUMINAIRE ARM FOR VIDEO SYSTEM|CCTV METAL POLE"
    r"|SUPPORT, BREAKAWAY STL BM|SUPPORTS, OMNI-DIRECTIONAL BREAKAWAY")
SHARED_FAMS = {"5125", "5150", "5155", "5175", "5180", "5185", "5190", "5195",
               "5200", "5205", "5210", "5215", "5220", "5240"}
SUBS = {"5005": "pole", "5010": "pole", "5015": "pole", "5020": "control",
        "5030": "luminaire", "5080": "assembly", "5120": "control",
        "5145": "control", "5260": "lighting-lump", "5025": "infrastructure",
        "5070": "infrastructure", "5270": "work"}


def classify(code, section, desc):
    """-> 'lighting' | 'shared' | 'excluded' | None."""
    fam = code[:4]
    d = desc.upper()
    sec = section if section.isdigit() else ""
    if EXCLUDE_WORDS.search(d):
        return "excluded"
    if sec == "1413" or "PORTABLE LIGHTING" in d:
        return "excluded"  # §1413 Portable Lighting
    if fam in SHARED_FAMS:
        return "shared"
    if fam.isdigit() and 5000 <= int(fam) <= 5299:
        return "lighting"
    if sec and 1400 <= int(sec) <= 1413:
        return "lighting"
    if LIGHT_WORDS.search(d):
        return "lighting"
    return None


def sub_for(code, desc):
    s = SUBS.get(code[:4])
    if s == "lighting-lump":
        return "work" if re.search(r"REMOVE|RELOCATE|REINSTALL", desc.upper()) else "luminaire"
    return s or ("infrastructure" if code[:4] in SHARED_FAMS else None)


def load_xls(path):
    """-> {contract: {line_no: item}} with per-bidder unit prices/extensions."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    contracts = {}
    for row in ws.iter_rows(values_only=True):
        cid = row[5]
        if not cid or row[16] is None:
            continue  # summary rows: 9900 CONTRACT TOTAL, 9901 category, 9999 bidder order
        line = str(row[16])
        items = contracts.setdefault(cid, {})
        desc = " ".join(str(x) for x in (row[19], row[20]) if x)
        it = items.setdefault(line, {
            "line": line, "code": str(row[14] or ""), "section": str(row[15] or ""),
            "desc": desc, "qty": float(row[21] or 0), "unit": str(row[23] or row[22] or ""),
            "prices": {}, "ext": {}})
        for base in (24, 29, 34):
            name = row[base]
            if not name:
                continue
            unit_p = row[base + 2]
            ext = row[base + 3]
            if unit_p is None and ext is None:
                continue
            it["prices"][str(name)] = float(Decimal(str(unit_p)))
            it["ext"][str(name)] = Decimal(str(ext))
    return contracts


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--"))
    itemc = json.load(open(args[0], encoding="utf-8"))
    out_path = args[1]
    xls = load_xls(args[2]) if len(args) > 2 else None
    award = opts.get("award", "apparent")
    award_note = opts.get("award-note", "")

    date = itemc["date"].title().replace("Mc", "Mc")  # e.g. "September 15, 2026"
    mon, day, year = re.match(r"(\w+) (\d+), (\d+)", date).groups()
    MON = {"January": "01", "February": "02", "March": "03", "April": "04",
           "May": "05", "June": "06", "July": "07", "August": "08",
           "September": "09", "October": "10", "November": "11", "December": "12"}
    iso = f"{year}-{MON[mon]}-{int(day):02d}"
    short = f"{mon[:3]} {int(day)}, {year}"
    lid = "L" + year[2:] + MON[mon] + f"{int(day):02d}"

    all_rows, lighting, shared = [], [], []
    for c in itemc["contracts"]:
        row = {
            "id": c["id"], "rpn": c.get("rpn"), "tip": c.get("tip", ""),
            "wbs": c.get("wbs", ""), "funding": c.get("funding", ""),
            "county": c.get("county", ""), "div": c.get("div"),
            "desc": c.get("typeOfWork", ""), "location": c.get("location", ""),
            "lengthMiles": c.get("lengthMiles"), "let": short,
            "estimate": c.get("estimate"), "nBidders": c.get("nBidders"),
            "low": title_name(c.get("low", "")), "lowAmt": c.get("lowAmt"),
            "bidders": [[title_name(b["name"]), b["amt"]] for b in c["bidders"]],
        }
        verdict = None
        if xls is not None:
            items = xls.get(c["id"])
            if items:
                # find the low bidder's sheet name (uppercase prefix match)
                sheet_names = set()
                for it in items.values():
                    sheet_names.update(it["ext"].keys())
                low_sheet = match_name(c.get("low", ""), sheet_names)
                recon = False
                if low_sheet:
                    total = sum(it["ext"].get(low_sheet, Decimal(0))
                                for it in items.values())
                    recon = (total == Decimal(str(c["lowAmt"])))
                row["itemsReconciled"] = bool(recon)
                row["lowSheet"] = low_sheet
                if recon:
                    verdict = judge(c, items, low_sheet, lighting, shared, short)
                else:
                    verdict = "UNVERIFIED"  # partial item list - no verdict
            else:
                row["itemsReconciled"] = False
                verdict = "UNVERIFIED"
        else:
            verdict = "UNKNOWN"  # no bid tabs posted yet
        row["cls"] = verdict
        row["award"] = award
        if award_note:
            row["awardNote"] = award_note
        all_rows.append(row)

    delta = {
        "letting": {
            "id": lid, "date": short, "iso": iso,
            "n": len(itemc["contracts"]),
            "low": round(sum(c["lowAmt"] for c in itemc["contracts"]), 2),
            "bids": sum(c.get("nBidders", 0) for c in itemc["contracts"]),
            "estimateTotal": itemc.get("estimateTotal"),
            "printedLettingTotal": itemc.get("lettingTotal"),
            "award": award,
        },
        "lettingNote": opts.get("letting-note", ""),
        "all": all_rows, "lighting": lighting, "shared": shared,
    }
    pt = delta["letting"]["printedLettingTotal"]
    delta["letting"]["reconciled"] = (pt is not None and
                                      abs(pt - delta["letting"]["low"]) < 0.005)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(delta, f, indent=1)
    print(json.dumps(delta["letting"], indent=1))
    for r in all_rows:
        print(r["id"], r["county"], "cls=" + str(r["cls"]),
              "reconciled=" + str(r.get("itemsReconciled")))
    print("lighting rows:", len(lighting), " shared-only rows:", len(shared))


def judge(c, items, low_sheet, lighting, shared, short):
    """Classify a reconciled contract; append to lighting/shared lists."""
    light_items, shared_items, excluded = [], [], []
    for it in sorted(items.values(), key=lambda x: int(x["line"])):
        k = classify(it["code"], it["section"], it["desc"])
        if k == "lighting":
            light_items.append(it)
        elif k == "shared":
            shared_items.append(it)
        elif k == "excluded":
            excluded.append(it)
    if not light_items and not shared_items:
        return "NONE"
    if not light_items:  # shared electrical alone - listed, not counted
        amt = float(sum(it["ext"].get(low_sheet, Decimal(0)) for it in shared_items))
        shared.append({"id": c["id"], "tip": c.get("tip", ""),
                       "county": c.get("county", ""), "div": c.get("div"),
                       "let": short, "low": title_name(c.get("low", "")),
                       "amount": round(amt, 2),
                       "what": "; ".join(sorted({it["desc"].split(" ")[0].title()
                                                 for it in shared_items}))})
        return "SHARED_ONLY"
    counted = light_items + shared_items  # shared counts beside lighting
    l2 = float(sum(it["ext"].get(low_sheet, Decimal(0)) for it in counted))
    split = {"hardware": 0.0, "infrastructure": 0.0, "work": 0.0, "lump": 0.0}
    split_hw = {"luminaire": 0.0, "pole": 0.0, "assembly": 0.0, "control": 0.0}
    out_items = []
    for it in counted:
        sub = sub_for(it["code"], it["desc"]) or "infrastructure"
        ext = float(it["ext"].get(low_sheet, Decimal(0)))
        if sub in split_hw:
            split["hardware"] += ext
            split_hw[sub] += ext
        elif sub == "work":
            split["work"] += ext
        else:
            split["infrastructure"] += ext
        out_items.append({"line": it["line"], "code": it["code"],
                          "section": it["section"], "desc": it["desc"],
                          "qty": it["qty"], "unit": it["unit"],
                          "prices": it["prices"], "sub": sub})
    lighting.append({
        "id": c["id"], "tip": c.get("tip", ""), "county": c.get("county", ""),
        "div": c.get("div"), "let": short, "low": title_name(c.get("low", "")),
        "lowAmt": c["lowAmt"], "l2": round(l2, 2),
        "product": round(split["hardware"], 2), "nItems": len(items),
        "items": out_items, "lowSheet": low_sheet,
        "split": {k: round(v, 2) for k, v in split.items()},
        "splitHw": {k: round(v, 2) for k, v in split_hw.items()},
        "cls": "L2", "share": round(l2 / c["lowAmt"], 4),
        "reconciled": True})
    return "L2"


def match_name(itemc_name, sheet_names):
    a = re.sub(r"[^A-Z0-9]", "", itemc_name.upper())
    for s in sheet_names:
        b = re.sub(r"[^A-Z0-9]", "", s.upper())
        if a.startswith(b) or b.startswith(a):
            return s
    return None


def title_name(n):
    """Mirror the year record's mixed-case bidder style."""
    keep_upper = {"LLC", "JV", "II", "FSC", "NJR", "APAC", "BMCO", "CSX"}
    words = []
    for w in n.split():
        bare = w.rstrip(".,")
        if bare in keep_upper:
            words.append(w)
        elif bare == "DBA":
            words.append(w.lower())
        else:
            words.append(w.title())
    return " ".join(words)


if __name__ == "__main__":
    main()
