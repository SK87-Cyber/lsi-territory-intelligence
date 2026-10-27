#!/usr/bin/env python3
"""Emit AL/stip_update.json from parsed STIP lighting candidates.

Usage: python3 -I al_stip_emit_oct26.py <candidates.json> <PIPELINE_AL.json> \
                <county_div_AL.json> <out stip_update.json>
Merges duplicate blocks (same project printed twice), classifies hits,
carries kind/tip identity from the existing registry, and diffs against it.
"""
import json, re, sys

FALSE_FRIENDS = ['LIGHTWOOD', 'CAUTION LIGHT', 'DAYLIGHT', 'LIGHT DUTY',
                 'LIGHTWEIGHT', 'FLIGHT', 'SLIGHT', 'TWILIGHT', 'LIGHTHOUSE']
# kind for projects not in the Sep 1 registry (reviewed by hand)
NEW_KIND = {
    'STPHV 4524 ()': 'component',   # addl lanes incl streetlights
    'TAPNU TA27 (913)': 'component',  # sidewalk + pedestrian lighting
}
NEW_NOTE = {
    'STPHV 4524 ()': 'STIP table programs PE/RW FY27 only; UT FY29/CN FY30 per phase memo',
}

def norm(s): return re.sub(r'\s+', ' ', s).strip()

def clean_desc(s):
    s = norm(s)
    s = re.sub(r'([A-Z0-9])- (\d)', r'\1-\2', s)  # fix hyphen line-wrap "SR- 261"
    return s

def trim(s, n=200):
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'

def is_rr(h):
    d = h['desc']
    if any(p.startswith(('RHPD', 'RHCH')) for p in h['projnums']):
        return True
    return 'RAILROAD CROSSING' in d or 'RR XING' in d or 'RR CROSSING' in d

def only_false_friends(h):
    t = h['desc'] + ' ' + h['types'] + ' ' + ' '.join(h['extra'])
    for w in FALSE_FRIENDS:
        t = t.replace(w, '')
    return 'LIGHT' not in t

def year_str(fys):
    fys = sorted(fys)
    if not fys:
        return ''
    return fys[0] if fys[0] == fys[-1] else fys[0] + '–' + fys[-1]

def main(cand_p, pipe_p, cmap_p, out_p):
    cand = json.load(open(cand_p))
    pipeline = json.load(open(pipe_p))
    cmap = json.load(open(cmap_p))

    rr = other = 0
    road = []
    for h in cand['hits']:
        if is_rr(h):
            rr += 1
        elif only_false_friends(h):
            other += 1
        else:
            road.append(h)

    # merge duplicate blocks: same (county, cleaned description)
    merged = {}
    for h in road:
        key = (h['county'], clean_desc(h['desc']))
        m = merged.get(key)
        if m is None:
            h = dict(h)
            h['desc'] = clean_desc(h['desc'])
            h['totalCost'] = h['totalCost'] or 0
            h['blocks'] = 1
            merged[key] = h
        else:
            m['totalCost'] += h['totalCost'] or 0
            m['fys'] = sorted(set(m['fys']) | set(h['fys']))
            m['constructionFYs'] = sorted(set(m['constructionFYs']) | set(h['constructionFYs']))
            m['projnums'] = sorted(set(m['projnums']) | set(h['projnums']))
            m['blocks'] += 1
            if m['route'] in ('NA', 'CR-NA') and h['route'] not in ('NA', 'CR-NA'):
                m['route'] = h['route']

    # match to existing registry by project number (exact or prefix)
    def match_existing(projnums):
        for ex in pipeline:
            exn = norm(ex['tip'])
            for p in projnums:
                pn = norm(p)
                if pn == exn or exn.startswith(pn + ' ') or exn.startswith(pn + '('):
                    return ex
        return None

    rows, matched_tips, newprojs = [], set(), []
    for h in merged.values():
        ex = match_existing(h['projnums'])
        if ex:
            tip, kind = ex['tip'], ex['kind']
            matched_tips.add(tip)
            note = ''
            if len(h['projnums']) > 1 and any(norm(p) not in norm(tip) and norm(tip) not in norm(p)
                                              for p in h['projnums']):
                note = 'block also funds: ' + ', '.join(
                    p for p in h['projnums'] if norm(p) != norm(tip))
        else:
            tip = h['projnums'][0] if h['projnums'] else ''
            kind = NEW_KIND.get(tip)
            if kind is None:
                raise SystemExit('UNCLASSIFIED NEW PROJECT: %r %r' % (tip, h['desc'][:80]))
            note = NEW_NOTE.get(tip, '')
            newprojs.append(tip)
        cfys = h['constructionFYs']
        if cfys:
            stage = 'Construction FY ' + max(cfys)
        elif tip in NEW_NOTE:
            stage = 'Construction FY 2030'
        else:
            stage = 'Programmed FY ' + max(h['fys'])
        rows.append({
            'tip': tip, 'wbs': 'FY 2024–2027 STIP', 'county': h['county'],
            'div': cmap.get(h['county'], 0), 'route': h['route'],
            'cost': h['totalCost'] * 1000, 'year': year_str(h['fys']),
            'kind': kind, 'src': 'stip', 'cls': 'L4',
            'what': trim(h['desc']), 'stage': stage, 'note': note})

    rows.sort(key=lambda r: (r['kind'] != 'pure', -r['cost']))
    gone = [ex['tip'] for ex in pipeline if ex['tip'] not in matched_tips]

    out = {
        'printDate': '2026-10-26',
        'plan': cand['plan'],
        'totalProjects': cand['totalProjects'],
        'lighting': rows,
        'excludedRRCrossings': rr,
        'excludedOther': other,
        'diff': {'kept': len(matched_tips), 'gone': gone, 'new': sorted(newprojs)},
    }
    with open(out_p, 'w') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    pure = [r for r in rows if r['kind'] == 'pure']
    comp = [r for r in rows if r['kind'] == 'component']
    print('blocks naming LIGHT:', len(cand['hits']),
          '| distinct projects:', len(merged) + rr + other)
    print('roadway rows:', len(rows), '= pure', len(pure), '+ component', len(comp),
          '| RR excluded:', rr, '| other excluded:', other)
    print('pure-scope cost: $%.2fM' % (sum(r['cost'] for r in pure) / 1e6))
    print('kept:', len(matched_tips), 'gone:', gone, 'new:', sorted(newprojs))

if __name__ == '__main__':
    main(*sys.argv[1:5])
