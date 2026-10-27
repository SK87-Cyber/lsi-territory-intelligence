#!/usr/bin/env python3
"""Classify the parsed TDOT letting per TN_DICT and emit the year-record delta:
a letting entry, 'all' census entries, lighting contract records (universal
shape), and shared-only entries. Gates: every published contract reconciled;
sub-class sums re-add to the split; split re-adds to l2.

Usage: tn_emit.py <parsed.json> <TN_YEAR.json> <county_div.json> <letting-date> <iso> <out.json>
"""
import sys, json, re

parsed, yearf, cdivf, DATE, ISO, out = sys.argv[1:7]
P = json.load(open(parsed))
CD = json.load(open(cdivf))  # county name (title) -> region number

# ---------- Apparent Bid Results census ----------
abr = P['abr_text']
calls = {}
for m in re.finditer(r'Call\s+(\d{3})\s+Contract\s+(\S+)\s+Project\s+(\S+)\s+County\s+(.+)', abr):
    calls[m.group(1)] = {'id': m.group(2), 'tip': m.group(3), 'county': m.group(4).strip()}
# bidders per call
segs = re.split(r'Call\s+(\d{3})', abr)
for k in range(1, len(segs), 2):
    call, seg = segs[k], segs[k+1]
    rows = re.findall(r'^([A-Z][A-Za-z0-9 \.,&\'\-\(\)/]+?)\s{2,}\$([\d,]+\.\d{2})\s*$', seg, re.M)
    calls[call]['bidders'] = [[n.strip().title().replace('Llc','LLC'), float(a.replace(',',''))]
                              for n, a in rows
                              if 'Total Bid' not in n and 'Letting Total' not in n and 'Low Bid' not in n]
mlt = re.search(r'Letting Total\s*-\s*\$([\d,]+\.\d{2})', abr)
printed_letting_total = float(mlt.group(1).replace(',','')) if mlt else None

# ---------- Contract Awards ----------
aw = P['awards_text']
awards = {}
asegs = re.split(r'Call\s+(\d{3})', aw)
for k in range(1, len(asegs), 2):
    call, seg = asegs[k], asegs[k+1]
    if 'ALL BIDS REJECTED' in seg.upper():
        awards[call] = {'status': 'rejected'}
    elif 'CONTRACT WITHDRAWN' in seg.upper():
        awards[call] = {'status': 'withdrawn'}
    elif 'CONTRACT PENDING' in seg.upper():
        awards[call] = {'status': 'pending'}
    else:
        m = re.search(r'^\s*([A-Z][A-Z0-9 \.,&\'\-\(\)/]+?)\s{2,}\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s*$', seg, re.M)
        if m:
            awards[call] = {'status': 'awarded', 'contractor': m.group(1).strip().title().replace('Llc','LLC'),
                            'amt': float(m.group(2).replace(',','')), 'est': float(m.group(3).replace(',',''))}

# ---------- classification (TN_DICT v0.1) ----------
LIGHT_ANCHOR = re.compile(r'LIGHT STANDARD|LUMINAIRE|LIGHTING POLE|BRACKET ARM|STRUCTURAL LIGHTING|NAVIGATIONAL LIGHTING|FOUNDATION.*LIGHT STANDARD|STREET LIGHT|FLOOD LIGHT', re.I)
FALSE_FRIEND = re.compile(r'^(712-05|790-65|790-32\.27|725|730|713)')
SHARED714 = re.compile(r'^714-(02|03|04|05|06|07|12|25|70|72)')
S790_WORK = re.compile(r'^790-36')

def sub_of(code, desc):
    d = desc.upper()
    # removal / relocation / transfer of anything is work, whatever the family
    # (3.20 precedent: "INSTALL LUMINAIRE POLE" and relocations are work, not hardware)
    if re.search(r'REMOV|RELOCAT|REINSTALL|REDRILL|TRANSFER', d): return 'work'
    if code.startswith('714-09'): return 'luminaire'
    if code.startswith('790-70'): return 'assembly'
    if code.startswith(('714-01','714-16')) and re.search(r'LIGHTING', d): return 'lump'
    if code.startswith('714-75'): return 'control'
    if code.startswith(('714-71','714-74','714-14')): return 'pole'
    if code.startswith('714-08'):
        if 'FOUNDATION' in d: return 'infrastructure'
        return 'pole'
    return 'infrastructure'

def is_anchor(code, desc):
    if FALSE_FRIEND.match(code): return False
    d = desc.upper()
    if code.startswith('790-70'): return True
    if not code.startswith('714'): return False
    if code.startswith(('714-01','714-16')):
        return bool(re.search(r'LIGHTING', d))       # structural / navigational lighting lumps only
    return bool(LIGHT_ANCHOR.search(desc)) or code.startswith(('714-08','714-09','714-71','714-74','714-75','714-14'))

def is_shared(code, desc):
    if FALSE_FRIEND.match(code): return False
    d = desc.upper()
    if S790_WORK.match(code): return 'LIGHT' in d    # 790-36 transfer-light only
    if code.startswith('714') and not is_anchor(code, desc): return True
    return False

def div_of(county):
    c = county.split(',')[0].split('/')[0].strip().title()
    return CD.get(c, 0)

all_rows, lighting, shared = [], [], []
nbids = 0
low_total = 0.0
for c in sorted(P['contracts'], key=lambda x: x['call']):
    call = c['call']
    census = calls.get(call, {})
    # SOB names are canonical (proper case, every bidder); census is the cross-check
    bidders = sorted([[n, a] for n, a in c['totals'].items()], key=lambda x: x[1])
    cen_b = census.get('bidders') or []
    if cen_b and len(cen_b) != len(bidders):
        print(f'  CENSUS MISMATCH call {call}: ABR {len(cen_b)} bidders vs SOB {len(bidders)}')
    low_name, low_amt = bidders[0]
    nbids += len(bidders)
    low_total += low_amt
    a = awards.get(call, {'status': 'apparent'})
    county = c['county'].title()
    row = {'id': c['id'], 'call': call, 'tip': c['tip'], 'county': county, 'div': div_of(c['county']),
           'desc': c['desc'][:250], 'let': DATE, 'low': low_name, 'lowAmt': round(low_amt, 2),
           'bidders': [[n, round(v,2)] for n, v in bidders],
           'award': a.get('status', 'apparent')}
    all_rows.append(row)
    # classify
    anchors = [it for it in c['items'] if is_anchor(it['code'], it['desc'])]
    shr     = [it for it in c['items'] if is_shared(it['code'], it['desc'])]
    def lowprice(it): return it['ext'].get(low_name, it['ext'].get(low_name.upper(), 0.0)) or list(it['ext'].values())[0] if it['ext'] else 0.0
    # map extension by the low bidder: bidder keys in items are the SOB names
    def ext_low(it):
        for k, v in it['ext'].items():
            if k.strip().lower() == low_name.strip().lower(): return v
        # SOB names may differ in case/punct from ABR; fall back to min-total bidder of this contract
        sob_low = min(c['totals'], key=lambda k: c['totals'][k]) if c['totals'] else None
        return it['ext'].get(sob_low, 0.0)
    if anchors:
        items = []
        split = {'hardware': 0.0, 'infrastructure': 0.0, 'work': 0.0, 'lump': 0.0}
        splitHw = {'luminaire': 0.0, 'pole': 0.0, 'assembly': 0.0, 'control': 0.0}
        lumN = poleN = 0.0
        for it in anchors + shr:
            s = sub_of(it['code'], it['desc'])
            e = ext_low(it)
            if s in ('luminaire','pole','assembly','control'):
                split['hardware'] += e; splitHw[s] += e
                if s == 'luminaire': lumN += it['qty'] or 0
                if s == 'pole': poleN += it['qty'] or 0
                if s == 'assembly': lumN += it['qty'] or 0; poleN += it['qty'] or 0
            else:
                split[s] += e
            items.append({'line': '', 'code': it['code'], 'section': it['code'][:3], 'desc': it['desc'],
                          'qty': it['qty'], 'unit': it['unit'], 'prices': it['prices'], 'sub': s})
        l2 = round(sum(split.values()), 2)
        # bidder range on lighting items where every bidder priced
        rng = None
        try:
            names = set(c['totals'].keys())
            if all(set(it['ext'].keys()) == names for it in anchors + shr):
                sums = {n: sum(it['ext'][n] for it in anchors + shr) for n in names}
                rng = [round(min(sums.values()),2), round(max(sums.values()),2)]
        except Exception: pass
        cls = 'L1' if l2 >= 0.75 * low_amt else 'L2'
        lighting.append({'id': c['id'], 'tip': c['tip'], 'county': county, 'div': div_of(c['county']),
            'districtLabel': f"Region {div_of(c['county'])}", 'let': DATE, 'low': low_name,
            'lowAmt': round(low_amt,2), 'bidders': len(bidders), 'l2': l2,
            'product': round(split['hardware'],2),
            'split': {k: round(v,2) for k,v in split.items()},
            'nItems': len(items), 'rng': rng or [l2, l2], 'cls': cls, 'desc': c['desc'][:400],
            'share': round(l2/low_amt, 3) if low_amt else 0,
            'award': a.get('status','apparent'), 'reconciled': c['reconciled'], 'residual': c['residual'],
            'quantities': [], 'items': items,
            'splitHw': {k: round(v,2) for k,v in splitHw.items()}, 'lumN': lumN, 'poleN': poleN})
    elif shr:
        amt = round(sum(ext_low(it) for it in shr), 2)
        shared.append({'id': c['id'], 'tip': c['tip'], 'county': county, 'div': div_of(c['county']),
                       'let': DATE, 'low': low_name, 'amount': amt,
                       'what': 'Section 714 conduit, cable, pull boxes, control centers or electrical connections with no lighting-specific 714 item beside it'})

# census-only calls (in ABR, not in SOB)
sob_calls = {c['call'] for c in P['contracts']}
for call, cen in sorted(calls.items()):
    if call not in sob_calls:
        a = awards.get(call, {'status': 'apparent'})
        bd = cen.get('bidders', [])
        bd = sorted(bd, key=lambda x: x[1]) if bd else []
        all_rows.append({'id': cen['id'], 'call': call, 'tip': cen['tip'], 'county': cen['county'].title(),
                         'div': div_of(cen['county']), 'desc': '', 'let': DATE,
                         'low': bd[0][0] if bd else 'UNKNOWN', 'lowAmt': bd[0][1] if bd else 0,
                         'bidders': bd, 'award': a.get('status','apparent'), 'cls': 'UNKNOWN',
                         'note': 'in the Apparent Bid Results but not the Summary of Bids — TDOT omits rejected and pending calls from the Summary'})
        nbids += len(bd)

awarded_n = sum(1 for r in all_rows if r['award'] == 'awarded')
rejected_n = sum(1 for r in all_rows if r['award'] == 'rejected')
# gate: every apparent low (including census-only calls) must sum to the printed Letting Total
all_low = sum(r['lowAmt'] for r in all_rows)
if printed_letting_total is not None:
    assert abs(all_low - printed_letting_total) < 0.01, ('letting total mismatch', all_low, printed_letting_total)
    print(f'letting total gate: ${all_low:,.2f} == printed ${printed_letting_total:,.2f} RECONCILED')

letting = {'id': 'L' + ISO.replace('-','')[2:], 'date': DATE, 'iso': ISO, 'n': len(all_rows),
           'low': round(low_total,2), 'bids': nbids, 'awarded': awarded_n, 'rejected': rejected_n,
           'withdrawn': sum(1 for r in all_rows if r['award']=='withdrawn'),
           'awardArtifact': True, 'read': len(P['contracts'])}

# gates
for L in lighting:
    s = L['split']
    assert abs(sum(s.values()) - L['l2']) < 0.05, (L['id'], 'split != l2')
    hw = sum(L['splitHw'].values())
    assert abs(hw - s['hardware']) < 0.05, (L['id'], 'splitHw != hardware')

json.dump({'letting': letting, 'all': all_rows, 'lighting': lighting, 'shared': shared,
           'awards': awards}, open(out, 'w'), indent=1)
print(f"letting {DATE}: {letting['n']} calls, {nbids} bids, low ${low_total:,.2f}, "
      f"{awarded_n} awarded, {rejected_n} rejected; lighting {len(lighting)} "
      f"(${sum(l['l2'] for l in lighting):,.2f}), shared-only {len(shared)}")
for L in lighting:
    print(f"  {L['id']} {L['county']} {L['cls']} l2=${L['l2']:,.2f} hw=${L['split']['hardware']:,.2f} award={L['award']} low={L['low']}")
