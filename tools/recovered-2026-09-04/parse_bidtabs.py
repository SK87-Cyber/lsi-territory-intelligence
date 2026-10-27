#!/usr/bin/env python3
"""Bid-tab spreadsheet -> classified item rows.

NCDOT publishes each letting's tabulation as one flat sheet: one row per
(contract x item x bidder). Legacy .xls is converted to .xlsx first:

    soffice --headless --convert-to xlsx --outdir <dir> <file>.xls

Usage:  python3 parse_bidtabs.py <letting>.xlsx [--contract C205219] [--json out.json]

Columns (0-based, observed on L260616/L260721/L260723/L260818):
  0 letting  5 contract  6 wbs  7 tip  9 counties  12/13 description
  14 pay item code  15 spec section  16 line no  17 bidder rank
  19 item description  20 supplemental description  21 qty  22 unit
  24 bidder  25 bidder city  26 unit price  27 extended amount
"""
import sys, json, re
import openpyxl

C = dict(letting=0, contract=5, wbs=6, tip=7, counties=9, desc=12, desc2=13,
         code=14, section=15, line=16, rank=17, item=19, item2=20,
         qty=21, unit=22, bidder=24, city=25, unit_price=26, amount=27)

# Division 14 = Roadway Lighting. Two independent tests, both structural:
#   (1) the pay-item code family 50xx-52xx, which NCDOT reserves for lighting, and
#   (2) a spec section of 1400-1413.
# Keywords are NOT used to classify. "SUPPORT, BREAKAWAY STL BM" (S903) and
# "SUPPORTS, OMNI-DIRECTIONAL BREAKAWAY" (4360000000-N, signing) both read as
# lighting to a keyword rule and are not lighting.
DIV14_SECTION = re.compile(r'^14\d\d$')
DIV14_CODES = ('50', '51', '52')
# Temporary or non-roadway items inside the family, plus ITS hardware that borrows
# the word luminaire.
EXCLUDE = re.compile(r'PORTABLE LIGHTING|WZ PRESENCE LIGHTING|PORTABLE LIGHT TOWER|'
                     r'VIDEO SYSTEM|CCTV|CAMERA')
# Product: the hardware a manufacturer supplies, identified by pay-item code family
# rather than wording - NCDOT abbreviates ("LITE STD LUM" is a light standard with a
# luminaire) and description matching misses those.
#   5005/5010/5015 high mount standards   5020 portable drive unit
#   5030 high mount luminaire             5080 light standard with luminaire
#   5120 service pole                     5145 lighting control cabinet
#   5260 generic lighting, lump sum (smart node / luminaire)
# Everything else in the family is infrastructure or labour: foundations (5025, 5070),
# service lateral (5125), duct (5150, 5155, 5265), feeder (5175-5220), junction boxes
# (5240), and remove/relocate/reinstall work (5270).
PRODUCT_CODES = ('5005', '5010', '5015', '5020', '5030', '5080', '5120', '5145', '5260')

# Lighting-SPECIFIC items: they exist only because there is lighting. Standards,
# luminaires, drive units, control cabinets, their foundations, and conduit that
# names street lighting.
SPECIFIC_CODES = PRODUCT_CODES + ('5025', '5070', '5265', '5270')
# SHARED electrical: duct, feeder, junction boxes and service laterals sit in
# Division 14 but serve signals and ITS just as often as lighting. Per the
# dictionary rule they count only alongside a lighting-specific item - a contract
# carrying nothing but these is not a lighting contract.
SHARED_CODES = ('5125', '5150', '5155', '5175', '5180', '5205', '5210', '5215', '5220', '5240')


def is_specific(code, desc=''):
    # Items that name lighting outright anchor a contract just as a standard does.
    return code[:4] in SPECIFIC_CODES or bool(NAMED.search(desc))


def is_product(code):
    return code[:4] in PRODUCT_CODES


# A lighting item can be coded outside Division 14 entirely - NCDOT has priced
# "ELECTRICAL CONDUIT SYSTEM FOR LIGHTING" as a structures item and "REMOVE LUMINAIRE
# LIGHT AND STRUCTURE" as a signal item. Wording alone is unsafe as a classifier
# (BREAKAWAY sign supports), but an item that says LIGHTING or LUMINAIRE outright,
# and is not on the exclusion list, is a lighting item wherever it is coded.
NAMED = re.compile(r'\bLIGHTING\b|\bLUMINAIRE\b|\bLIGHT STANDARD\b|\bHIGH MOUNT\b|'
                   r'\bLITE STD\b|\bLIGHT POLE\b|\bSTREET LIGHT|\bLITE CNTRL\b')


def in_family(code, section):
    return code[:2] in DIV14_CODES or bool(DIV14_SECTION.match(section))


def is_lighting(code, section, desc):
    return in_family(code, section) or bool(NAMED.search(desc))


def rows(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    for r in ws.iter_rows(values_only=True):
        if r[C['contract']]:
            yield r
    wb.close()


def num(v):
    try:
        return float(str(v).replace(',', ''))
    except (TypeError, ValueError):
        return 0.0


def parse(path):
    contracts = {}
    for r in rows(path):
        cid = str(r[C['contract']]).strip()
        c = contracts.setdefault(cid, dict(
            id=cid, tip=str(r[C['tip']] or '').strip(), wbs=str(r[C['wbs']] or '').strip(),
            counties=str(r[C['counties']] or '').strip(),
            desc=' '.join(x for x in (r[C['desc']], r[C['desc2']]) if x).strip(),
            bidders={}, items=[]))
        bidder = str(r[C['bidder']] or '').strip()
        if not bidder:
            continue
        amt = num(r[C['amount']])
        b = c['bidders'].setdefault(bidder, dict(
            name=bidder, city=str(r[C['city']] or '').strip(),
            rank=r[C['rank']], total=0.0))
        b['total'] += amt
        section = str(r[C['section']] or '').strip()
        desc = ' '.join(x for x in (r[C['item']], r[C['item2']]) if x).upper().strip()
        c['items'].append(dict(
            line=r[C['line']], code=str(r[C['code']] or '').strip(), section=section,
            desc=desc, qty=num(r[C['qty']]), unit=str(r[C['unit']] or '').strip(),
            bidder=bidder, unit_price=num(r[C['unit_price']]), amount=amt))
    for c in contracts.values():
        c['low'] = min(c['bidders'].values(), key=lambda b: b['total']) if c['bidders'] else None
        classify(c)
    return contracts


def classify(c):
    """Tag each item, then class the contract. Nothing is inferred from the title."""
    lighting, excluded = [], []
    for it in c['items']:
        if not is_lighting(it['code'], it['section'], it['desc']):
            continue
        (excluded if (EXCLUDE.search(it['desc']) or it['section'] == '1413') else lighting).append(it)
    c['lighting'], c['excluded'] = lighting, excluded
    low = c['low']['name'] if c['low'] else None
    total = c['low']['total'] if c['low'] else 0.0
    mine = [i for i in lighting if i['bidder'] == low]
    # The anchor test: shared electrical only counts when a lighting-specific item
    # is present. Without one, the Division 14 dollars cannot be claimed as lighting.
    c['anchored'] = any(is_specific(i['code'], i['desc']) for i in mine)
    c['shared_only'] = bool(mine) and not c['anchored']
    if not c['anchored']:
        mine = []
    c['l2_low'] = round(sum(i['amount'] for i in mine), 2)
    c['has_device'] = any(is_product(i['code']) for i in mine)
    prod = [i for i in mine if is_product(i['code'])]
    c['product'] = round(sum(i['amount'] for i in prod), 2)
    c['product_items'] = [(i['line'], i['desc'], i['qty'], i['unit'], i['amount']) for i in prod]
    lowrows = [i for i in c['items'] if i['bidder'] == low]
    biggest_ls = max([i['amount'] for i in lowrows if i['unit'] == 'LS'], default=0.0)
    # One lump-sum line carrying most of the bid means the contract was never
    # itemised (design-build). Lighting is then invisible, not absent.
    lump = bool(total) and biggest_ls / total >= 0.5
    if mine:
        share = c['l2_low'] / total if total else 0
        # Any priced Division 14 item makes the contract L2. Whether that money buys
        # hardware or only conduit is the `product` figure's job, not the class's.
        c['cls'] = 'L1' if share >= 0.75 else 'L2'
    elif lump:
        c['cls'] = 'LUMP'
    else:
        c['cls'] = 'None'
    c['lump_share'] = round(biggest_ls / total, 4) if total else 0
    c['n_items'] = len(set(i['line'] for i in lowrows))
    by_bidder = {}
    for i in lighting:
        by_bidder[i['bidder']] = by_bidder.get(i['bidder'], 0) + i['amount']
    c['l2_range'] = (round(min(by_bidder.values()), 2), round(max(by_bidder.values()), 2)) if by_bidder else None
    c['n_bidders_itemised'] = len(c['bidders'])


def report(contracts, only=None):
    for cid in sorted(contracts):
        if only and cid != only:
            continue
        c = contracts[cid]
        low = c['low']
        print(f"\n{'='*78}\n{cid}  {c['tip']}  {c['counties']}  [{c['cls']}]")
        print(f"  {c['desc'][:100]}")
        print(f"  bidders {len(c['bidders'])} | low {low['name']} ${low['total']:,.2f}" if low else "  no bids")
        print(f"  items {c['n_items']} | lighting {len(set(i['line'] for i in c['lighting']))}"
              f" | excluded {len(set(i['line'] for i in c['excluded']))} | lump share {c['lump_share']:.0%}")
        if c['l2_low']:
            print(f"  L2 at low bidder: ${c['l2_low']:,.2f}   of which product ${c['product']:,.2f}"
                  f"   range across bidders {c['l2_range']}")
        for tag, group in (('LIGHTING', c['lighting']), ('EXCLUDED', c['excluded'])):
            seen = set()
            for i in group:
                if i['line'] in seen or (low and i['bidder'] != low['name']):
                    continue
                seen.add(i['line'])
                print(f"    {tag:8} {i['line']:>5} {i['code']:<14} §{i['section']:<5} {i['desc'][:46]:<46}"
                      f" {i['qty']:>10,.2f} {i['unit']:<4} @{i['unit_price']:>12,.2f} = {i['amount']:>13,.2f}")


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    only = sys.argv[sys.argv.index('--contract') + 1] if '--contract' in sys.argv else None
    cs = parse(args[0])
    report(cs, only)
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
        json.dump(cs, open(out, 'w'), indent=1, default=str)
        print(f"\nwrote {out}  ({len(cs)} contracts)")
