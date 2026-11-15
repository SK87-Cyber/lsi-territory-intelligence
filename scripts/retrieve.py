"""Scheduled retrieval: list what each public source has posted and record what is new or changed.

It reads listings only (file names, notice titles, agreement headers, payment totals). It does not
open bid documents, mark anything verified, or change a research record. Each new item is a lead
for a reviewed research update. Detail is stored in the private database; the public run summary
shows counts only.
"""
from datetime import datetime, timezone
import html
import json
import re
import sys
import time
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError

HOSTS = {'connect.ncdot.gov', 'www.dot.state.al.us', 'secure2.kentucky.gov', 'myfiles.dot.ga.gov', 'www.tdot.tn.gov'}
UA = 'LSI-Retrieval/1.0 (weekly public-listing check; contact via github.com/SK87-Cyber/lsi-territory-intelligence)'
LIGHTING = re.compile(r'light(?!\s*rail)|luminaire|high\s*-?\s*mast|illuminat|electrical maintenance', re.I)
MAX_BYTES = 12_000_000

def is_lighting(text):
    return bool(LIGHTING.search(text or ''))

def fetch(url, method='GET', body=None, headers=None, pause=1.0):
    if urlsplit(url).scheme != 'https' or urlsplit(url).hostname not in HOSTS:
        raise ValueError('Host not on the retrieval list')
    req = Request(url, method=method, data=body, headers={'User-Agent': UA, 'Accept': 'text/html,application/json,*/*;q=0.8', **(headers or {})})
    time.sleep(pause)
    with urlopen(req, timeout=60) as r:
        return r.status, dict(r.headers), (b'' if method == 'HEAD' else r.read(MAX_BYTES))

# ---- parsers (pure; tested with fixtures) ----
def cells(row):
    return [' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', c)).split()) for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.S | re.I)]

def parse_al_agreements(page):
    out = []
    for row in re.findall(r'<tr[^>]*>(.*?)</tr>', page, re.S | re.I):
        c, link = cells(row), re.search(r'href="([^"]+)"', row)
        m = re.search(r'Agreement #\s*([\w-]+)', c[0]) if len(c) >= 3 else None
        if m:
            out.append((m.group(1), {'state': 'AL', 'title': re.sub(r'^Contract Name - Vendor\s*', '', c[1]), 'expires': c[2],
                                     'url': 'https://www.dot.state.al.us/business/' + link.group(1) if link else None}))
    return out

def parse_al_notices(page):
    out = []
    for row in re.findall(r'<tr[^>]*>(.*?)</tr>', page, re.S | re.I):
        c, link = cells(row), re.search(r'href="(procurements/[^"]+)"', row)
        if len(c) >= 5 and link:
            strip = lambda label, v: re.sub('^' + label + r'\s*', '', v)
            out.append((link.group(1).split('/')[1], {'state': 'AL', 'status': strip('Status', c[0]), 'title': strip('Notice of Need', c[1]),
                        'region': strip('Region/Bureau', c[2]), 'posted': strip('Posted', c[3]), 'closes': strip('Expiration', c[4]),
                        'url': 'https://www.dot.state.al.us/business/' + link.group(1)}))
    return out

def parse_ga_listing(page):
    """One item per contract: how many pay estimates are posted and the newest one."""
    found = {}
    for day, _size, cid, num in re.findall(r'(\d+/\d+/\d+)\s+\d+:\d+ [AP]M\s+(\d+) <A HREF="/SmallEstimate/([^"]+?)\.(\d+)\.PDF"', page, re.I):
        cur = found.setdefault(cid, {'state': 'GA', 'estimates': 0, 'latest': 0, 'latest_posted': day})
        cur['estimates'] += 1
        if int(num) >= cur['latest']:
            cur['latest'], cur['latest_posted'] = int(num), day
    for cid, p in found.items():
        p['url'] = f"https://myfiles.dot.ga.gov/SmallEstimate/{quote(cid)}.{p['latest']:04d}.PDF"
    return sorted(found.items())

# ---- watchers ----
def nc_lettings(_conn):
    api = "https://connect.ncdot.gov/letting/_api/web/lists/getbytitle('{}')/items?$select=FileRef,FSObjType,Created&$top=300&$orderby=Created%20desc"
    out = []
    for lib in [f'Division {n} Letting' for n in range(1, 15)] + ['Central Letting', '12 Month Tentative Letting Library']:
        _, _, raw = fetch(api.format(quote(lib)), headers={'Accept': 'application/json;odata=nometadata'})
        for it in json.loads(raw)['value']:
            if it['FSObjType'] == 0:
                ref = it['FileRef']
                out.append((ref, {'state': 'NC', 'library': lib, 'letting': ref.split('/')[-2], 'title': ref.split('/')[-1],
                                  'posted': it['Created'][:10], 'url': 'https://connect.ncdot.gov' + quote(ref)}))
    return out

def al_procurement(_conn):
    base = 'https://www.dot.state.al.us/business/'
    return ([('agreement:' + k, p) for k, p in parse_al_agreements(fetch(base + 'TITB_Awarded_MA_Contracts.html')[2].decode('utf-8', 'replace'))] +
            [('notice:' + k, p) for k, p in parse_al_notices(fetch(base + 'Procurementsupplies.html')[2].decode('utf-8', 'replace'))])

KY_WATCHED = re.compile(r'ELLIOT|WESCO|ARROW ELECTRIC|FONROCHE|GRAYBAR', re.I)
def ky_contracts(_conn):
    """Every open Transportation agreement. The service lists vendor and term but not the title, so
    lighting is flagged by vendor; any other new agreement still appears as new."""
    out, start = [], 0
    while True:
        body = json.dumps({'wildCardText': None, 'beginAmount': None, 'endAmount': None, 'beginDate': None, 'endDate': None, 'sortOrder': None,
                           'judicialBranch': None, 'exectutiveBranch': None, 'departmentCodes': ['605'], 'categoryCodes': None,
                           'sortExpression': None, 'maxRows': 3000, 'startIndex': start}).encode()
        rows = json.loads(fetch('https://secure2.kentucky.gov/TransparencyWebApi/v1/Contract/GetContracts', 'POST', body, {'Content-Type': 'application/json'})[2]).get('contractArray') or []
        for c in rows:
            watched = bool(KY_WATCHED.search(c['legalName'] or ''))
            out.append((f"{c['documentCode']} {c['documentDepartmentCode']} {c['documentID']}",
                        {'state': 'KY', 'title': ('Lighting or electrical vendor: ' if watched else 'Agreement with ') + (c['legalName'] or ''),
                         'begins': (c.get('effectiveBeginDate') or '')[:10], 'expires': (c.get('effectiveEndDate') or '')[:10],
                         'procurement': c.get('procurementTypeName'),
                         'url': f"https://secure2.kentucky.gov/TransparencyWebApi/v1/Contract/ContractPDF?documentId={c['documentID']}&docId={c['pdfDocumentCode']}"}))
        if len(rows) < 3000 or start > 20000: break
        start += 3000
    return out

KY_VENDORS = ['DAVIS H ELLIOT CONSTRUCTION COMPANY,  INC', 'WESCO DISTRIBUTION', 'Arrow Electric Co Inc', 'Fonroche Lighting America']
def ky_payments(_conn, today=None):
    today = today or datetime.now(timezone.utc)
    fy = today.year + (1 if today.month >= 7 else 0)
    out = []
    for year in (fy - 1, fy):
        for vendor in KY_VENDORS:
            url = ('https://secure2.kentucky.gov/TransparencyWebApi/v1/SpendingVendorDetail?requestYear=%d&branchCode=&cabinetCode=35&departmentCode=&classCode='
                   '&objectCode=&vendorName=%s&beginDate=&endDate=&maxReturnRows=5000&startingIndex=0') % (year, quote(vendor))
            rows = json.loads(fetch(url)[2]).get('spendingVendorDetails') or []
            out.append((f'{vendor.split(",")[0]} FY{year}', {'state': 'KY', 'title': f'Payments to lighting or electrical vendor {vendor.split(",")[0]}, FY{year}',
                        'payments': len(rows), 'total': round(sum(r['amount'] for r in rows), 2),
                        'latest': max((r['dateOfService'][:10] for r in rows), default=None), 'url': 'https://transparency.ky.gov/'}))
    return out

def ga_estimates(_conn):
    return parse_ga_listing(fetch('https://myfiles.dot.ga.gov/SmallEstimate/')[2].decode('latin-1'))

def tn_folders(cid):
    return ['2026 contracts', '2026 Contracts'] if cid.startswith('CN26') else [cid[:3] + ' Contracts']
def tn_payments(conn):
    out = []
    for (cid,) in conn.execute("select contract_id from lsi.contracts where state='TN' and identified_lighting_usd>0 order by 1").fetchall():
        payload = {'state': 'TN', 'title': f'Lighting contract {cid}: progress payment file', 'posted': None, 'size': None, 'url': None}
        for folder in tn_folders(cid):
            url = f'https://www.tdot.tn.gov/PublicDocuments/Construction/Progress_Payments/{quote(folder)}/{quote(cid)}.pdf'
            try:
                _, head, _ = fetch(url, 'HEAD')
                payload.update(posted=head.get('Last-Modified'), size=head.get('Content-Length'), url=url)
                break
            except HTTPError as exc:
                if exc.code != 404: raise
        out.append((cid, payload))
    return out

WATCHERS = {'nc-lettings': nc_lettings, 'al-procurement': al_procurement, 'ky-contracts': ky_contracts,
            'ky-payments': ky_payments, 'ga-pay-estimates': ga_estimates, 'tn-progress-payments': tn_payments}

# ---- storage ----
def record(conn, run_id, source, items):
    """First sight of a source is a baseline (no events). Afterwards: new and changed items become events."""
    from psycopg.types.json import Jsonb
    from database import payload_hash
    known = dict(conn.execute('select item_key,payload_hash from lsi.watch_items where source=%s', (source,)).fetchall())
    baseline, counts = not known, {'listed': len(items), 'new': 0, 'changed': 0, 'lighting': 0}
    for key, payload in items:
        digest, flag = payload_hash(payload), is_lighting(json.dumps(payload))
        before = known.get(key)
        if before == digest:
            conn.execute('update lsi.watch_items set last_seen_at=now() where source=%s and item_key=%s', (source, key))
            continue
        old = conn.execute('select payload from lsi.watch_items where source=%s and item_key=%s', (source, key)).fetchone() if before else None
        conn.execute('''insert into lsi.watch_items(source,item_key,payload,payload_hash,lighting) values(%s,%s,%s,%s,%s)
            on conflict(source,item_key) do update set payload=excluded.payload,payload_hash=excluded.payload_hash,lighting=excluded.lighting,last_seen_at=now()''',
                     (source, key, Jsonb(payload), digest, flag))
        if baseline: continue
        action = 'changed' if before else 'new'
        conn.execute('insert into lsi.watch_events(run_id,source,item_key,action,lighting,payload,old_payload) values(%s,%s,%s,%s,%s,%s,%s)',
                     (run_id, source, key, action, flag, Jsonb(payload), Jsonb(old[0]) if old else None))
        counts[action] += 1
        counts['lighting'] += flag
    counts['baseline'] = baseline
    return counts

def main(only=None):
    from pathlib import Path
    from psycopg.types.json import Jsonb
    from database import connect, migrate
    with connect() as conn:
        migrate(conn); conn.commit()
        run = conn.execute("insert into lsi.job_runs(job,status) values('retrieval','RUNNING') returning id").fetchone()[0]
        conn.commit()
        summary, failed = {}, 0
        for name, watcher in WATCHERS.items():
            if only and name not in only: continue
            try:
                summary[name] = record(conn, run, name, watcher(conn))
                conn.commit()
            except Exception as exc:  # one source failing must not stop the others
                conn.rollback(); failed += 1
                summary[name] = {'error': type(exc).__name__}
        status = 'COMPLETE' if not failed else ('PARTIAL' if failed < len(summary) else 'FAILED')
        conn.execute('update lsi.job_runs set finished_at=now(),status=%s,summary=%s where id=%s', (status, Jsonb(summary), run))
        conn.commit()
    lines = ['# Scheduled retrieval', 'Listings only. New items are leads to read, not verified facts. Detail is in the private database.', '',
             '| Source | Listed | New | Changed | Lighting-related | Note |', '|---|---|---|---|---|---|']
    for name, c in summary.items():
        lines.append(f"| {name} | — | — | — | — | failed: {c['error']} |" if 'error' in c else
                     f"| {name} | {c['listed']} | {c['new']} | {c['changed']} | {c['lighting']} | {'first run: baseline recorded' if c['baseline'] else ''} |")
    Path('reports').mkdir(exist_ok=True)
    Path('reports/retrieval.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return 0 if status != 'FAILED' else 1

if __name__ == '__main__':
    try: sys.exit(main(set(sys.argv[1:]) or None))
    except Exception as exc:
        print('Retrieval failed (' + type(exc).__name__ + '); credentials and connection details suppressed.', file=sys.stderr)
        sys.exit(1)
