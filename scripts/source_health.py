"""Bounded public-government URL checks. Never scrape login portals or approve research."""
from datetime import datetime, timezone, date
import ipaddress
import json
from pathlib import Path
import socket
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from database import connect

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def allowed_url(url,resolve=True):
    try:
        u=urlsplit(url)
        if u.scheme!='https' or u.username or u.password or u.port not in (None,443): return False
        if not u.hostname or not u.hostname.endswith('.gov'): return False
        if resolve:
            addresses=socket.getaddrinfo(u.hostname,443,type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses): return False
        return True
    except (ValueError,OSError): return False

def check_url(url):
    if not allowed_url(url): return {'outcome':'manual_or_non_gov','status_code':None,'etag':None,'last_modified':None}
    try:
        req=Request(url,method='HEAD',headers={'User-Agent':'LSI-SourceHealth/1.0 (public-source reachability; no crawling)'})
        with build_opener(NoRedirect).open(req,timeout=15) as r:
            return {'outcome':'reachable','status_code':r.status,'etag':r.headers.get('ETag'),'last_modified':r.headers.get('Last-Modified')}
    except HTTPError as exc:
        return {'outcome':'redirect_review' if 300<=exc.code<400 else 'access_or_http_error','status_code':exc.code,'etag':None,'last_modified':None}
    except (URLError,TimeoutError,OSError):
        return {'outcome':'network_error','status_code':None,'etag':None,'last_modified':None}

def overdue(records,today=None,grace=14):
    today=today or datetime.now(timezone.utc).date()
    result=[]
    for state,payload in records:
        for row in payload:
            due=row.get('next')
            if not due: continue
            try: days=(today-date.fromisoformat(due)).days
            except ValueError: continue
            if days>0: result.append({'state':state,'layer':row['layer'],'due':due,'days_overdue':days,'status':'STALE' if days>grace else 'DUE','basis':row['basis']})
    return result

def main():
    from psycopg.types.json import Jsonb
    with connect() as conn:
        run=conn.execute("insert into lsi.job_runs(job,status) values('source-health','RUNNING') returning id").fetchone()[0]
        conn.commit()
        sources=conn.execute('''select s.source_key,s.url from lsi.sources s
          left join lateral(select max(checked_at) as checked from lsi.source_health h where h.source_key=s.source_key) h on true
          order by h.checked nulls first,s.source_key limit 16''').fetchall()
        observations=[]
        for key,url in sources:
            r=check_url(url)
            conn.execute('insert into lsi.source_health(source_key,url,status_code,outcome,etag,last_modified) values(%s,%s,%s,%s,%s,%s)',(key,url,r['status_code'],r['outcome'],r['etag'],r['last_modified']))
            observations.append({'source':key,**r})
            conn.commit()
            time.sleep(1)
        freshness=conn.execute("select state,payload from lsi.records where kind='freshness'").fetchall()
        summary={'checked_at':datetime.now(timezone.utc).isoformat(),'checked':observations,'due':overdue(freshness),'note':'HTTP reachability is not research verification. No product findings or as-of dates were changed.'}
        conn.execute("update lsi.job_runs set finished_at=now(),status='COMPLETE',summary=%s where id=%s",(Jsonb(summary),run))
        Path('reports').mkdir(exist_ok=True)
        Path('reports/source-health.json').write_text(json.dumps(summary,indent=2))
        lines=['# Source review queue',summary['note'],'',f"Checked {len(observations)} URLs; {len(summary['due'])} dated layers due for review.",'']
        lines += [f"- {r['state']} / {r['layer']}: {r['status']}, due {r['due']} ({r['days_overdue']} days)." for r in summary['due']]
        Path('reports/source-health.md').write_text('\n'.join(lines)+'\n')
        print(lines[3])

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('Source health failed ('+type(exc).__name__+'); credentials and connection details suppressed.',file=sys.stderr)
        sys.exit(1)
