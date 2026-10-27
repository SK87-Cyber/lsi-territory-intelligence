"""Transactional, repeatable imports; evidence and prior versions are never discarded."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

def payload_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def validate_snapshot(data):
    if data.get('schema_version') != 1 or not data.get('records') or not data.get('content_hash'):
        raise ValueError('Unsupported or empty snapshot')
    identities = [(r['kind'],r.get('state') or '',r['key']) for r in data['records']]
    if len(identities) != len(set(identities)):
        raise ValueError('Duplicate record identity')
    if {r['state'] for r in data['records'] if r['kind']=='state'} != {'NC','SC','GA','AL','MS','TN','KY','AR'}:
        raise ValueError('The eight-state registry is incomplete')

def connect():
    import psycopg
    value=os.environ.get('LSI_DATABASE_URL')
    if not value: raise RuntimeError('LSI_DATABASE_URL is missing')
    sslmode='require'
    if os.getenv('LSI_TEST_DATABASE')=='1':
        from psycopg.conninfo import conninfo_to_dict
        if conninfo_to_dict(value).get('host') not in ('localhost','127.0.0.1'):
            raise RuntimeError('Test databases must be local ephemeral services')
        sslmode='disable'
    return psycopg.connect(value,connect_timeout=20,application_name='lsi-infrastructure',sslmode=sslmode)

def migrate(conn):
    conn.execute('select pg_advisory_xact_lock(48278301)')
    for p in sorted((ROOT/'supabase/migrations').glob('*.sql')):
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        exists=conn.execute("select to_regclass('lsi.migrations')").fetchone()[0]
        prior=conn.execute('select sha256 from lsi.migrations where name=%s',(p.name,)).fetchone() if exists else None
        if prior:
            if prior[0]!=digest: raise ValueError('Applied migration was modified: '+p.name)
            continue
        conn.execute(p.read_text())
        conn.execute('insert into lsi.migrations(name,sha256) values(%s,%s)',(p.name,digest))

def sync(conn,data):
    from psycopg.types.json import Jsonb
    validate_snapshot(data)
    conn.execute('select pg_advisory_xact_lock(48278301)')
    release=data['content_hash']
    if conn.execute('select 1 from lsi.releases where content_hash=%s',(release,)).fetchone():
        return {'result':'unchanged','records':len(data['records']),'changes':0}
    conn.execute('insert into lsi.releases(content_hash,build,research_date,git_sha,record_count,snapshot) values(%s,%s,%s,%s,%s,%s)',
                 (release,data['build'],data['research_date'],os.getenv('GITHUB_SHA'),len(data['records']),Jsonb(data)))
    old={(k,s,key):h for k,s,key,h in conn.execute('select kind,state,record_key,payload_hash from lsi.records')}
    changes=0
    for r in data['records']:
        identity=(r['kind'],r.get('state') or '',r['key']); digest=payload_hash(r['payload'])
        before=old.pop(identity,None)
        if before==digest: continue
        conn.execute('insert into lsi.record_versions(kind,state,record_key,payload_hash,payload,first_release) values(%s,%s,%s,%s,%s,%s) on conflict do nothing',(*identity,digest,Jsonb(r['payload']),release))
        conn.execute('insert into lsi.records(kind,state,record_key,payload_hash,payload,release_hash) values(%s,%s,%s,%s,%s,%s) on conflict(kind,state,record_key) do update set payload_hash=excluded.payload_hash,payload=excluded.payload,release_hash=excluded.release_hash,updated_at=now()',(*identity,digest,Jsonb(r['payload']),release))
        conn.execute('insert into lsi.change_events(release_hash,kind,state,record_key,action,old_hash,new_hash) values(%s,%s,%s,%s,%s,%s,%s)',(release,*identity,'added' if before is None else 'changed',before,digest))
        changes+=1
    # Remove only from the current projection; every old payload and release remains recoverable.
    for identity,before in old.items():
        conn.execute('insert into lsi.change_events(release_hash,kind,state,record_key,action,old_hash) values(%s,%s,%s,%s,%s,%s)',(release,*identity,'removed',before))
        conn.execute('delete from lsi.records where kind=%s and state=%s and record_key=%s',identity)
        changes+=1
    return {'result':'imported','records':len(data['records']),'changes':changes}

def smoke(conn):
    tables=['migrations','releases','records','record_versions','change_events','source_health','job_runs']
    for name in tables:
        assert conn.execute("select relrowsecurity from pg_class where oid=%s::regclass",('lsi.'+name,)).fetchone()[0], 'RLS missing: '+name
    for role in ['anon','authenticated']:
        if conn.execute('select 1 from pg_roles where rolname=%s',(role,)).fetchone():
            assert not conn.execute("select has_schema_privilege(%s,'lsi','USAGE')",(role,)).fetchone()[0], 'Browser role can access private schema'
    return {'private_schema':'PASS','rls':'PASS','releases':conn.execute('select count(*) from lsi.releases').fetchone()[0],
            'records':conn.execute('select count(*) from lsi.records').fetchone()[0]}

if __name__=='__main__':
    try:
        with connect() as conn:
            migrate(conn)
            print(json.dumps(sync(conn,json.loads(Path(sys.argv[1]).read_text()))))
            print(json.dumps(smoke(conn)))
    except Exception as exc:
        # Database exceptions can contain credentials, connection strings or source data.
        print('Database operation failed ('+type(exc).__name__+'). Check credentials/connectivity and migration compatibility; no secret values logged.',file=sys.stderr)
        sys.exit(1)
