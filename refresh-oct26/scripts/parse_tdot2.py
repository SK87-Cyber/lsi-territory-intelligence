#!/usr/bin/env python3
"""Parse a TDOT letting (Summary of Bids + Apparent Bid Results + Contract Awards)
into the universal contract record. Rewritten Oct 26, 2026 (kit parser not on hand);
layout rules follow the 3.16 read's documentation. Gate: every bidder's
sum(extensions) must reconcile to the printed TOTAL CONTRACT (cent rounding).

Usage: parse_tdot2.py <letting_dir> <yyyymmdd>   (expects <yyyymmdd>_SummaryOfBids.pdf etc.)
Writes <letting_dir>/parsed_<yyyymmdd>.json
"""
import sys, os, re, json, subprocess

d, ymd = sys.argv[1], sys.argv[2]

def txt(pdf, layout=True):
    out = pdf + ('.layout.txt' if layout else '.raw.txt')
    if not os.path.exists(out):
        subprocess.run(['pdftotext'] + (['-layout'] if layout else []) + [pdf, out], check=True)
    return open(out, encoding='utf-8', errors='replace').read()

MONEY = r'\$([\d,]+\.\d{2,4})'
def f(m): return float(m.replace(',', ''))

# ---------- Summary of Bids ----------
sob = txt(os.path.join(d, f'{ymd}_SummaryOfBids.pdf'))
lines = sob.split('\n')

# contract header forms seen Oct 2026: "X COUNTY (Contract No. CN… Call nnn)",
# "A, B, AND C (Contract No. …)", "COUNTIES A, B (Contract No. …)", a bare
# "(Contract No. …)" with the counties on the previous line, and a wrap before
# "No." — normalize by joining a line ending in "(Contract" with its successor.
HDR = re.compile(r'^(.*?)\(Contract\s+No\.\s+(\S+)\s+Call\s+(\d+)\)\s*$')
WRAP = re.compile(r'\(Contract(\s+No\.)?\s*$')
ITEM = re.compile(r'^(\d{3}[A-Z]?-\d{2}(?:\.\d{2})?)\s+(.+)$')
QTY  = re.compile(r'^\s+([\d,]+\.?\d*)\s+([A-Z][A-Za-z\.\$ ]{0,12})\s*$')
BIDROW = re.compile(r'^\s{2,}(.+?)\s+\$([\d,]+\.\d{4})\s+\$([\d,]+\.\d{2})\s*$')
TOTROW = re.compile(r'^(\S.*?)\s+\$([\d,]+\.\d{2})\s*$')

contracts = []
cur = None
i = 0
mode = None  # None | 'totals' | 'items'
pend_item = None
pend_hdr = None

def close(cur):
    if cur: contracts.append(cur)

while i < len(lines):
    ln = lines[i].rstrip()
    s = ln.strip()
    if WRAP.search(s) and i + 1 < len(lines):
        s = s + ' ' + lines[i+1].strip()
        i += 1
    m = HDR.match(s)
    if m:
        county, cid, call = m.group(1), m.group(2), m.group(3)
        county = re.sub(r'\s*COUNT(?:Y|IES)\s*$', '', county.strip())
        county = re.sub(r'^COUNTIES\s+', '', county).strip() or '(prev line)'
        if county == '(prev line)':
            # bare "(Contract No. …)" header — counties were on the previous non-empty line
            k = i - 1
            while k >= 0 and not lines[k].strip(): k -= 1
            county = re.sub(r'\s*COUNT(?:Y|IES)\s*$', '', lines[k].strip()) if k >= 0 else 'UNKNOWN'
        close(cur)
        cur = {'id': cid, 'call': call, 'county': county.title(), 'tip': '', 'desc': [],
               'totals': {}, 'items': [], 'ab': False, 'descdone': False}
        mode = 'head'; pend_item = None
        # next non-empty line = project number
        j = i + 1
        while j < len(lines) and not lines[j].strip(): j += 1
        if j < len(lines): cur['tip'] = lines[j].strip(); i = j
        i += 1
        continue
    if cur is None:
        i += 1; continue
    # page furniture
    if re.match(r'^\s*PAGE\s+\d+', ln) or re.match(r'^\s*CONTRACT\s+\S+\s*$', s) or 'UNIT PRICE' in ln and 'EXTENSION' in ln:
        i += 1; continue
    if s in ('STATE OF TENNESSEE', 'DEPARTMENT OF TRANSPORTATION', 'SUMMARY OF BIDS') or s.startswith('LETTING OF'):
        i += 1; continue
    if s == 'TOTAL CONTRACT' or s.startswith('TOTAL CONTRACT'):
        mode = 'totals'; i += 1; continue
    if s.startswith('COST(A)') or ('Cost(A)' in s):
        cur['ab'] = True; mode = 'totals'; i += 1; continue
    if s.endswith('CATEGORY'):
        mode = 'items'; i += 1; continue
    if mode == 'head':
        if s.startswith('PROJECT LENGTH') or s.startswith('COMPLETION TIME'):
            cur['descdone'] = True
        elif s and not cur['descdone']:
            cur['desc'].append(s)
        i += 1; continue
    if mode == 'totals':
        # A+B rows print cost, days, A+B — take the cost figure (first $)
        if s and '$' in s and 'SUBTOTAL' not in s.upper() and 'CATEGORY' not in s.upper():
            if cur['ab']:
                mab = re.match(r'^(\S.*?)\s+\$([\d,]+\.\d{2})\s+.*\$[\d,]+\.\d{2}\s*$', s)
                if mab:
                    nm = mab.group(1).strip()
                    cur['totals'][nm] = f(mab.group(2))
                    cur.setdefault('abTotals', {})[nm] = f(re.findall(r'\$([\d,]+\.\d{2})', s)[-1])
                    i += 1; continue
            mt = TOTROW.match(s)
            if mt and not ITEM.match(s):
                cur['totals'][mt.group(1).strip()] = f(mt.group(2))
        i += 1; continue
    if mode == 'items':
        mi = ITEM.match(s)
        if mi and not BIDROW.match(ln):
            pend_item = {'code': mi.group(1), 'desc': mi.group(2).strip(), 'qty': None, 'unit': '', 'prices': {}, 'ext': {}}
            cur['items'].append(pend_item)
            i += 1
            # qty line (may wrap)
            while i < len(lines):
                q = lines[i]
                mq = re.match(r'^\s+([\d,]+\.?\d*)\s+([A-Za-z\.\$][A-Za-z\.\$ ]{0,12})\s*$', q)
                if mq:
                    pend_item['qty'] = f(mq.group(1)); pend_item['unit'] = mq.group(2).strip()
                    i += 1
                    break
                elif q.strip() and not BIDROW.match(q) and '$' not in q:
                    # wrapped description or wrapped quantity continuation
                    pend_item['desc'] += ' ' + q.strip()
                    i += 1
                else:
                    break
            continue
        mb = BIDROW.match(ln)
        if mb and pend_item is not None:
            nm = mb.group(1).strip()
            pend_item['prices'][nm] = f(mb.group(2))
            pend_item['ext'][nm] = f(mb.group(3))
        i += 1; continue
    i += 1
close(cur)

# reconcile
recon = []
for c in contracts:
    sums = {}
    for it in c['items']:
        for nm, e in it['ext'].items():
            sums[nm] = sums.get(nm, 0.0) + e
    c['desc'] = ' '.join(c['desc'])
    ok = True; worst = 0.0
    for nm, tot in c['totals'].items():
        got = sums.get(nm)
        if got is None: ok = False; continue
        dmax = max(0.011, 0.006 * len(c['items']))
        delta = abs(got - tot)
        worst = max(worst, delta)
        if delta > dmax: ok = False
    c['reconciled'] = ok and bool(c['totals'])
    c['residual'] = round(worst, 4)
    recon.append((c['id'], len(c['items']), len(c['totals']), c['reconciled'], c['residual']))

# ---------- Apparent Bid Results (census) ----------
abr_pdf = None
for cand in (f'{ymd}_ApparentBidResults.pdf',):
    p = os.path.join(d, cand)
    if os.path.exists(p): abr_pdf = p
abr = txt(abr_pdf) if abr_pdf else ''

# ---------- Contract Awards ----------
ca_pdf = os.path.join(d, f'{ymd}_ContractAwards.pdf')
ca = txt(ca_pdf) if os.path.exists(ca_pdf) else ''

json.dump({'contracts': contracts, 'abr_text': abr, 'awards_text': ca},
          open(os.path.join(d, f'parsed_{ymd}.json'), 'w'))
print(f'{len(contracts)} contracts parsed')
bad = [r for r in recon if not r[3]]
print(f'reconciled: {len(recon)-len(bad)} of {len(recon)}')
for r in bad[:20]: print('  MISMATCH', r)
