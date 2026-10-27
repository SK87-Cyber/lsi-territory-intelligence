#!/usr/bin/env python3
"""Parse a KYTC Letting Results / Letting Day Results text dump (pdftotext
-layout output, or concatenated tesseract OCR pages for the vector-path
Sep 24 file) into the letting-day census: every call, every bidder, the
engineer's estimate.

Output: {"calls": [{call, contid, ptype, county, syp, project, road,
estimate, bids: [[name, amt], ...]}]}  (bids in printed order; the low
bidder is the minimum, not the first - KYTC does not sort the list).
"""
import json
import re
import sys

MONEY = re.compile(r'\$\s?([\d,]+\.\d{2})')


def to_num(tok):
    return float(tok.replace(',', '').replace(' ', ''))


def parse(paths):
    text = '\n'.join(open(p, encoding='utf-8', errors='replace').read() for p in paths)
    # OCR artifact: a space inside a decimal ("$2,490,780. 41")
    text = re.sub(r'(\$[\d,]+\.)\s+(\d{2})\b', r'\1\2', text)
    calls = []
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r'^CALL\s*#\s*:\s*(\d+)\s+ContID:\s*(\S+)\s+Project Type:\s*(.*)$', line)
        if m:
            cur = {'call': m.group(1), 'contid': m.group(2), 'ptype': m.group(3).strip(),
                   'county': None, 'syp': None, 'project': None, 'road': None,
                   'estimate': None, 'bids': []}
            calls.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r'^County:\s*(.*?)(?:\s+SYP:\s*(.*))?$', line)
        if m and line.startswith('County:'):
            cur['county'] = m.group(1).strip().title()
            cur['syp'] = (m.group(2) or '').strip() or None
            continue
        if line.startswith('Project ') and cur['project'] is None:
            cur['project'] = line[len('Project '):].strip()
            continue
        if line.startswith('Road:'):
            cur['road'] = line[len('Road:'):].strip()
            continue
        if line.replace("’", "'").upper().startswith("ENGINEER'S ESTIMATE"):
            m = MONEY.search(line)
            if m:
                cur['estimate'] = to_num(m.group(1))
            continue
        if re.match(r'^(Page \d+|KENTUCKY|DEPARTMENT|DIVISION|FRANKFORT|DATE|Letting)', line):
            continue
        m = re.match(r'^(.*?)\s+\$\s?([\d,]+\.\d{2})$', line)
        if m and cur['estimate'] is not None:
            cur['bids'].append([m.group(1).strip(), to_num(m.group(2))])
    return calls


def main():
    out = sys.argv[-1]
    calls = parse(sys.argv[1:-1])
    with open(out, 'w') as f:
        json.dump({'calls': calls}, f, indent=1)
    nb = sum(len(c['bids']) for c in calls)
    print(f"{len(calls)} calls, {nb} bids")
    for c in calls:
        low = min(c['bids'], key=lambda b: b[1]) if c['bids'] else None
        print(c['call'], c['contid'], c['county'], len(c['bids']), 'bids, est',
              c['estimate'], 'low:', low)


if __name__ == '__main__':
    main()
