#!/usr/bin/env python3
"""Parse ALDOT STIP statewide highway report (pdftotext -layout) for lighting scope.

Usage: python3 -I al_stip_parse_oct26.py <stip.txt> <out_candidates.json>
Emits every project block that mentions LIGHT in description, type-of-work,
or stray in-block text, with parsed phases, county, and TOTAL COST (thousands).
"""
import json, re, sys

DATE_HDR = re.compile(r'^\s*\d{1,2}/\d{1,2}/\d{4}\s+ALABAMA STATEWIDE TRANSPORTATION IMPROVEMENT PROGRAM\s+\d+ of \d+\s*$')
PLAN_HDR = re.compile(r'^\s*\d{1,2}/\d{1,2}/\d{4}-\d{1,2}/\d{1,2}/\d{4}\s+(STIP PLAN: .*?)\s+HIGHWAY PROJECTS - (.+?)\s*$')
ROUTE = re.compile(r'^Route\s+(\S+)\s+Project Description:\s*(.*)$')
PLEN = re.compile(r'^Project Length')
COLHDR = re.compile(r'^\s*Database ID\s')
SCOPES = ['PRELIMINARY ENGINEERING', 'FEDERAL MAINT CN', 'RIGHT OF WAY',
          'DESIGN BUILD', 'CONSTRUCTION', 'UTILITIES', 'SPECIAL']
PHASE = re.compile(r'^\s*(\d{9})\s+(.+?)\s+(\d{4})\s+\$([\d,]+)\s+\$([\d,]+)\s+\$([\d,]+)\s+\$([\d,]+)\s*$')
PRIOR = re.compile(r'^\s*\d{9}\s+(PE|RW|CN|UT|RR)\s+\d{4}')  # prior-phase memo lines
TCOST = re.compile(r'TOTAL COST:\s*\$([\d,]+)\s+\$([\d,]+)\s+\$([\d,]+)\s+\$([\d,]+)\s*$')

def money(s): return int(s.replace(',', ''))

def split_mid(mid):
    """mid = '<projnum>  <scope>  <type>'; return (projnum, scope, type)."""
    for sc in SCOPES:
        m = re.search(r'\s{2,}' + re.escape(sc) + r'(?:\s{2,}|\s(?=\S))', mid)
        if m:
            projnum = re.sub(r'\s+', ' ', mid[:m.start()].strip())
            typ = re.sub(r'\s+', ' ', mid[m.end():].strip())
            return projnum, sc, typ
    return None, None, None

def main(txt_path, out_path):
    plan = None
    county = None
    blocks = []
    cur = None
    unparsed = []

    with open(txt_path, encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.rstrip('\n')
            if DATE_HDR.match(line):
                continue
            m = PLAN_HDR.match(line)
            if m:
                if plan is None:
                    plan = m.group(1).strip()
                county = m.group(2).strip().title()
                continue
            m = ROUTE.match(line)
            if m:
                cur = {'route': m.group(1), 'desc': [m.group(2).strip()],
                       'county': county, 'phases': [], 'total': None,
                       'extra': [], 'in_desc': True}
                blocks.append(cur)
                continue
            if cur is None:
                continue
            if cur['in_desc']:
                if PLEN.match(line):
                    cur['in_desc'] = False
                    continue
                s = line.strip()
                if s and not COLHDR.match(line):
                    cur['desc'].append(s)
                continue
            if COLHDR.match(line) or PLEN.match(line) or not line.strip():
                continue
            m = TCOST.search(line)
            if m:
                cur['total'] = money(m.group(4))
                cur = None
                continue
            if PRIOR.match(line):
                continue
            m = PHASE.match(line)
            if m:
                projnum, sc, typ = split_mid(m.group(2))
                if projnum is not None:
                    cur['phases'].append({
                        'dbid': m.group(1), 'projnum': projnum, 'scope': sc,
                        'type': typ, 'fy': m.group(3),
                        'total': money(m.group(7))})
                    continue
            cur['extra'].append(line.strip())
            unparsed.append(line)

    out = {'plan': plan, 'totalProjects': len(blocks),
           'noTotal': sum(1 for b in blocks if b['total'] is None),
           'noPhases': sum(1 for b in blocks if not b['phases']),
           'phaseRows': sum(len(b['phases']) for b in blocks),
           'unparsedCount': len(unparsed),
           'unparsed': unparsed[:60],
           'hits': []}

    for b in blocks:
        desc = re.sub(r'\s+', ' ', ' '.join(b['desc'])).strip().upper()
        types = ' | '.join(p['type'].upper() for p in b['phases'])
        extra = ' '.join(b['extra']).upper()
        if 'LIGHT' in desc or 'LIGHT' in types or 'LIGHT' in extra:
            fys = sorted({p['fy'] for p in b['phases']})
            cfys = sorted({p['fy'] for p in b['phases']
                           if p['scope'] in ('CONSTRUCTION', 'FEDERAL MAINT CN', 'DESIGN BUILD')})
            out['hits'].append({
                'county': b['county'], 'route': b['route'], 'desc': desc,
                'types': types, 'extra': b['extra'],
                'projnums': sorted({p['projnum'] for p in b['phases']}),
                'scopes': sorted({p['scope'] for p in b['phases']}),
                'fys': fys, 'constructionFYs': cfys,
                'totalCost': b['total']})

    with open(out_path, 'w') as f:
        json.dump(out, f, indent=1)
    print('blocks:', len(blocks), 'hits:', len(out['hits']),
          'noTotal:', out['noTotal'], 'noPhases:', out['noPhases'],
          'phaseRows:', out['phaseRows'], 'unparsed:', out['unparsedCount'])

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
