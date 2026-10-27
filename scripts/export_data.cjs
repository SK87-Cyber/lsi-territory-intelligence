// Reuse the product's actual acceptance gate and evaluated registries.
// Do not regex-parse or independently reclassify the embedded research.
const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');
if (!process.argv[2] || !process.argv[3]) throw Error('usage: export_data.cjs built.html output.json');
const output = process.argv[3];
require('../verify.js'); // exits nonzero if any original acceptance gate fails
const t = globalThis.__t;
const records = [];
const add = (kind, state, key, payload) => records.push({kind, state, key:String(key), payload});
for (const state of t.STATES) {
  const sid = state.id;
  add('state', sid, sid, state);
  state.sources.forEach((s,i) => add('source', sid, `${sid}-${i}`, {title:s[0],url:s[1],basis:s[2] ?? null}));
  const year = t.YEAR[sid];
  if (year) {
    add('year', sid, sid, year);
    const all = new Map((year.all || []).map(c => [String(c.id), c]));
    for (const c of year.lighting || []) all.set(String(c.id), {...(all.get(String(c.id)) || {}), ...c});
    for (const [key,c] of all) add('contract',sid,key,c);
  }
  (t.PIPELINE[sid] || []).forEach((p,i) => add('project',sid,p.tip || p.id || `row-${i}`,p));
  t.buildContacts(state).forEach(c => add('contact',sid,`${c[1]}:${c[2]}`,c));
  add('freshness',sid,sid,t.freshness(sid).map(({layer,asOf,next,basis})=>({layer,asOf,next,basis})));
  if(t.MFR[sid]) add('manufacturer_evidence',sid,sid,t.MFR[sid]);
  if(t.OWNERSHIP[sid]) add('ownership',sid,sid,t.OWNERSHIP[sid]);
}
add('registry',null,'cadence',t.CADENCE);
add('registry',null,'historical_snapshots',t.SNAPSHOTS);
add('registry',null,'roadmap',t.ROADMAP_STATUS);
add('registry',null,'contact_log',t.CONTACT_LOG);
// Stable build content, independent of when this export is generated.
const seen = new Set();
for (const r of records) {
  const key=JSON.stringify([r.kind,r.state,r.key]);
  if (seen.has(key)) throw Error(`Duplicate record identity: ${key}`);
  seen.add(key);
}
const digest=crypto.createHash('sha256').update(JSON.stringify(records)).digest('hex');
const data={schema_version:1,build:t.ROADMAP_STATUS.build,research_date:t.ROADMAP_STATUS.date,content_hash:digest,records};
fs.writeFileSync(output,JSON.stringify(data));
fs.writeFileSync(path.join(path.dirname(output),'build-manifest.json'),JSON.stringify({build:data.build,content_hash:digest,records:records.length},null,2));
console.log(`Exported ${records.length} evidence-preserving records; sha256 ${digest}`);
