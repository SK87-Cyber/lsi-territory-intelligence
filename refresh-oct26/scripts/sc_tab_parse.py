#!/usr/bin/env python3
"""Parse one SCDOT certified Tabulation of Bids PDF (Trns*port form) to JSON.

Usage: python3 -I sc_tab_parse.py <tab.pdf> [out.json]

Output: {meta, vendors, items, totals, reconcile}
 - vendors: [{rank, vid, name, total, pct}] in rank order (= column numbering)
 - items:   [{line, code, qty, lump, unit, desc, prices{rank: unit}, exts{rank: ext}}]
 - totals:  {rank: printed Contract Total}
 - reconcile: {rank: {sumExt, printed, ok}}  ok == to-the-cent match
"""
import json, re, subprocess, sys

UNIT_RE = re.compile(r'^[A-Z][A-Z0-9\.\'"/%]{0,5}$')
NUM_RE = re.compile(r'^-?[\d,]+\.\d+$')
ITEM_RE = re.compile(r'^\s{0,4}(\d{4}[A-Z]?)\s+([0-9A-Z]{7})\s+(.+)$')
RANK_RE = re.compile(r'^\s*(\d+)\s+(\S{4,8})\s{2,}(.+?)\s+\$([\d,]+\.\d{2})\s+([\d,\.]+)%\s*$')
RANK_CONT_RE = re.compile(r'^\s{30,}([A-Z0-9&.,\-\'()/ ]+?)\s*$')


def num(s):
    return float(s.replace(',', ''))


def pdftext(path):
    r = subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('pdftotext failed: ' + r.stderr[:200])
    return r.stdout


def parse(path):
    text = pdftext(path)
    pages = text.split('\f')
    meta = {}
    vendors = []
    items = {}      # (line, code) -> item dict
    order = []      # first-seen order of (line, code)
    totals = {}     # rank -> contract total
    warn = []
    last_group = None

    def metaval(line, key):
        m = re.search(re.escape(key) + r':\s*(.*?)(?:\s{3,}[A-Z][\w\(\)]*\(?s?\)?:|$)', line)
        return m.group(1).strip() if m else None

    for page in pages:
        lines = page.split('\n')
        joined = page
        is_rank = 'Vendor Ranking' in joined
        is_tab = 'Tabulation of Bids' in joined
        # --- header metadata (both page types carry it) ---
        for ln in lines[:14]:
            for key, mk in [('Contract ID', 'id'), ('Letting Date', 'letting'),
                            ('Call Order', 'call'), ('Counties', 'counties'),
                            ('District(s)', 'districts'), ('Project(s)', 'projects'),
                            ('Contract Description', 'desc'), ('PCN(s)', 'pcn')]:
                if key + ':' in ln:
                    v = metaval(ln, key)
                    if v and mk not in meta:
                        meta[mk] = v
        if is_rank:
            just_parsed = False
            for ln in lines:
                m = RANK_RE.match(ln)
                if m:
                    vendors.append({'rank': int(m.group(1)), 'vid': m.group(2),
                                    'name': re.sub(r'\s+', ' ', m.group(3).strip()),
                                    'total': num(m.group(4)), 'pct': float(m.group(5).replace(',', ''))})
                    just_parsed = True
                    continue
                if just_parsed and vendors:
                    mc = RANK_CONT_RE.match(ln)
                    if mc and 'CERTIFY' not in ln and 'Rank' not in ln:
                        vendors[-1]['name'] += ' ' + mc.group(1).strip()
                        continue
                if ln.strip():
                    just_parsed = False
            continue
        if not is_tab:
            continue
        # --- bidder column group: the (k) indices in the header block ---
        hdr_i = next((i for i, l in enumerate(lines) if 'Line No / Item ID' in l), None)
        alt_i = next((i for i, l in enumerate(lines) if 'Alt Set / Alt Member' in l), None)
        if hdr_i is None or alt_i is None:
            # overflow page (e.g. Contract Totals spilled past the last item page):
            # it carries no column header, so it continues the previous page's group
            if last_group and 'Contract Totals' in joined:
                group = last_group
                alt_i = -1
            else:
                continue
        else:
            group = []
            for l in lines[hdr_i:alt_i]:
                group += [int(x) for x in re.findall(r'\((\d+)\)', l)]
            group = sorted(set(group))
            if not group:
                warn.append('page with no bidder group header')
                continue
            last_group = group
        # --- walk body lines ---
        i = alt_i + 1
        cur = None  # current item key collecting desc
        first_seen_group = min(group) == 1
        while i < len(lines):
            ln = lines[i]
            s = ln.strip()
            if not s:
                i += 1
                continue
            if s.startswith('SECTION:') or s.startswith('Section Totals') \
               or s.startswith('Cost Plus Time') or s.startswith('( ) indicates') \
               or 'South Carolina Department' in s or 'Tabulation of Bids' in s:
                cur = None
                i += 1
                continue
            if s.startswith('Contract Totals'):
                amts = re.findall(r'\$([\d,]+\.\d{2})', s)
                if len(amts) != len(group):
                    warn.append(f'contract totals count {len(amts)} != group {len(group)}')
                for k, a in zip(group, amts):
                    totals[k] = num(a)
                cur = None
                i += 1
                continue
            m = ITEM_RE.match(ln)
            if m:
                lineno, code, rest = m.group(1), m.group(2), m.group(3)
                toks = rest.split()
                lump = False
                qty = None
                if toks and re.match(r'^\(\d+\)$', toks[0]):
                    lump = True
                    toks = toks[1:]
                elif toks and NUM_RE.match(toks[0]):
                    qty = num(toks[0])
                    toks = toks[1:]
                else:
                    warn.append(f'{lineno} {code}: unreadable qty token {toks[:1]}')
                    i += 1
                    continue
                nums = [t for t in toks if NUM_RE.match(t)]
                if len(nums) != len(toks) or len(nums) != 2 * len(group):
                    warn.append(f'{lineno} {code}: expected {2*len(group)} numbers, got {len(nums)}')
                key = (lineno, code)
                if key not in items:
                    items[key] = {'line': lineno, 'code': code, 'qty': qty, 'lump': lump,
                                  'unit': None, 'descLines': [], 'prices': {}, 'exts': {}}
                    order.append(key)
                it = items[key]
                for j, k in enumerate(group):
                    if 2 * j + 1 < len(nums):
                        it['prices'][k] = num(nums[2 * j])
                        it['exts'][k] = num(nums[2 * j + 1])
                cur = key if first_seen_group else None
                i += 1
                continue
            # description continuation line (only collected on first group pass)
            if cur is not None:
                it = items[cur]
                if not it['descLines'] and len(ln) - len(ln.rstrip()) >= 0:
                    # first desc line: unit token sits in its own column (>=2 spaces before)
                    mm = re.match(r'^(.*?)\s{2,}(\S+)\s*$', ln.rstrip())
                    if mm and UNIT_RE.match(mm.group(2)):
                        it['unit'] = mm.group(2)
                it['descLines'].append(re.sub(r'\s+', ' ', s))
            i += 1

    # finalize items
    out_items = []
    for key in order:
        it = items[key]
        desc = ' '.join(it.pop('descLines'))
        it['desc'] = desc
        out_items.append(it)

    # reconcile: sum of printed ext per bidder vs printed Contract Totals
    rec = {}
    ranks = sorted({k for it in out_items for k in it['exts']})
    for k in ranks:
        sm = round(sum(it['exts'].get(k, 0.0) for it in out_items), 2)
        pr = totals.get(k)
        rec[k] = {'sumExt': sm, 'printed': pr, 'ok': (pr is not None and abs(sm - pr) < 0.005)}
    # cross-check qty*unit vs printed ext (half-cent tolerance per item)
    for it in out_items:
        if it['lump'] or it['qty'] is None:
            continue
        for k, up in it['prices'].items():
            calc = round(it['qty'] * up, 2)
            if abs(calc - it['exts'].get(k, 0.0)) > 0.011:
                warn.append(f"{it['line']} {it['code']} rank{k}: qty*unit {calc} != ext {it['exts'].get(k)}")
    # ranking totals must equal tab contract totals
    for v in vendors:
        t = totals.get(v['rank'])
        if t is not None and abs(t - v['total']) > 0.005:
            warn.append(f"rank {v['rank']} ranking total {v['total']} != tab total {t}")

    return {'meta': meta, 'vendors': vendors, 'items': out_items,
            'totals': {str(k): v for k, v in totals.items()},
            'reconcile': {str(k): v for k, v in rec.items()},
            'reconciled': bool(rec) and all(r['ok'] for r in rec.values()),
            'warnings': warn}


if __name__ == '__main__':
    res = parse(sys.argv[1])
    out = json.dumps(res, indent=1)
    if len(sys.argv) > 2:
        open(sys.argv[2], 'w').write(out)
        print(f"{res['meta'].get('id')}: {len(res['items'])} items, "
              f"{len(res['vendors'])} vendors, reconciled={res['reconciled']}, "
              f"warnings={len(res['warnings'])}")
    else:
        print(out)
