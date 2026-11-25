#!/usr/bin/env python3
"""Parse an ALDOT Tabulation of Bids PDF text dump (pdftotext -layout) into the shape al_emit_delta.py reads.
Usage: python3 -I al_tab_parse.py <tab.txt> <out.json>   (untrusted input; nothing from it is executed)
Each contract: Vendor Ranking page(s) (every bidder and printed total), then Tabulation pages, three bidders to a page set.
Gate: every bidder's item extensions must re-add to its printed total to the cent, else reconciled=false."""
import json, re, sys
MONEY = r"[\d,]+\.\d{2}"
def cents(s): return int(round(float(s.replace(",", "")) * 100))
def main(src, out):
    pages = open(src, encoding="utf-8").read().split("\f")
    C = {}
    for pg in pages:
        m = re.search(r"Call Order:\s*(\d+)\s+Contract ID:\s*(\d+)\s+County:\s*(.*?)\s*$", pg, re.M)
        if not m: continue
        cid = m.group(2)
        c = C.setdefault(cid, {"call": m.group(1), "cid": cid, "county_raw": m.group(3).strip(), "desc": "", "tip": "",
                               "ranking": [], "items": {}, "order": []})
        lines = pg.split("\n")
        if not c["desc"]:
            for i, ln in enumerate(lines):
                pm = re.search(r"Contract Description:\s+Project\(s\):\s*(.*?)\s*$", ln)
                if pm:
                    c["tip"] = pm.group(1).strip(); d = []
                    for l2 in lines[i + 1:]:
                        if not l2.strip() or re.match(r"\s+(Rank|Line No)", l2): break
                        d.append(l2.strip())
                    c["desc"] = " ".join(d); break
        if "Vendor Ranking" in pg:
            for rk, vid, name, amt in re.findall(r"^\s+(\d+)\s+(\S+)\s{2,}(\S.*?)\s{2,}\$(" + MONEY + r")\s*$", pg, re.M):
                c["ranking"].append({"rank": int(rk), "name": name.strip(), "total": cents(amt)})
            continue
        if "Tabulation of Bids" not in pg: continue
        hdr = next((l for l in lines if "Line No / Item ID" in l), None)
        if hdr is None: continue
        cols = [int(x) for x in re.findall(r"\((\d+)\)", hdr)]
        i = 0
        while i < len(lines):
            ln = lines[i]
            m2 = re.match(r"^\s*(\d{4})\s+(\S+)\s+(\(?[\d,]+\.\d{3}\)?)\s+(.*)$", ln)
            if not m2: i += 1; continue
            line, code, q, rest = m2.groups()
            nums = re.findall(MONEY, rest)
            lump = q.startswith("("); qty = float(q.strip("()").replace(",", ""))
            j = i + 1; dl = []
            while j < len(lines) and not re.match(r"^\s*\d{4}\s+\S+\s+\(?[\d,]+\.\d{3}\)?\s", lines[j]) and "SECTION:" not in lines[j] and "Alabama Department" not in lines[j]:
                if lines[j].strip(): dl.append(lines[j])
                j += 1
            unit = ""; desc = []
            for k, l2 in enumerate(dl):
                s = l2.strip()
                if k == 0:
                    um = re.match(r"^(.*?)\s{3,}(\S+)$", s)
                    if um: desc.append(um.group(1)); unit = um.group(2)
                    else: desc.append(s)
                elif not re.search(MONEY, s): desc.append(s)
            it = c["items"].setdefault(line, {"line": line, "code": code, "desc": " ".join(desc).strip(), "qty": qty, "unit": unit, "lump": lump, "p": {}})
            if line not in c["order"]: c["order"].append(line)
            if len(nums) == 2 * len(cols):
                for k, col in enumerate(cols): it["p"][col] = {"unit": cents(nums[2 * k]), "ext": cents(nums[2 * k + 1])}
            else:
                it.setdefault("bad", []).append((cols, nums))
            i = j
    outl = []
    for cid, c in sorted(C.items()):
        rk = sorted(c["ranking"], key=lambda r: r["rank"]); names = {r["rank"]: r["name"] for r in rk}
        items = []; sums = {r["rank"]: 0 for r in rk}; bad = []
        for line in c["order"]:
            it = c["items"][line]
            if it.get("bad") and len(it["p"]) < len(rk): bad.append(line)
            for col, p in it["p"].items():
                if col in sums: sums[col] += p["ext"]
            items.append({"line": it["line"], "code": it["code"], "desc": it["desc"], "qty": it["qty"], "unit": it["unit"], "lump": it["lump"],
                          "prices": {names[col]: p for col, p in it["p"].items() if col in names}})
        ok = bool(rk) and not bad and all(sums[r["rank"]] == r["total"] for r in rk)
        outl.append({"call": c["call"], "cid": cid, "county_raw": c["county_raw"], "desc": c["desc"], "tip": c["tip"],
                     "ranking": [{"name": r["name"], "total": r["total"]} for r in rk], "items": items, "nItems": len(items),
                     "reconciled": ok, "hardware": 0, "residuals": {names[k]: (sums[k] - r["total"]) / 100 for k, r in ((r["rank"], r) for r in rk)}, "badLines": bad})
        print(c["call"], cid, c["county_raw"][:18], "bidders", len(rk), "items", len(items), "OK" if ok else "NOT RECONCILED " + str({k: v for k, v in outl[-1]["residuals"].items() if v})[:150] + str(bad[:5]))
    json.dump(outl, open(out, "w"), indent=1)
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
