#!/usr/bin/env python3
"""Emit MDOT letting deltas + the Aug 25 awards update from parsed artifacts.

Usage:
  python3 -I ms_emit.py <scratch_dir> <records_dir> <out_dir>

Reads (all produced by ms_census_parse.py / ms_tab_parse.py / ms_awards_parse.py
from UNTRUSTED pdfs; this script only treats them as data):
  <scratch>/census_<yyyymmdd>.json, <scratch>/tabs/<proposal>000.json,
  <scratch>/awards_<yyyymmdd>.json
Reference (read-only): <records>/MS_YEAR.json, <records>/county_div_MS.json
Writes: <out>/delta_YYYY-MM-DD.json, <out>/awards_update.json
"""
import json, os, re, sys
from datetime import datetime

# ---- lighting dictionary (records/MS_DICT.json, encoded as rules) ----------
FALSE_FRIENDS = re.compile(
    r"^(619-G|683-D|685-C|907-634-(?!PP)|907-636|202-B251)")
LIGHT_SPECIFIC = [
    (re.compile(r"^683-A"), "assembly"),
    (re.compile(r"^683-B"), "assembly"),
    (re.compile(r"^683-C"), "assembly"),
    (re.compile(r"^907-683-PP"), "assembly"),
    (re.compile(r"^907-634-PP"), "assembly"),
    (re.compile(r"^684-"), "infrastructure"),
    (re.compile(r"^686-"), "work"),
    (re.compile(r"^202-B(160|176|177|178)"), "work"),
    (re.compile(r"^907-683-G"), "work"),
    (re.compile(r"^907-683"), "work"),
]
SHARED = re.compile(r"^(682-|685-[BD]|907-682)")


def classify(code):
    """-> ('light', sub) | ('shared', 'infrastructure') | (None, None)"""
    if FALSE_FRIENDS.match(code):
        return None, None
    for rx, sub in LIGHT_SPECIFIC:
        if rx.match(code):
            return "light", sub
    if SHARED.match(code):
        return "shared", "infrastructure"
    return None, None


MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}
ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def dates(long_date):
    m = re.match(r"(\w+) (\d{1,2}), (\d{4})", long_date)
    mo, dy, yr = MONTHS[m.group(1)], int(m.group(2)), int(m.group(3))
    return (f"{ABBR[mo-1]} {dy}, {yr}", f"{yr}-{mo:02d}-{dy:02d}",
            f"L{str(yr)[2:]}{mo:02d}{dy:02d}")


def match_columns(tab, bidders):
    """tab column -> census bidder, matched by printed total (cost figure)."""
    out = {}
    used = set()
    for c, tot in tab["col_totals"].items():
        hits = [i for i, b in enumerate(bidders)
                if abs(b["amount"] - tot) < 0.005 and i not in used]
        if len(hits) != 1:
            return None
        out[int(c)] = bidders[hits[0]]
        used.add(hits[0])
    return out if len(out) == len(bidders) else None


def main(scratch, records, out_dir):
    year = json.load(open(os.path.join(records, "MS_YEAR.json")))
    rows_by_id = {r["id"]: r for r in year["all"]}

    LETTINGS = [
        ("20260821", "Emergency", "MS-57", "MS-58"),
        ("20260901", "Special", "MS-62", "MS-63"),
        ("20260922", "Regular", "MS-64", None),
        ("20260929", "Special", "MS-66", None),
    ]
    report = {}
    for key, kind, tc, ac in LETTINGS:
        census = json.load(open(os.path.join(scratch, f"census_{key}.json")))
        apath = os.path.join(scratch, f"awards_{key}.json")
        awards = json.load(open(apath)) if os.path.exists(apath) else None
        award_by_prop = {}
        if awards:
            for e in awards["entries"]:
                for p in e["proposals"]:
                    award_by_prop[p] = e

        long_date = census["letting"] or datetime.strptime(key, "%Y%m%d").strftime("%B %d, %Y").replace(" 0", " ")
        let_disp, iso, lid = dates(long_date)
        all_rows, light_rows, shared_rows = [], [], []
        bids = 0
        lowsum = 0.0
        recon_ok = recon_n = 0
        n_awarded = n_rejected = 0
        for c in census["calls"]:
            if c["withdrawn"]:
                continue
            prop = c["proposal"]
            tabp = os.path.join(scratch, "tabs", f"{prop}000.json")
            tab = json.load(open(tabp))
            cols = match_columns(tab, c["bidders"])
            assert cols, f"column/bidder total mismatch {prop}"
            rec = tab["reconcile"]
            ok = all(rec[str(cc)]["ok"] for cc in sorted(cols))
            recon_n += 1
            recon_ok += ok
            bids += len(c["bidders"])
            low = c["bidders"][0]
            lowsum += low["amount"]

            award = "apparent"
            if awards:
                e = award_by_prop.get(prop)
                if e and e["section"] == "awarded":
                    award = "awarded"
                    n_awarded += 1
                    assert abs(e["amount"] - low["amount"]) < 0.005, prop
                elif e:
                    award = "rejected"
                    n_rejected += 1

            desc_src = (tab["desc"] or c["desc"]).strip()
            is_ac = any(b["ac"] for b in c["bidders"])

            # ---- lighting / shared pass over every item -------------------
            items_l = []
            has_anchor = False
            shared_items = []
            for it in tab["items"]:
                kind2, sub = classify(it["code"])
                if kind2 == "light":
                    has_anchor = True
                if kind2 == "light":
                    items_l.append((it, sub))
                elif kind2 == "shared":
                    shared_items.append(it)
                elif kind2 is None and re.search(r"\blight|luminair", it["desc"], re.I) \
                        and not FALSE_FRIENDS.match(it["code"]):
                    print(f"  NOTE unclassified lighting-worded item {it['code']} "
                          f"'{it['desc']}' in {prop}")

            row = {
                "id": prop, "call": c["call"], "tip": c["tip"],
                "county": c["county"], "div": c["div"], "desc": desc_src[:150],
                "let": let_disp, "low": low["name"], "lowAmt": low["amount"],
                "bidders": [[b["name"], b["amount"]] for b in c["bidders"]],
                "cls": "L2" if has_anchor else "None",
                "award": award, "reconciled": ok, "estimate": c["estimate"],
            }
            if is_ac:
                row["note"] = ("A+C bid — ranked on cost plus time consideration "
                               f"(${low['ac']:,.2f} for the low bidder); the cost figure is shown")
            all_rows.append(row)

            if has_anchor:
                light_rows.append(build_light_row(row, tab, cols, items_l, shared_items, let_disp))
            elif shared_items:
                # low bidder is census rank 1 -> find its tab column
                lowcol = [cc for cc, b in cols.items() if b is low][0]
                amt = sum(it["qty"] * it["prices"][str(lowcol)]
                          for it in shared_items if str(lowcol) in it["prices"])
                codes = sorted({it["code"].split("-")[0] if not it["code"].startswith("907") else it["code"][:7]
                                for it in shared_items})
                shared_rows.append({
                    "id": prop, "tip": c["tip"], "county": c["county"], "div": c["div"],
                    "let": let_disp, "low": low["name"], "amount": round(amt, 2),
                    "what": "Section " + " and ".join(codes) +
                            " junction boxes or service poles with no lighting-specific item beside them",
                })

        letting = {
            "id": lid, "date": let_disp, "iso": iso, "n": len(all_rows),
            "low": round(lowsum, 2), "bids": bids,
            "awarded": n_awarded, "rejected": n_rejected,
            "awardArtifact": bool(awards), "tc": tc, "ac": ac,
            "read": len(all_rows), "kind": kind,
            "awardDate": awards["actionDate"] if awards else None,
            "unmatched": 0,
        }
        nwd = sum(1 for c in census["calls"] if c["withdrawn"])
        if nwd:
            letting["withdrawn"] = nwd
        delta = {"letting": letting, "all": all_rows, "lighting": light_rows, "shared": shared_rows}
        op = os.path.join(out_dir, f"delta_{iso}.json")
        with open(op, "w") as f:
            json.dump(delta, f, indent=1)
        report[key] = dict(letting, reconciled=f"{recon_ok} of {recon_n}",
                           lighting=len(light_rows), shared=len(shared_rows))
        print(f"{iso}: n={letting['n']} bids={bids} low={lowsum:,.2f} "
              f"reconciled {recon_ok}/{recon_n} lighting={len(light_rows)} "
              f"shared={len(shared_rows)} awards={'yes' if awards else 'no'} "
              f"awarded={n_awarded} rejected={n_rejected}")

    # ---- Aug 25 awards update ------------------------------------------------
    aw = json.load(open(os.path.join(scratch, "awards_20260825.json")))
    upd = {}
    flips = []
    for e in aw["entries"]:
        p = e["proposals"][0]
        rec = rows_by_id.get(p)
        if e["section"] == "awarded":
            name = e["contractor"]
            if rec and abs(rec["lowAmt"] - e["amount"]) < 0.005:
                name = rec["low"]  # census name beats the award-list block
            upd[p] = {"status": "awarded", "contractor": name,
                      "amount": e["amount"], "actionDate": aw["actionDate"]}
            flips.append((p, rec["award"] if rec else "(not in record)", "awarded"))
        else:
            ent = {"status": "rejected", "contractor": None, "amount": None,
                   "actionDate": aw["actionDate"],
                   "note": "Listed under POSTPONED, WITHDRAWN, REJECTED &/OR TO BE "
                           "READVERTISED on the Aug 25, 2026 Bid Awards list"}
            if len(e["proposals"]) > 1:
                ent["memberProposals"] = e["proposals"]
            if rec is None:
                ent["note"] += " — no bids were read for this call on Aug 25, 2026"
            upd[p] = ent
            flips.append((p, rec["award"] if rec else "(no bids read Aug 25)", "rejected"))
    with open(os.path.join(out_dir, "awards_update.json"), "w") as f:
        json.dump({"letting": "L260825", "actionDate": aw["actionDate"],
                   "source": "MS/20260825/20260825BidAwards.pdf", "awards": upd}, f, indent=1)
    print("\nAug 25 award flips:")
    for p, old, new in flips:
        print(f"  {p}: {old} -> {new}")


def build_light_row(row, tab, cols, items_l, shared_items, let_disp):
    # Not exercised in this refresh (no lighting items found), kept for parity
    # with the MS_YEAR lighting[] shape.
    lowcol = [c for c in sorted(cols) if cols[c]["rank"] == 1][0]
    counted = items_l + [(it, "infrastructure") for it in shared_items]
    split = {"hardware": 0.0, "infrastructure": 0.0, "work": 0.0, "lump": 0.0}
    splitHw = {"luminaire": 0, "pole": 0, "assembly": 0.0, "control": 0}
    out_items, quantities = [], []
    lumN = poleN = 0.0
    sums = {c: 0.0 for c in cols}
    for it, sub in counted:
        for c in cols:
            if str(c) in it["prices"]:
                sums[c] += it["qty"] * it["prices"][str(c)]
        v = it["qty"] * it["prices"].get(str(lowcol), 0.0)
        split["hardware" if sub == "assembly" else sub] += v
        if sub == "assembly":
            splitHw["assembly"] += v
            lumN += it["qty"]
            poleN += it["qty"]
            quantities.append(f"{it['qty']:g} × {it['desc']}")
        sec = it["code"].rsplit("-", 1)[0] if it["code"].startswith("907") else it["code"].split("-")[0]
        out_items.append({"line": it["line"], "code": it["code"], "section": sec,
                          "desc": it["desc"], "qty": it["qty"], "unit": it["unit"],
                          "prices": {cols[c]["name"]: it["prices"][str(c)]
                                     for c in cols if str(c) in it["prices"]},
                          "sub": sub})
    l2 = round(sums[lowcol], 2)
    rng = [round(min(sums.values()), 2), round(max(sums.values()), 2)]
    return {
        "id": row["id"], "tip": row["tip"], "county": row["county"], "div": row["div"],
        "districtLabel": f"District {row['div']}", "let": let_disp,
        "low": row["low"], "lowAmt": row["lowAmt"], "bidders": len(cols),
        "l2": l2, "product": round(split["hardware"], 2),
        "split": {k: round(v, 2) for k, v in split.items()},
        "nItems": tab["nItems"], "rng": rng, "cls": "L2", "desc": tab["desc"],
        "share": round(l2 / row["lowAmt"], 3), "award": row["award"],
        "reconciled": row["reconciled"], "residual": 0.0,
        "quantities": quantities, "items": out_items,
        "splitHw": splitHw, "lumN": lumN, "poleN": poleN,
    }


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
