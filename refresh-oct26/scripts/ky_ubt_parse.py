#!/usr/bin/env python3
"""Parse a KYTC "Unit Bid Tabulations" (Bid Tabs of Awarded Projects) PDF.

Layout (documented from the prior read):
- Each call opens with "Call: NNN  Contid: YY-XXXX", a county/district line,
  a proposal-description line, the project-type/road line, "Number of Bidders N",
  N bidder lines (rank, vendor id, name, printed total), the engineer's estimate
  and the apparent-low line.
- Items print under a "Prop Line ... Bidder1..Bidder6" header. Items are
  description-keyed (no code column). Bidder columns print in blocks of up to
  6 bidders; for 7+ bidders the items repeat in continuation blocks - merged
  here by prop-line number.
- Rows with fewer prices than the block's bidders are ALTERNATES placed by
  column position (only when short; otherwise sequential - prices drift left
  of the printed headers).
- Bare "A" tokens beside prices are flags, not units or prices; they are
  dropped. The unit token must be two or more letters.

Output JSON: {"calls": [{call, contid, county, district, syp, project,
typeroad, nBidders, bidders: [{rank, vid, name, total}], estimate,
apparentLow, items: [{line, desc, qty, unit, prices: {bidderIdx: price},
alt}], printedTotals: {bidderIdx: total}}]}
"""
import json
import re
import sys

import pdfplumber

MONEY = re.compile(r'^-?[\d,]*\.\d{2}$')
PROPLINE = re.compile(r'^\d{4}$')


def to_num(tok):
    return float(tok.replace(',', ''))


def lines_of(page):
    words = page.extract_words(keep_blank_chars=False)
    words.sort(key=lambda w: (w['top'], w['x0']))
    out = []
    cur = []
    last_top = None
    for w in words:
        if last_top is None or w['top'] - last_top <= 2.5:
            cur.append(w)
        else:
            out.append(sorted(cur, key=lambda x: x['x0']))
            cur = [w]
        last_top = w['top']
    if cur:
        out.append(sorted(cur, key=lambda x: x['x0']))
    return out


def text_of(ws):
    return ' '.join(w['text'] for w in ws)


def parse(path):
    calls = []
    cur = None               # current call dict
    expect_bidders = 0
    header_cols = None       # x0 list of Bidder1..6 headers
    block = 0                # bidder block index (0-based): bidders block*6 .. block*6+5
    col_right = {}           # calibrated right edge per column (within block layout)

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for ws in lines_of(page):
                txt = text_of(ws)
                toks = [w['text'] for w in ws]

                if txt.startswith('KYTC DEPARTMENT') or txt.startswith('BID TABS') \
                        or txt.startswith('Date Run'):
                    continue

                if toks[0] == 'Call:':
                    cur = {'call': toks[1], 'contid': txt.split('Contid:')[1].strip().split()[0],
                           'county': None, 'district': None, 'syp': None, 'project': None,
                           'typeroad': '', 'nBidders': 0, 'bidders': [], 'estimate': None,
                           'apparentLow': None, 'items': [], 'printedTotals': {}}
                    calls.append(cur)
                    expect_bidders = 0
                    header_cols = None
                    block = 0
                    col_right = {}
                    continue
                if cur is None:
                    continue

                if toks[0] == 'County:':
                    m = re.match(r'County:\s*(.*?)\s+District:\s*(\S+)\s+Date Let:.*?(?:SYP:\s*(\S.*))?$', txt)
                    if m:
                        cur['county'] = re.sub(r'\s+COUNTY$', '', m.group(1).strip())
                        cur['district'] = int(m.group(2))
                        cur['syp'] = (m.group(3) or '').strip() or None
                    continue
                if txt.startswith('Proposal Description:'):
                    body = txt.split('Proposal Description:')[1]
                    cur['project'] = body.split('Length:')[0].split('Time:')[0].strip()
                    continue
                if txt.startswith('Number of Bidders'):
                    cur['nBidders'] = int(toks[-1])
                    expect_bidders = cur['nBidders']
                    continue
                if expect_bidders and cur['nBidders'] and not cur['items'] \
                        and toks[0].isdigit() and len(toks) >= 4 and MONEY.match(toks[-1]) \
                        and re.match(r'^\d{5}$', toks[1]):
                    cur['bidders'].append({'rank': int(toks[0]), 'vid': toks[1],
                                           'name': ' '.join(toks[2:-1]),
                                           'total': to_num(toks[-1])})
                    expect_bidders -= 1
                    continue
                if txt.startswith('ENGINEERS ESTIMATE'):
                    cur['estimate'] = to_num(toks[2])
                    continue
                if txt.startswith('Apparent Low Bidder'):
                    cur['apparentLow'] = txt.split('>')[1].strip() if '>' in txt else None
                    continue
                if toks[0] == 'Prop' and 'Bidder1' in toks:
                    header_cols = [w['x0'] for w in ws if w['text'].startswith('Bidder')]
                    continue
                # type/road line: between proposal-description and Number of Bidders
                if cur['project'] and not cur['nBidders'] and not txt.startswith('Number'):
                    cur['typeroad'] = (cur['typeroad'] + ' ' + txt).strip()
                    continue

                if header_cols is None:
                    continue

                # Total Bid line closes a block
                if txt.startswith('Total Bid'):
                    vals = [(w, to_num(w['text'])) for w in ws if MONEY.match(w['text'])]
                    nb_block = min(6, cur['nBidders'] - 6 * block)
                    if len(vals) == nb_block:
                        for i, (w, v) in enumerate(vals):
                            cur['printedTotals'][6 * block + i] = v
                    else:  # place by column
                        for w, v in vals:
                            cur['printedTotals'][6 * block + col_of(w, col_right)] = v
                    continue

                # Item row
                if PROPLINE.match(toks[0]) and ws[0]['x0'] < 60:
                    qty = unit = None
                    desc_ws, price_ws = [], []
                    for w in ws[1:]:
                        t = w['text']
                        if w['x0'] < 348:
                            desc_ws.append(t)
                        elif w['x0'] < 405 and qty is None and re.match(r'^[\d,]*\.\d+$', t):
                            qty = to_num(t)
                        elif w['x0'] < 450 and unit is None and re.match(r'^[A-Z]{2,}$', t):
                            unit = t  # unit must be 2+ letters: a bare "A" flag is not a unit
                        elif t == 'A':
                            continue
                        elif w['x0'] > 450 and (MONEY.match(t) or re.match(r'^\.\d+$', t)):
                            price_ws.append(w)
                    if qty is None or unit is None:
                        # not a clean item row; skip (guards stray lines)
                        continue
                    line_no = toks[0]
                    existing = next((it for it in cur['items'] if it['line'] == line_no), None)
                    if existing is not None and cur['items'] and line_no == cur['items'][0]['line'] \
                            and cur['nBidders'] > 6 * (block + 1):
                        # items repeat from the top -> continuation block for bidders 7+
                        block += 1
                        col_right = {}
                    nb_block = min(6, cur['nBidders'] - 6 * block)
                    prices = {}
                    vals = [(w, to_num(w['text'])) for w in price_ws]
                    if len(vals) == nb_block:        # sequential (prices drift left of headers)
                        for i, (w, v) in enumerate(vals):
                            prices[6 * block + i] = v
                            c = 6 * block + i
                            col_right.setdefault(c, []).append(w['x1'])
                    else:                            # short row = alternate, by column position
                        for w, v in vals:
                            prices[6 * block + col_of(w, col_right, block)] = v
                    alt = len(vals) < nb_block
                    if existing is not None:
                        existing['prices'].update(prices)
                        existing['alt'] = existing['alt'] or alt
                    else:
                        cur['items'].append({'line': line_no, 'desc': ' '.join(desc_ws),
                                             'qty': qty, 'unit': unit,
                                             'prices': prices, 'alt': alt})
                    continue
    # finalize: prices keys to int
    for c in calls:
        for it in c['items']:
            it['prices'] = {int(k): v for k, v in it['prices'].items()}
        c['printedTotals'] = {int(k): v for k, v in c['printedTotals'].items()}
    return calls


def col_of(w, col_right, block=0):
    """Nearest calibrated column for a price word (by right edge)."""
    cal = {c - 6 * block: sum(v) / len(v) for c, v in col_right.items()} if col_right else {}
    best, bestd = 0, 1e9
    for k in range(6):
        ref = cal.get(k, 534.0 + 81.0 * k)
        d = abs(w['x1'] - ref)
        if d < bestd:
            best, bestd = k, d
    return best


def main():
    path, out = sys.argv[1], sys.argv[2]
    calls = parse(path)
    with open(out, 'w') as f:
        json.dump({'calls': calls}, f, indent=1)
    for c in calls:
        print(f"call {c['call']} {c['contid']} {c['county']} D{c['district']} "
              f"bidders={c['nBidders']} items={len(c['items'])} "
              f"totals={len(c['printedTotals'])} est={c['estimate']}")


if __name__ == '__main__':
    main()
