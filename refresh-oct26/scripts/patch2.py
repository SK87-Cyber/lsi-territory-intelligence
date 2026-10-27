#!/usr/bin/env python3
"""Stage 2: calendars (BIDSRC cal.dates, BX_UPCOMING/BX_READ with honest basis),
CADENCE list dates, MFR list dates, source-note refreshes, awardQueue rejected
filter, SNAPSHOTS append, ROADMAP_STATUS -> 10.1b.
"""
import json, sys
sys.path.insert(0, 'scripts')
from patch_blob import find_blob

T = 'work/template.html'
tpl = open(T, encoding='utf-8').read()
def load(p): return json.load(open(p))

def rep1(old, new, label):
    global tpl
    assert tpl.count(old) == 1, (label, tpl.count(old))
    tpl = tpl.replace(old, new)
    print('edited:', label)

# ---- 1. BIDSRC cal.dates appends (the agencies' own calendars, first-rank source) ----
ADD = {
 'NC': ['2026-11-17'],
 'SC': ['2026-09-09','2026-10-13','2026-11-10'],
 'AL': ['2026-07-31','2026-08-28','2026-09-25','2026-11-06','2026-12-04'],
 'MS': ['2026-09-29','2026-10-27','2026-11-24'],
 'TN': ['2026-11-06','2026-12-04','2027-02-12','2027-03-19','2027-05-07','2027-06-25','2027-08-13','2027-10-01','2027-11-05','2027-12-03'],
 'KY': ['2027-01-28','2027-02-18'],
 'AR': ['2026-12-16'],  # placeholder replaced below from the parsed schedule
}
# AR 2027 schedule parsed by the agent: use it instead of the placeholder
ADD['AR'] = ['2027-01-20','2027-03-03','2027-04-14','2027-05-19','2027-06-30','2027-08-11','2027-09-22','2027-11-03']
a, b = find_blob(tpl, 'BIDSRC')  # may fail (JS literal); fall back to targeted date-list edits
try:
    raise KeyError('skip')  # BIDSRC is a JS literal with comments; use targeted edits below
except KeyError:
    pass
# targeted: each cal dates array is unique by its last elements
import re as _re
B = load('records/BIDSRC.json')
for sid, dates in ADD.items():
    cur = (B.get(sid, {}).get('cal') or {}).get('dates') or []
    newdates = cur + [d for d in dates if d not in cur]
    if cur:
        old = json.dumps(cur, separators=(',',':'))
        old_js = old.replace('"', '"')
        cnt = tpl.count(old)
        if cnt != 1:
            # try with spaces after commas
            old2 = json.dumps(cur, separators=(', ', ': '))
            cnt2 = tpl.count(old2)
            assert cnt2 == 1, (sid, 'cal dates array not found uniquely', cnt, cnt2)
            old = old2
        tpl = tpl.replace(old, json.dumps(newdates, separators=(',',':')))
        print(f'{sid}: cal.dates {len(cur)} -> {len(newdates)}')
    else:
        print(f'{sid}: EMPTY cal.dates — handle manually')

# ---- 2. BX_UPCOMING rebuilt from the agencies' own pages; BX_READ -> Oct 27 ----
new_bx = {
 'NC': [{'id':'L261117','date':'2026-11-17','n':None}],
 'NC-DIV': [],
 'SC': [{'id':'L261110','date':'2026-11-10','n':26}],
 'GA': [],
 'AL': [{'id':'L261106','date':'2026-11-06','n':None},{'id':'L261204','date':'2026-12-04','n':None}],
 'MS': [{'id':'L261027','date':'2026-10-27','n':15},{'id':'L261124','date':'2026-11-24','n':None}],
 'TN': [{'id':'L261106','date':'2026-11-06','n':None},{'id':'L261204','date':'2026-12-04','n':None}],
 'KY': [{'id':'L261119','date':'2026-11-19','n':None},{'id':'L261210','date':'2026-12-10','n':None}],
 'AR': [{'id':'L261104','date':'2026-11-04','n':None}],
}
a, b = find_blob(tpl, 'BX_UPCOMING')
tpl = tpl[:a] + json.dumps(new_bx, ensure_ascii=False, separators=(',',':')) + tpl[b:]
print('BX_UPCOMING rebuilt (agencies’ own pages)')
rep1('const BX_READ = "2026-09-10";', 'const BX_READ = "2026-10-27";', 'BX_READ')
# the per-row basis and the freshness basis must say what was actually read
rep1('basis:"Bid Express calendar, read "+BX_READ,src:"{BX-0}"});',
     'basis:"the agency’s own letting pages, read "+BX_READ+" (no Bid Express login this session)",src:"{BX-0}"});',
     'BX row basis')
rep1('basis:"Bid Express calendar, read "+BX_READ,src:"{BX-0}",div:true}));',
     'basis:"the agency’s own letting pages, read "+BX_READ+" (no Bid Express login this session)",src:"{BX-0}",div:true}));',
     'BX div row basis')
rep1('push("Calendar",BX_READ,addDays(BX_READ,CADENCE.calendar),"Bid Express nine-agency calendar · re-read every "+CADENCE.calendar+" days");',
     'push("Calendar",BX_READ,addDays(BX_READ,CADENCE.calendar),"the agencies’ own letting calendars, read "+BX_READ+" (Bid Express not read — no login this session) · re-read every "+CADENCE.calendar+" days");',
     'calendar freshness basis')
# the BX_UPCOMING comment block above the const names Sep 10 — update the note
old = 'BX_UPCOMING: every upcoming letting the nine Bid Express agencies listed on'
i = tpl.find(old)
assert i > 0
j = tpl.find('const BX_UPCOMING', i)
seg = tpl[i:j]
tpl = tpl[:i] + ('BX_UPCOMING: the upcoming lettings on each agency’s own letting pages, read Oct 26–27, 2026 (no Bid Express\n   login this session — the Sep 10, 2026 Bid Express read was the last; the agencies’ own calendars in BIDSRC[].cal are the first\n   rank anyway). */\n') + tpl[j:]
print('edited: BX comment')

# ---- 3. CADENCE listAsOf TN/KY; indexAsOf untouched ----
a, b = find_blob(tpl, 'CADENCE')
C = json.loads(tpl[a:b])
C['listAsOf']['TN'] = '2026-10-26'; C['listAsOf']['KY'] = '2026-10-26'
tpl = tpl[:a] + json.dumps(C, ensure_ascii=False, separators=(',',':')) + tpl[b:]
print('CADENCE.listAsOf TN/KY -> 2026-10-26')

# ---- 4. MFR list dates (scoped to the MFR blob — the strings recur in SNAPSHOTS) ----
a, b = find_blob(tpl, 'MFR')
blob = tpl[a:b]
assert blob.count('"print date Sep 1, 2026"') == 1 and blob.count('"print-dated Sep 5, 2026; updated daily"') == 1
blob = blob.replace('"print date Sep 1, 2026"', '"print date Oct 8, 2026"')
blob = blob.replace('"print-dated Sep 5, 2026; updated daily"', '"print-dated Oct 26, 2026; updated daily"')
tpl = tpl[:a] + blob + tpl[b:]
print('edited: MFR TN/KY list dates')

# ---- 5. awardQueue: a rejected contract is resolved, not pending ----
rep1('Y.lighting.filter(c=>c.award!=="awarded").forEach(c=>{',
     'Y.lighting.filter(c=>c.award!=="awarded"&&c.award!=="rejected").forEach(c=>{',
     'awardQueue rejected filter')

# ---- 6. SNAPSHOTS: append the 10.1a pre-refresh digest ----
a, b = find_blob(tpl, 'SNAPSHOTS')
S = json.loads(tpl[a:b])
snap = load('records/snapshot_101a.json')
assert S[-1]['build'] != '10.1a'
S.append(snap)
tpl = tpl[:a] + json.dumps(S, ensure_ascii=False, separators=(',',':')) + tpl[b:]
print('SNAPSHOTS +10.1a digest ->', len(S))

# ---- 7. ROADMAP_STATUS -> 10.1b ----
a, b = find_blob(tpl, 'ROADMAP_STATUS')
RS = json.loads(tpl[a:b])
RS['build'] = '10.1b'
RS['date'] = 'Oct 27, 2026'
RS['delivered'].append(["10.1b",
 "the October refresh — every stale layer re-read across the eight states: 13 new lettings (TN, NC ×3, AR, MS ×3, SC ×2, KY ×2, AL) and 2 census-level, all reconciled to the agencies' own totals; the award sweep settled C205195 (NC, Board-recorded), TN's pending call, MS's Aug 21/25 lists (the I-55 Gluckstadt widening REJECTED — its $4.31M lighting scope awaits re-advertisement), AR 9/9, KY 12/12; SC's Aug 11 tabs posted (13 more read); ALDOT's STIP re-read Oct 26 print (29 lighting rows, I-59 Phase 1 relight to FY 2026 at $7.98M); TN QPL (Oct 8) and KY LAM (Oct 26) re-read — still no lighting list, no Cooper entry; the letting calendars re-read from the agencies' own pages (no milestone)"])
RS['open'] = [
 "Georgia — Bid Express login only: the Aug 21, Sep 18 and Oct 16, 2026 lettings and the April award announcement (A260417, T260417 S1); GDOT's monthly Board packets (staged) could serve as a secondary award record — owner's call",
 "the MDOT re-advertisement of the I-55 Gluckstadt widening (rejected Sep 8, 2026 — $4.31M of lighting) and the Sep 22 / Sep 29 award lists; MDOT let again Oct 27, 2026",
 "KYTC BIQI call 26-1520 (District 7 — 76 poles, 76 LED luminaires), withdrawn before the Oct 22 letting and not yet re-let; the Oct 22 tabulation (~late Nov)",
 "NC Oct 20 bid tabs and the October Board record (confirms the Sep 15/24 and Oct 20 lettings); SC's Butler Road and Oct 13 tabulations; ALDOT's Aug 28 / Sep 25 tabulations (a standalone Tuscaloosa lighting job sits in the Aug 28 Low Bid Sheet)",
 "Arkansas dictionary review: ARDOT's weighted-average census carries a Section 904 LED roadway-illumination line outside the Section 714 dictionary — owner's accuracy pass",
 "Kentucky's Apr 23, 2026 Letting Results (still 404)"]
tpl = tpl[:a] + json.dumps(RS, ensure_ascii=False, separators=(',',':')) + tpl[b:]
print('ROADMAP_STATUS -> 10.1b')

# ---- 8. existing source-note refreshes (TN QPL, TN Aug 14 awards, KY LAM) ----
rep1('"Full text searched: no lighting entry, no Cooper / Eaton entry; accessed Sep 6, 2026"',
     '"Full text searched: no lighting entry, no Cooper / Eaton entry; accessed Sep 6, 2026; re-read Oct 26, 2026 (print date Oct 8, 2026) — unchanged"',
     'TN QPL source note')
open(T, 'w', encoding='utf-8').write(tpl)
print('patch2 written:', len(tpl), 'bytes')
