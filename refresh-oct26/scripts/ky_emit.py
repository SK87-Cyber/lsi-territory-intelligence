#!/usr/bin/env python3
"""Build the KY delta/check deliverables from parsed UBT / BIQI / Letting
Results JSON (see ky_ubt_parse.py, ky_biqi_parse.py, ky_results_parse.py).

Usage:
  ky_emit.py delta  <ubt.json|-> <biqi.json|-> <lr.json> <KY_YEAR.json> \
                    <county_div.json> <iso-date> <cite> <out.json>
  ky_emit.py aug20  <ubt.json> <KY_YEAR.json> <out.json>
  ky_emit.py jun25  <ubt.json> <KY_YEAR.json> <out.json>

Rules (mirroring records/KY_YEAR.json and records/KY_DICT.json exactly):
- Award = presence in the Unit Bid Tabulations ("Bid Tabs of Awarded
  Projects"); a call in the Letting Results but not the tab stays apparent.
- Lighting-specific codes 04700-04725 (pole), 04740/04750 (infrastructure),
  04760 (pole) / 04761 (control), 04940/04942 (work), 24589ED/24749EC/20337ED
  (luminaire), 22939ND (work), 23161EN (infrastructure), 20410ED (work),
  23842EC/24831EC (pole). Shared 04780-04899 (infrastructure) counts only
  beside a lighting-specific item; otherwise it feeds the shared[] listing.
  Loop/piezo detection (04829, 04830, 04895; any LOOP/PIEZO desc) is signal
  work and is never counted.
- l2 = low bidder's lighting+counted-shared sum; product/split.hardware =
  pole+luminaire+control; rng = [min, max] across bidders; share = l2/lowAmt.
- Reconciliation per bidder: |sum(qty*price) - printed total| <=
  min(0.005 * sum(qty), 0.0002 * total) (cent-rounded unit prices vs finer
  accepted bids), else reconciled:false.
"""
import json
import re
import sys

LIGHT_SUB = {}
for i in range(0, 15):
    LIGHT_SUB[f'047{i:02d}'] = 'pole'          # 04700-04714 poles
for i in range(20, 26):
    LIGHT_SUB[f'047{i:02d}'] = 'pole'          # 04720-04725 brackets
LIGHT_SUB.update({'04740': 'infrastructure', '04750': 'infrastructure',
                  '04760': 'pole', '04761': 'control',
                  '04940': 'work', '04942': 'work',
                  '24589ED': 'luminaire', '24749EC': 'luminaire',
                  '20337ED': 'luminaire', '22939ND': 'work',
                  '23161EN': 'infrastructure', '20410ED': 'work',
                  '23842EC': 'pole', '24831EC': 'pole'})
LOOP_CODES = {'04829', '04830', '04895'}
LOOP_DESC = re.compile(r'LOOP|PIEZO')
# exact-description fallback for items with no Bid Item Quantity Index join,
# matching the prior read's assignments (KY_YEAR items with code "")
DESC_SUB = {
    'POLE BASE': 'infrastructure', 'TRANSFORMER BASE': 'infrastructure',
    'LIGHTING CONTROL EQUIPMENT': 'control',
    'POLE W/SECONDARY CONTROL EQUIP': 'pole',
    'LED LUMINAIRE': 'luminaire', 'HIGH MAST LED LUMINAIRE': 'luminaire',
    'DECORATIVE LUMINAIRE': 'luminaire', 'REMOVE LIGHTING': 'work',
    'REMOVE STORE & REINSTALL POLE': 'work', 'MAINTAIN LIGHTING': 'work',
    'INSTALL LUMINAIRE POLE': 'work', 'POLE BASE-HIGH MAST': 'infrastructure',
}
DESC_POLE = re.compile(r'^(POLE \d+ FT MTG HT|BRACKET \d+ FT)')
DESC_SHARED = re.compile(r'^(CONDUIT-|WIRE-NO\. (12|8|6|4)$|CABLE-NO\.|'
                         r'ELECTRICAL JUNCTION BOX|TRENCHING AND BACKFILLING|'
                         r'OPEN CUT ROADWAY|FUSED CONNECTOR KIT|ELECTRICAL SERVICE)')
WHAT = ('conduit, wire, cable, junction boxes or trenching (04792–04899) '
        'with no lighting item beside them')


def shared_code(code):
    return bool(re.match(r'^04(78\d|79\d|8\d\d)$', code)) and code not in LOOP_CODES


def join_codes(call_items, biqi_rows):
    """Attach item codes from the Bid Item Quantity Index (description-keyed
    tab; code + pre-let quantity per call). Two passes: desc+qty, then unique
    desc."""
    pool = list(biqi_rows)
    for it in call_items:
        it['code'] = ''
        d = ' '.join(it['desc'].split())
        hit = next((r for r in pool
                    if ' '.join(r['desc'].split()) == d and abs(r['qty'] - it['qty']) < 0.005), None)
        if hit:
            it['code'] = hit['code']
            pool.remove(hit)
    for it in call_items:
        if it['code']:
            continue
        d = ' '.join(it['desc'].split())
        cands = [r for r in pool if ' '.join(r['desc'].split()) == d]
        if len(cands) == 1:
            it['code'] = cands[0]['code']
            pool.remove(cands[0])


def classify_item(it):
    """-> (kind, sub): kind in light|shared|none."""
    code = it.get('code', '')
    desc = ' '.join(it['desc'].split())
    if code:
        if code in LIGHT_SUB:
            return 'light', LIGHT_SUB[code]
        if shared_code(code) and not LOOP_DESC.search(desc):
            return 'shared', 'infrastructure'
        return 'none', None
    # no code join: exact prior-read description families only
    if LOOP_DESC.search(desc):
        return 'none', None
    if desc in DESC_SUB:
        return 'light', DESC_SUB[desc]
    if DESC_POLE.match(desc):
        return 'light', 'pole'
    if DESC_SHARED.match(desc):
        return 'shared', 'infrastructure'
    return 'none', None


def reconcile(call):
    """Per-bidder residuals vs the printed totals. Returns (ok, maxres)."""
    sq = sum(it['qty'] for it in call['items'])
    ok, maxres = True, 0.0
    for i, b in enumerate(call['bidders']):
        s = sum(it['qty'] * it['prices'][i] for it in call['items'] if i in it['prices'])
        tol = max(min(0.005 * sq, 0.0002 * b['total']), 0.005)
        res = s - b['total']
        maxres = max(maxres, abs(res))
        if abs(res) > tol:
            ok = False
    return ok, maxres


def norm_prices(call):
    for it in call['items']:
        it['prices'] = {int(k): v for k, v in it['prices'].items()}
    call['printedTotals'] = {int(k): v for k, v in call['printedTotals'].items()}


def lighting_detail(call):
    """Classify a call's items; returns dict or None if no lighting-specific
    item (the anchor rule)."""
    marked = []
    has_light = False
    for it in call['items']:
        kind, sub = classify_item(it)
        if kind == 'light':
            has_light = True
        if kind in ('light', 'shared'):
            marked.append((it, kind, sub))
    if not has_light:
        shared_amt = round(sum(it['qty'] * it['prices'][0]
                               for it, k, _ in marked if 0 in it['prices']), 2)
        return None, (shared_amt if marked else None)
    names = [b['name'] for b in call['bidders']]
    sums = []
    for i in range(len(names)):
        sums.append(round(sum(it['qty'] * it['prices'][i]
                              for it, _, _ in marked if i in it['prices']), 2))
    split = {'hardware': 0.0, 'infrastructure': 0.0, 'work': 0.0}
    hw = {'luminaire': 0.0, 'pole': 0.0, 'assembly': 0, 'control': 0.0}
    lumN = poleN = brN = 0.0
    quantities = []
    items_out = []
    for it, kind, sub in marked:
        p0 = it['prices'].get(0)
        amt = round(it['qty'] * p0, 2) if p0 is not None else 0.0
        if sub in ('pole', 'luminaire', 'control'):
            split['hardware'] += amt
            if sub == 'control':
                hw['control'] += amt
            else:
                hw[sub] += amt
        else:
            split[sub] += amt
        if sub == 'luminaire':
            lumN += it['qty']
        if sub == 'pole':
            if it['desc'].startswith('POLE'):
                poleN += it['qty']
            elif it['desc'].startswith('BRACKET'):
                brN += it['qty']
        if kind == 'light' and it['unit'] == 'EACH':
            q = it['qty']
            quantities.append(f"{int(q) if q == int(q) else q} × {it['desc']}")
        items_out.append({'line': it['line'], 'code': it['code'], 'section': '716',
                          'desc': it['desc'], 'qty': it['qty'], 'unit': it['unit'],
                          'prices': {names[i]: v for i, v in sorted(it['prices'].items())},
                          'sub': sub})
    split = {k: round(v, 2) for k, v in split.items()}
    hw = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in hw.items()}
    if poleN == 0:
        poleN = brN   # brackets stand in when the contract sets no new poles
    return {'l2': sums[0], 'rng': [min(sums), max(sums)],
            'samePrice': len(set(sums)) == 1 and len(sums) > 1,
            'split': split, 'splitHw': hw, 'product': split['hardware'],
            'lumN': lumN, 'poleN': poleN, 'quantities': quantities,
            'items': items_out, 'sums': sums}, None


def county_fmt(raw):
    return re.sub(r'\s+', ' ', raw.strip()).title()


def div_of(county, district, county_div):
    first = county.split(',')[0].strip()
    first = re.sub(r'\s+Count(y|ies)$', '', first, flags=re.I)
    for k, v in county_div.items():
        if k.lower() == first.lower():
            return v
    return district


def main():
    mode = sys.argv[1]
    if mode == 'delta':
        (ubt_p, biqi_p, lr_p, year_p, cd_p, iso, cite, out_p) = sys.argv[2:10]
        county_div = json.load(open(cd_p))
        year = json.load(open(year_p))
        lr = json.load(open(lr_p))['calls']
        ubt = json.load(open(ubt_p))['calls'] if ubt_p != '-' else []
        biqi = json.load(open(biqi_p))['byCall'] if biqi_p != '-' else {}
        for c in ubt:
            norm_prices(c)
            join_codes(c['items'], biqi.get(c['call'], []))
        ubt_by_call = {c['call']: c for c in ubt}
        y, m, d = iso.split('-')
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
                  'Sep', 'Oct', 'Nov', 'Dec']
        let_label = f"{months[int(m)]} {int(d)}, {y}"
        all_rows, lighting_rows, shared_rows, estimates = [], [], [], {}
        maxres_let = 0.0
        n_read = 0
        for c in lr:
            tab = ubt_by_call.get(c['call'])
            cid = c['contid']
            estimates[cid] = c['estimate']
            county = county_fmt(c['county'])
            if tab:
                n_read += 1
                ok, maxres = reconcile(tab)
                maxres_let = max(maxres_let, maxres)
                county = county_fmt(tab['county'])
                div = div_of(county, tab['district'], county_div)
                tip = tab['project']
                bidders = [[b['name'], b['total']] for b in tab['bidders']]
                detail, shared_amt = lighting_detail(tab)
                cls = 'L2' if detail else 'None'
                row = {'id': cid, 'call': c['call'], 'tip': tip,
                       'reconciled': ok, 'county': county, 'div': div,
                       'desc': f"{tip} — {tab['typeroad']}",
                       'let': let_label, 'low': bidders[0][0],
                       'lowAmt': bidders[0][1], 'bidders': bidders,
                       'cls': cls, 'award': 'awarded'}
                all_rows.append(row)
                if detail:
                    note = ("Awarded — the contract appears in KYTC's Unit Bid "
                            f"Tabulations for the {let_label} letting, which the "
                            "Cabinet titles “Bid Tabs of Awarded Projects”; "
                            "every bidder's items sum to the printed total within "
                            f"${maxres:.2f} (cent-rounded unit prices) {{{cite}}}.")
                    lighting_rows.append({
                        'id': cid, 'tip': tip, 'county': county, 'div': div,
                        'districtLabel': f"District {div:02d}", 'let': let_label,
                        'low': bidders[0][0], 'lowAmt': bidders[0][1],
                        'bidders': len(bidders), 'l2': detail['l2'],
                        'product': detail['product'], 'split': detail['split'],
                        'nItems': len(tab['items']), 'rng': detail['rng'],
                        'cls': 'L2', 'desc': f"{tip} — {tab['typeroad']}",
                        'share': round(detail['l2'] / bidders[0][1], 3),
                        'award': 'awarded', 'reconciled': ok,
                        'residual': round(maxres, 2), 'awardDate': None,
                        'awardNote': note, 'quantities': detail['quantities'],
                        'items': detail['items'], 'samePrice': detail['samePrice'],
                        'splitHw': detail['splitHw'], 'lumN': detail['lumN'],
                        'poleN': detail['poleN']})
                elif shared_amt is not None:
                    shared_rows.append({'id': cid, 'tip': tip, 'county': county,
                                        'div': div, 'let': let_label,
                                        'low': bidders[0][0], 'amount': shared_amt,
                                        'what': WHAT})
            else:
                bids = sorted(c['bids'], key=lambda b: b[1])
                birows = biqi.get(c['call'], [])
                dist = birows[0]['district'] if birows else None
                div = div_of(county, dist, county_div)
                tip = (birows[0]['project'] if birows else c['project'])
                all_rows.append({'id': cid, 'call': c['call'], 'tip': tip,
                                 'reconciled': None, 'county': county, 'div': div,
                                 'desc': c['ptype'], 'let': let_label,
                                 'low': bids[0][0], 'lowAmt': bids[0][1],
                                 'bidders': bids, 'cls': 'UNKNOWN',
                                 'award': 'apparent'})
        letting = {'id': f"L{y[2:]}{m}{d}", 'date': let_label, 'iso': iso,
                   'n': len(lr), 'low': round(sum(r['lowAmt'] for r in all_rows), 2),
                   'bids': sum(len(r['bidders']) for r in all_rows),
                   'awarded': n_read, 'awardArtifact': bool(ubt),
                   'tc': cite, 'ac': cite if ubt else '',
                   'lr': True, 'ubt': bool(ubt), 'biqi': 1, 'read': n_read}
        delta = {'letting': letting, 'all': all_rows, 'lighting': lighting_rows,
                 'shared': shared_rows, 'estimates': estimates}
        if not ubt:
            # census-level only: award pending until the Unit Bid Tabulations post
            biqi_light = {}
            for call, rows in biqi.items():
                ls = [r for r in rows if r['code'] in LIGHT_SUB]
                if ls:
                    biqi_light[rows[0]['contract']] = {
                        'call': call, 'project': rows[0]['project'],
                        'district': rows[0]['district'],
                        'items': [{'code': r['code'], 'desc': r['desc'],
                                   'qty': r['qty'], 'unit': r['unit']} for r in ls],
                        'inLettingDayResults': any(c['call'] == call for c in lr)}
            delta['biqiLighting'] = biqi_light
        json.dump(delta, open(out_p, 'w'), indent=1)
        print(f"letting {let_label}: n={letting['n']} bids={letting['bids']} "
              f"low={letting['low']} read={n_read} lighting={len(lighting_rows)} "
              f"shared={len(shared_rows)} maxres={maxres_let:.2f}")

    elif mode in ('aug20', 'jun25'):
        ubt_p, year_p, out_p = sys.argv[2:5]
        label = 'Aug 20, 2026' if mode == 'aug20' else 'Jun 25, 2026'
        year = json.load(open(year_p))
        ubt = json.load(open(ubt_p))['calls']
        rec_rows = {r['id']: r for r in year['all'] if r['let'] == label}
        rec_light = {r['id']: r for r in year['lighting'] if r['let'] == label}
        rec_shared = {r['id']: r for r in year['shared'] if r['let'] == label}
        awarded, flips, mismatches = [], [], []
        cols_ok = cols_total = 0
        maxres_all = 0.0
        for c in ubt:
            norm_prices(c)
            # join codes from the record's own read of this letting (the staged
            # refresh carries no BIQI for it); desc+qty keyed
            for it in c['items']:
                it['code'] = ''
                it['_rec'] = False
            rl = rec_light.get(c['contid'])
            if rl:
                pool = list(rl['items'])
                for it in c['items']:
                    hit = next((r for r in pool if r['desc'] == it['desc']
                                and abs(r['qty'] - it['qty']) < 0.005), None)
                    if hit:
                        it['code'] = hit['code'] or ''
                        it['_rec'] = True
                        pool.remove(hit)
            ok, maxres = reconcile(c)
            maxres_all = max(maxres_all, abs(maxres))
            sq = sum(it['qty'] for it in c['items'])
            for i, b in enumerate(c['bidders']):
                s = sum(it['qty'] * it['prices'][i] for it in c['items'] if i in it['prices'])
                tol = max(min(0.005 * sq, 0.0002 * b['total']), 0.005)
                cols_total += 1
                if abs(s - b['total']) <= tol:
                    cols_ok += 1
            rec = rec_rows.get(c['contid'])
            entry = {'id': c['contid'], 'call': c['call'],
                     'tabLowBidder': c['bidders'][0]['name'],
                     'tabTotal': c['bidders'][0]['total'],
                     'reconciled': ok, 'maxResidual': round(maxres, 2)}
            if rec is None:
                entry['note'] = 'not in the year record'
            else:
                entry['recordAward'] = rec['award']
                entry['recordLowAmt'] = rec['lowAmt']
                name_ok = (rec['low'] == entry['tabLowBidder']
                           or entry['tabLowBidder'].startswith(rec['low'])
                           or rec['low'].startswith(entry['tabLowBidder']))
                entry['agree'] = (abs(rec['lowAmt'] - entry['tabTotal']) < 0.005
                                  and name_ok)
                if rec['award'] != 'awarded':
                    flips.append(c['contid'])
                if not entry['agree']:
                    mismatches.append(c['contid'])
            awarded.append(entry)
        in_tab = {c['contid'] for c in ubt}
        still_apparent = [rid for rid, r in rec_rows.items()
                          if r['award'] == 'apparent' and rid not in in_tab]
        # lighting reconciliation against the record
        light_check = []
        for cid, rl in rec_light.items():
            c = next((x for x in ubt if x['contid'] == cid), None)
            if c is None:
                light_check.append({'id': cid, 'inTab': False})
                continue
            # compare on the record's own item basis: the record's code joins
            # came from that letting's Bid Item Quantity Index (not staged in
            # this refresh), so items it excluded carry non-04780-04899 codes
            sub = dict(c, items=[it for it in c['items'] if it['_rec']])
            detail, _ = lighting_detail(sub)
            comp = {'id': cid, 'inTab': True,
                    'basis': "record's counted items, priced from the official tab",
                    'recordItemsMatchedInTab':
                        f"{len(sub['items'])} of {len(rec_light[cid]['items'])}"}
            if detail is None:
                comp['agree'] = False
                comp['note'] = 'no lighting found in official tab'
            else:
                for k in ('l2', 'product'):
                    comp[k] = {'record': rl[k], 'officialTab': detail[k],
                               'agree': abs(rl[k] - detail[k]) < 0.01}
                comp['split'] = {'record': rl['split'], 'officialTab': detail['split'],
                                 'agree': all(abs(rl['split'].get(k, 0) - detail['split'].get(k, 0)) < 0.01
                                              for k in set(rl['split']) | set(detail['split']))}
                comp['rng'] = {'record': rl['rng'], 'officialTab': detail['rng'],
                               'agree': all(abs(a - b) < 0.01 for a, b in zip(rl['rng'], detail['rng']))}
                comp['nLightItems'] = {'record': len(rl['items']),
                                       'officialTab': len(detail['items'])}
                comp['agree'] = all(comp[k]['agree'] for k in ('l2', 'product', 'split', 'rng'))
            light_check.append(comp)
        # shared rows check (desc families minus EN/NS-coded junction box TYPE A,
        # which sits outside 04780-04899 - verified against the record)
        shared_check = []
        for cid, rs in rec_shared.items():
            c = next((x for x in ubt if x['contid'] == cid), None)
            if c is None:
                shared_check.append({'id': cid, 'inTab': False})
                continue
            s = sum(it['qty'] * it['prices'][0] for it in c['items']
                    if DESC_SHARED.match(it['desc'])
                    and not LOOP_DESC.search(it['desc'])
                    and it['desc'] != 'ELECTRICAL JUNCTION BOX TYPE A'
                    and 0 in it['prices'])
            shared_check.append({'id': cid, 'recordAmount': rs['amount'],
                                 'officialTab': round(s, 2),
                                 'agree': abs(s - rs['amount']) < 0.01})
        out = {'letting': label,
               'source': "Unit Bid Tabulations (“Bid Tabs of Awarded Projects”), "
                         "posted on the KYTC letting page; presence in the tab is the award",
               'contractsInTab': len(ubt),
               'bidderColumnsReconciled': f"{cols_ok} of {cols_total}",
               'allReconciled': all(e['reconciled'] for e in awarded),
               'maxResidual': round(maxres_all, 2),
               'awarded': awarded, 'awardFlips': flips,
               'totalMismatches': mismatches,
               'stillApparentNotInTab': still_apparent,
               'lightingReconciliation': light_check,
               'sharedReconciliation': shared_check}
        json.dump(out, open(out_p, 'w'), indent=1)
        print(f"{label}: {len(ubt)} in tab, flips={flips}, mismatches={mismatches}, "
              f"apparent-still={still_apparent}, maxres={maxres_all:.2f}")
        for lc in light_check:
            print(' lighting', json.dumps(lc)[:300])
        for sc in shared_check:
            print(' shared', json.dumps(sc))


if __name__ == '__main__':
    main()
