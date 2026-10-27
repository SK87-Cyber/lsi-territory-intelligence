#!/usr/bin/env python3
"""Build SC delta JSONs from parsed tabs + apparent-bids census.

Usage: python3 -I sc_emit.py <tabs_dir> <ab0909.json> <ab1013.json> <SC_YEAR.json> \
                             <county_div_SC.json> <out_dir>

Writes: <out_dir>/delta_2026-09-09.json, <out_dir>/delta_2026-10-13.json,
        <out_dir>/aug11_tabs_update.json
"""
import glob, json, os, re, sys


def load(p):
    with open(p) as f:
        return json.load(f)


def z(x):
    """0 as int, else rounded float — matches SC_YEAR's zero style."""
    x = round(x, 2)
    return 0 if x == 0 else x


def classify(code, desc):
    """SC lighting dictionary: sub-class or None. Mirrors SC_YEAR / SC_DICT."""
    sec = code[:3]
    D = desc.upper()
    if sec == '658':
        if 'BARRICADE' in D:
            return None                      # 6584690 permanent barricade — false friend
        if 'DESIGN' in D and 'LIGHTING' in D:
            return 'lump'                    # 6581000 design-and-install system, lump per lit site
        if 'HIGH MAST' in D and ('LIGHT' in D or 'LT.' in D) and ('STANDARD' in D or 'STD' in D):
            return 'pole'                    # 6585015 100-ft high mast
        if 'LIGHT STD' in D or 'LIGHT STANDARD' in D or 'LT.STD' in D or 'LT STD' in D:
            return 'pole'                    # 6581145 35-ft standard
        if 'LUMINAIRE' in D:
            return 'luminaire'
        if 'DRIVE MOTOR' in D or 'LOWERING DEVICE' in D:
            return 'control'                 # 6585050 portable drive motor
        return None
    if sec == '665' and ('LT.STD' in D or 'LT STD' in D or 'LIGHT STD' in D or 'LIGHT STANDARD' in D):
        return 'pole'                        # light standards on signal jobs
    return None


HW = ('pole', 'luminaire', 'assembly', 'control')


def div_of(districts):
    m = re.search(r'District\s+(\d+)', districts or '')
    return int(m.group(1)) if m else 0


def fmt_date(iso):
    MON = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    y, m, d = iso.split('-')
    return f'{MON[int(m)]} {int(d)}, {int(y)}'


def qfmt(q):
    return str(int(q)) if q == int(q) else str(q)


def lighting_row(tab, let_label, cite, errors):
    """Full lighting row in the SC_YEAR lighting[] shape, or None."""
    m = tab['meta']
    vendors = sorted(tab['vendors'], key=lambda v: v['rank'])
    names = {v['rank']: v['name'] for v in vendors}
    lits = [it for it in tab['items'] if classify(it['code'], it['desc'])]
    if not lits:
        return None
    low = vendors[0]
    split = {'hardware': 0.0, 'infrastructure': 0.0, 'work': 0.0, 'lump': 0.0}
    splitHw = {'luminaire': 0.0, 'pole': 0.0, 'assembly': 0.0, 'control': 0.0}
    items, quantities = [], []
    lumN = poleN = 0.0
    per_rank = {v['rank']: 0.0 for v in vendors}
    for it in lits:
        sub = classify(it['code'], it['desc'])
        ext_low = it['exts'].get('1', it['exts'].get(1, 0.0))
        if sub == 'lump':
            split['lump'] += ext_low
        else:
            split['hardware'] += ext_low
            splitHw[sub] += ext_low
            if it['qty'] is not None:
                quantities.append(f"{qfmt(it['qty'])} × {it['desc']}")
                if sub == 'pole' and it['code'][:3] == '658':
                    poleN += it['qty']
                if sub == 'luminaire':
                    lumN += it['qty']
        for r, e in it['exts'].items():
            per_rank[int(r)] = per_rank.get(int(r), 0.0) + e
        items.append({
            'line': it['line'], 'code': it['code'], 'section': it['code'][:3],
            'desc': it['desc'], 'qty': it['qty'], 'unit': it['unit'],
            'prices': {names[int(r)]: p for r, p in it['prices'].items()},
            'sub': sub})
    l2 = round(split['lump'] + split['hardware'], 2)
    totals = sorted(round(v, 2) for v in per_rank.values())
    resid = round(l2 - sum(z(v) if isinstance(z(v), (int, float)) else v
                           for v in (split['lump'], split['hardware'])), 2)
    if resid != 0:
        errors.append(f"{m['id']}: split does not re-add to l2 (residual {resid})")
    hw_resid = round(split['hardware'] - sum(splitHw.values()), 2)
    if hw_resid != 0:
        errors.append(f"{m['id']}: splitHw does not re-add to hardware (residual {hw_resid})")
    return {
        'id': m['id'], 'tip': m.get('projects') or m.get('pcn') or m['id'],
        'county': m.get('counties', ''), 'div': div_of(m.get('districts')),
        'districtLabel': m.get('districts', ''), 'let': let_label,
        'low': low['name'], 'lowAmt': low['total'], 'bidders': len(vendors),
        'l2': l2, 'product': z(split['hardware']),
        'split': {k: z(v) for k, v in split.items()},
        'nItems': len(tab['items']), 'rng': [totals[0], totals[-1]],
        'cls': 'L2', 'desc': m.get('desc', ''), 'share': round(l2 / low['total'], 3),
        'award': 'apparent', 'reconciled': True, 'residual': 0.0,
        'awardDate': None,
        'awardNote': 'Apparent — SCDOT posts the certified tabulation about a month '
                     'after the letting but publishes no award list beside it, so nothing '
                     'here is confirmed awarded {' + cite + '}.',
        'quantities': quantities, 'items': items,
        'splitHw': {k: z(v) for k, v in splitHw.items()},
        'lumN': z(lumN) if lumN else 0, 'poleN': z(poleN) if poleN else 0}


def main(tabs_dir, ab09_p, ab13_p, year_p, cdiv_p, out_dir):
    ab09, ab13 = load(ab09_p), load(ab13_p)
    year, cdiv = load(year_p), load(cdiv_p)
    tabs = {}
    for p in sorted(glob.glob(os.path.join(tabs_dir, '*.json'))):
        t = load(p)
        tabs[t['meta']['id']] = t
    errors, notes = [], []

    # ---- letting membership from each tab's own printed letting date ----
    by_let = {}
    for pid, t in tabs.items():
        by_let.setdefault(t['meta']['letting'], []).append(pid)
    for k in by_let:
        by_let[k].sort()

    # ---- gate: every tab reconciled to the cent, or excluded with reason ----
    usable = {}
    for pid, t in tabs.items():
        if t['reconciled'] and not t['warnings']:
            usable[pid] = t
        else:
            errors.append(f'{pid}: EXCLUDED (reconciled={t["reconciled"]}, '
                          f'warnings={t["warnings"][:2]})')

    def all_row(c, let_label, tab):
        county = c['counties']
        if tab:
            m = tab['meta']
            row = {'id': c['proposal'], 'call': c['call'],
                   'tip': m.get('projects') or m.get('pcn') or c['proposal'],
                   'county': m.get('counties', county), 'div': div_of(m.get('districts')),
                   'desc': m.get('desc') or c['desc'], 'let': let_label,
                   'low': c['bidders'][0][0], 'lowAmt': c['bidders'][0][1],
                   'bidders': c['bidders'],
                   'cls': 'L2' if any(classify(i['code'], i['desc']) for i in tab['items']) else 'None',
                   'award': 'apparent', 'reconciled': True}
            # cross-check census low vs tab rank-1 total, to the cent
            v1 = sorted(tab['vendors'], key=lambda v: v['rank'])[0]
            if abs(v1['total'] - c['bidders'][0][1]) > 0.005:
                errors.append(f"{c['proposal']}: census low {c['bidders'][0][1]} != tab low {v1['total']}")
            if len(tab['vendors']) != len(c['bidders']):
                errors.append(f"{c['proposal']}: census {len(c['bidders'])} bidders != tab {len(tab['vendors'])}")
            return row
        first = county.split(',')[0].strip()
        return {'id': c['proposal'], 'call': c['call'], 'tip': c['proposal'],
                'county': county, 'div': cdiv.get(first, div_of(county)),
                'desc': c['desc'], 'let': let_label,
                'low': c['bidders'][0][0], 'lowAmt': c['bidders'][0][1],
                'bidders': c['bidders'], 'cls': 'UNKNOWN', 'award': 'apparent',
                'reconciled': None}

    def build_delta(ab, iso, tc, lid):
        label = fmt_date(iso)
        calls = [c for c in ab['calls'] if c['bidders']]
        moved = [c for c in ab['calls'] if not c['bidders']]
        rows, lrows, read = [], [], 0
        for c in sorted(calls, key=lambda c: c['call']):
            t = usable.get(c['proposal'])
            if t and t['meta']['letting'] != {'2026-09-09': 'September 09, 2026',
                                              '2026-10-13': 'October 13, 2026'}[iso]:
                errors.append(f"{c['proposal']}: tab letting {t['meta']['letting']} "
                              f'does not match census letting {label}')
                t = None
            rows.append(all_row(c, label, t))
            if t:
                read += 1
                lr = lighting_row(t, label, tc, errors)
                if lr:
                    lrows.append(lr)
        letting = {'id': lid, 'date': label, 'iso': iso, 'n': len(rows),
                   'low': round(sum(r['lowAmt'] for r in rows), 2),
                   'bids': sum(len(r['bidders']) for r in rows), 'awarded': 0,
                   'awardArtifact': False, 'tc': tc, 'ac': None, 'read': read,
                   'lr': True, 'ubt': read > 0}
        gap = []
        unread = [r['id'] for r in rows if not r['reconciled']]
        if unread:
            gap.append(f"{len(unread)} call(s) have no certified tabulation yet: {', '.join(unread)}.")
        for c in moved:
            gap.append(f"Call {c['call']} ({c['proposal']}, {c['desc']}) — {c['note']}; "
                       'listed in the Apparent Bids file with no bids, not counted.')
        return {'letting': letting, 'all': rows, 'lighting': lrows, 'shared': [],
                'gap': ' '.join(gap)}

    d09 = build_delta(ab09, '2026-09-09', 'SC-34', 'L260909')
    d13 = build_delta(ab13, '2026-10-13', 'SC-35', 'L261013')

    # ---- Aug 11 (and earlier) newly certified tabs: update package ----
    missing_lets = {'August 11, 2026': ('Aug 11, 2026', 'SC-33', 'L260811')}
    old_rows = {r['id']: r for r in year['all']}
    upd_all, upd_light, upd_ids = [], [], []
    for let_print, (label, tc, lid) in missing_lets.items():
        for pid in by_let.get(let_print, []):
            t = usable.get(pid)
            if not t:
                continue
            old = old_rows.get(pid)
            if old is None:
                errors.append(f'{pid}: certified tab for {label} but no census row in SC_YEAR')
                continue
            m = t['meta']
            v1 = sorted(t['vendors'], key=lambda v: v['rank'])[0]
            if abs(v1['total'] - old['lowAmt']) > 0.005:
                errors.append(f"{pid}: SC_YEAR low {old['lowAmt']} != tab low {v1['total']}")
            if len(t['vendors']) != len(old['bidders']):
                errors.append(f"{pid}: SC_YEAR {len(old['bidders'])} bidders != tab {len(t['vendors'])}")
            row = dict(old)
            row['tip'] = m.get('projects') or m.get('pcn') or pid
            row['county'] = m.get('counties', old['county'])
            row['div'] = div_of(m.get('districts'))
            row['desc'] = m.get('desc') or old['desc']
            row['cls'] = 'L2' if any(classify(i['code'], i['desc']) for i in t['items']) else 'None'
            row['reconciled'] = True
            upd_all.append(row)
            upd_ids.append(pid)
            lr = lighting_row(t, label, tc, errors)
            if lr:
                upd_light.append(lr)
    aug_let = next(L for L in year['lettings'] if L['id'] == 'L260811')
    new_aug = dict(aug_let)
    new_aug['read'] = aug_let['read'] + sum(1 for pid in upd_ids
                                            if old_rows[pid]['let'] == 'Aug 11, 2026')
    new_aug['ubt'] = True
    still = sorted(set(r['id'] for r in year['all'] if r['let'] == 'Aug 11, 2026') - set(upd_ids))
    notes.append(f"Aug 11, 2026: {len(upd_ids)} of {aug_let['n']} tabulations now certified "
                 f"(posted to the bidtabs library 2026-09-09); still missing: {', '.join(still)}.")
    notes.append('2973030 (Aug 11, no tab) was re-let as 2973031 in the Oct 13, 2026 letting; '
                 '4175570 (Jan 13, 2026, no tab) was re-let as 4175571 in the Oct 13, 2026 letting.')
    upd = {'letting': new_aug, 'proposals': upd_ids, 'all': upd_all,
           'lighting': upd_light, 'shared': [], 'notes': notes}

    os.makedirs(out_dir, exist_ok=True)
    for name, obj in [('delta_2026-09-09.json', d09), ('delta_2026-10-13.json', d13),
                      ('aug11_tabs_update.json', upd)]:
        with open(os.path.join(out_dir, name), 'w') as f:
            json.dump(obj, f, indent=1)
    print('tab letting membership:', {k: len(v) for k, v in by_let.items()})
    print('Sep 9 letting:', d09['letting'], '| lighting rows:', len(d09['lighting']),
          '| gap:', d09['gap'])
    print('Oct 13 letting:', d13['letting'], '| gap:', d13['gap'])
    print('Aug 11 update:', len(upd_all), 'rows, lighting', len(upd_light),
          '| new read:', new_aug['read'], 'of', new_aug['n'])
    if errors:
        print('ERRORS:')
        for e in errors:
            print('  ', e)
        sys.exit(1)
    print('GATES PASSED: all parsed tabs reconciled; splits re-add.')


if __name__ == '__main__':
    main(*sys.argv[1:7])
