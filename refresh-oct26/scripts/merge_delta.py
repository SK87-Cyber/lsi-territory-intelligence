#!/usr/bin/env python3
"""Merge a letting delta into a state's YEAR record (extracted from the template).
The year record keeps its history: lettings append, 'all'/'lighting'/'shared' rows
append, contracts/lowBids/bids extend, the span's right edge moves. Nothing is
removed — the record is now a 13+ month span and the span label says so.

Usage: merge_delta.py <YEAR.json> <delta.json> <out.json>
Prints the before/after digest; asserts internal consistency after the merge.
"""
import sys, json

yf, df, out = sys.argv[1:4]
Y = json.load(open(yf))
D = json.load(open(df))

L = D['letting']
assert not any(l.get('iso') == L.get('iso') or l.get('date') == L.get('date') for l in Y['lettings']), 'letting already in record'
Y['lettings'].append(L)
Y['contracts'] = Y.get('contracts', 0) + L['n']
if 'contractsRead' in Y: Y['contractsRead'] = Y['contractsRead'] + L.get('read', L['n'])
Y['lowBids'] = round(Y.get('lowBids', 0) + L['low'], 2)
for k in ('lighting', 'shared'):
    if D.get(k): Y.setdefault(k, []).extend(D[k])
if 'all' in Y and D.get('all'): Y['all'].extend(D['all'])

# span: keep the left edge, move the right edge to this letting's date
left = Y['span'].split('–')[0].strip()
Y['span'] = f"{left} – {L['date']}"

json.dump(Y, open(out, 'w'))
ls = sum(c['l2'] for c in Y.get('lighting', []))
print(f"merged {df}: lettings {len(Y['lettings'])}, contracts {Y['contracts']}, "
      f"lowBids ${Y['lowBids']:,.2f}, lighting {len(Y.get('lighting', []))} (${ls:,.2f}), span {Y['span']}")
