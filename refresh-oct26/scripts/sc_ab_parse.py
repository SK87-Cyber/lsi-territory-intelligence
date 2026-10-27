#!/usr/bin/env python3
"""Parse an SCDOT Apparent Bids PDF (Bid Express capture) to JSON.

Usage: python3 -I sc_ab_parse.py <apparentbids.pdf> [out.json]

Output: {letting, calls: [{call, proposal, counties, desc, bidders: [[name, amt]...],
                           nBids, note}]}
"""
import json, re, subprocess, sys

CALL_RE = re.compile(r'^\s*Call order:\s*(\d+)\s+Proposal:\s*(\w+)\s*$')
BIDDER_RE = re.compile(r'^\s*(.+?)\s+(\w{4,8})\s+\$([\d,]+\.\d{2})\s*$')
NBIDS_RE = re.compile(r'^\s*\((\d+) apparent bids?\)\s*$')


def num(s):
    return float(s.replace(',', ''))


def parse(path):
    r = subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('pdftotext failed: ' + r.stderr[:200])
    lines = r.stdout.replace('\f', '\n').split('\n')

    letting = None
    for ln in lines[:30]:
        m = re.search(r'Apparent Bids for Letting of\s+(.+?)\s*$', ln)
        if m:
            letting = m.group(1).strip()
            break

    calls = []
    cur = None
    state = None
    for ln in lines:
        s = ln.strip()
        if 'Apparent Bids for Letting' in s or s.startswith('Letting ID') \
           or s.startswith('Cut-off Time') or s.startswith('Copyright') \
           or s == 'South Carolina Department of Transportation':
            continue
        m = CALL_RE.match(ln)
        if m:
            cur = {'call': m.group(1), 'proposal': m.group(2), 'counties': None,
                   'desc': [], 'bidders': [], 'nBids': None, 'note': None}
            calls.append(cur)
            state = 'head'
            continue
        if cur is None:
            continue
        if s.startswith('Counties:'):
            cur['counties'] = s[len('Counties:'):].strip()
            state = 'desc'
            continue
        if re.match(r'^\s*Bidder\s{2,}Bidder ID\s{2,}Total\s*$', ln):
            state = 'bidders'
            continue
        m = NBIDS_RE.match(ln)
        if m:
            cur['nBids'] = int(m.group(1))
            state = None
            continue
        if not s:
            continue
        if state == 'bidders':
            mb = BIDDER_RE.match(ln)
            if mb:
                cur['bidders'].append([re.sub(r'\s+', ' ', mb.group(1).strip()), num(mb.group(3))])
            continue
        if state == 'desc':
            # free text after the description is a status note (e.g. moved to a future letting)
            if re.match(r'^(Proposal|No bids|All bids)', s):
                cur['note'] = (cur['note'] + ' ' + s) if cur['note'] else s
            elif cur['note'] is None:
                cur['desc'].append(s)
            continue

    out = []
    warn = []
    for c in calls:
        c['desc'] = re.sub(r'\s+', ' ', ' '.join(c['desc'])).strip()
        if c['nBids'] is not None and c['nBids'] != len(c['bidders']):
            warn.append(f"call {c['call']} {c['proposal']}: printed {c['nBids']} bids, parsed {len(c['bidders'])}")
        # bidders should already be ascending by total; verify
        amts = [b[1] for b in c['bidders']]
        if amts != sorted(amts):
            warn.append(f"call {c['call']} {c['proposal']}: bidder amounts not ascending")
        out.append(c)
    return {'letting': letting, 'calls': out, 'warnings': warn}


if __name__ == '__main__':
    res = parse(sys.argv[1])
    s = json.dumps(res, indent=1)
    if len(sys.argv) > 2:
        open(sys.argv[2], 'w').write(s)
        wb = [c for c in res['calls'] if c['bidders']]
        print(f"{res['letting']}: {len(res['calls'])} calls, {len(wb)} with bids, "
              f"{sum(len(c['bidders']) for c in wb)} bids total, warnings={len(res['warnings'])}")
        for w in res['warnings']:
            print('  WARN:', w)
    else:
        print(s)
