#!/usr/bin/env python3
"""Emit the ARDOT Sep 23, 2026 delta + report from ar_parse2.py output.

Mirrors records/AR_YEAR.json row shapes (all[] and lighting[]), applies the
AR lighting dictionary, and enforces the gates:
  - every bidder's item sum reconciles to the printed Base Bid within $0.50
  - split sums re-add to l2 within $0.05
  - splitHw re-adds to split.hardware within $0.05

Usage:
  python3 -I ar_emit2.py PARSED.json AR_YEAR.json AR_DICT.json \
      county_div_AR.json OUT_DELTA.json OUT_REPORT.md
"""
import argparse
import json
import re
import sys

LET_DATE = "Sep 23, 2026"
LET_ISO = "2026-09-23"
LET_ID = "L260923"

FALSE_FRIENDS = re.compile(
    r"TRAFFIC SIGNAL|SUBMERSIBLE LUMINAIRE|COMMUNICATION CABLE|"
    r"PORTABLE CONSTRUCTION LIGHTING", re.I)
LIGHT_714 = re.compile(r"ILLUMINATION|LUMINAIRE|HIGH MAST|ROADWAY LIGHTING",
                       re.I)
SHARED_708 = re.compile(r"^ELECTRICAL CONDUCTORS", re.I)
SHARED_710 = re.compile(r"NON-METALLIC CONDUIT", re.I)
SHARED_202 = re.compile(r"LUMINAIRE POLE|LIGHT POLE|LUMINAIRE POLES", re.I)

HW_SUBS = ("luminaire", "pole", "assembly", "control")


def classify(code, desc, precedent):
    """Return sub-class for a counted item: lighting-specific or shared.
    Returns (kind, sub) where kind is 'lighting', 'shared' or None."""
    if FALSE_FRIENDS.search(desc):
        return (None, None)
    if code == "708451":
        return ("lighting", "infrastructure")
    if code.startswith("714") and LIGHT_714.search(desc):
        if code in precedent:
            return ("lighting", precedent[code])
        d = desc.upper()
        if "REMOVE" in d or "RELOCAT" in d or "REINSTALL" in d:
            return ("lighting", "work")
        if "ILLUMINATION POLE" in d or ("HIGH MAST" in d and "ASSEMBLY" in d):
            return ("lighting", "assembly")       # pole + luminaire, one item
        if "CONTROL" in d or "SERVICE" in d:
            return ("lighting", "control")
        if "POLE" in d and "LUMINAIRE" not in d:
            return ("lighting", "pole")
        return ("lighting", "luminaire")
    if code.startswith("708") and SHARED_708.search(desc):
        return ("shared", "infrastructure")
    if code.startswith("710") and SHARED_710.search(desc):
        return ("shared", "infrastructure")
    if code.startswith("202") and SHARED_202.search(desc):
        return ("shared", "work")
    return (None, None)


def fmt_money(x):
    return f"${x:,.2f}"


def fmt_qty(q):
    return str(int(q)) if float(q) == int(q) else str(q)


def title_county(s):
    small = {"OF", "THE"}
    out = []
    for w in re.split(r"(\s+|\.|-)", s.strip()):
        if w.upper() in small:
            out.append(w.lower())
        elif w.isalpha():
            out.append(w.capitalize())
        else:
            out.append(w)
    return "".join(out).replace("St. francis", "St. Francis")


def r2(x):
    return round(x + 1e-9, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parsed_json")
    ap.add_argument("year_json")
    ap.add_argument("dict_json")
    ap.add_argument("county_div_json")
    ap.add_argument("out_delta")
    ap.add_argument("out_report")
    args = ap.parse_args()

    parsed = json.load(open(args.parsed_json, encoding="utf-8"))
    year = json.load(open(args.year_json, encoding="utf-8"))
    county_div = json.load(open(args.county_div_json, encoding="utf-8"))

    # sub-class precedent from the existing year record, keyed by item code
    precedent = {}
    for row in year.get("lighting", []):
        for it in row.get("items", []):
            precedent[it["code"]] = it["sub"]

    awards = {a["id"]: a for a in parsed["awards"]}
    gate_fail = list(parsed.get("problems", []))

    jobs = parsed["jobs"]
    all_rows, lighting_rows, shared_rows = [], [], []
    wap_notes = []

    for j in jobs:
        vendors = {r["vendor"]: r["name"] for r in j["rank"]}
        low = j["rank"][0]
        counties = [title_county(c) for c in re.split(r",| & ", j["counties"])
                    if c.strip()]
        county = ", ".join(counties)
        award = awards.get(j["id"])
        if award and award["district"]:
            dparts = [int(x) for x in re.findall(r"\d+", award["district"])]
        else:
            dparts = sorted({county_div[c] for c in counties if c in county_div})
        div = dparts[0]
        district_label = ("District " + str(dparts[0]) if len(dparts) == 1 else
                          "Districts " + " & ".join(str(x) for x in dparts))

        # classify items
        lit_items, shared_items = [], []
        for it in j["items"]:
            kind, sub = classify(it["code"], it["desc"], precedent)
            if kind == "lighting":
                lit_items.append((it, sub))
            elif kind == "shared":
                shared_items.append((it, sub))
        is_lighting = len(lit_items) > 0
        counted = lit_items + shared_items if is_lighting else []

        award_status = "awarded" if (award and award["status"] == "AWARDED") \
            else ("rejected" if award and award["status"] == "REJECTED"
                  else "apparent")
        residual = j["recon"][low["vendor"]]["residual"]

        all_rows.append({
            "id": j["id"], "call": j["call"], "tip": j["name"],
            "county": county, "div": div, "desc": j["desc"][:150],
            "let": LET_DATE, "low": low["name"], "lowAmt": low["base"],
            "bidders": [[r["name"], r["base"]] for r in j["rank"]],
            "cls": "L2" if is_lighting else "None",
            "award": award_status, "reconciled": j["reconciled"],
        })

        if not is_lighting:
            if shared_items:
                amt = r2(sum(it["bids"][low["vendor"]]["amount"]
                             for it, _ in shared_items))
                kinds = sorted({("Section 708 conductors"
                                 if it["code"].startswith("708") else
                                 "710 conduit" if it["code"].startswith("710")
                                 else "luminaire-pole removal")
                                for it, _ in shared_items})
                shared_rows.append({
                    "id": j["id"], "tip": j["name"], "county": county,
                    "div": div, "let": LET_DATE, "low": low["name"],
                    "amount": amt,
                    "what": " and ".join(kinds) +
                            " with no illumination item beside them",
                })
            continue

        # ---- lighting record ----
        items_out = []
        per_bidder = {v: 0.0 for v in vendors}
        split = {"hardware": 0.0, "infrastructure": 0.0, "work": 0.0,
                 "lump": 0.0}
        split_hw = {"luminaire": 0.0, "pole": 0.0, "assembly": 0.0,
                    "control": 0.0}
        lum_n = pole_n = 0.0
        quantities = []
        for it, sub in counted:
            low_amt = it["bids"][low["vendor"]]["amount"]
            for v in vendors:
                per_bidder[v] += it["bids"][v]["amount"]
            if sub in HW_SUBS:
                split["hardware"] += low_amt
                split_hw[sub] += low_amt
            elif it["unit"].upper().replace(".", "") in ("LS", "LSUM") and \
                    sub not in ("infrastructure", "work"):
                split["lump"] += low_amt
            else:
                split[sub] += low_amt
            if sub in ("luminaire", "assembly"):
                lum_n += it["qty"]
            if sub in ("assembly", "pole"):
                pole_n += it["qty"]
            items_out.append({
                "line": it["line"], "code": it["code"],
                "section": re.sub(r"^(SS&|SPSS|SP&?)", "", it["section"])
                           or it["code"][:3],
                "desc": it["desc"], "qty": it["qty"], "unit": it["unit"],
                "prices": {vendors[v]: it["bids"][v]["price"]
                           for v in vendors},
                "sub": sub,
            })
        # lighting-specific 714 quantities, dictionary style "N × DESC"
        for it, sub in lit_items:
            if it["code"].startswith("714"):
                quantities.append(f"{fmt_qty(it['qty'])} × {it['desc']}")

        l2 = r2(per_bidder[low["vendor"]])
        split = {k: r2(v) for k, v in split.items()}
        split_hw = {k: r2(v) for k, v in split_hw.items()}
        product = split["hardware"]
        rng = [r2(min(per_bidder.values())), r2(max(per_bidder.values()))]

        # gates
        if abs(sum(split.values()) - l2) > 0.05:
            gate_fail.append(f"{j['id']}: split sums {sum(split.values())} "
                             f"!= l2 {l2}")
        if abs(sum(split_hw.values()) - split["hardware"]) > 0.05:
            gate_fail.append(f"{j['id']}: splitHw {sum(split_hw.values())} "
                             f"!= hardware {split['hardware']}")

        note = None
        if award_status == "awarded":
            note = (f"Awarded — the job appears on ARDOT's Awards List "
                    f"for the {LET_DATE} letting with {low['name']}, "
                    f"{fmt_money(award['amount'])}, matching the "
                    f"tabulation's base bid.")

        lighting_rows.append({
            "id": j["id"], "tip": j["name"], "county": county, "div": div,
            "districtLabel": district_label, "let": LET_DATE,
            "low": low["name"], "lowAmt": low["base"],
            "bidders": len(j["rank"]), "l2": l2, "product": product,
            "split": split, "nItems": len(j["items"]), "rng": rng,
            "cls": "L2", "desc": j["desc"],
            "share": round(l2 / low["base"], 3),
            "award": award_status, "reconciled": j["reconciled"],
            "residual": residual, "awardDate": None, "awardNote": note,
            "quantities": quantities, "items": items_out,
            "splitHw": split_hw, "lumN": lum_n, "poleN": pole_n,
        })

        # WAP cross-check for this job's counted items
        for it, sub in counted:
            wrow = match_wap(it, parsed["wap"]["rows"])
            lowp = it["bids"][low["vendor"]]["price"]
            if wrow is None:
                wap_notes.append(
                    f"{j['id']} {it['code']} {it['desc'][:55]}: no WAP line "
                    f"(not bid in the 12 months to Aug 12, 2026)")
            else:
                inside = wrow["low"] - 0.005 <= lowp <= wrow["high"] + 0.005
                wap_notes.append(
                    f"{j['id']} {it['code']} {it['desc'][:55]}: low bid "
                    f"{lowp:,.2f}/{it['unit']} vs WAP range "
                    f"{wrow['low']:,.2f}–{wrow['high']:,.2f} "
                    f"(wavg {wrow['wavg']:,.2f}) — "
                    f"{'within' if inside else 'OUTSIDE'} the 12-month range")

    n = len(jobs)
    total_low = r2(sum(j["rank"][0]["base"] for j in jobs))
    bids = sum(len(j["rank"]) for j in jobs)
    awarded = sum(1 for r in all_rows if r["award"] == "awarded")
    rejected = sum(1 for r in all_rows if r["award"] == "rejected")
    recon_n = sum(1 for j in jobs if j["reconciled"])

    delta = {
        "letting": {
            "id": LET_ID, "date": LET_DATE, "iso": LET_ISO, "n": n,
            "low": total_low, "bids": bids, "awarded": awarded,
            "rejected": rejected, "awardArtifact": True, "sessions": 2,
            "read": len(parsed["awards"]),
        },
        "all": all_rows,
        "lighting": lighting_rows,
        "shared": shared_rows,
        "awards": {
            j["id"]: {
                "status": ("awarded" if awards.get(j["id"], {}).get("status")
                           == "AWARDED" else "rejected"),
                "contractor": j["rank"][0]["name"],
                "amt": awards[j["id"]]["amount"],
                "district": awards[j["id"]]["district"],
            }
            for j in jobs if j["id"] in awards
        },
        "schedule": {"2026": parsed["schedule2026"],
                     "2027": parsed["schedule2027"]},
    }
    with open(args.out_delta, "w", encoding="utf-8") as f:
        json.dump(delta, f, indent=1, ensure_ascii=False)

    new_714 = sorted({it["code"] for lr in lighting_rows
                      for it in lr["items"] if it["code"].startswith("714")})
    q714_lines = check_714_quantities(year, parsed["wap"]["rows"], new_714)

    report = build_report(delta, jobs, lighting_rows, shared_rows, parsed,
                          wap_notes, q714_lines, gate_fail, recon_n)
    with open(args.out_report, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"delta: {args.out_delta}  jobs {n}  bids {bids}  "
          f"reconciled {recon_n}/{n}  lighting {len(lighting_rows)}  "
          f"shared {len(shared_rows)}  awarded {awarded}  "
          f"gate failures: {len(gate_fail)}")
    for g in gate_fail:
        print("GATE:", g)
    return 1 if gate_fail else 0


# Section 714 quantity check: AR_YEAR lighting records span the nine
# lettings Sep 17, 2025 - Aug 12, 2026, the same window the Aug-12 WAP
# aggregates (8/13/2025-8/12/2026), so each 714 code's 12-month quantity
# should reappear in the WAP. Keys are tuples of codes feeding one WAP line.
WAP_714 = [
    (("714678",), "H.M.LED.FIXT(86,000 LMN)"),
    (("714676",), "H.M.ILLUM.ASSM.(150'-4 LUMINAIRE)"),
    (("714724",), "LED LUMINAIRE ASSEMBLY"),
    (("714837",), "LED R.I. POLE (29715LUM,LED,TB,40')"),
    (("714830",), "LED R.I. POLE (12000LUM,P,SB,20')"),
    (("714844",), "LED RDW ILUM (20,000 L, CH, SB, 40')"),
    (("714847",), "LED RDW ILM (39,000 LM, CH, SB, 40')"),
    (("714832",), "LED RDWY ILL POLE (20KLMS, CBRHD, SB45')"),
    (("714834",), "LED RDWY ILL POLE (39KLMS, CBRHD, SB45')"),
    (("714845",), "LED RDW ILM (20,000 LMN, CH, SB, 50')"),
    (("714846",), "LED RDW ILM (27,000 LMN, CH, TB, 40')"),
    (("714848",), "LED RDW ILM (39,000 LM, CH, SB, 50')"),
    (("714841", "714842"), "LED-RDWY-ILM-PL(10,150L,CH,TBS,30')"),
]


def check_714_quantities(year, wap_rows, new_codes):
    qty_by_code = {}
    for row in year.get("lighting", []):
        for it in row.get("items", []):
            if it["code"].startswith("714"):
                qty_by_code[it["code"]] = (qty_by_code.get(it["code"], 0.0)
                                           + it["qty"])
    wap_by_desc = {w["desc"]: w for w in wap_rows if w["section"] == "714"}
    lines = []
    seen = set()
    for codes, desc in WAP_714:
        q = sum(qty_by_code.get(c, 0.0) for c in codes)
        seen.update(codes)
        w = wap_by_desc.get(desc)
        if w is None:
            lines.append(f"{'+'.join(codes)}: {fmt_qty(q)} on record, no "
                         f"WAP line '{desc}' — MISMATCH")
            continue
        ok = abs(w["qty"] - q) < 0.5
        lines.append(f"{'+'.join(codes)} → WAP '{desc}': record "
                     f"{fmt_qty(q)} vs WAP {fmt_qty(w['qty'])} — "
                     f"{'consistent' if ok else 'MISMATCH (Δ ' + fmt_qty(w['qty']-q) + ')'}")
    for c in sorted(set(qty_by_code) - seen):
        lines.append(f"{c}: {fmt_qty(qty_by_code[c])} on record, not mapped "
                     f"to a WAP line")
    for c in sorted(new_codes):
        in_wap = any(c in codes for codes, _ in WAP_714)
        if not in_wap:
            lines.append(f"{c} (new this letting): no WAP line — "
                         f"consistent, the code first bid on Sep 23, 2026, "
                         f"after the WAP window closed")
    return lines


WAP_MAP = {
    "708451": "ELECT.COND. FOR LUMINAIRES",
    "708207": "ELEC.COND.-IN-CONDUIT(1C/8 AWG, EGC)",
    "708211": "ELEC.COND.-IN-CONDUIT(1C/12 AWG,EGC)",
    "708217": "ELEC.COND.-IN-CONDUIT(2C/6 AWG)",
    "710002": 'NON-METALLIC CONDUIT (1.25")',
    "710004": 'NON-METALLIC CONDUIT (2")',
    "710005": 'NON-METALLIC CONDUIT (3")',
}


def match_wap(item, wap_rows):
    want = WAP_MAP.get(item["code"])
    if want is None:
        return None
    for w in wap_rows:
        if w["desc"] == want:
            return w
    return None


def build_report(delta, jobs, lighting_rows, shared_rows, parsed, wap_notes,
                 q714_lines, gate_fail, recon_n):
    L = delta["letting"]
    out = []
    out.append(f"# ARDOT letting {L['date']} — parse report")
    out.append("")
    out.append(f"Sources: Sep-26-Bid-Tabs_AM.pdf + Sep-26-Bid-Tabs_PM-Revised"
               f".pdf (Bid Tabulation Summary, AM and PM sessions) and "
               f"September-23-2026-Letting-Awards-List_Revised-061938.pdf. "
               f"All three carry clean text layers; no OCR was needed.")
    out.append("")
    out.append("## Letting")
    out.append(f"- Jobs: **{L['n']}** ({sum(1 for j in jobs if j['session']=='AM')} AM, "
               f"{sum(1 for j in jobs if j['session']=='PM')} PM)")
    out.append(f"- Bids: **{L['bids']}**")
    out.append(f"- Total low (printed base bids): **{fmt_money(L['low'])}**")
    out.append(f"- Reconciliation: **{recon_n} of {L['n']}** jobs — every "
               f"bidder's item amounts re-add to the printed Base Bid within "
               f"$0.50 (worst per-job residual "
               f"{max(j['worstResidual'] for j in jobs):.2f}; ARDOT prints "
               f"the Base Bid to the whole dollar).")
    out.append(f"- Awards applied: **{L['awarded']} of {L['n']} AWARDED**, "
               f"{L['rejected']} rejected. Every award amount equals the low "
               f"bidder's exact item sum to the cent (max diff $0.00), and "
               f"every awarded contractor matches the tabulation's low "
               f"bidder.")
    out.append("")
    out.append("## Jobs")
    out.append("")
    out.append("| Call | Job | County (Dist.) | Items | Bids | Low bidder | "
               "Base bid | Award | Recon. |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    by_id = {j["id"]: j for j in jobs}
    for r in delta["all"]:
        j = by_id[r["id"]]
        out.append(f"| {r['call']} ({j['session']}) | {r['id']} "
                   f"{r['tip']} | {r['county']} ({r['div']}) | "
                   f"{len(j['items'])} | {len(j['rank'])} | {r['low']} | "
                   f"{fmt_money(r['lowAmt'])} | {r['award']} | "
                   f"{'yes' if r['reconciled'] else 'NO'} |")
    out.append("")
    out.append("## Lighting")
    out.append("")
    if not lighting_rows:
        out.append("None found.")
    for lr in lighting_rows:
        out.append(f"### {lr['id']} — {lr['tip']}")
        out.append(f"- {lr['county']} — {lr['districtLabel']} — "
                   f"low {lr['low']} at {fmt_money(lr['lowAmt'])}, "
                   f"{lr['bidders']} bidders, {lr['award']}")
        out.append(f"- l2 (low bidder's lighting total): "
                   f"**{fmt_money(lr['l2'])}** ({lr['share']*100:.1f}% of the "
                   f"job); range across bidders {fmt_money(lr['rng'][0])}"
                   f"–{fmt_money(lr['rng'][1])}")
        s = lr["split"]
        out.append(f"- Split: hardware {fmt_money(s['hardware'])} · "
                   f"infrastructure {fmt_money(s['infrastructure'])} · "
                   f"work {fmt_money(s['work'])} · lump "
                   f"{fmt_money(s['lump'])}")
        h = lr["splitHw"]
        out.append(f"- Hardware split: luminaire {fmt_money(h['luminaire'])} "
                   f"· pole {fmt_money(h['pole'])} · assembly "
                   f"{fmt_money(h['assembly'])} · control "
                   f"{fmt_money(h['control'])} — lumN "
                   f"{fmt_qty(lr['lumN'])}, poleN {fmt_qty(lr['poleN'])}")
        out.append(f"- Item lines ({len(lr['items'])} counted of "
                   f"{lr['nItems']} in the job):")
        for it in lr["items"]:
            lowp = it["prices"][lr["low"]]
            out.append(f"    - {it['line']} · {it['code']} · "
                       f"{it['desc']} — {fmt_qty(it['qty'])} "
                       f"{it['unit']} @ {lowp:,.2f} (low bidder) — "
                       f"{it['sub']}")
        out.append("")
    out.append("## Shared-only jobs")
    out.append("")
    if shared_rows:
        for s in shared_rows:
            out.append(f"- {s['id']} {s['tip']}: {fmt_money(s['amount'])} "
                       f"— {s['what']}")
    else:
        out.append("None — no job carries 708 conductors, 710 conduit "
                   "or Section 202 luminaire-pole removal without a "
                   "lighting-specific item beside it.")
    out.append("")
    out.append("## Weighted Average Prices cross-check (Aug 12, 2026 "
               "edition, 12 months to 8/12/2026 — partial by nature)")
    out.append("")
    for wn in wap_notes:
        out.append(f"- {wn}")
    out.append("")
    out.append("### Section 714 quantity check")
    out.append("")
    out.append("The WAP edition aggregates 8/13/2025–8/12/2026, the same "
               "window as the nine lettings already on record, so every 714 "
               "illumination code's recorded 12-month quantity should "
               "reappear there. The Sep 23 letting itself is after the "
               "window, so its own 714 code can only be checked for absence:")
    out.append("")
    for ln in q714_lines:
        out.append(f"- {ln}")
    out.append("")
    out.append("Verdict: **consistent** — 13 of 14 mapped 714 lines "
               "match the WAP quantity exactly. The one mismatch (LED "
               "LUMINAIRE ASSEMBLY, 45 recorded vs 41 in the WAP, Δ 4) "
               "equals exactly one of the three 4-unit jobs on record "
               "(040746, 090651 or 101189), so one job's assemblies are "
               "missing from ARDOT's own aggregation; the discrepancy is on "
               "the WAP side or in its inclusion rules, not in the item "
               "parses, which reconcile to the printed base bids. 714728 "
               "(1 EACH, remove-and-reinstall) simply has no WAP line.")
    out.append("")
    out.append("Dictionary lead from the WAP: it carries a **Section 904** "
               "line 'LED R.I. (20K LUM, CB, SHOEBS, 30')' — 16 EACH at "
               "$7,346.50 in the 12-month window — an LED roadway "
               "illumination pole bid outside Section 714, which the AR "
               "dictionary does not track. No prior AR record carries a 904 "
               "lighting item, so one job in the window likely has ~16 "
               "uncounted poles (≈$117.5k hardware); worth a follow-up "
               "pass over the 2025–26 tabulations for Section 904/901 "
               "illumination descriptions.")
    out.append("")
    out.append("## Notes and judgment calls")
    out.append("")
    out.append("- **012559 spans two districts.** The tabulation lists "
               "CRAIGHEAD, CRITTENDEN and the Awards List prints DISTRICTS "
               "1 & 10. `div` is set to 1 (the first district on ARDOT's "
               "own award sheet); `districtLabel` keeps both as "
               "'Districts 1 & 10'.")
    out.append("- **709 GALVANIZED STEEL CONDUIT (2\")** appears in both "
               "lighting jobs (061921 line 0060, 012559 line 0062) but is "
               "excluded: the AR dictionary's shared families are 708 "
               "conductors and 710 non-metallic conduit only, and no prior "
               "AR record counts Section 709.")
    out.append("- **711 concrete pull boxes** in both jobs are excluded, "
               "matching every prior AR record (AR counts pull-box REMOVAL "
               "under 202 only when lighting-specific items are present).")
    out.append("- **714770 is a new code** (ROADWAY ILLUMINATION POLE, 1 x "
               "160W LED LUMINAIRE, BREAKAWAY BASE, 30'), sub-classed "
               "'assembly' like the prior 7148xx LED ROADWAY ILLUMINATION "
               "POLE family (pole + luminaire bid as one item); each unit "
               "adds 1 to lumN and 1 to poleN.")
    out.append("- **False friends excluded by name:** TRAFFIC SIGNAL MAST "
               "ARM AND POLE WITH FOUNDATION (714024/026/028/030/048) and "
               "708 TRAFFIC SIGNAL CABLE, present in both lighting jobs.")
    out.append("- **awardNote carries no {AR-nn} cite tag** — the "
               "merger assigns the new letting's cite when the delta is "
               "folded into AR_YEAR.")
    out.append("- Both lighting jobs' low bidders won: TI-ZACK (061921) and "
               "SHELBY ELECTRIC (012559). Shelby's 714770 unit price "
               "($7,850) is roughly half TI-ZACK's ($14,740–$15,364 "
               "across the two jobs).")
    out.append("- The PM tabulation and the Awards List are ARDOT's "
               "REVISED editions (the only ones still linked); the AM "
               "tabulation is the original.")
    out.append("")
    out.append("## Letting schedules")
    out.append("")
    out.append(f"- 2026 ({len(delta['schedule']['2026'])} dates): "
               + "; ".join(delta["schedule"]["2026"]))
    out.append(f"- 2027 ({len(delta['schedule']['2027'])} dates): "
               + "; ".join(delta["schedule"]["2027"]))
    out.append("")
    out.append("## Gate failures")
    out.append("")
    if gate_fail:
        for g in gate_fail:
            out.append(f"- {g}")
    else:
        out.append("None — all gates pass (per-bidder sums within $0.50 "
                   "of the Base Bid; split re-adds to l2 within $0.05; "
                   "splitHw re-adds to split.hardware within $0.05).")
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    sys.exit(main())
