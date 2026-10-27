#!/usr/bin/env python3
"""Finalize merged year records: cite tokens on new letting entries, refreshed
gap/callout/lettingsLabel prose computed from the record itself.
Run from /home/claude/refresh-oct26 with python3 -I scripts/prep_final.py
"""
import json

R = 'records/'
def load(p): return json.load(open(R + p))
def save(p, o): json.dump(o, open(R + p, 'w'))
def M(v): return '$' + format(round(v), ',')

NUM = {10:'Ten',11:'Eleven',12:'Twelve',13:'Thirteen',14:'Fourteen'}

def sums(Y):
    L = Y['lighting']
    return dict(n=len(L), l2=sum(c['l2'] for c in L),
        hw=sum(c['split']['hardware'] if c.get('split') else c.get('product',0) for c in L),
        lump=sum((c['split'].get('lump',0) if c.get('split') else 0) for c in L),
        awN=sum(1 for c in L if c['award']=='awarded'),
        aw=sum(c['l2'] for c in L if c['award']=='awarded'))

# ---------- TN ----------
Y = load('TN_YEAR.new.json')
for l in Y['lettings']:
    if l['iso'] == '2026-10-02': l['tc'] = 'TN-56'; l['ac'] = 'TN-57'; l['awardPosted'] = 'Oct 26, 2026'
s = sums(Y)
Y['lettingsLabel'] = 'Eleven lettings'
Y['gap'] = ("14 of 412 calls have no Summary of Bids entry — TDOT omits the calls it rejects or holds "
 "(13 ALL BIDS REJECTED, and the Aug 14, 2026 CONTRACT PENDING call, resolved to awarded — Dement Construction "
 "Group, $5,976,400 — on the revised Contract Awards file dated Sep 9, 2026, its items still unpublished). "
 "The Jul 25, 2025 special letting sits just outside the span; the Oct 2, 2026 letting reads 25 of 26 calls, "
 "its apparent lows summing to TDOT's printed Letting Total of $89,510,160.07 to the cent.")
Y['callout'] = ("<strong>What the Tennessee read says.</strong> %d of %d read contracts carried a Section 714 lighting item — %s identified, "
 "%s of it hardware (light standards, LED luminaires, high-mast assemblies) and %s in structural and navigational lighting lump sums. "
 "3 are standalone lighting contracts (L1) let to electrical contractors — interstate lighting rebuilds on I-24, I-26 and I-40 — and the rest "
 "ride inside interchange, widening and bridge work. The Oct 2, 2026 letting added two L2 packages that are relocation and foundations rather "
 "than new hardware — an Anderson County turn lane that relocates two light standards, and the Sullivan County S.I.A. route serving Eastman "
 "Chemical (23 post-top foundations, conduit and cable, $290,120). TDOT builds interstate lighting where a local agency agrees to maintain it, "
 "and the read shows exactly that pattern.") % (s['n'], Y['contractsRead'], M(s['l2']), M(s['hw']), M(s['lump']))
save('TN_YEAR.final.json', Y)
print('TN', s)

# ---------- NC ----------
Y = load('NC_YEAR.new.json')
Y['gap'] = ("All eighteen Central lettings posted through October 20, 2026 are included. The Sep 15, 2026 letting read 8 of 8 "
 "at item level (C205204 withdrawn before letting); Sep 24 was a single CM/GC bridge package, awarded Oct 1; the Oct 20, 2026 "
 "letting is census-level from its Item C until the bid tabulations post.")
save('NC_YEAR.final.json', Y)
print('NC lighting awarded', sums(Y)['awN'], 'of', sums(Y)['n'])

# ---------- AR ----------
Y = load('AR_YEAR.new.json')
for l in Y['lettings']:
    if l.get('iso') == '2026-09-23': l['tc'] = 'AR-51'; l['ac'] = 'AR-52'
s = sums(Y)
Y['lettingsLabel'] = 'Ten lettings'
Y['callout'] = ("<strong>What the Arkansas read says.</strong> The control read confirms the request-state model: %d of %d jobs carried an "
 "illumination item, %s identified and %s of it hardware, all inside interchange, intersection, widening and pedestrian jobs — no standalone "
 "lighting contract in the record. The one sizeable package is the I-57/Hwy 5 interchange at Cabot (Jan 21, 2026; Weaver-Bailey; $983,003 of "
 "lighting). The Sep 23, 2026 letting added two pedestrian-improvement jobs ($537,533 of lighting between them) priced on a pay item new to the "
 "record — 714770, a 30-ft breakaway roadway illumination pole with one 160W LED luminaire — and ARDOT's own twelve-month Weighted Average "
 "Unit Prices to Aug 12, 2026 still match the record's Section 714 quantities (13 of 14 exactly). Section 714 is shared with traffic-signal "
 "mast-arm poles, which are excluded by name.") % (s['n'], Y['contracts'], M(s['l2']), M(s['hw']))
save('AR_YEAR.final.json', Y)
print('AR', s)

# ---------- MS ----------
Y = load('MS_YEAR.new.json')
tok = {'2026-09-01':('MS-81',None),'2026-09-22':('MS-82',None),'2026-09-29':('MS-83',None)}
for l in Y['lettings']:
    if l.get('iso') in tok: l['tc'] = tok[l['iso']][0]; l['ac'] = None
    if l.get('iso') == '2026-08-21': l['ac'] = 'MS-79'
    if l.get('iso') == '2026-08-25': l['ac'] = 'MS-80'
s = sums(Y)
Y['lettingsLabel'] = '27 lettings'
Y['gap'] = ("The Commission's September 8, 2026 award actions settled the Aug 21 and Aug 25, 2026 lettings — 10 contracts awarded, 2 rejected, "
 "among them the I-55 Gluckstadt widening, whose $195.95M low bid ran 48% over the state estimate; its $4.31M lighting scope returns to the "
 "letting calendar when MDOT re-advertises. The Sep 22 and Sep 29, 2026 award lists are not yet posted, so those calls are apparent. Two "
 "lettings (Jan 27 and Feb 25, 2026) advertised calls with no bids read on the day; the Feb 3, 2026 tabulations are decoded Type 3 copies.")
Y['callout'] = ("<strong>What the Mississippi read says.</strong> %d of %d read contracts carried a lighting item — %s identified, %s of it "
 "lighting assemblies (poles with LED luminaires, high mast and low mast). Every one rides inside an interstate widening, interchange or "
 "bridge job, and none is standalone. The largest — the I-55 Gluckstadt widening at Madison, carrying $4.31M of the $5.51M — was "
 "<b>rejected</b> by the Commission on September 8, 2026 (the low bid 48%% over estimate) and awaits re-advertisement: the single biggest "
 "open lighting opportunity in the state. The four lettings since Aug 25 (one emergency, two specials, one regular) carried no lighting. "
 "The statute state reads as expected: MDOT lights its own interchanges and buys the assembly as one pay item; surface-street lighting "
 "stays with the municipalities.") % (s['n'], Y['contractsRead'], M(s['l2']), M(s['hw']))
save('MS_YEAR.final.json', Y)
print('MS', s)

# ---------- SC ----------
Y = load('SC_YEAR.new.json')
for l in Y['lettings']:
    if l.get('iso') == '2026-09-09': l['tc'] = 'SC-54'
    if l.get('iso') == '2026-10-13': l['tc'] = 'SC-55'
s = sums(Y)
Y['lettingsLabel'] = 'Thirteen lettings'
Y['gap'] = ("Aug 11, 2026's certified tabulations posted in September — 13 of its 15 calls now read at item level (2973030 was re-let Oct 13 "
 "as 2973031; 4670730 has no tabulation). Sep 9's certified tabulations posted Oct 7 (26 of 27 read — the Butler Road call's is pending); "
 "the Oct 13, 2026 letting is census-level until certification. 5 earlier calls still have no tabulation in the library (withdrawn or not "
 "awarded — the Apparent Bids files still list them).")
Y['callout'] = ("<strong>What the South Carolina read says.</strong> %d of %d read contracts carried a lighting item — %s identified, %s of it "
 "light standards and %s in “design and installation of roadway lighting electrical system” lump sums, one per lit intersection. The Sep 9, "
 "2026 letting added two intersection packages on the same pattern (Beaufort $149,200; Calhoun $158,800). SCDOT buys lighting as a "
 "design-build package inside its road contracts: the standard is a pay item, the system is a lump — the permit-state model, read. SCDOT "
 "publishes no award artifact, so every winner stays apparent; the Nov 10, 2026 letting's notice already lists one lighting system and "
 "eighteen 35-ft light standards on an Anderson County intersection job.") % (s['n'], Y['contractsRead'], M(s['l2']), M(s['hw']), M(s['lump']))
save('SC_YEAR.final.json', Y)
print('SC', s)

# ---------- AL ----------
Y = load('AL_YEAR.new.json')
for l in Y['lettings']:
    if l.get('iso') == '2026-07-31': l['tc'] = 'AL-51'; l['ac'] = 'AL-51'
s = sums(Y)
Y['lettingsLabel'] = 'Twelve lettings'
Y['gap'] = ("The Jul 31, 2026 tabulation posted in October (11 contracts, all awarded by ALDOT's release rule, no Section 750 item — two "
 "conduit-only contracts listed, not counted). The Aug 28 and Sep 25, 2026 lettings are bid-opened but not yet awarded — ALDOT posts a "
 "tabulation only when every project in the letting is awarded or rejected; their Low Bid Sheets flag one standalone lighting call "
 "(Tuscaloosa, I-20/59 Exit 89 ramps, “HIGHWAY LIGHTING UPGRADES”, all three listed bidders electrical contractors, Inline Electric apparent "
 "low $449,978) and one I-10 widening at Daphne naming traffic lighting — counted nowhere until the tabulations post. Six earlier lettings "
 "(Dec 6, 2024 – Jun 27, 2025) were read the same way and sit outside the span.")
save('AL_YEAR.final.json', Y)
print('AL', s)
