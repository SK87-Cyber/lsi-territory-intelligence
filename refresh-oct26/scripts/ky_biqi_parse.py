#!/usr/bin/env python3
"""Parse a KYTC Bid Item Quantity Index (pdftotext -layout output).

Emits {"byCall": {call: [{code, desc, qty, unit}]}} - the five-digit (or
alphanumeric, e.g. 24589ED) item code plus pre-let quantity per call, used to
join codes onto the description-keyed Unit Bid Tabulations.
"""
import json
import re
import sys

ITEM = re.compile(r'^Item Code:\s*(\S+)\s+(.*?)\s{2,}Quantity\s+Unit\s*$')
ROW = re.compile(r'^Call:\s*(\d+)\s+Contract:\s*(\S+)\s+District:\s*(\d+)\s+(.*?)\s{2,}([\d,]*\.?\d+)\s+(\S+)\s*$')


def parse(path):
    by_call = {}
    code = desc = None
    for raw in open(path, encoding='utf-8', errors='replace'):
        line = raw.rstrip('\n').strip()
        m = ITEM.match(line)
        if m:
            code, desc = m.group(1), m.group(2).strip()
            continue
        m = ROW.match(line)
        if m and code is not None:
            call, contract, dist, proj, qty, unit = m.groups()
            by_call.setdefault(call, []).append({
                'code': code, 'desc': desc, 'qty': float(qty.replace(',', '')),
                'unit': unit, 'contract': contract, 'district': int(dist),
                'project': proj.strip()})
    return by_call


def main():
    path, out = sys.argv[1], sys.argv[2]
    by_call = parse(path)
    with open(out, 'w') as f:
        json.dump({'byCall': by_call}, f, indent=1)
    n = sum(len(v) for v in by_call.values())
    print(f"{len(by_call)} calls, {n} item rows")
    for c in sorted(by_call):
        print(c, by_call[c][0]['contract'], len(by_call[c]), 'rows')


if __name__ == '__main__':
    main()
