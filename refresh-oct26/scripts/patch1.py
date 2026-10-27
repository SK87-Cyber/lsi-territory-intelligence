#!/usr/bin/env python3
"""Stage 1 template patch: six states' year blobs, LETS appends, sources,
AL pipeline + snapshot. Run: python3 -I scripts/patch1.py  (from refresh-oct26)
"""
import json, sys
sys.path.insert(0, 'scripts')
from patch_blob import replace_blob, find_blob

T = 'work/template.html'
tpl = open(T, encoding='utf-8').read()
R = 'records/'
def load(p): return json.load(open(p))

# ---- 1. year blobs ----
for name, f in [('TN_YEAR','TN_YEAR.final.json'),('NC_YEAR','NC_YEAR.final.json'),
                ('AR_YEAR','AR_YEAR.final.json'),('MS_YEAR','MS_YEAR.final.json'),
                ('SC_YEAR','SC_YEAR.final.json'),('AL_YEAR','AL_YEAR.final.json'),('KY_YEAR','KY_YEAR.final.json')]:
    tpl = replace_blob(tpl, name, load(R+f))
    print('replaced', name)

# ---- 2. LETS appends ----
def lets_rows(delta, lit_ids):
    rows = []
    for r in delta['all']:
        rows.append({'call': r.get('call',''), 'id': r.get('tip') or r.get('id'),
                     'county': r.get('county',''), 'desc': (r.get('desc') or '')[:200],
                     'bidders': [[b[0], b[1]] for b in (r.get('bidders') or [])] if isinstance(r.get('bidders'), list) else [[r.get('low'), r.get('lowAmt')]],
                     'lit': r.get('id') in lit_ids})
    return rows

def lets_entry(delta, src, note, kind='tab'):
    L = delta['letting']
    lit_ids = {c['id'] for c in delta.get('lighting', [])}
    return {'date': L['date'], 'iso': L['iso'], 'kind': kind, 'src': '{%s}' % src,
            'note': note, 'read': bool(L.get('read')), 'rows': lets_rows(delta, lit_ids)}

appends = {
 'TN_LETS': [lets_entry(load('TN/2026-10-02/delta.json'), 'TN-56',
   "From TDOT's Apparent Bid Results (every call and bidder; the printed Letting Total of $89,510,160.07 matched to the cent), the Summary of Bids (25 of 26 calls at item level, every bidder's rows summed to the printed TOTAL CONTRACT) and the Contract Awards file modified Oct 26, 2026 (25 awarded, 1 all bids rejected).")],
 'MS_LETS': [lets_entry(load('MS/delta_2026-09-01.json'), 'MS-81',
   "Special letting — the two calls pulled from Aug 25 re-let and read at item level (2 of 2 reconciled); both awarded by the Commission Sep 8, 2026."),
  lets_entry(load('MS/delta_2026-09-22.json'), 'MS-82',
   "Regular letting — 11 calls read at item level and reconciled (call 06, the re-advertised Madison I-55 group, withdrawn again); the Bid Awards list is not yet posted, so every call is apparent."),
  lets_entry(load('MS/delta_2026-09-29.json'), 'MS-83',
   "Special letting — the deferred Sep 22 call 05 (Rankin SR 25 widening, A+C, 291 items, reconciled); the Bid Awards list is not yet posted.")],
 'SC_LETS': [lets_entry(load('SC/delta_2026-09-09.json'), 'SC-54',
   "From the Apparent Bids file (27 calls with bids, 90 bids) and 26 certified per-contract Tabulations of Bids posted Oct 7, 2026, each reconciled to its printed Contract Totals to the cent; the Butler Road call's tabulation is pending."),
  lets_entry(load('SC/delta_2026-10-13.json'), 'SC-55',
   "From the Apparent Bids file — 14 calls, 69 bids, contract level only until the certified tabulations post.")],
 'AR_LETS': [lets_entry(load('AR/delta_2026-09-23.json'), 'AR-51',
   "From ARDOT's Bid Tabulation Summaries (AM and revised PM) and the revised Awards List — 9 jobs, 32 bids, 9 of 9 reconciled to the printed Base Bid, 9 of 9 awarded.")],
 'KY_LETS': [lets_entry(load('KY/delta_2026-09-24.json'), 'KY-51',
   "From the Letting Results (vector-text, OCR'd and cross-verified against the tabulation's printed totals), the Unit Bid Tabulations posted after the October Awards Committee (12 of 12 calls present = awarded; 32 of 32 bidder columns reconciled) and the Bid Item Quantity Index."),
  lets_entry(load('KY/delta_2026-10-22.json'), 'KY-52',
   "From the Letting Day Results — 44 calls, 110 bids, contract level only until the Unit Bid Tabulations post after the November Awards Committee. Six Bid Item Quantity Index calls never reached letting day, among them 26-1520 (NHPP 0754(069), District 7): 76 poles and 76 LED luminaires, withdrawn before the day and not yet re-let.")],
 'AL_LETS': [lets_entry(load('AL/delta_2026-07-31.json'), 'AL-51',
   "From ALDOT's Jul 31, 2026 Tabulation of Bids, posted in October — 11 contracts, 39 bids, 11 of 11 reconciled to the Contract Totals; presence in the posted tabulation is award under ALDOT's release rule. No Section 750 item in the letting.")],
}
for name, entries in appends.items():
    a, b = find_blob(tpl, name)
    arr = json.loads(tpl[a:b])
    have = {e['iso'] for e in arr}
    for e in entries:
        assert e['iso'] not in have, (name, e['iso'])
        arr.append(e)
    tpl = tpl[:a] + json.dumps(arr, ensure_ascii=False, separators=(',',':')) + tpl[b:]
    print('appended', len(entries), 'to', name, '->', len(arr))

# ---- 3. sources ----
SRC = {
 'NC': [
  ["NCDOT Board of Transportation — September 3, 2026 meeting minutes and meeting archive (Item C: Award of Highway Construction Contracts from August 2026 Letting)",
   "https://www.ncdot.gov/about-us/board-offices/boards/board-transportation/Pages/archives.aspx",
   "Award layer: “Chairman Lathrop stated for the record for Item C that all projects were awarded by the Secretary to the low bidder”; the archived Item C prints AWARDED as typeset text under every contract of the Aug 18 letting, C205195 included — read Oct 26, 2026"],
  ["NCDOT Central Letting of September 15, 2026 — letting details page, Item C and the XLS bid tabulation",
   "https://connect.ncdot.gov/letting/pages/Central-Letting-Details.aspx?let_type=Central&let_date=2026-09-15%2000:00:00",
   "Bid layer: 8 contracts, 37 bids, $83,263,570.96 of low bids reconciled to the printed LETTING TOTAL to the cent; every contract item-read; no Division 14 lighting; C205204 withdrawn — read Oct 26, 2026"],
  ["NCDOT letting of September 24, 2026 — C205140 (New Hanover HB-0040) with the Notification of Award of October 1, 2026",
   "https://connect.ncdot.gov/letting/pages/Central-Letting-Details.aspx?let_type=Central&let_date=2026-09-24%2000:00:00",
   "One CM/GC bridge package, one bidder (Balfour Beatty, $8,665,580.39, reconciled); awarded by the Secretary per the award letter — read Oct 26, 2026"],
  ["NCDOT Central Letting of October 20, 2026 — Item C",
   "https://connect.ncdot.gov/letting/pages/Central-Letting-Details.aspx?let_type=Central&let_date=2026-10-20%2000:00:00",
   "Census layer: 6 contracts, 26 bids, $75,612,601.28 reconciled to the printed LETTING TOTAL; bid tabulations not yet posted, so the letting is contract-level and apparent — read Oct 26, 2026"]],
 'TN': [
  ["TDOT letting of October 2, 2026 — Apparent Bid Results and Summary of Bids",
   "https://www.tn.gov/tdot/tdot-construction-division/bid-lettings/2026-bid-lettings.html",
   "Bid layer: 26 calls, 80 bids; 25 of 25 Summary contracts reconciled to the printed TOTAL CONTRACT to the cent, and the apparent lows (incl. the rejected call) sum to the printed Letting Total $89,510,160.07 exactly — read Oct 26, 2026"],
  ["TDOT Contract Awards for the letting of October 2, 2026 (file modified Oct 26, 2026)",
   "https://www.tn.gov/content/dam/tn/tdot/construction/2026_bid_lettings/october-2,-2026-letting/20261002_ContractAwards.pdf",
   "Award layer: 25 of 26 calls awarded, 1 ALL BIDS REJECTED (CN262061, Hamilton) — read Oct 26, 2026"]],
 'AR': [
  ["ARDOT letting of September 23, 2026 — Bid Tabulation Summary (Sep-26-Bid-Tabs_AM.pdf, Sep-26-Bid-Tabs_PM-Revised.pdf)",
   "https://media.ark.org/ardot/Sep-26-Bid-Tabs_AM.pdf",
   "Bid layer: 9 jobs, 32 bids, 9 of 9 reconciled to the printed Base Bid (worst residual $0.48); two pedestrian-improvement jobs carry illumination on the new pay item 714770 — read Oct 27, 2026"],
  ["ARDOT September 23, 2026 Letting Awards List (revised edition)",
   "https://media.ark.org/ardot/September-23-2026-Letting-Awards-List_Revised-061938.pdf",
   "Award layer: 9 of 9 jobs AWARDED; every amount equals the low bidder's item sum to the cent — read Oct 27, 2026"],
  ["ARDOT Letting Schedules for 2026 and 2027",
   "https://media.ark.org/ardot/Letting-Schedule_2027.pdf",
   "Calendar: 2026 — Jan 21, Mar 4, Apr 8, May 20, Jun 24, Aug 12, Sep 23, Nov 4; 2027 — Jan 20, Mar 3, Apr 14, May 19, Jun 30, Aug 11, Sep 22, Nov 3 — read Oct 27, 2026"],
  ["ARDOT Weighted Average Unit Prices — twelve months to August 12, 2026",
   "https://media.ark.org/ardot/Aug-12-2026-Weighted-Average-Prices.pdf",
   "Census check: 13 of 14 mapped Section 714 quantities match the record exactly; the list also carries a Section 904 “LED R.I. (20K LUM, CB, SHOEBS, 30')” line — 16 poles in the window — an illumination item outside the 714 dictionary, flagged for the owner's dictionary review — read Oct 27, 2026"]],
 'MS': [
  ["MDOT Bid Awards — emergency letting of August 21, 2026 (Commission action September 8, 2026)",
   "https://mdot.ms.gov/bidsystem_data/20260821/LETDOCS/20260821BidAwards.pdf",
   "Award layer: both calls awarded (Phillips $426,530; Dunn Roadbuilders $1,499,198) — read Oct 26, 2026"],
  ["MDOT Bid Awards — letting of August 25, 2026 (Commission action September 8, 2026)",
   "https://mdot.ms.gov/bidsystem_data/20260825/LETDOCS/20260825BidAwards.pdf",
   "Award layer: 8 of 10 read calls awarded ($23,319,880.15, cross-foots to the printed total); 108168301 (I-55 Gluckstadt widening, $4.31M of lighting) and 110041301 REJECTED — the Gluckstadt low bid ran 48% over estimate and awaits re-advertisement — read Oct 26, 2026"],
  ["MDOT special letting of September 1, 2026 — Checked Bid Results and tabulations",
   "https://mdot.ms.gov/Applications/BidSystem/lettingInfo.aspx?r=1&date=September%201,%202026",
   "Bid layer: the two calls pulled from Aug 25, re-let and reconciled 2 of 2; both awarded Sep 8, 2026; no lighting — read Oct 26, 2026"],
  ["MDOT letting of September 22, 2026 — Checked Bid Results and 11 tabulations",
   "https://mdot.ms.gov/Applications/BidSystem/lettingInfo.aspx?r=0&date=September%2022,%202026",
   "Bid layer: 11 calls read and reconciled, 45 bids, $28.54M of low bids; call 06 (the re-advertised Madison I-55 group) withdrawn again; awards not yet posted; no lighting — read Oct 26, 2026"],
  ["MDOT special letting of September 29, 2026 — Checked Bid Results and tabulation",
   "https://mdot.ms.gov/Applications/BidSystem/lettingInfo.aspx?r=1&date=September%2029,%202026",
   "Bid layer: the deferred Rankin SR 25 widening (A+C, 291 items, reconciled); awards not yet posted; only false-friend and anchor-less shared electrical — read Oct 26, 2026"]],
 'SC': [
  ["SCDOT letting of September 9, 2026 — Apparent Bids and 26 certified Tabulations of Bids (posted Oct 7, 2026)",
   "https://info2.scdot.org/bidsreceived/apparentbids/09092026_apparentbids.pdf",
   "Bid layer: 27 calls with bids, 90 bids, $214,012,469.23 of low bids; 26 of 27 read at item level and reconciled to the cent; two lighting contracts (Beaufort, Calhoun) — read Oct 27, 2026"],
  ["SCDOT letting of October 13, 2026 — Apparent Bids",
   "https://info2.scdot.org/bidsreceived/apparentbids/10132026_apparentbids.pdf",
   "Census layer: 14 calls, 69 bids, $111,839,837.11; certified tabulations not yet posted — read Oct 27, 2026"],
  ["SCDOT certified Tabulations of Bids for the August 11, 2026 letting (13 files, posted Sep 9, 2026)",
   "https://info2.scdot.org/bidtabs/BidTabsDocuments",
   "Bid layer: 13 of the letting's 15 calls read at item level and reconciled to the cent (2973030 re-let Oct 13 as 2973031; 4670730 unposted); no lighting item among them — read Oct 27, 2026"]],
 'KY': [
  ["KYTC letting of September 24, 2026 — Letting Results, Unit Bid Tabulations and Bid Item Quantity Index",
   "https://transportation.ky.gov/Construction-Procurement/Pages/default.aspx",
   "Bid layer: 12 calls, 32 bids, $33,853,786.89 of low bids; all 12 in the Unit Bid Tabulations (= awarded), 32 of 32 bidder columns reconciled; four lighting contracts, $430,853 identified — read Oct 27, 2026"],
  ["KYTC letting of October 22, 2026 — Letting Day Results and Bid Item Quantity Index",
   "https://transportation.ky.gov/Construction-Procurement/Pages/default.aspx",
   "Census layer: 44 calls, 110 bids, $20,946,613.82 of apparent lows; the tabulation posts after the November Awards Committee. BIQI call 26-1520 (District 7; 76 poles, 76 LED luminaires) was withdrawn before letting day and has not re-let — read Oct 27, 2026"],
  ["KYTC Unit Bid Tabulations for the lettings of June 25 and August 20, 2026 (posted on the Cabinet's letting pages)",
   "https://transportation.ky.gov/Construction-Procurement/Pages/default.aspx",
   "Confirmation: the newly posted official tabs reproduce the record exactly — Jun 25 7 of 7 awards, 23 of 23 columns, $0.00 residual, both I-75 rest-area lighting jobs to the cent ($790,615.00 and $187,795.26); Aug 20 43 awards, 101 of 101 columns — read Oct 27, 2026"]],
 'AL': [
  ["ALDOT Tabulation of Bids — letting of July 31, 2026 (posted October 2026)",
   "https://alletting.dot.state.al.us/BidTabs/bidtab_pdf/ljul3126.pdf",
   "Bid layer: 11 contracts, 39 bids, 11 of 11 reconciled to the Contract Totals to the cent; awarded by ALDOT's release rule; no Section 750 item (two conduit-only contracts listed, not counted) — read Oct 26, 2026"],
  ["ALDOT Low Bid Sheets — lettings of August 28 and September 25, 2026 (bids opened, awards pending)",
   "https://alletting.dot.state.al.us/DW_Pages/Bid_Tabs/Bidtab_2026.html",
   "Census: 15 and 17 contracts (up to three low bidders each); the Aug 28 call 008 is a standalone “HIGHWAY LIGHTING UPGRADES” job on the I-20/59 Exit 89 ramps at Vance (Tuscaloosa), Inline Electric apparent low $449,978 over two other electrical firms — no dollars counted until the tabulations post — read Oct 26, 2026"],
  ["ALDOT FY 2024–2027 STIP — statewide highway report, print date October 26, 2026 (owner download; the Office Engineer portal now serves it only in a browser session)",
   "https://cpmsapps.aldot.gov/OfficeEngineer/Plan/Statewide",
   "Programme re-read: 2,032 projects; 29 name roadway lighting (12 lighting-only, $23.20M of pure scope); the I-59 Birmingham Phase 1 relight moved to FY 2026 at $7.98M (Amendment #29); two projects new since Sep 1 — read Oct 27, 2026"]],
}
# append sources into each state's sources array inside STATES
# STATES is one big const; patch per-state by locating "id":"XX" then its "sources":[ ... ]
counts = load(R+'src_counts.json')
for sid, rows in SRC.items():
    # STATES uses unquoted keys: {id:"NC",...,sources:[...]}
    key = 'id:"%s"' % sid
    i = tpl.find(key)
    assert i > 0, sid
    j = tpl.find('sources:', i)
    assert j > 0 and j - i < 400000, (sid, 'sources array not near id')
    a = tpl.find('[', j)
    # match brackets
    depth = 0; instr = False; escp = False; k = a
    while True:
        ch = tpl[k]
        if instr:
            if escp: escp = False
            elif ch == '\\': escp = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == '[': depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0: break
        k += 1
    arr = json.loads(tpl[a:k+1])
    assert len(arr) == counts[sid], (sid, len(arr), counts[sid])
    first = counts[sid]
    # insert rather than reserialize, preserving the existing array text exactly
    ins = ',' + ','.join(json.dumps(r, ensure_ascii=False, separators=(',',':')) for r in rows)
    tpl = tpl[:k] + ins + tpl[k:]
    print(f'{sid}: sources {counts[sid]} -> {counts[sid]+len(rows)} (tokens {sid}-{first}..{sid}-{counts[sid]+len(rows)-1})')

# ---- 4. AL pipeline + snapshot ----
stip = load('AL/stip_update.json')
a, b = find_blob(tpl, 'AL_PIPELINE')
tpl = tpl[:a] + json.dumps(stip['lighting'], ensure_ascii=False, separators=(',',':')) + tpl[b:]
print('AL_PIPELINE ->', len(stip['lighting']), 'rows')
a, b = find_blob(tpl, 'PIPE_SNAPSHOT')
PS = json.loads(tpl[a:b])
PS['AL'] = {'asOf': 'Oct 27, 2026', 'iso': '2026-10-27',
  'source': 'ALDOT FY 2024–2027 STIP statewide highway report (print date Oct 26, 2026; owner download — the Office Engineer portal serves it only in a browser session)',
  'key': 'federal-aid project number on both', 'joinable': True}
tpl = tpl[:a] + json.dumps(PS, ensure_ascii=False, separators=(',',':')) + tpl[b:]
print('PIPE_SNAPSHOT.AL -> Oct 27, 2026')

open(T, 'w', encoding='utf-8').write(tpl)
print('patch1 written:', len(tpl), 'bytes')
