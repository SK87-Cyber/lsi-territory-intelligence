"""Append a recovery release from an existing snapshot; never delete historical evidence.

Usage: python scripts/restore_snapshot.py <release-content-hash>
Run only when the owner explicitly requests database rollback.
"""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
import sys
from database import connect,sync,smoke

def restore(conn,original_hash):
    row=conn.execute('select snapshot from lsi.releases where content_hash=%s',(original_hash,)).fetchone()
    if not row: raise ValueError('Requested release does not exist')
    data=deepcopy(row[0])
    data['restored_from']=original_hash
    data['restored_at']=datetime.now(timezone.utc).isoformat()
    data['content_hash']=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
    return sync(conn,data)

if __name__=='__main__':
    try:
        with connect() as conn:
            print(json.dumps(restore(conn,sys.argv[1])))
            print(json.dumps(smoke(conn)))
    except Exception as exc:
        print('Restore failed ('+type(exc).__name__+'); no secret details logged.',file=sys.stderr)
        sys.exit(1)
