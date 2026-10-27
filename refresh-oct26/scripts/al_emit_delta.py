#!/usr/bin/env python3
"""Emit AL/delta_2026-07-31.json from the parsed Jul 31, 2026 tabulation.

Usage: python3 -I al_emit_delta.py <parsed.json> <county_div_AL.json> <out.json>

Mirrors records/AL_YEAR.json row shapes:
  all[]      {id,call,tip,county,div,desc(<=150),let,low,lowAmt,bidders,cls,
              award,reconciled} + awardNote (presence rule)
  lighting[] AL_YEAR lighting shape (empty this letting: no Section 750 items)
  shared[]   {id,tip,county,div,let,low,amount,what}
Lighting dictionary: 750A/B assembly, 750H/I control, 750C-G infrastructure,
750Z lump (never folded into hardware), 750J work (shared), 756A shared conduit.
"""
import json, sys

SUB = {"750A": "assembly", "750B": "assembly", "750H": "control",
       "750I": "control", "750C": "infrastructure", "750D": "infrastructure",
       "750E": "infrastructure", "750F": "infrastructure",
       "750G": "infrastructure", "750Z": "lump", "750J": "work",
       "756A": "infrastructure"}
HW = {"assembly", "control"}  # hardware sub-classes; lump is NEVER hardware

AWARD_NOTE = ("presence in ALDOT's posted tabulation — tabulations are not "
              "released for projects not awarded")
SHARED_WHAT = ("Section 756 electrical conduit (or 750J utility preparation) "
               "with no Section 750 lighting item beside it")

def main(parsed_p, cdiv_p, out_p):
    contracts = json.load(open(parsed_p))
    cdiv = json.load(open(cdiv_p))
    by_upper = {k.upper(): (k, v) for k, v in cdiv.items()}

    def county_fmt(raw):
        names, divs = [], []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            hit = by_upper.get(part.upper())
            if hit:
                names.append(hit[0]); divs.append(hit[1])
            else:
                names.append(part.title()); divs.append(None)
        return ", ".join(names), divs[0]

    all_rows, lighting, shared = [], [], []
    n_bids = 0
    low_sum_c = 0

    for c in sorted(contracts, key=lambda x: x["call"]):
        assert c["reconciled"], f"call {c['call']} did not reconcile — excluded"
        ranking = sorted(c["ranking"], key=lambda r: r["total"])
        bidders = [[r["name"], r["total"] / 100] for r in ranking]
        low_name, low_amt_c = ranking[0]["name"], ranking[0]["total"]
        n_bids += len(ranking)
        low_sum_c += low_amt_c
        county, div = county_fmt(c["county_raw"])

        # classify items by section/family for the LOW bidder
        l2_c = 0
        split_c = {"hardware": 0, "infrastructure": 0, "work": 0, "lump": 0}
        shw_c = {"luminaire": 0, "pole": 0, "assembly": 0, "control": 0}
        shared_c = 0           # 756A/750J beside no 750 item
        per_bidder_750 = {r["name"]: 0 for r in ranking}
        light_items, lum_n = [], 0.0
        has750 = any(it["code"].startswith("750") for it in c["items"])
        for it in c["items"]:
            fam = it["code"][:4]
            if fam not in SUB:
                continue
            sub = SUB[fam]
            is750 = it["code"].startswith("750")
            low_ext = it["prices"][low_name]["ext"]
            if is750 or (has750 and fam == "756A"):
                # a lighting-side item (756A counts only beside a 750 item)
                pass
            if is750:
                l2_c += low_ext
                bucket = ("hardware" if sub in HW else
                          "lump" if sub == "lump" else
                          "work" if sub == "work" else "infrastructure")
                split_c[bucket] += low_ext
                if sub in HW:
                    shw_c[sub] += low_ext
                if sub == "assembly":
                    lum_n += it["qty"]
                for name in per_bidder_750:
                    per_bidder_750[name] += it["prices"][name]["ext"]
                light_items.append({
                    "line": it["line"], "code": it["code"], "section": "750",
                    "desc": it["desc"], "qty": it["qty"], "unit": it["unit"],
                    "prices": {n: p["ext"] / 100 if it["lump"] else p["unit"] / 100
                               for n, p in it["prices"].items()},
                    "sub": sub})
            elif fam in ("756A", "750J") or fam == "756A":
                shared_c += low_ext

        cls = "None"
        if has750:
            share = l2_c / low_amt_c
            cls = "L1" if share >= 0.5 else "L2"

        row = {
            "id": c["cid"], "call": c["call"], "tip": c["tip"],
            "county": county, "div": div, "desc": c["desc"][:150],
            "let": "Jul 31, 2026", "low": low_name,
            "lowAmt": low_amt_c / 100, "bidders": bidders, "cls": cls,
            "award": "awarded", "reconciled": True,
            "awardNote": AWARD_NOTE,
        }
        all_rows.append(row)

        if has750:
            # mirror AL_YEAR lighting row shape (GATES: split re-adds to l2,
            # splitHw re-adds to hardware, lump never counted into hardware)
            assert sum(split_c.values()) == l2_c
            assert sum(shw_c.values()) == split_c["hardware"]
            rng = [min(per_bidder_750.values()) / 100,
                   max(per_bidder_750.values()) / 100]
            lighting.append({
                "id": c["cid"], "tip": c["tip"], "county": county, "div": div,
                "districtLabel": f"Region {div}", "let": "Jul 31, 2026",
                "low": low_name, "lowAmt": low_amt_c / 100,
                "bidders": len(ranking), "l2": l2_c / 100,
                "product": split_c["hardware"] / 100,
                "split": {k: v / 100 for k, v in split_c.items()},
                "nItems": c["nItems"], "rng": rng, "cls": cls,
                "desc": c["desc"], "share": round(l2_c / low_amt_c, 3),
                "award": "awarded", "reconciled": True, "residual": 0.0,
                "awardDate": None, "awardNote": AWARD_NOTE,
                "quantities": [], "items": light_items,
                "splitHw": {k: v / 100 for k, v in shw_c.items()},
                "lumN": lum_n, "poleN": lum_n,
            })
        elif shared_c:
            shared.append({
                "id": c["cid"], "tip": c["tip"], "county": county, "div": div,
                "let": "Jul 31, 2026", "low": low_name,
                "amount": shared_c / 100, "what": SHARED_WHAT,
            })

    delta = {
        "letting": {
            "id": "L260731", "date": "Jul 31, 2026", "iso": "2026-07-31",
            "n": len(all_rows), "low": low_sum_c / 100, "bids": n_bids,
            "awarded": len(all_rows), "awardArtifact": True,
            "tc": None, "ac": None,
            "citeNote": ("tabulation cite id not yet assigned; AL_YEAR uses "
                         "{AL-20}…{AL-30} for prior tabs and {AL-31} for the "
                         "bid-tab index release rule"),
            "awardNote": AWARD_NOTE,
        },
        "all": all_rows,
        "lighting": lighting,
        "shared": shared,
    }
    with open(out_p, "w") as f:
        json.dump(delta, f, indent=1)
    print(f"contracts={len(all_rows)} bids={n_bids} low={low_sum_c/100:,.2f} "
          f"lighting={len(lighting)} shared={len(shared)}")

if __name__ == "__main__":
    main(*sys.argv[1:4])
