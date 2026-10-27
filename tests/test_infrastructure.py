from copy import deepcopy
from datetime import date
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from database import validate_snapshot,payload_hash,connect,migrate,sync,smoke
from source_health import allowed_url,overdue
from restore_snapshot import restore

class ValidationTests(unittest.TestCase):
    def test_reject_duplicate_record_identity(self):
        data=json.loads((ROOT/'dist/snapshot.json').read_text())
        data['records'].append(data['records'][0])
        with self.assertRaises(ValueError): validate_snapshot(data)
    def test_reject_missing_state(self):
        data=json.loads((ROOT/'dist/snapshot.json').read_text())
        data['records']=[r for r in data['records'] if not(r['kind']=='state' and r['state']=='TN')]
        with self.assertRaises(ValueError): validate_snapshot(data)
    def test_record_hash_ignores_object_order_but_preserves_money(self):
        self.assertEqual(payload_hash({'a':1,'b':2}),payload_hash({'b':2,'a':1}))
        self.assertNotEqual(payload_hash({'amount':100}),payload_hash({'amount':101}))
    def test_health_checks_do_not_follow_credentials_or_private_hosts(self):
        for url in ['http://www.tn.gov/','https://user:password@www.tn.gov/','https://127.0.0.1/','https://example.com/','https://www.tn.gov:8443/']:
            self.assertFalse(allowed_url(url,resolve=False),url)
        self.assertTrue(allowed_url('https://www.tn.gov/path',resolve=False))
    def test_due_and_stale_are_distinct(self):
        r=overdue([('TN',[{'layer':'QPL','next':'2026-10-01','basis':'monthly'},{'layer':'calendar','next':'2026-10-20','basis':'agency calendar'}])],date(2026,10,27))
        self.assertEqual([x['status'] for x in r],['STALE','DUE'])

@unittest.skipUnless(os.getenv('LSI_DATABASE_URL'),'Integration database not configured')
class DatabaseTests(unittest.TestCase):
    def test_import_idempotence_change_history_and_rollback(self):
        data=json.loads((ROOT/'dist/snapshot.json').read_text())
        # A throwaway CI database only: no production writes are made by tests.
        self.assertEqual(os.environ.get('LSI_TEST_DATABASE'),'1','Refusing integration tests without explicit test-database flag')
        with connect() as conn:
            conn.execute('create role anon nologin')
            conn.execute('create role authenticated nologin')
            migrate(conn); migrate(conn)
            first=sync(conn,data)
            self.assertGreater(first['changes'],0)
            self.assertEqual(sync(conn,data)['changes'],0)
            revision=deepcopy(data);revision['content_hash']='test-revision'
            revision['records'][0]['payload']['test_revision']='controlled fixture'
            self.assertEqual(sync(conn,revision)['changes'],1)
            self.assertGreater(conn.execute('select count(*) from lsi.record_versions').fetchone()[0],len(data['records']))
            self.assertEqual(smoke(conn)['rls'],'PASS')
            self.assertEqual(restore(conn,data['content_hash'])['changes'],1)
            self.assertFalse(conn.execute("select exists(select 1 from lsi.records where payload ? 'test_revision')").fetchone()[0])
            self.assertEqual(conn.execute('select count(*) from lsi.contracts').fetchone()[0],len([r for r in data['records'] if r['kind']=='contract']))
            # A failed transaction must not leave half a release or half its changes.
            try:
                with conn.transaction():
                    bad=deepcopy(revision);bad['content_hash']='must-rollback'
                    sync(conn,bad)
                    raise RuntimeError('simulated failure')
            except RuntimeError: pass
            self.assertIsNone(conn.execute("select 1 from lsi.releases where content_hash='must-rollback'").fetchone())
            conn.rollback()

if __name__=='__main__': unittest.main()
