#!/usr/bin/env python3
"""ARDOT Sep 23, 2026 letting parser.

Parses the AM + PM Bid Tabulation Summary PDFs, the Awards List PDF, the
2026/2027 letting-schedule PDFs and the Aug-12-2026 Weighted Average Prices
PDF into one intermediate JSON. All inputs are untrusted downloads; run with
python3 -I and pass every path as an argument.

Usage:
  python3 -I ar_parse2.py AM.pdf PM.pdf AWARDS.pdf SCHED26.pdf SCHED27.pdf \
      WAP.pdf OUT.json [--workdir DIR]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

MONEY = r"[\d,]+\.\d{2}"


def pdftotext(pdf_path, workdir):
    out = os.path.join(workdir, os.path.basename(pdf_path) + ".txt")
    subprocess.run(["pdftotext", "-layout", pdf_path, out], check=True)
    with open(out, encoding="utf-8") as f:
        return f.read()


def to_f(s):
    return float(s.replace(",", "").replace("$", ""))


RE_HEADER = re.compile(
    r"^Call Order:\s+(\d+)\s+Contract ID:\s+(\S+)\s+Counties:\s+(.+?)\s*$")
RE_JOBNAME = re.compile(r"Job Name:\s+(.+?)\s*$")
RE_LETDATE = re.compile(r"^Letting Date:\s+(\S+)\s+-\s+(.+?)\s{2,}")
RE_RANK = re.compile(
    r"^\s{0,4}(\d{1,2})\s+([A-Z0-9]{4,8})\s+(.+?)\s+\$([\d,]+)\s+[\d.]+%\s*$")
RE_ITEM = re.compile(
    r"^(\d{4}) - (\S+) - (\S+) - (.+) - ([\d,]+\.\d{3}) (\S+)\s*$")
RE_BID = re.compile(
    r"^\s+([A-Z0-9]{4,8})\s+(.+?)\s+(" + MONEY + r")\s+(" + MONEY + r")\s*$")


def parse_tab(text, session):
    """Parse one Bid Tabulation Summary into a list of job dicts."""
    jobs = {}
    order = []
    cur = None          # current job dict
    cur_item = None     # current item dict
    in_desc = False
    lines = text.split("\n")
    for ln in lines:
        m = RE_HEADER.match(ln)
        if m:
            call, cid, counties = m.group(1), m.group(2), m.group(3).strip()
            key = (call, cid)
            if key not in jobs:
                jobs[key] = {
                    "session": session, "call": call, "id": cid,
                    "counties": counties, "name": None, "letDate": None,
                    "desc": [], "rank": [], "items": [],
                }
                order.append(key)
            cur = jobs[key]
            cur_item = None
            in_desc = False
            continue
        if cur is None:
            continue
        m = RE_JOBNAME.search(ln)
        if m and cur["name"] is None:
            cur["name"] = m.group(1).strip()
        m = RE_LETDATE.match(ln)
        if m and cur["letDate"] is None:
            cur["letDate"] = m.group(1)
        if ln.startswith("Contract Description:"):
            in_desc = True
            cur["desc"].append(ln.split("Contract Description:", 1)[1].strip())
            continue
        if in_desc:
            if ln.strip() == "" or ln.lstrip().startswith(("Rank ", "Percent")):
                in_desc = False
            else:
                cur["desc"].append(ln.strip())
            continue
        m = RE_ITEM.match(ln)
        if m:
            cur_item = {
                "line": m.group(1), "code": m.group(2), "section": m.group(3),
                "desc": m.group(4).strip(), "qty": to_f(m.group(5)),
                "unit": m.group(6), "bids": {},
            }
            cur["items"].append(cur_item)
            continue
        m = RE_RANK.match(ln)
        if m and not cur["items"]:
            # rank table appears before any item and only on the first page
            vend = m.group(2)
            if vend not in [r["vendor"] for r in cur["rank"]]:
                cur["rank"].append({
                    "rank": int(m.group(1)), "vendor": vend,
                    "name": m.group(3).strip(), "base": to_f(m.group(4)),
                })
            continue
        m = RE_BID.match(ln)
        if m and cur_item is not None:
            vend = m.group(1)
            known = {r["vendor"] for r in cur["rank"]}
            if vend in known:
                cur_item["bids"][vend] = {
                    "price": to_f(m.group(3)), "amount": to_f(m.group(4)),
                }
            continue
    out = []
    for key in order:
        j = jobs[key]
        j["desc"] = " ".join(d for d in j["desc"] if d)
        out.append(j)
    return out


def validate_jobs(jobs):
    """Check completeness and per-bidder reconciliation against the Base Bid."""
    problems = []
    for j in jobs:
        vendors = [r["vendor"] for r in j["rank"]]
        j["recon"] = {}
        for it in j["items"]:
            missing = [v for v in vendors if v not in it["bids"]]
            if missing:
                problems.append(
                    f"{j['id']} item {it['line']} missing bids: {missing}")
            for v, b in it["bids"].items():
                calc = round(it["qty"] * b["price"], 2)
                if abs(calc - b["amount"]) > 0.015:
                    problems.append(
                        f"{j['id']} item {it['line']} {v}: qty*price "
                        f"{calc} != printed {b['amount']}")
        worst = 0.0
        for r in j["rank"]:
            s = round(sum(it["bids"][r["vendor"]]["amount"]
                          for it in j["items"] if r["vendor"] in it["bids"]), 2)
            resid = round(abs(s - r["base"]), 2)
            j["recon"][r["vendor"]] = {"sum": s, "base": r["base"],
                                       "residual": resid,
                                       "ok": resid <= 0.50}
            worst = max(worst, resid)
            if resid > 0.50:
                problems.append(
                    f"{j['id']} {r['vendor']}: sum {s} vs base {r['base']} "
                    f"(residual {resid})")
        j["reconciled"] = all(v["ok"] for v in j["recon"].values())
        j["worstResidual"] = worst
    return problems


def norm_name(s):
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def parse_awards(text):
    """Awards List: blocks starting with the job number at column 0."""
    awards = []
    cur = None
    for ln in text.split("\n"):
        if re.match(r"^\s*TOTAL AMOUNT", ln):
            cur = None
            continue
        m = re.match(r"^([A-Z0-9]{6})\s+(.*\S)\s+\$(" + MONEY + r")\s*$", ln)
        if m and not ln.lstrip().startswith("JOB"):
            cur = {"id": m.group(1), "firstLine": m.group(2).strip(),
                   "amount": to_f(m.group(3)), "block": [ln.strip()],
                   "district": None, "status": "AWARDED"}
            # an explicit status code (01-08) may sit right after the job no.
            sm = re.match(r"^(\d{2})\s+(.*)$", cur["firstLine"])
            if sm and len(sm.group(1)) == 2 and m.group(1) != sm.group(1):
                cur["statusCode"] = sm.group(1)
            awards.append(cur)
            continue
        if re.search(r"ALL BIDS REJECTED", ln, re.I):
            jm = re.match(r"^([A-Z0-9]{6})\s", ln)
            if jm:
                awards.append({"id": jm.group(1), "firstLine": ln.strip(),
                               "amount": None, "block": [ln.strip()],
                               "district": None, "status": "REJECTED"})
                cur = awards[-1]
            elif cur:
                cur["status"] = "REJECTED"
            continue
        if cur is not None and ln.strip():
            cur["block"].append(ln.strip())
            dm = re.match(r"^DISTRICTS?\s+(.+?)(?:\s{2,}|$)", ln.strip())
            if dm and cur["district"] is None:
                cur["district"] = dm.group(1).strip()
    return awards


def parse_schedule(text):
    dates = re.findall(
        r"^\s*((?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},\s+\d{4})\s*$",
        text, re.M)
    return [re.sub(r"\s+", " ", d) for d in dates]


def parse_wap(text):
    """Keep the lighting-relevant Weighted Average Price lines."""
    keep = re.compile(
        r"ILLUM|LUMINAIRE|HIGH MAST|H\.M\.|NON-METALLIC CONDUIT|"
        r"ELEC\.?T?\.? ?COND|LED R|LED-R|RDWY|RDW ", re.I)
    rows = []
    for ln in text.split("\n"):
        m = re.match(
            r"^(\d{3})\s+(.+?)\s+([A-Z.]+)\s+([\d,]+\.\d{2})\s+"
            r"([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s*\*?\s*$",
            ln)
        if m and keep.search(m.group(2)):
            rows.append({"section": m.group(1), "desc": m.group(2).strip(),
                         "unit": m.group(3), "qty": to_f(m.group(4)),
                         "high": to_f(m.group(5)), "low": to_f(m.group(6)),
                         "wavg": to_f(m.group(7))})
    window = None
    wm = re.search(r"FROM\s+([\d/]+)\s+TO\s+([\d/]+)", text)
    if wm:
        window = [wm.group(1), wm.group(2)]
    return {"window": window, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("am_pdf")
    ap.add_argument("pm_pdf")
    ap.add_argument("awards_pdf")
    ap.add_argument("sched26_pdf")
    ap.add_argument("sched27_pdf")
    ap.add_argument("wap_pdf")
    ap.add_argument("out_json")
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    workdir = args.workdir or tempfile.mkdtemp(prefix="ar_parse2_")
    os.makedirs(workdir, exist_ok=True)

    jobs = (parse_tab(pdftotext(args.am_pdf, workdir), "AM")
            + parse_tab(pdftotext(args.pm_pdf, workdir), "PM"))
    problems = validate_jobs(jobs)

    awards_text = pdftotext(args.awards_pdf, workdir)
    awards = parse_awards(awards_text)

    # Cross-check every award amount against the tabulation (OCR/typo guard)
    by_id = {j["id"]: j for j in jobs}
    for a in awards:
        j = by_id.get(a["id"])
        if j is None:
            problems.append(f"award {a['id']} has no tabulation")
            continue
        if a["status"] != "AWARDED" or a["amount"] is None:
            continue
        low = j["rank"][0]
        lowsum = j["recon"][low["vendor"]]["sum"]
        a["amountVsItemSum"] = round(a["amount"] - lowsum, 2)
        a["amountVsBaseBid"] = round(a["amount"] - low["base"], 2)
        a["lowBidderInBlock"] = norm_name(low["name"]) in norm_name(
            " ".join(a["block"]))
        if abs(a["amountVsItemSum"]) > 0.02:
            problems.append(
                f"award {a['id']}: amount {a['amount']} vs low-bid item sum "
                f"{lowsum} (diff {a['amountVsItemSum']})")
        if not a["lowBidderInBlock"]:
            problems.append(
                f"award {a['id']}: low bidder '{low['name']}' not found in "
                f"awards block")

    out = {
        "lettingDateRaw": jobs[0]["letDate"] if jobs else None,
        "jobs": jobs,
        "awards": awards,
        "schedule2026": parse_schedule(pdftotext(args.sched26_pdf, workdir)),
        "schedule2027": parse_schedule(pdftotext(args.sched27_pdf, workdir)),
        "wap": parse_wap(pdftotext(args.wap_pdf, workdir)),
        "problems": problems,
    }
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)

    print(f"jobs: {len(jobs)}  "
          f"bids: {sum(len(j['rank']) for j in jobs)}  "
          f"reconciled: {sum(1 for j in jobs if j['reconciled'])}/{len(jobs)}")
    print(f"awards rows: {len(awards)}  problems: {len(problems)}")
    for p in problems:
        print("PROBLEM:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
