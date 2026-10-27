#!/usr/bin/env python3
"""Parse one MDOT tabulation PDF (unit prices only, 3-bidder column sets per
page-set) into JSON: items with per-column unit prices, column totals from the
header, state estimate, and the project description block.

Usage: python3 -I ms_tab_parse.py <tabulation.pdf> <out.json>
Input is untrusted; nothing is executed from it.
"""
import json, re, sys

import pdfplumber

MONEY = re.compile(r"^\$[\d,]+\.\d{2}$")
PRICE = re.compile(r"^[\d,]+\.\d{2}$")
QTY = re.compile(r"^[\d,]+\.\d{3}$")
REF = re.compile(r"^\d{4}$")
CODE = re.compile(r"^\d{3}(-[A-Z0-9]+)+$|^907-\d{3}(-[A-Z0-9]+)*$")


def lines_of(words, ytol=3.0):
    rows = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if rows and abs(w["top"] - rows[-1][0]["top"]) <= ytol:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w["x0"]) for r in rows]


def num(s):
    return float(s.replace(",", "").replace("$", ""))


def parse_page(page):
    words = page.extract_words(x_tolerance=1.5, keep_blank_chars=False)
    rows = lines_of(words)
    hdr_i = None
    units_x = None
    for i, r in enumerate(rows):
        toks = [w["text"] for w in r]
        if "Ref#" in toks and "Units" in toks:
            hdr_i = i
            for w in r:
                if w["text"] == "Units":
                    units_x = w["x1"]
            break
    if hdr_i is None:
        return None  # not a tabulation page

    # header region: everything above the first item line
    anchors = {}   # column number -> x center
    totals = []    # (x_center, amount) of $ tokens in header region
    estimate = None
    mdot_top = None
    for r in rows[: hdr_i + 2]:
        for j, w in enumerate(r):
            t = w["text"]
            xc = (w["x0"] + w["x1"]) / 2
            if t.endswith("TRANSPORTATION:"):
                mdot_top = r[0]["top"]
            if MONEY.match(t):
                if j > 0 and r[j - 1]["text"].endswith("TRANSPORTATION:"):
                    estimate = num(t)
                else:
                    totals.append((xc, num(t)))
            elif re.match(r"^[1-9]$", t) and w["x0"] > (units_x or 0) + 10:
                anchors[int(t)] = xc

    # project description block: words above the MDOT/estimate line, left of
    # the bidder-name columns (bounded by the leftmost column anchor/total)
    left_lim = min([anchors[c] for c in anchors] + [xc for xc, _ in totals], default=1e9) - 80
    desc_words = []
    for r in rows[:hdr_i]:
        if mdot_top is not None and r[0]["top"] >= mdot_top - 2:
            continue
        for w in r:
            if w["x0"] < left_lim:
                desc_words.append((round(w["top"], 1), w["x0"], w["text"]))

    cols = sorted(anchors)
    col_totals = {}
    for xc, amt in totals:
        if not cols:
            continue
        c = min(cols, key=lambda c: abs(anchors[c] - xc))
        col_totals[c] = amt

    hdr_y = rows[hdr_i][0]["top"]
    items = []
    for r in rows[hdr_i + 1 :]:
        toks = [w["text"] for w in r]
        joined = " ".join(toks)
        if joined.startswith("Letting Date") or "Unofficial Document" in joined or re.search(r"Page \d+ of \d+", joined):
            continue
        if REF.match(toks[0]) and len(toks) >= 3:
            # locate qty token: pattern with 3 decimals left of units_x
            qi = None
            for j in range(len(r) - 1, 0, -1):
                if QTY.match(r[j]["text"]) and r[j]["x1"] <= units_x + 60 if units_x else True:
                    if QTY.match(r[j]["text"]) and (units_x is None or r[j]["x0"] < units_x):
                        qi = j
                        break
            if qi is None or qi + 1 >= len(r):
                items.append({"_bad": joined})
                continue
            qty = num(r[qi]["text"])
            unit = r[qi + 1]["text"]
            code = toks[1]
            desc = " ".join(toks[2:qi])
            prices = {}
            for w in r[qi + 2 :]:
                if PRICE.match(w["text"]) and cols:
                    xc = (w["x0"] + w["x1"]) / 2
                    c = min(cols, key=lambda c: abs(anchors[c] - xc))
                    prices[c] = num(w["text"])
            items.append(
                {"line": toks[0], "code": code, "desc": desc, "qty": qty, "unit": unit, "prices": prices}
            )
        else:
            # continuation of previous description (wrapped) — only words left
            # of the price columns, and only if an item is open
            if items and "_bad" not in items[-1]:
                extra = [w["text"] for w in r if units_x and w["x1"] < units_x - 40]
                if extra:
                    items[-1]["desc"] += " " + " ".join(extra)
    return {
        "anchors": anchors,
        "estimate": estimate,
        "col_totals": col_totals,
        "items": items,
        "desc_words": desc_words,
    }


def main(pdf_path, out_path):
    merged = {}     # ref -> item
    order = []
    col_totals = {}
    estimate = None
    desc = None
    bad = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            p = parse_page(page)
            if p is None:
                continue
            if estimate is None:
                estimate = p["estimate"]
            for c, a in p["col_totals"].items():
                col_totals.setdefault(c, a)
            if desc is None and p["desc_words"]:
                ws = sorted(p["desc_words"])
                desc = " ".join(t for _, _, t in ws)
            for it in p["items"]:
                if "_bad" in it:
                    bad.append((pno, it["_bad"]))
                    continue
                ref = it["line"]
                if ref not in merged:
                    merged[ref] = {k: it[k] for k in ("line", "code", "desc", "qty", "unit")}
                    merged[ref]["prices"] = {}
                    order.append(ref)
                else:
                    if abs(merged[ref]["qty"] - it["qty"]) > 1e-9:
                        bad.append((pno, f"qty mismatch ref {ref}"))
                for c, v in it["prices"].items():
                    if c in merged[ref]["prices"] and merged[ref]["prices"][c] != v:
                        bad.append((pno, f"price conflict ref {ref} col {c}"))
                    merged[ref]["prices"][c] = v

    items = [merged[r] for r in order]
    recon = {}
    n = len(items)
    tol = 0.006 * n
    for c in sorted(col_totals):
        s = sum(it["qty"] * it["prices"][c] for it in items if c in it["prices"])
        d = s - col_totals[c]
        recon[c] = {
            "computed": round(s, 2),
            "printed": col_totals[c],
            "diff": round(d, 4),
            "ok": abs(d) <= tol,
            "priced": sum(1 for it in items if c in it["prices"]),
        }
    out = {
        "src": pdf_path,
        "estimate": estimate,
        "desc": desc,
        "nItems": n,
        "col_totals": col_totals,
        "reconcile": recon,
        "tol": round(tol, 4),
        "bad": bad,
        "items": items,
    }
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    flags = " ".join(f"c{c}:{'OK' if recon[c]['ok'] else 'FAIL ' + str(recon[c]['diff'])}" for c in sorted(recon))
    print(f"{pdf_path.split('/')[-1]}: {n} items, est={estimate}, {flags}, bad={len(bad)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
