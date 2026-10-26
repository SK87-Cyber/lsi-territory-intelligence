// Verify a built site without a browser: node verify.js <built.html>
// Executes the page's <script> against a DOM stub; fails on any syntax/runtime error.
// Then re-checks the letting totals against the numbers NCDOT prints.
const fs = require("fs");
const file = process.argv[2];
if (!file) { console.error("usage: node verify.js <built.html>"); process.exit(2); }
const html = fs.readFileSync(file, "utf8");
const m = html.match(/<script>([\s\S]*)<\/script>/);
// Literal escape sequences in the static HTML render as raw text ("—" on
// the page). Shipped twice before this check existed.
{ const staticHtml = html.slice(0, html.indexOf("<script>"));
  const esc = staticHtml.match(/\\u[0-9a-fA-F]{4}/g);
  if (esc) { console.log("LITERAL ESCAPES IN STATIC HTML:", esc.slice(0,6).join(" ")); process.exit(1); }
  console.log("static HTML: no literal escape sequences"); }
function el() { return { addEventListener(){}, setAttribute(){}, set innerHTML(v){this._h=v}, get innerHTML(){return this._h||""}, appendChild(){}, querySelector:()=>el(), querySelectorAll:()=>[], onclick:null, onkeydown:null, style:{}, classList:{add(){},remove(){},toggle(){}}, dataset:{}, scrollIntoView(){}, getBoundingClientRect:()=>({left:0,top:0,width:100,height:100}), setPointerCapture(){}, insertAdjacentHTML(){}, remove(){}, textContent:"" }; }
const MADE = [];
const document = { body: el(), getElementById:()=>{ const e=el(); MADE.push(e); return e; }, createElement:()=>{ const e=el(); MADE.push(e); return e; }, addEventListener(){}, querySelector:()=>el(), querySelectorAll:()=>[] };
global.window = { innerWidth: 1200, innerHeight: 800 };
global.fetch = () => Promise.reject(new Error("offline"));
try {
  new Function("document", m[1] + "\n;globalThis.__t={STATES,GEO,FUND,FUND_SHORT,BUDGET_OBJECT,ALTDEL,ALTDEL_RULE,ALTDEL_AHEAD,NC_DIV,NHCCI,PIPE_SNAPSHOT,ladder,pipeJoin,nhFactor,MFR,mfrNote,narrative,briefState,briefOverview,BRIEF_ORDER,CADENCE,SNAPSHOTS,freshness,freshStatus,liveDigest,whatChanged,awardQueue,BX_UPCOMING,recurring,lightingCadence,nextLettings,programmedDue,termOf,recurClass,DIR_CAPTURED,SLA,OWNERS,CONTACT_LOG,LEDGER,contactStatus,slaCounts,slaStatus,buildContacts,COMPETE,PIPELINE,PIPEREAD,ROADMAP_STATUS,NC_DIVISIONS,NC_RUN6,NC_JUNE,NC_JULY,NC_PIPELINE,NC_YEAR,citeIndex,buildContacts,LAYERS,has,coverage,coverageCount,missingCard,TERRITORIES,TERR_COUNTY,OWNERSHIP,OFFICES,PIPELINE,ITEMS,LETSAMPLE,BIDSRC,BID_CHECK,bidScore,parseLetDate,calStrip,YEAR,LIGHTING_TILE_SPLIT};")(document);
  console.log("script executes: OK");
} catch (e) { console.log("JS ERROR:", e.stack.split("\n").slice(0, 3).join(" | ")); process.exit(1); }
const t = globalThis.__t;
const n = Object.values(t.NC_DIVISIONS).reduce((a, b) => a + b.length, 0);
console.log(`NC counties assigned: ${n} (expect 100), divisions: ${Object.keys(t.NC_DIVISIONS).length} (expect 14)`);
function letting(name, L, expectLow, expectEst) {
  const c = L.contracts, low = c.reduce((a, x) => a + (x.lowAmt || 0), 0), est = c.reduce((a, x) => a + (x.est || 0), 0);
  const ok = Math.abs(low - expectLow) < 0.01 && Math.abs(est - expectEst) < 0.01;
  console.log(`${name}: ${c.length} contracts, ${c.reduce((a,x)=>a+(+x.bidders||0),0)} bids, low ${low.toFixed(2)} vs printed ${expectLow} — ${ok ? "RECONCILED" : "MISMATCH"}`);
}
letting("Aug 18, 2026", t.NC_RUN6, 107629319.05, 118161000);
letting("Jun 16, 2026", t.NC_JUNE, 83246728.42, 78272000);
letting("Jul 21/23, 2026", t.NC_JULY, 61474490.86, 65108968.06);
// Every captured contract must carry a verdict. UNKNOWN is a regression:
// once an item list has been read, nothing may silently fall back to "not read".
const CLASSES = new Set(["L1", "L2", "L3", "LUMP", "None"]);
const all = [...t.NC_RUN6.contracts, ...t.NC_JUNE.contracts, ...t.NC_JULY.contracts];
const unread = all.filter(c => !CLASSES.has(c.cls));
const noEvidence = all.filter(c => !c.evidence || c.evidence.length < 30);
console.log(`contract verdicts: ${all.length - unread.length} of ${all.length} classified` +
  (unread.length ? ` — UNCLASSIFIED: ${unread.map(c => c.id).join(", ")}` : " — COMPLETE"));
if (noEvidence.length) console.log(`MISSING EVIDENCE: ${noEvidence.map(c => c.id).join(", ")}`);
const lit = all.filter(c => c.cls === "L1" || c.cls === "L2");
console.log(`carrying permanent lighting: ${lit.length} (${lit.map(c => `${c.id} $${(c.l2||0).toLocaleString()}`).join(", ") || "none"})`);
// Twelve-month set: internal consistency, and agreement with the three-month detail.
const Y = t.NC_YEAR;
const yContracts = Y.lettings.reduce((a, l) => a + l.n, 0);
const yLow = Y.lettings.reduce((a, l) => a + l.low, 0);
const idSum = Y.lighting.reduce((a, c) => a + c.l2, 0);
const prodSum = Y.lighting.reduce((a, c) => a + c.product, 0);
const okC = yContracts === Y.contracts, okL = Math.abs(yLow - Y.lowBids) < 0.01;
console.log(`12-month: ${Y.lettings.length} lettings, ${Y.contracts} contracts, $${Y.lowBids.toFixed(2)} low bids — ` +
  `${okC && okL ? "RECONCILED" : "MISMATCH"}`);
console.log(`12-month lighting: ${Y.lighting.length} contracts, $${idSum.toFixed(2)} identified, $${prodSum.toFixed(2)} product`);
const inYear = Y.lighting.find(c => c.id === "C205195");
const inAug = t.NC_RUN6.contracts.find(c => c.id === "C205195");
const agree = inYear && inAug && Math.abs(inYear.l2 - inAug.l2) < 0.01;
console.log(`C205195 across both reads: $${inAug.l2.toFixed(2)} vs $${inYear.l2.toFixed(2)} — ${agree ? "AGREE" : "DISAGREE"}`);
const noEv = Y.lighting.filter(c => !c.note || !c.awardNote);
if (noEv.length) console.log(`MISSING EVIDENCE (12-month): ${noEv.map(c => c.id).join(", ")}`);
for (const s of t.STATES) console.log(`${s.id} contacts: ${t.buildContacts(s).length}, sources: ${s.sources.length}`);
/* ---------------------------------------------------------------------------
   Milestone 2.1 acceptance test — the layer split.
   "A state adds with the seven transferable layers populated and the five
   bid-derived layers empty, without breaking a single view."
   The seven non-NC states ARE that case today: transferable layers only, no
   bid data at all. So the test is run against them rather than a mock.
   ------------------------------------------------------------------------- */
let layerFail = 0;
const T = t.LAYERS.filter(L => L.grp === "T"), B = t.LAYERS.filter(L => L.grp === "B");
console.log(`layers: ${t.LAYERS.length} (${T.length} transferable, ${B.length} bid-derived)`);
if (T.length !== 7 || B.length !== 5) { console.log("LAYER SPLIT WRONG — expected 7 transferable and 5 bid-derived"); layerFail++; }

// 1. every predicate must run for every state without throwing
for (const s of t.STATES) for (const L of t.LAYERS) {
  try { L.has(s); } catch (e) { console.log(`PREDICATE THREW: ${s.id}/${L.id} — ${e.message}`); layerFail++; }
}

// 2. NC is the reference: all twelve on file
const ncT = t.coverageCount(t.STATES[0], "T"), ncB = t.coverageCount(t.STATES[0], "B");
console.log(`NC coverage: ${ncT}/7 transferable, ${ncB}/5 bid-derived`);
if (ncT !== 7 || ncB !== 5) { console.log("NC SHOULD CARRY ALL TWELVE LAYERS"); layerFail++; }

// 2b. Alabama: all seven transferable layers, pipeline filled from the owner-supplied STIP Excel (Sep 2, 2026)
const al = t.STATES.find(x => x.id === "AL");
const alT = t.coverageCount(al, "T");
console.log(`AL coverage: ${alT}/7 transferable (ownership ${t.has(al,"ownership")}, decision ${t.has(al,"decision")}, pipeline ${t.has(al,"pipeline")})`);
if (alT !== 7 || !t.has(al,"pipeline")) { console.log("AL LAYER COVERAGE WRONG — expected 7/7 with pipeline present"); layerFail++; }
// AL pipeline integrity: 27 roadway-lighting projects (12 pure), every row complete, region matches the county's territory
{ const AP = t.PIPELINE.AL || [];
  const pure = AP.filter(p => p.kind === "pure").length;
  const bad = AP.filter(p => !p.tip || !p.county || !p.div || !p.what || !p.kind || !Number.isFinite(p.cost));
  const wrongDiv = AP.filter(p => t.TERR_COUNTY.AL[p.county] !== p.div);
  console.log(`AL pipeline: ${AP.length} projects (${pure} pure)` + (bad.length ? ` — INCOMPLETE: ${bad.length}` : "") + (wrongDiv.length ? ` — REGION MISMATCH: ${wrongDiv.map(p=>p.county).join(",")}` : ""));
  if (AP.length !== 27 || pure !== 12 || bad.length || wrongDiv.length) { console.log("AL PIPELINE WRONG"); layerFail++; } }

// 2b2. Georgia (3.3): all seven transferable layers; pipeline from GDOT's own map service
const ga = t.STATES.find(x => x.id === "GA");
const gaT = t.coverageCount(ga, "T");
console.log(`GA coverage: ${gaT}/7 transferable (ownership ${t.has(ga,"ownership")}, decision ${t.has(ga,"decision")}, pipeline ${t.has(ga,"pipeline")})`);
if (gaT !== 7 || !t.has(ga,"pipeline")) { console.log("GA LAYER COVERAGE WRONG — expected 7/7"); layerFail++; }
{ const GP = t.PIPELINE.GA || [];
  const pure = GP.filter(p => p.kind === "pure").length, lump = GP.filter(p => p.what.startsWith("LUMP SUM")).length;
  console.log(`GA pipeline: ${GP.length} projects (${pure} pure, ${lump} annual lump-sum years)`);
  if (GP.length !== 15 || pure !== 14 || lump !== 10) { console.log("GA PIPELINE WRONG — expected 15 rows, 14 pure, 10 lump-sum years"); layerFail++; } }
// NC award record: 5 of 7 lighting contracts confirmed awarded after the owner-supplied stamped Item C (Sep 2, 2026)
{ const aw = t.NC_YEAR.lighting.filter(c => c.award === "awarded");
  console.log(`NC lighting awards: ${aw.length} of ${t.NC_YEAR.lighting.length} awarded (${aw.map(c=>c.id).join(", ")})`);
  if (aw.length !== 6) { console.log("NC AWARD COUNT WRONG — expected 6 after the April 2026 stamped Item C"); layerFail++; } }

// 2b4. Kentucky (3.5): fourth ownership shape — state-owned, legislature-gated. 7/7 with pipeline.
const ky = t.STATES.find(x => x.id === "KY");
const kyT = t.coverageCount(ky, "T");
console.log(`KY coverage: ${kyT}/7 transferable (ownership ${t.has(ky,"ownership")}, decision ${t.has(ky,"decision")}, pipeline ${t.has(ky,"pipeline")})`);
if (kyT !== 7 || !t.has(ky,"pipeline")) { console.log("KY LAYER COVERAGE WRONG — expected 7/7 with pipeline present"); layerFail++; }
{ const KP = t.PIPELINE.KY || [];
  const pure = KP.filter(p => p.kind === "pure").length;
  const tot = KP.reduce((a,p)=>a+(p.cost||0),0);
  const wrongDiv = KP.filter(p => t.TERR_COUNTY.KY[p.county] !== p.div);
  console.log(`KY pipeline: ${KP.length} dedicated lighting line items (${pure} pure, $${tot.toLocaleString()} enacted — full HB 533 sweep)` + (wrongDiv.length ? ` — DISTRICT MISMATCH: ${wrongDiv.map(p=>p.county).join(",")}` : ""));
  if (KP.length !== 5 || pure !== 5 || tot !== 5300000 || wrongDiv.length) { console.log("KY PIPELINE WRONG — expected 5 rows, all pure, $5,300,000 enacted, districts matching counties"); layerFail++; } }

// 2b5. South Carolina (3.6): ownership and decision layers present (two-key permit gate), pipeline honestly absent
const sc = t.STATES.find(x => x.id === "SC");
const scT = t.coverageCount(sc, "T");
console.log(`SC coverage: ${scT}/7 transferable (ownership ${t.has(sc,"ownership")}, decision ${t.has(sc,"decision")}, pipeline ${t.has(sc,"pipeline")})`);
if (scT !== 7 || !t.has(sc,"ownership") || !t.has(sc,"decision") || !t.has(sc,"pipeline")) { console.log("SC LAYER COVERAGE WRONG — expected 7/7 with pipeline present (3.18)"); layerFail++; }

// 2b6. Arkansas (3.7): the last state — ownership and decision present (distributed, third instance), pipeline honestly absent
const ar = t.STATES.find(x => x.id === "AR");
const arT = t.coverageCount(ar, "T");
console.log(`AR coverage: ${arT}/7 transferable (ownership ${t.has(ar,"ownership")}, decision ${t.has(ar,"decision")}, pipeline ${t.has(ar,"pipeline")})`);
if (arT !== 7 || !t.has(ar,"ownership") || !t.has(ar,"decision") || !t.has(ar,"pipeline")) { console.log("AR LAYER COVERAGE WRONG — expected 7/7 with pipeline present (3.18)"); layerFail++; }
// Every state now carries an ownership model: the Overview chart must have no "not yet modeled" row.
{ const missing = t.STATES.filter(s => !(t.OWNERSHIP[s.id] && t.OWNERSHIP[s.id].reg));
  console.log(`ownership models on file: ${t.STATES.length - missing.length} of ${t.STATES.length}` + (missing.length ? ` — MISSING: ${missing.map(s=>s.id).join(",")}` : " — territory complete"));
  if (missing.length) { console.log("OWNERSHIP LAYER INCOMPLETE — every state should be modeled after 3.7"); layerFail++; } }

// 2b3. Mississippi (3.4): ownership and decision layers present, pipeline honestly absent
const ms = t.STATES.find(x => x.id === "MS");
const msT = t.coverageCount(ms, "T");
console.log(`MS coverage: ${msT}/7 transferable (ownership ${t.has(ms,"ownership")}, decision ${t.has(ms,"decision")}, pipeline ${t.has(ms,"pipeline")})`);
if (msT !== 7 || !t.has(ms,"ownership") || !t.has(ms,"decision") || !t.has(ms,"pipeline")) { console.log("MS LAYER COVERAGE WRONG — expected 7/7 with pipeline present (3.18)"); layerFail++; }

// 2c. Tennessee (3.2): third ownership shape — the conditional two-key gate
const tn = t.STATES.find(x => x.id === "TN");
const tnT = t.coverageCount(tn, "T");
console.log(`TN coverage: ${tnT}/7 transferable (ownership ${t.has(tn,"ownership")}, decision ${t.has(tn,"decision")}, pipeline ${t.has(tn,"pipeline")})`);
if (tnT !== 7 || !t.has(tn,"ownership") || !t.has(tn,"decision") || !t.has(tn,"pipeline")) { console.log("TN LAYER COVERAGE WRONG — expected 7/7 with pipeline present (3.18)"); layerFail++; }

// 2d. Territory assignments beyond NC (3.2b): every county assigned exactly once.
for (const sid in t.TERRITORIES) {
  const T2 = t.TERRITORIES[sid].counties, all2 = Object.values(T2).flat();
  const dupes = all2.filter((c, i) => all2.indexOf(c) !== i);
  const expect = { TN: 95, AL: 67, GA: 159, SC: 46, KY: 120, MS: 82, AR: 75 }[sid];
  console.log(`${sid} territory map: ${all2.length} counties in ${Object.keys(T2).length} ${t.TERRITORIES[sid].unit}s` + (dupes.length ? ` — DUPES: ${dupes.join(",")}` : ""));
  if (dupes.length || (expect && all2.length !== expect)) { console.log(`${sid} TERRITORY ASSIGNMENT WRONG — expected ${expect} unique counties`); layerFail++; }
  if (!(t.GEO[sid] && t.GEO[sid].length === Object.keys(T2).length)) { console.log(`${sid}: GEO leader rows do not match territory count`); layerFail++; }
}
// 2d2. Field-office layer (3.2c): every office row complete — city, person, phone, coords.
for (const sid in t.OFFICES) {
  const O = t.OFFICES[sid];
  const bad = [...O.areas.map(r => ["area", r[0], r[2], r[3], r[4], r[5]]), ...O.districts.map(r => ["dist", r[1], r[2], r[3], r[4], r[5]])]
    .filter(r => !r[1] || !r[2] || !/\(\d{3}\) \d{3}-\d{4}/.test(r[3]) || !Number.isFinite(r[4]) || !Number.isFinite(r[5]));
  console.log(`${sid} offices: ${O.areas.length} area, ${O.districts.length} district` + (bad.length ? ` — INCOMPLETE ROWS: ${bad.length}` : ""));
  if (bad.length) layerFail++;
  if (sid === "AL" && (O.areas.length !== 10 || O.districts.length !== 41)) { console.log("AL OFFICE COUNTS WRONG — map legend holds 10 area and 41 district offices"); layerFail++; }
}

// 2e. The Overview regulatory chart and the ownership panels share one registry.
for (const sid of ["NC", "AL", "TN", "GA", "MS", "KY", "SC", "AR"]) {
  const o = t.OWNERSHIP[sid];
  if (!o || !o.reg || !o.reg.basis || !o.reg.owns || !o.reg.decides || !o.reg.customer) { console.log(`${sid}: OWNERSHIP.reg incomplete — the comparison chart would drop the row`); layerFail++; }
}

// 3. the acceptance case: every other state carries zero bid-derived layers,
//    renders a page, and shows UNKNOWN — never a zero — where a layer is absent.
const dossiers = MADE.filter(e => (e.innerHTML || "").includes("state-head"));
console.log(`state pages rendered: ${dossiers.length} (expect ${t.STATES.length})`);
// 3a. Tennessee's third decision shape must actually render (a forced fit into
//     the committee or distributed branch would drop the two-key table silently).
{ const tnIdx = t.STATES.findIndex(x => x.id === "TN"), tnPage = dossiers[tnIdx];
  if (!tnPage || !(tnPage.innerHTML || "").includes("two-key")) { console.log("TN DECISION SHAPE NOT RENDERED — expected the two-key gate"); layerFail++; } }
// 3b. Kentucky's fourth decision shape (central) must actually render its gates table.
{ const kyIdx = t.STATES.findIndex(x => x.id === "KY"), kyPage = dossiers[kyIdx];
  if (!kyPage || !(kyPage.innerHTML || "").includes("How it turns")) { console.log("KY DECISION SHAPE NOT RENDERED — expected the central single-owner gate table"); layerFail++; } }
// 3c. Every PIPELINE state must have a PM prose branch, or the panel silently vanishes.
{ const pipeStates = Object.keys(t.PIPELINE).filter(k => (t.PIPELINE[k]||[]).length);
  for (const sid of pipeStates) { const idx = t.STATES.findIndex(x => x.id === sid), pg = dossiers[idx];
    if (pg && !(pg.innerHTML || "").includes("programmed pipeline")) { console.log(`${sid}: PIPELINE DATA PRESENT BUT PANEL NOT RENDERED — missing PM branch?`); layerFail++; } } }
if (dossiers.length !== t.STATES.length) { console.log("A STATE PAGE FAILED TO RENDER"); layerFail++; }
for (let i = 1; i < t.STATES.length; i++) {
  const s = t.STATES[i], h = dossiers[i] ? dossiers[i].innerHTML : "";
  const bid = t.coverageCount(s, "B");
  // 3.8b: Alabama carries exactly two bid-derived layers from its item census — item reads and the dictionary. Never dollars, competition or awards from a census.
  // 3.9: Georgia carries four from its lettings read at item level — reads, dollars, dictionary, awards; 3.10: Kentucky the same four. Competition waits on a generic panel (the data now exists for both).
  const expectB = (s.id === "SC") ? 4 : (s.id === "GA" || s.id === "KY" || s.id === "AR" || s.id === "TN" || s.id === "MS" || s.id === "AL") ? 5 : 0;   // 3.18: Alabama gains awards by ALDOT's own release rule; South Carolina alone has no award artifact   // 3.17: Mississippi carries all five — a Commission Bid Awards list exists   // 3.16: Tennessee carries all five — a Contract Awards list exists   // 3.12: Alabama reads, dollars, dictionary, competition — never awards (no award artifact published)   // 3.13: GA and KY carry all five — reads, dollars, dictionary, awards, competition (full-year sets)
  if (bid !== expectB) { console.log(`${s.id}: expected ${expectB} bid-derived layers, found ${bid}`); layerFail++; }
  if (s.id === "SC" && t.has(s, "awards")) { console.log(`${s.id}: no award artifact exists — awards must stay off`); layerFail++; }
  if (!h) { console.log(`${s.id}: rendered nothing`); layerFail++; continue; }
  for (const bad of ["NaN", "undefined", "$0<", "$0 ", "Infinity"]) {
    if (h.includes(bad)) { console.log(`${s.id}: rendered "${bad}" — a missing layer must read UNKNOWN, never a zero`); layerFail++; }
  }
  if (!h.includes("UNKNOWN")) { console.log(`${s.id}: no UNKNOWN shown despite ${5 - bid} absent bid layers`); layerFail++; }
  if (t.YEAR[s.id] && /no letting in this state has been read at item level yet/.test(h)) { console.log(`${s.id}: bid-record panel denies a read that exists`); layerFail++; }
}
/* 3.13a: the North Carolina page gets the same zero / NaN scan as the others. */
{ const h = dossiers[0] ? dossiers[0].innerHTML : ""; for (const bad of ["NaN", "undefined", "$0<", "Infinity"]) if (h.includes(bad)) { console.log(`NC: rendered "${bad}"`); layerFail++; } }
/* 3.13a: every {ST-n} cite token anywhere in the script must resolve to a source index. */
{ const toks = Array.from(new Set((m[1].match(/\{[A-Z]{2}-\d+\}/g) || []))); const badTok = toks.filter(x => !t.citeIndex[x.slice(1, -1)]);
  console.log(`cite tokens: ${toks.length} distinct, ${badTok.length} unresolved${badTok.length ? " — " + badTok.join(" ") : ""}`);
  if (badTok.length) layerFail++; }
/* 3.13a: every contract published with a class was reconciled; an unreconciled one publishes UNKNOWN. */
{ for (const id of Object.keys(t.YEAR)) { const Y = t.YEAR[id]; if (!Y.all || Y.all[0].reconciled === undefined) continue;
    const leak = Y.all.filter(c => c.reconciled === false && c.cls !== "UNKNOWN"), read = Y.all.filter(c => c.cls !== "UNKNOWN").length;
    console.log(`${id}: ${read} of ${Y.all.length} contracts read and reconciled; contractsRead=${Y.contractsRead}`);
    if (leak.length || read !== Y.contractsRead) { console.log(`${id}: RECONCILIATION GATE LEAK`); layerFail++; } } }
console.log(layerFail ? `LAYER MODEL: ${layerFail} failure(s)` : "layer model: 12 layers, every predicate safe, absent layers read UNKNOWN — ACCEPTED");

/* ---------------------------------------------------------------------------
   Milestone 3.8 — the bid-artifact catalogue. Every state carries a BIDSRC
   entry with all four checklist items, a valid status, and a citation that
   resolves; KY and AR (anchor and control) confirm 4/4 and 3/4+1; every state
   page renders the bid-record panel; every calendar date parses; the
   catalogue is metadata, so no non-NC state gains a bid-derived layer from it.
   ------------------------------------------------------------------------- */
{ let bidFail = 0;
  const STAT = new Set(["ok","partial","gated","owner","no"]);
  for (const s of t.STATES) {
    const b = t.BIDSRC[s.id];
    if (!b) { console.log(`${s.id}: NO BIDSRC ENTRY`); bidFail++; continue; }
    for (const [k] of t.BID_CHECK) {
      const c = b.check[k];
      if (!c || !STAT.has(c[0]) || !c[1] || c[1].length < 20) { console.log(`${s.id}/${k}: checklist row incomplete`); bidFail++; continue; }
      const m = /\{([A-Z]{2})-(\d+)\}/.exec(c[2] || "");
      if (!m || !t.citeIndex[m[1] + "-" + m[2]]) { console.log(`${s.id}/${k}: citation ${c[2]} does not resolve`); bidFail++; }
    }
    if (!b.role || !b.tier || !b.scheme || !b.expect || b.expect.length !== 2 || !b.ff || !b.ff.length || !b.channel2 || !b.cal || !b.cal.pattern) { console.log(`${s.id}: BIDSRC fields missing`); bidFail++; }
    const badDates = (b.cal.dates || []).filter(d => !t.parseLetDate(d));
    if (badDates.length) { console.log(`${s.id}: unparseable calendar dates ${badDates.join(",")}`); bidFail++; }
    const sc = t.bidScore(s.id);
    console.log(`${s.id} bid catalogue: ${sc.ok}/4 confirmed, ${sc.part} half — ${b.role.split(" — ")[0]}; ${(b.cal.dates||[]).length || (s.id==="NC" ? t.NC_YEAR.lettings.length : 0)} calendar dates`);
  }
  const ky = t.bidScore("KY"), ar = t.bidScore("AR"), nc = t.bidScore("NC");
  if (ky.ok !== 4) { console.log("KY CATALOGUE WRONG — expected 4/4 after the Sep 5 probes (Section 716; award = presence in the Unit Bid Tabulations)"); bidFail++; }
  if (ar.ok !== 4) { console.log("AR CATALOGUE WRONG — expected 4/4 confirmed"); bidFail++; }
  if (nc.ok !== 4) { console.log("NC CATALOGUE WRONG — the reference adapter must be 4/4"); bidFail++; }
  // every state page renders the panel and the calendar strip; NC's strip carries all 15 lettings with 5 lighting-bearing ones
  for (let i = 0; i < t.STATES.length; i++) { const h = dossiers[i] ? dossiers[i].innerHTML : "";
    if (!h.includes("The bid record")) { console.log(`${t.STATES[i].id}: BID PANEL NOT RENDERED`); bidFail++; }
    if (!h.includes("calstrip")) { console.log(`${t.STATES[i].id}: CALENDAR STRIP NOT RENDERED`); bidFail++; } }
  { const strip = t.calStrip(t.STATES[0]); const ticks = (strip.match(/<span class="ct/g) || []).length, lit = (strip.match(/<span class="ct lit/g) || []).length;
    const litLettings = new Set(t.NC_YEAR.lighting.map(c => c.let)).size;
    console.log(`NC calendar strip: ${ticks} lettings, ${lit} carrying lighting (expect ${t.NC_YEAR.lettings.length} and ${litLettings})`);
    if (ticks !== t.NC_YEAR.lettings.length || lit !== litLettings) { console.log("NC CALENDAR STRIP WRONG"); bidFail++; } }
  { const strip = t.calStrip(t.STATES.find(x => x.id === "KY")); const ticks = (strip.match(/<span class="ct/g) || []).length;
    if (ticks !== 12) { console.log(`KY CALENDAR STRIP WRONG — expected 12 scheduled lettings, found ${ticks}`); bidFail++; } }
  /* 3.9 — Georgia, two lettings at item level: internal consistency and the award record. */
  { const G = t.YEAR.GA; if (!G) { console.log("GA YEAR MISSING"); bidFail++; }
    else { const n = G.lettings.reduce((a, l) => a + l.n, 0), low = G.lettings.reduce((a, l) => a + l.low, 0), bids = G.lettings.reduce((a, l) => a + l.bids, 0);
      const lit = G.lighting, aw = lit.filter(c => c.award === "awarded"), id = lit.reduce((a, c) => a + c.l2, 0), hw = lit.reduce((a, c) => a + c.split.hardware, 0);
      const splitOk = lit.every(c => Math.abs(c.split.hardware + c.split.infrastructure + c.split.work - c.l2) < 0.01);
      const allAw = G.all.filter(c => c.award === "awarded").length;
      console.log(`GA fourteen lettings: ${G.contracts} contracts, ${bids} bids, $${low.toFixed(2)} low bids — ${n === G.contracts && Math.abs(low - G.lowBids) < 0.01 ? "RECONCILED" : "MISMATCH"}; lighting ${lit.length} contracts $${id.toFixed(2)} (hardware $${hw.toFixed(2)}), ${aw.length} awarded; ${allAw}/${G.all.length} contracts awarded; split ${splitOk ? "sums" : "DOES NOT SUM"}`);
      // fourteen consecutive lettings (Jun 2025 – Jul 2026): 325 contracts, 1,396 bids; 36 lighting contracts, 34 awarded; 297 of 325 awarded overall (April 2026 main announcement outstanding)
      if (n !== 325 || G.contracts !== 325 || bids !== 1396 || Math.abs(low - G.lowBids) > 0.01 || lit.length !== 36 || aw.length !== 34 || allAw !== 297 || !splitOk || aw.some(c => !/\{GA-\d+\}/.test(c.awardNote))) { console.log("GA READ WRONG"); bidFail++; }
      const LSS = t.LETSAMPLE; if (!LSS.SC || LSS.SC.length !== 11 || LSS.SC.find(l => l.iso === "2026-08-11").rows.length !== 15 || LSS.SC.find(l => l.iso === "2026-06-09").rows.length !== 26 || !LSS.KY || LSS.KY.length !== 12 || !LSS.KY.find(l => l.iso === "2026-08-20") || LSS.KY.find(l => l.iso === "2026-08-20").rows.length !== 47 || LSS.KY.find(l => l.iso === "2026-08-20").rows.reduce((a, r) => a + r.bidders.length, 0) !== 105 || !LSS.NC || LSS.NC.length !== 227 || LSS.NC.reduce((a, l) => a + l.rows.length, 0) !== 414) { console.log("SC / KY / NC DIVISION SAMPLES WRONG"); bidFail++; } } }
  /* 3.10 — Kentucky, twelve lettings at item level from the Cabinet's own PDFs: internal consistency and the award rule. */
  { const K = t.YEAR.KY; if (!K) { console.log("KY YEAR MISSING"); bidFail++; }
    else { const n = K.lettings.reduce((a, l) => a + l.n, 0), bids = K.lettings.reduce((a, l) => a + l.bids, 0), awn = K.lettings.reduce((a, l) => a + l.awarded, 0);
      const lit = K.lighting, id = lit.reduce((a, c) => a + c.l2, 0), hw = lit.reduce((a, c) => a + c.split.hardware, 0);
      const splitOk = lit.every(c => Math.abs(c.split.hardware + c.split.infrastructure + c.split.work - c.l2) < 0.01);
      const allAw = K.all.filter(c => c.award === "awarded").length;
      console.log(`KY twelve lettings: ${K.contracts} contracts, ${bids} bids, $${K.lowBids.toFixed(2)} low bids; lighting ${lit.length} contracts $${id.toFixed(2)} (hardware $${hw.toFixed(2)}); ${allAw}/${K.all.length} awarded (presence in the Unit Bid Tabulations); split ${splitOk ? "sums" : "DOES NOT SUM"}`);
      // twelve lettings Sep 25, 2025 – Aug 20, 2026: 395 calls, 1,011 bids; 370 awarded (twelve tabulations); 24 lighting contracts, all awarded; April 23 has no Letting Results (404)
      if (n !== 395 || K.contracts !== 395 || bids !== 1011 || awn !== 370 || allAw !== 370 || lit.length !== 24 || !lit.every(c => c.award === "awarded" && /\{KY-\d+\}/.test(c.awardNote)) || !splitOk || K.lettings.length !== 12) { console.log("KY READ WRONG"); bidFail++; }
      const jun = K.lettings.find(l => l.iso === "2026-06-25"), apr = K.lettings.find(l => l.iso === "2026-04-23");
      if (!jun || jun.awarded !== 7 || !jun.awardArtifact || !apr || apr.n !== apr.awarded) { console.log("KY GAPS MISSTATED — June 25 read (7 of 7), April 23 awarded-only"); bidFail++; } } }
  /* 3.11 — Arkansas, nine lettings at item level from the Department's own PDFs, controlled by its own twelve-month item census. */
  { const A = t.YEAR.AR; if (!A) { console.log("AR YEAR MISSING"); bidFail++; }
    else { const n = A.lettings.reduce((a, l) => a + l.n, 0), bids = A.lettings.reduce((a, l) => a + l.bids, 0), awn = A.lettings.reduce((a, l) => a + l.awarded, 0);
      const lit = A.lighting, id = lit.reduce((a, c) => a + c.l2, 0), hw = lit.reduce((a, c) => a + c.split.hardware, 0);
      const splitOk = lit.every(c => Math.abs(c.split.hardware + c.split.infrastructure + c.split.work - c.l2) < 0.01);
      const q = d => lit.reduce((a, c) => a + c.items.filter(it => it.section === "714" && it.desc.includes(d) && c.let !== "Aug 12, 2026").reduce((b, it) => b + it.qty, 0), 0);
      // ARDOT's Weighted Average Unit Prices, 6/25/2025 – 6/24/2026 {AR-21}: 2 high-mast assemblies, 6 high-mast LED fixtures, 45 LED luminaire assemblies, 97 LED illumination poles
      const census = q("HIGH MAST ILLUMINATION ASSEMBLY") === 2 && q("HIGH MAST LED FIXTURE") === 6 && q("LED LUMINAIRE ASSEMBLY") === 45 && q("LED ROADWAY ILLUMINATION POLE") === 97;
      console.log(`AR nine lettings: ${A.contracts} jobs, ${bids} bids, $${A.lowBids.toFixed(2)} base bids; lighting ${lit.length} $${id.toFixed(2)} (hardware $${hw.toFixed(2)}); ${awn}/${A.contracts} awarded; census ${census ? "MATCHES" : "DOES NOT MATCH"} ARDOT's weighted-average report; split ${splitOk ? "sums" : "DOES NOT SUM"}`);
      if (n !== 203 || A.contracts !== 203 || A.contractsRead !== 203 || bids !== 614 || awn !== 203 || lit.length !== 10 || !lit.every(c => c.award === "awarded" && /\{AR-\d+\}/.test(c.awardNote)) || !splitOk || !census || A.lettings.length !== 9) { console.log("AR READ WRONG"); bidFail++; } } }
  /* 3.12 — Alabama, eleven lettings at item level, checked against the item census of 3.8b. */
  { const A = t.YEAR.AL, C = t.ITEMS.AL; if (!A) { console.log("AL YEAR MISSING"); bidFail++; }
    else { const n = A.lettings.reduce((a, l) => a + l.n, 0), bids = A.lettings.reduce((a, l) => a + l.bids, 0), lit = A.lighting;
      const id = lit.reduce((a, c) => a + c.l2, 0), hw = lit.reduce((a, c) => a + c.split.hardware, 0), lump = lit.reduce((a, c) => a + (c.split.lump || 0), 0);
      const splitOk = lit.every(c => Math.abs(c.split.hardware + c.split.infrastructure + c.split.work + (c.split.lump || 0) - c.l2) < 0.01);
      // every census L2 contract inside the year's lettings must be a lighting contract in the read (matched by project number)
      const isos = new Set(A.lettings.map(l => l.iso)); const cen = C.contracts750.filter(c => c.cls === "L2" && isos.has(c.date));
      const norm = x => String(x).toUpperCase().replace(/[^A-Z0-9]/g, ""); const miss = cen.filter(c => !lit.some(r => norm(r.tip) === norm(c.id)));
      console.log(`AL eleven lettings: ${A.contracts} contracts, ${bids} bids, $${A.lowBids.toFixed(2)} low bids; lighting ${lit.length} $${id.toFixed(2)} (hardware $${hw.toFixed(2)}, lump $${lump.toFixed(2)}); census L2 in window ${cen.length}, unmatched ${miss.length}; split ${splitOk ? "sums" : "DOES NOT SUM"}`);
      if (n !== 222 || A.contracts !== 222 || A.contractsRead !== 222 || bids !== 628 || lit.length !== 12 || !lit.every(c => c.award === "awarded") || !A.all.every(c => c.award === "awarded") || !splitOk || miss.length || A.lettings.length !== 11 || A.lettings[0].iso !== "2025-07-25" || A.lettings[10].iso !== "2026-06-26") { console.log("AL READ WRONG"); bidFail++; } } }
  /* 3.15 — South Carolina, eleven lettings: apparent bids for every call, certified tabulations for 225. */
  { const S = t.YEAR.SC; if (!S) { console.log("SC YEAR MISSING"); bidFail++; }
    else { const n = S.lettings.reduce((a, l) => a + l.n, 0), bids = S.lettings.reduce((a, l) => a + l.bids, 0), lit = S.lighting;
      const id = lit.reduce((a, c) => a + c.l2, 0), hw = lit.reduce((a, c) => a + c.split.hardware, 0), lump = lit.reduce((a, c) => a + (c.split.lump || 0), 0);
      const splitOk = lit.every(c => Math.abs(c.split.hardware + c.split.infrastructure + c.split.work + (c.split.lump || 0) - c.l2) < 0.01);
      console.log(`SC eleven lettings: ${S.contracts} calls (${S.contractsRead} read), ${bids} bids, $${S.lowBids.toFixed(2)} apparent low bids; lighting ${lit.length} $${id.toFixed(2)} (hardware $${hw.toFixed(2)}, lump $${lump.toFixed(2)}); split ${splitOk ? "sums" : "DOES NOT SUM"}`);
      const aug = S.lettings.find(l => l.iso === "2026-08-11");
      if (n !== 245 || S.contracts !== 245 || S.contractsRead !== 225 || bids !== 908 || lit.length !== 11 || lit.some(c => c.award === "awarded") || !splitOk || S.lettings.length !== 11 || !aug || aug.read !== 0) { console.log("SC READ WRONG"); bidFail++; } } }
  /* 3.16 — Tennessee, ten lettings: Apparent Bid Results for every call, Summary of Bids at item level for every call TDOT did not reject or hold, Contract Awards for all. */
  { const T = t.YEAR.TN; if (!T) { console.log("TN YEAR MISSING"); bidFail++; }
    else { const n = T.lettings.reduce((a, l) => a + l.n, 0), bids = T.lettings.reduce((a, l) => a + l.bids, 0), lit = T.lighting, awN = T.lettings.reduce((a, l) => a + l.awarded, 0);
      const id = lit.reduce((a, c) => a + c.l2, 0), hw = lit.reduce((a, c) => a + c.split.hardware, 0), lump = lit.reduce((a, c) => a + (c.split.lump || 0), 0);
      const splitOk = lit.every(c => Math.abs(c.split.hardware + c.split.infrastructure + c.split.work + (c.split.lump || 0) - c.l2) < 0.01);
      const unread = T.all.filter(c => c.reconciled === null), gate = T.all.every(c => c.reconciled !== false && (c.reconciled || c.cls === "UNKNOWN"));
      const l1 = lit.filter(c => c.cls === "L1"), ab = T.all.filter(c => c.note && /A\+B/.test(c.note));
      console.log(`TN ten lettings: ${T.contracts} calls (${T.contractsRead} read), ${bids} bids, $${T.lowBids.toFixed(2)} low bids; ${awN} awarded; lighting ${lit.length} $${id.toFixed(2)} (hardware $${hw.toFixed(2)}, lump $${lump.toFixed(2)}), ${l1.length} L1; unread ${unread.length} (all rejected or pending: ${unread.every(c => c.award === "rejected" || /PENDING/.test(c.note || ""))}); A+B ${ab.length}; split ${splitOk ? "sums" : "DOES NOT SUM"}; gate ${gate ? "holds" : "BROKEN"}`);
      if (n !== 386 || T.contracts !== 386 || T.contractsRead !== 373 || bids !== 1036 || awN !== 373 || lit.length !== 24 || l1.length !== 3 || !lit.every(c => c.award === "awarded") || !splitOk || !gate || T.lettings.length !== 10 || unread.length !== 13 || !unread.every(c => c.award === "rejected" || /PENDING/.test(c.note || "")) || ab.length !== 3) { console.log("TN READ WRONG"); bidFail++; }
      const LSS = t.LETSAMPLE; if (!LSS.TN || LSS.TN.length !== 10 || LSS.TN.reduce((a, l) => a + l.rows.length, 0) !== 386) { console.log("TN LETSAMPLE WRONG"); bidFail++; } } }
  /* 3.17 — Mississippi, twenty-four lettings: Checked Bid Results for every call, a tabulation for every call with a bidder, Bid Awards for 22 of 24. */
  { const M = t.YEAR.MS; if (!M) { console.log("MS YEAR MISSING"); bidFail++; }
    else { const n = M.lettings.reduce((a, l) => a + l.n, 0), bids = M.lettings.reduce((a, l) => a + l.bids, 0), lit = M.lighting, awN = M.lettings.reduce((a, l) => a + l.awarded, 0), rej = M.lettings.reduce((a, l) => a + (l.rejected || 0), 0);
      const id = lit.reduce((a, c) => a + c.l2, 0), hw = lit.reduce((a, c) => a + c.split.hardware, 0);
      const splitOk = lit.every(c => Math.abs(c.split.hardware + c.split.infrastructure + c.split.work + (c.split.lump || 0) - c.l2) < 0.01);
      const gate = M.all.every(c => c.reconciled === true && c.cls !== "UNKNOWN"), feb3 = M.lettings.find(l => l.iso === "2026-02-03"), noaw = M.lettings.filter(l => !l.awardArtifact).map(l => l.iso);
      const irr = M.all.filter(c => c.note && /IRREGULAR/.test(c.note)).length, notLow = M.all.filter(c => c.note && /^Awarded to/.test(c.note)).length;
      console.log(`MS twenty-four lettings: ${M.contracts} calls (${M.contractsRead} read), ${bids} bids, $${M.lowBids.toFixed(2)} low bids; ${awN} awarded, ${rej} not; lighting ${lit.length} $${id.toFixed(2)} (hardware $${hw.toFixed(2)}); Feb 3 read ${feb3 ? feb3.read : "?"}; no awards yet ${noaw.join(",")}; irregular ${irr}, awarded-not-low ${notLow}; split ${splitOk ? "sums" : "DOES NOT SUM"}; gate ${gate ? "holds" : "BROKEN"}`);
      if (n !== 170 || M.contracts !== 170 || M.contractsRead !== 170 || bids !== 616 || awN !== 146 || rej !== 12 || lit.length !== 6 || lit.filter(c => c.award === "awarded").length !== 5 || !splitOk || !gate || M.lettings.length !== 24 || !feb3 || feb3.read !== 17 || noaw.join(",") !== "2026-08-21,2026-08-25" || notLow !== 4) { console.log("MS READ WRONG"); bidFail++; }
      const LSS = t.LETSAMPLE; if (!LSS.MS || LSS.MS.length !== 24 || LSS.MS.reduce((a, l) => a + l.rows.length, 0) !== 170) { console.log("MS LETSAMPLE WRONG"); bidFail++; } } }
  /* 9.1–9.3 — freshness and the diff: every layer of every state has an as-of and a next date or reads UNKNOWN; no layer the session
     controls (lettings, programme, people, list, calendar) is STALE at build time — an award layer may be, and is reported; the live
     digest matches snapshot.py's shape; the diff against the first snapshot is non-empty and against the last is what it is; the
     award queue lists only apparent contracts; the panels render. */
  { let ok = true; const stale = [], awardStale = []; let layers = 0;
    t.STATES.forEach(s => { const F = t.freshness(s.id); layers += F.length; if (F.length < 6) ok = false;
      F.forEach(f => { if (!["fresh", "due", "stale", "unknown"].includes(f.cls) || (f.cls !== "unknown" && !/^\d{4}-\d{2}-\d{2}$/.test(f.next)) || !f.basis) ok = false;
        if (f.cls === "stale") (f.layer === "Awards" ? awardStale : stale).push(s.id + ":" + f.layer); }); });
    if (t.freshStatus("2000-01-01").cls !== "stale" || t.freshStatus("2999-01-01").cls !== "fresh" || t.freshStatus("").cls !== "unknown") ok = false;
    const live = t.liveDigest(); const first = t.SNAPSHOTS[0], last = t.SNAPSHOTS[t.SNAPSHOTS.length - 1];
    if (!first || !last || t.SNAPSHOTS.length < 8 || first.build !== "3.18" || !live.states.NC || live.total.lighting !== 130 || live.total.l2 !== last.total.l2) ok = false;
    const d0 = t.whatChanged(first, live), d1 = t.whatChanged(last, live);
    if (d0.length < 5 || !d0.some(i => /Division channel/.test(i.text)) || !d0.some(i => /item shape/.test(i.text)) || !d0.some(i => /sources/.test(i.text))) ok = false;
    const q = t.awardQueue(); if (q.some(r => r.st === "AL") || q.filter(r => r.st === "SC").length !== 11 || q.some(r => r.st === "SC" && r.cls !== "unknown") || !q.some(r => r.st === "GA" && r.cls === "stale")) ok = false;
    const pages = MADE.map(e => e.innerHTML || ""); const wc = pages.find(h => /Compared at open/.test(h)) || ""; const ft = pages.find(h => /The award sweep/.test(h)) || ""; const chips = (html.match(/freshDots\(/g) || []).length >= 2;   /* 9.3d — lights, not chips, on the state head and the brief */
    console.log(`freshness: ${layers} layers across eight states; stale (session-side) ${JSON.stringify(stale)}; stale awards ${JSON.stringify(awardStale)}; snapshots ${t.SNAPSHOTS.map(x => x.build).join(",")}; changes since ${first.build}: ${d0.length}, since ${last.build}: ${d1.length}; award queue ${q.length}; panels ${wc && ft ? "rendered" : "MISSING"}`);
    if (awardStale.length) console.log(`freshness: award artifact overdue for ${awardStale.join(", ")} — the agency's artifact is the only way out of apparent (GA: A260417 not posted)`);
    if (!ok || stale.length || !wc || !ft || !chips) { console.log("FRESHNESS / DIFF WRONG" + (stale.length ? " — STALE LAYER: " + stale.join(", ") : "")); bidFail++; } }
  /* 9.3b — the money, state by state: FUND carries all ten fields for all eight states and every cite token in it resolves; the headline
     figures are the enacted or adopted instrument's (GA 4.65 total funds, MS 1.57 core, TN 3.53 Work Program) and no basis reads as a
     request, a recommendation or a derived context; the Overview section and every state's funding panel render; Kentucky's programme
     carries the enacted chapters' years (four items in 2029–2031, $5.3M unchanged); the NC HMIP lighting line is cited. */
  { const F = t.FUND || {}; const fields = ["figure", "status", "fy", "includes", "revenue", "law", "appropriator", "plan", "allocation", "decides", "lighting", "say"]; let ok = true; const unresolved = [];
    for (const s of t.STATES) { const f = F[s.id]; if (!f) { ok = false; continue; }
      for (const k of fields) { if (!f[k] || String(f[k]).length < 20) { console.log(`${s.id}: FUND.${k} missing`); ok = false; } }
      for (const k of fields) for (const m of String(f[k]).matchAll(/\{([A-Z]{2})-(\d+)\}/g)) { if (!t.citeIndex[m[1] + "-" + m[2]]) unresolved.push(`${s.id}.${k}:${m[0]}`); }
      if (/request|recommendation|derived|context/i.test(s.basis)) { console.log(`${s.id}: basis still reads as a request/recommendation/derived (${s.basis})`); ok = false; } }
    const bud = Object.fromEntries(t.STATES.map(s => [s.id, s.budget])); const expB = { NC: 5.95, SC: 2.78, GA: 4.65, AL: 2.56, MS: 1.57, TN: 3.53, KY: 3.42, AR: 3.55 };
    for (const k in expB) if (bud[k] !== expB[k]) { console.log(`${k}: budget ${bud[k]} ≠ ${expB[k]}`); ok = false; }
    const sec = MADE.map(e => e.innerHTML || "").find(h => /How the money is planned and allocated/.test(h)) || ""; const rows2 = (sec.match(/<tr>/g) || []).length;
    const panels = t.STATES.filter(s => (MADE.map(e => e.innerHTML || "").find(h => new RegExp("How " + s.agency + "'s money is planned and allocated").test(h)))).length;
    const KP = t.PIPELINE.KY || []; const ky29 = KP.filter(p => /2029/.test(p.year)).length; const kyTot = KP.reduce((a, p) => a + p.cost, 0);
    const hmip = (t.STATES.find(s => s.id === "NC").sources || []).some(r => /HMIP/.test(r[1]) && /3242/.test(r[0] + r[2]));
    console.log(`money: FUND ${Object.keys(F).length} states × ${fields.length} fields; unresolved cites ${unresolved.length}; budgets ${JSON.stringify(bud)}; Overview rows ${rows2}; state panels ${panels}/8; KY items in 2029+ ${ky29}, $${kyTot.toLocaleString()}; NC HMIP lighting source ${hmip}`);
    if (!ok || unresolved.length || rows2 < 16 || panels !== 8 || ky29 !== 4 || kyTot !== 5300000 || !hmip) { console.log("MONEY / FUND WRONG" + (unresolved.length ? " — unresolved: " + unresolved.slice(0, 6).join(", ") : "")); bidFail++; } }
  /* 10.1 — alternative delivery: ALTDEL carries all eight states; every project has its fields; no lighting string says 'likely'; every
     cite resolves; the per-state panels and the Overview section render; the counts are pinned (67 contracts, 16 naming lighting); the
     lighting rule is stated for all eight; nothing from ALTDEL reaches the ladder (ladder totals unchanged). */
  { const A = t.ALTDEL || {}; let ok = true; const unresolved = []; let nP = 0, nL = 0;
    for (const s of t.STATES) { const a = A[s.id]; if (!a || !a.projects) { console.log(`${s.id}: ALTDEL missing`); ok = false; continue; }
      for (const k of ["authority", "program", "lightingRule"]) { if (!a[k] || a[k].length < 20) { console.log(`${s.id}: ALTDEL.${k} missing`); ok = false; } for (const m of String(a[k]).matchAll(/\{([A-Z]{2})-(\d+)\}/g)) if (!t.citeIndex[m[1] + "-" + m[2]]) unresolved.push(`${s.id}.${k}:${m[0]}`); }
      if (!t.ALTDEL_RULE[s.id]) { console.log(`${s.id}: ALTDEL_RULE missing`); ok = false; }
      for (const p of a.projects) { nP++; if (p.named) nL++; for (const k of ["name", "id", "method", "team", "value", "awarded", "status", "lighting", "cite"]) if (p[k] === undefined || p[k] === "") { console.log(`${s.id}: ${p.name} lacks ${k}`); ok = false; }
        if (/\blikely\b/i.test(p.lighting)) { console.log(`${s.id}: ${p.name} — 'likely' is not evidence`); ok = false; }
        const m = /\{([A-Z]{2})-(\d+)\}/.exec(p.cite); if (!m || !t.citeIndex[m[1] + "-" + m[2]]) unresolved.push(`${s.id}.${p.id}`); } }
    const panels = t.STATES.filter(s => (MADE.map(e => e.innerHTML || "").find(h => /Alternative delivery — design-build, CM\/GC and P3/.test(h) && new RegExp(s.agency).test(h)))).length;
    const ov = MADE.map(e => e.innerHTML || "").find(h => /What is ahead, where lighting is named/.test(h)) || "";
    const lad = t.STATES.map(s => t.ladder(s.id).let).reduce((a, b) => a + b, 0);
    console.log(`altdel: ${Object.keys(A).length} states, ${nP} contracts, ${nL} name lighting; unresolved cites ${unresolved.length}; state panels ${panels}/8; Overview ${ov ? "rendered" : "MISSING"}; ahead ${t.ALTDEL_AHEAD.length}; ladder let total $${Math.round(lad).toLocaleString()}`);
    if (!ok || unresolved.length || nP !== 67 || nL !== 16 || panels !== 8 || !ov || Math.round(lad) !== 74892576) { console.log("ALTDEL WRONG" + (unresolved.length ? " — unresolved: " + unresolved.slice(0, 6).join(", ") : "")); bidFail++; } }
  /* 8.1–8.3 — the brief: every state's brief and the territory brief render with no undefined/NaN/raw token; every tile carries a basis;
     the narrative names the agency, the let figure and the next letting; the walk order is territory then the eight states; the nav and
     every state head carry the Brief control. */
  { let ok = t.BRIEF_ORDER.length === 9 && t.BRIEF_ORDER[0] === "overview"; const bad = []; let tiles = 0, based = 0;
    const check = (id, h) => { if (/undefined|NaN|\[object|\{[A-Z]{2}-\d+\}/.test(h)) bad.push(id); const tl = (h.match(/<div class="btile">/g) || []).length; const bs = (h.match(/<div class="b">/g) || []).length; tiles += tl; based += Math.min(tl, bs); };
    t.STATES.forEach(s => { const h = t.briefState(s); check(s.id, h); const nar = t.narrative(s); if (!nar.includes(s.agency) || !/Next letting/.test(nar) || !/let \$/.test(nar)) bad.push(s.id + ":narrative"); if (!/Who buys product/.test(h) || !/Who owns, who decides/.test(h) || !/Whose product qualifies/.test(h) || !/Ahead/.test(h)) bad.push(s.id + ":columns"); });
    const ov = t.briefOverview(); check("overview", ov); if (!/ranked by what let/.test(ov) || (ov.match(/bar-row/g) || []).length !== 8 || !/Alabama's list names Cooper/.test(ov)) bad.push("overview:content");
    const nav = /navBtn\("brief"/.test(html), heads = (html.match(/openBrief\('\$\{s\.id\}'\)/g) || []).length >= 1, container = /id="brief" role="dialog"/.test(html);
    console.log(`brief: ${t.STATES.length} state briefs + territory; ${tiles} tiles, ${based} with a basis line; defects ${JSON.stringify(bad)}; nav ${nav}, head buttons ${heads}, container ${container}`);
    if (!ok || bad.length || tiles < 64 || based < tiles - 8 || !nav || !heads || !container) { console.log("BRIEF WRONG"); bidFail++; } }
  /* 7.1–7.3 — manufacturer evidence: every state has a record whose cites resolve; the tier is M4 only where a mandatory list names
     Cooper (AL) and M5 elsewhere; MS's unread list is UNKNOWN (null), never false; no share language; panels and the Method table render. */
  { let ok = true; const M = t.MFR; const tiers = {};
    t.STATES.forEach(s => { const m = M[s.id]; if (!m) { ok = false; return; } tiers[s.id] = m.contractTier;
      [m.list.cite, m.cooper.cite, m.spec.cite, m.gate.cite].forEach(c => { const k = String(c).match(/^\{([A-Z]{2}-\d+)\}$/); if (!k || !t.citeIndex[k[1]]) ok = false; });
      if (!["M4", "M5"].includes(m.contractTier) || !m.spec.quote || m.spec.quote.length < 80 || !m.gate.quote || !m.verdict) ok = false;
      if (m.contractTier === "M4" && !(m.list.exists === true && m.cooper.listed === true)) ok = false; });
    if (tiers.AL !== "M4" || Object.entries(tiers).filter(([k, v]) => v === "M4").length !== 1) ok = false;
    if (M.MS.list.exists !== null || M.MS.cooper.listed !== null) ok = false;
    if (M.AL.entries.length < 5 || !/^Cooper/.test(M.AL.entries[0][0]) || M.NC.entries.length < 6 || M.NC.cooper.listed !== false || M.GA.list.poles !== true || M.GA.list.luminaires !== false) ok = false;
    const pages = MADE.map(e => e.innerHTML || ""); const panels = pages.filter(h => /Whose product qualifies — what/.test(h)).length; const table = pages.find(h => /What the eight records say/.test(h)) || "";
    const share = pages.some(h => /market share of|Cooper's share|share of the market/i.test(h)); const alNote = pages.find(h => /M4 — Cooper QPL-eligible/.test(h)) || "";
    console.log(`manufacturer evidence: tiers ${JSON.stringify(tiers)}; AL list ${M.AL.entries.length} makers, NC APL ${M.NC.entries.length} makers; panels ${panels}, Method table ${table ? "rendered" : "MISSING"}, AL contract note ${alNote ? "M4" : "MISSING"}, share language ${share ? "PRESENT" : "none"}`);
    if (!ok || panels < 8 || !table || !alNote || share) { console.log("MANUFACTURER EVIDENCE WRONG"); bidFail++; } }
  /* 6.1–6.3 — recurrence: the register reads only the agencies' titles (a plain resurfacing job is never recurring); term inference is
     exact; the calendar carries every state's next letting with a basis and never a let or past-year programme entry; panels render. */
  { let ok = true; const rc = t.recurClass;
    if (rc("2026 Upper State On-call Signing").join() !== "on-call,term" || rc("RESURFACING").length || rc("THE ON-CALL CABLE BARRIER REPAIR ON VARIOUS INTERSTATE AND STATE ROUTES").join() !== "on-call,programme" || rc("EMERGENCY PIPE REPLACEMENT").join() !== "emergency") ok = false;
    const tm = t.termOf("FY '26 & FY '27 Statewide Cable Barrier Repair"); if (!tm || tm.rebid !== "FY 2028") ok = false; if (t.termOf("MILLING AND RESURFACING")) ok = false; if (t.termOf("2025 Florence CTC resurfacing").rebid !== "2026") ok = false;
    const exp = { GA: 40, TN: 112, SC: 117, AL: 10, MS: 13, KY: 29, AR: 6, NC: 4 }; const got = {};
    for (const id in exp) { const R = t.recurring(id); got[id] = R.rows.length; if (R.rows.length !== exp[id]) ok = false; if (R.rows.some(r => !r.kinds.length || (r.lowAmt && !r.low))) ok = false; }
    const cad = t.lightingCadence("GA"); if (!cad || cad.l1.length !== 5 || cad.withLighting !== 13 || cad.lettings !== 14 || !cad.medGap) ok = false;
    if (t.lightingCadence("SC").l1.length !== 0 || t.lightingCadence("AL").l1.length !== 3 || t.lightingCadence("TN").l1.length !== 3) ok = false;
    const today = new Date().toISOString().slice(0, 10); let nextOk = true, nx = {};
    t.STATES.forEach(s => { const L = t.nextLettings(s.id); nx[s.id] = L.length ? L[0].date : null; if (!L.length || L.some(x => x.date < today || !x.basis)) nextOk = false; });
    const due = t.programmedDue("AL"); if (due.some(x => x.tip === "DEMO A211 (948)")) ok = false;   // let Sep 26, 2025 — never "ahead"
    if (due.filter(x => !x.past).some(x => +String(x.when).slice(-4) < new Date().getFullYear())) ok = false;
    const ms = t.programmedDue("MS"); if (!ms.some(x => /October 2026/.test(x.when)) || !ms.some(x => /January 2027/.test(x.when))) ok = false;
    const pages = MADE.map(e => e.innerHTML || ""); const cal = pages.find(h => /Bid Express calendar, read/.test(h) && /<th>Kind<\/th>/.test(h)) || ""; const panels = pages.filter(h => /The recurring-type contracts and who holds them|no standalone lighting contract in the year|standalone lighting contracts in the year/.test(h)).length; const rules = pages.find(h => /What the year says about lighting maintenance/.test(h)) || "";
    if (!cal || /2024|2025<\/b>/.test(cal.slice(0, 400)) || panels < 8 || !rules || !t.BX_UPCOMING.TN || t.BX_UPCOMING.TN[0].date !== "2026-10-02" || !/Bid Express — Infotech/.test(html)) ok = false;
    console.log(`recurrence: register ${JSON.stringify(got)}; GA cadence ${cad ? cad.l1.length + " L1, " + cad.withLighting + "/" + cad.lettings + " lettings, median " + cad.medGap + " d" : "MISSING"}; next lettings ${JSON.stringify(nx)}; MS programmed ${ms.length}; calendar ${cal ? "rendered" : "MISSING"}, panels ${panels}, rules ${rules ? "rendered" : "MISSING"}`);
    if (!ok || !nextOk) { console.log("RECURRENCE WRONG"); bidFail++; } }
  /* 5.1–5.3 — the people ledger: every contact has a computed status from a real date; the SLA thresholds behave; every state has a
     capture date and an owners record whose contacts are UNKNOWN; the verify workflow round-trips through the ledger; the Method ledger renders. */
  { let ok = t.SLA.active === 120 && t.SLA.stale === 365; let dated = 0, total = 0, unknownNoDate = 0;
    t.STATES.forEach(s => { if (!t.DIR_CAPTURED[s.id] || !/^\d{4}-\d{2}-\d{2}$/.test(t.DIR_CAPTURED[s.id])) ok = false; if (!t.OWNERS[s.id] || !t.OWNERS[s.id].cls || !t.OWNERS[s.id].cite) ok = false;
      t.buildContacts(s).forEach(r => { total++; const st = t.contactStatus(s.id, r); if (!["active", "stale", "unknown", "vacant"].includes(st.cls)) ok = false; if (st.date) dated++; if (st.cls === "unknown" && st.days === null) unknownNoDate++; }); });
    const d = new Date(); const iso = x => { const y = new Date(); y.setDate(y.getDate() - x); return y.toISOString().slice(0, 10); };
    if (t.slaStatus(iso(10)).cls !== "active" || t.slaStatus(iso(121)).cls !== "stale" || t.slaStatus(iso(366)).cls !== "unknown" || t.slaStatus("").cls !== "unknown") ok = false;
    // the workflow: log a verification, see it win; log "left", see UNKNOWN; then remove it so the stub run leaves nothing behind
    const s0 = t.STATES[0], r0 = t.buildContacts(s0).find(r => r[7] !== "x"); const key = s0.id + "|" + r0[1].trim().toLowerCase(); const before = t.contactStatus(s0.id, r0).cls;
    t.LEDGER.add({ key, sid: s0.id, date: iso(0), outcome: "confirmed", by: "verify.js", note: "stub" }); const after = t.contactStatus(s0.id, r0);
    t.LEDGER.add({ key, sid: s0.id, date: iso(0), outcome: "left", by: "verify.js", note: "stub" }); const gone = t.contactStatus(s0.id, r0);
    t.LEDGER.mem = t.LEDGER.mem.filter(e => e.by !== "verify.js"); const restored = t.contactStatus(s0.id, r0).cls;
    if (after.cls !== "active" || after.via !== "verify.js" || gone.cls !== "unknown" || restored !== before) ok = false;
    const pages = MADE.map(e => e.innerHTML || ""); const ledger = pages.find(h => /Oldest capture \/ verification/.test(h)) || ""; const owners = pages.filter(h => /Who else owns the light/.test(h)).length; const forms = pages.filter(h => /class="vform"/.test(h)).length;
    console.log(`people ledger: ${total} contacts in eight states, ${dated} dated, ${unknownNoDate} UNKNOWN for want of a date; SLA ${t.SLA.active}/${t.SLA.stale}; workflow ${after.cls}→${gone.cls}→${restored}; owners panels ${owners}, verify forms on ${forms} pages, ledger ${ledger ? "rendered" : "MISSING"}; baked log ${t.CONTACT_LOG.length}`);
    if (!ok || dated !== total || unknownNoDate || owners < 8 || forms < 8 || !ledger || !/The rule\./.test(ledger)) { console.log("PEOPLE LEDGER WRONG"); bidFail++; } }
  /* 4.1–4.3 — the financial overlay: the NHCCI series is complete and monotone in time; the ladder never deflates programme cost; the join
     finds Alabama's three let projects and nothing else (every other joinable programme is carried, KY/TN unreadable); an absent award
     layer reads UNKNOWN; the money board, every ladder and every price-book pair render. */
  { const NH = t.NHCCI, qs = Object.keys(NH.series); let ok = qs.length === 92 && NH.series["2003 Q1"] === 1 && NH.base === "2025 Q4" && Math.abs(NH.series["2025 Q4"] - 3.234373) < 1e-5;
    const f25 = t.nhFactor("Sep 9, 2025"), f26 = t.nhFactor("Aug 18, 2026"), f23 = t.nhFactor("Jan 15, 2003"); if (f25.held || !f26.held || Math.abs(f26.f - 1) > 1e-9 || Math.abs(f23.f - NH.series["2025 Q4"]) > 1e-6) ok = false;
    const exp = { AL: [3, 24, true], GA: [0, 15, true], NC: [0, 14, true], SC: [0, 3, true], MS: [0, 2, true], AR: [0, 0, true], KY: [0, 0, false], TN: [0, 0, false] }; const got = {};
    for (const id in exp) { const J = t.pipeJoin(id); got[id] = [J.let.length, J.carried.length, J.joinable]; if (J.let.length !== exp[id][0] || J.carried.length !== exp[id][1] || J.joinable !== exp[id][2]) ok = false; if (!exp[id][2] && J.unjoinable.length !== (t.PIPELINE[id] || []).length) ok = false; }
    const alJ = t.pipeJoin("AL"); if (!alJ.let.every(x => x.lit) || alJ.let.map(x => x.c.id).sort().join() !== "20250926015,20251107020,20251205011") ok = false;
    let ladOk = true; t.STATES.forEach(s => { const L = t.ladder(s.id); if (L.read && (L.letK <= 0 || L.let <= 0)) ladOk = false; if (L.programmed && !L.costPublished) ladOk = false; if (s.id === "SC" && (L.awardLayer || L.awardedN)) ladOk = false; if (!t.PIPE_SNAPSHOT[s.id] || !t.PIPE_SNAPSHOT[s.id].asOf) ladOk = false; });
    const scL = t.ladder("SC"); const scK = scL.letK / scL.let; if (!(scK > 0.95 && scK < 1.05) || Math.abs(scK - 1) < 1e-6) ladOk = false;   // Sep 2025–Aug 2026 lettings restated to 2025 Q4: a small, non-zero correction
    const pages = MADE.map(e => e.innerHTML || ""); const ladN = pages.filter(h => /Where the lighting money is/.test(h)).length; const pbK = pages.filter(h => /in 2025 Q4 dollars/.test(h) && /price book/.test(h)).length; const rules = pages.find(h => /The five rules of the overlay/.test(h)) || "";
    const board = /id="moneyMode"/.test(html) && /Lighting programmed/.test(html) && /id="moneyK"/.test(html);
    const scPage = pages.find(h => /Where the lighting money is/.test(h) && /SCDOT/.test(h)) || ""; const scUnknown = /UNKNOWN<\/b> — the agency publishes no award artifact/.test(scPage) || /UNKNOWN/.test(scPage);
    console.log(`financial overlay: NHCCI ${qs.length} quarters (${qs[0]} → ${NH.base}); factor Sep 2025 ${f25.f.toFixed(4)}, 2026 held ${f26.held}; join ${JSON.stringify(got)}; ladders ${ladN}, price books restated ${pbK}, rules ${rules ? "rendered" : "MISSING"}, board ${board ? "present" : "MISSING"}; SC awarded ${scUnknown ? "UNKNOWN" : "NOT UNKNOWN"}`);
    if (!ok || !ladOk || ladN < 8 || pbK < 8 || !rules || !board || !scUnknown || !/Federal indices/.test(html)) { console.log("FINANCIAL OVERLAY WRONG"); bidFail++; } }
  /* 3.21 — the NC Division channel (3.19), all 14 Divisions at contract level, and NC's year record in the item shape. The Division 5 sample
     rows read by the owner in 3.16 must reappear unchanged inside the full read; every winner is the lowest regular bid; the NC price book renders. */
  { const D = t.NC_DIV, Y = t.YEAR.NC; let ok = !!D && D.lettings.length === 227 && D.contracts === 414 && D.divisionsRead === 14 && Math.abs(D.lowBids - 762053442.01) < 0.01 && D.bids === 1274 && Object.keys(D.byDiv).length === 14;
    const s = D && D.all.find(r => r.id === "DE00444"); if (!s || s.div !== 5 || s.iso !== "2026-08-12" || s.low !== "TMI SERVICES INC" || Math.abs(s.lowAmt - 1860839.58) > 0.005 || s.nBidders !== 5) ok = false;
    let lowBad = 0, sumChk = 0; if (D) D.all.forEach(r => { const reg = r.bidders.filter(b => !b[2] && b[1] > 0); if (reg.length && (r.low !== reg[0][0] || Math.abs(r.lowAmt - reg[0][1]) > 0.005)) lowBad++; if (r.lowAmt) sumChk += r.lowAmt; });
    if (lowBad || Math.abs(sumChk - D.lowBids) > 0.05) ok = false;
    const divSum = D ? Object.values(D.byDiv).reduce((a, b) => a + b.contracts, 0) : 0; if (divSum !== 414) ok = false;
    if (D && D.all.some(r => r.bidders.some(b => b[2] && b[1] === 0 && !b[3]))) ok = false;   // an amount-less irregular bid keeps its reason
    const ncItems = Y && Y.lighting.every(c => Array.isArray(c.items) && c.items.length && c.splitHw && c.split && typeof c.split.lump === "number" && c.items.every(it => it.prices && typeof it.prices[c.low] === "number"));
    const ncL2 = Y ? Y.lighting.reduce((a, c) => a + c.l2, 0) : 0, ncHw = Y ? Y.lighting.reduce((a, c) => a + c.split.hardware, 0) : 0;
    const pb = MADE.map(e => e.innerHTML || "").find(h => /The North Carolina price book/.test(h)) || "";
    const ncPage = MADE.map(e => e.innerHTML || "").find(h => /all 14 Divisions read at contract level/.test(h)) || "";
    console.log(`NC Division channel: ${D ? D.lettings.length : 0} lettings, ${D ? D.contracts : 0} contracts, $${D ? D.lowBids.toFixed(2) : 0}, ${D ? D.divisionsRead : 0} Divisions, ${lowBad} low-bid errors; NC items on ${Y ? Y.lighting.filter(c => c.items).length : 0} of ${Y ? Y.lighting.length : 0} lighting contracts, l2 $${ncL2.toFixed(2)} hardware $${ncHw.toFixed(2)}; price book ${pb ? "rendered" : "MISSING"}; Division section ${ncPage ? "rendered" : "MISSING"}; D5 sample row ${s ? "found" : "MISSING"}`);
    if (!ok || !ncItems || Math.abs(ncL2 - 1433387.64) > 0.01 || Math.abs(ncHw - 490639.08) > 0.01 || !pb || !ncPage || !/Division 14/.test(ncPage) || !/DJ00561/.test(ncPage)) { console.log("NC DIVISION CHANNEL / PRICE BOOK WRONG"); bidFail++; } }
  /* 3.20 — the accuracy pass, data side: every lighting contract in the seven item-shaped states carries splitHw whose four classes
     re-add to its published hardware (within $0.05); luminaire/pole counts are numbers; the accuracy section renders with the threshold table. */
  { let nC = 0, bad = 0, sub = { luminaire: 0, pole: 0, assembly: 0, control: 0 }, tot = 0;
    for (const id of ["NC", "GA", "KY", "AR", "AL", "SC", "TN", "MS"]) { const Y = t.YEAR[id]; if (!Y || !Y.lighting) { console.log(`${id} YEAR MISSING`); bidFail++; continue; }
      for (const c of Y.lighting) { nC++; tot += c.l2; const s = c.splitHw; if (!s || typeof c.lumN !== "number" || typeof c.poleN !== "number") { bad++; continue; }
        const hw = s.luminaire + s.pole + s.assembly + s.control; if (Math.abs(hw - c.split.hardware) > 0.05) bad++; for (const k in sub) sub[k] += s[k];
        if (!c.items.every(it => ["luminaire", "pole", "assembly", "control", "infrastructure", "work", "lump"].includes(it.sub))) bad++; } }
    const acc = MADE.map(e => e.innerHTML || "").find(h => /What a threshold would do/.test(h)) || "";
    const rowsAll = t.STATES.flatMap(s => (t.YEAR[s.id] && t.YEAR[s.id].lighting) || []); const keep50 = rowsAll.filter(c => c.l2 >= 50000).length;
    console.log(`accuracy pass: ${nC} contracts in eight states, ${bad} without a re-adding splitHw; luminaires $${sub.luminaire.toFixed(0)} · poles $${sub.pole.toFixed(0)} · assemblies $${sub.assembly.toFixed(0)} · control $${sub.control.toFixed(0)}; table over ${rowsAll.length} contracts, $50k floor keeps ${keep50}; section ${acc.length} chars`);
    if (nC !== 130 || bad || rowsAll.length !== 130 || keep50 !== 112 || !/id="accuracyPass"/.test(html) || !acc || !/keep · change · drop/.test(acc) || !/nothing is applied/.test(acc) || (acc.match(/<tr>/g) || []).length < 40) { console.log("ACCURACY PASS WRONG"); bidFail++; } }
  /* 3.18a — the roadmap tab is part of the product: ROADMAP_STATUS must name the build ROADMAP.md §0 names, its next item must be §0's next item,
     and the rendered tab must carry it (the tab had stopped at 3.10 while the file went on to 3.18). */
  { const R = t.ROADMAP_STATUS; let md = ""; try { md = require("fs").readFileSync(require("path").join(__dirname, "ROADMAP.md"), "utf8"); } catch (e) {}
    const cur = md.match(/\*\*Current build\*\* \| `southeast-dot-lighting-intelligence-build-([0-9.]+[a-z]?)\.html`/);
    const nextRow = (md.match(/\| \*\*Next milestone\*\* \|([^\n]*)/) || [])[1] || "";
    const staticTab = html.slice(html.indexOf('id="view-roadmap"'), html.indexOf("<script>"));
    const tab = staticTab + (MADE.map(e => e.innerHTML || "").find(h => /Where the roadmap stands/.test(h)) || "");
    const firstNext = R && R.next && R.next[0] ? R.next[0][0] : "";
    const key = firstNext.replace(/^\d+\.\d+\s+/, "").split(" ").slice(0, 3).join(" ").toLowerCase();
    console.log(`roadmap tab: status build ${R ? R.build : "MISSING"} vs ROADMAP.md ${cur ? cur[1] : "?"}; next "${firstNext}"; ${R ? R.delivered.length : 0} delivered listed; tab ${tab.length} chars`);
    if (!R || !cur || R.build.replace(/[a-z]$/, "") !== cur[1].replace(/[a-z]$/, "")) { console.log("ROADMAP TAB OUT OF DATE — ROADMAP_STATUS.build must equal ROADMAP.md §0's current build"); bidFail++; }
    if (!nextRow || !nextRow.toLowerCase().includes(key)) { console.log(`ROADMAP TAB OUT OF DATE — §0's next-milestone row does not mention "${key}"`); bidFail++; }
    if (!/id="roadmapStatus"/.test(staticTab) || !/Where the roadmap stands/.test(tab) || !tab.includes(R ? R.build : "\u0000") || /next: 3\.11 Arkansas/.test(tab)) { console.log("ROADMAP TAB DID NOT RENDER THE STATUS BLOCK"); bidFail++; }
    const stamped = (tab.match(/[Bb]uild \d+\.\d+[a-z]?/g) || []).filter(x => /^Build/.test(x) && !x.replace(/[a-z]$/, "").endsWith(R.build.replace(/[a-z]$/, ""))); if (stamped.length) { console.log(`roadmap tab: ${stamped.length} "Build N.N" strings other than the current build — build.py stamps that form; history must say "build N.N"`); } }
  /* 3.18 — the pipeline layer filled for SC, TN, MS and AR: every PIPELINE state has a PM branch (renders a panel), AR is a measured zero. */
  { const exp = { TN: [16, 3], MS: [2, 2], SC: [3, 0], AR: [0, 0] };
    for (const id in exp) { const P = t.PIPELINE[id] || [], pure = P.filter(p => p.kind === "pure").length;
      console.log(`${id} pipeline: ${P.length} projects name lighting, ${pure} pure` + (id === "AR" ? ` (programme read: ${t.PIPEREAD && t.PIPEREAD.AR ? t.PIPEREAD.AR.scanned + " projects, none)" : "MISSING"}` : ""));
      if (P.length !== exp[id][0] || pure !== exp[id][1] || (id === "AR" && !(t.PIPEREAD && t.PIPEREAD.AR))) { console.log(`${id} PIPELINE WRONG`); bidFail++; }
      const s = t.STATES.find(x => x.id === id), i = t.STATES.indexOf(s), h = dossiers[i] ? dossiers[i].innerHTML : "";
      if (!/Lighting on the horizon/.test(h)) { console.log(`${id}: pipeline panel did not render`); bidFail++; } } }
  /* 3.13 — the generic competition record: built from the year record, same measures as NC. */
  { for (const id of ["GA", "KY", "AR", "AL", "SC", "TN", "MS"]) { const K = t.COMPETE[id], Y = t.YEAR[id]; if (!K) { console.log(`${id} COMPETE MISSING`); bidFail++; continue; }
      const rows = Y.all.filter(c => c.bidders && c.bidders.length && c.lowAmt); const tot = rows.reduce((a, c) => a + c.lowAmt, 0);
      const sumC = K.contractors.reduce((a, c) => a + c.n, 0), sumV = K.contractors.reduce((a, c) => a + c.val, 0);
      console.log(`${id} competition: ${K.winners} winners, ${K.contracts} contracts, $${(K.total / 1e9).toFixed(2)}B, CR1 ${K.cr1}% CR3 ${K.cr3}% HHI ${K.hhi}, broadest ${K.broadest.name} in ${K.broadest.divs} districts`);
      if (K.contracts !== rows.length || Math.abs(K.total - tot) > 0.01 || sumC !== K.contracts || Math.abs(sumV - tot) > 0.01 || K.hhi < 100 || K.hhi > 10000 || K.cr1 > K.cr3) { console.log(`${id} COMPETE INCONSISTENT`); bidFail++; } }
    for (const id of Object.keys(t.COMPETE)) { const Y = t.YEAR[id]; if (id !== "NC" && !(Y && Y.lettings.length >= 6)) { console.log(`${id} COMPETE CLAIMED WITHOUT A FULL YEAR`); bidFail++; } } }
  /* 3.14 — map modes and the price book: every state with items priced per bidder renders a price book; every year state renders the mode bar. */
  { for (let i = 1; i < t.STATES.length; i++) { const s = t.STATES[i], h = dossiers[i] ? dossiers[i].innerHTML : ""; if (!t.YEAR[s.id]) continue;
      if (!h.includes("price book")) { console.log(`${s.id}: PRICE BOOK MISSING`); bidFail++; }
      if (!h.includes("mapmode-btn")) { console.log(`${s.id}: MAP MODE BAR MISSING`); bidFail++; } } }
  if (t.LIGHTING_TILE_SPLIT !== true) { console.log("LIGHTING_TILE_SPLIT is off — the owner adopted the three-component tile on Sep 4, 2026 (3.8b)"); bidFail++; }
  /* 3.8b — the Alabama item census: reconciled to the summary's own counts and to the Low Bid Sheet. */
  { const C = t.ITEMS && t.ITEMS.AL; if (!C) { console.log("AL ITEM CENSUS MISSING"); bidFail++; }
    else { const L2 = C.contracts750.filter(c => c.cls === "L2"), lum = L2.reduce((a, c) => a + c.lum, 0), hm = L2.reduce((a, c) => a + c.hm, 0);
      const lets = C.lettings.length, cons = C.lettings.reduce((a, l) => a + l.n, 0);
      const LSS = t.LETSAMPLE.AL, dec = LSS.find(x => x.iso === "2025-12-05"), jan = LSS.find(x => x.iso === "2026-01-30");
      // 3.12: eleven ALDOT tabulations read whole (May 30, 2025 – Apr 24, 2026); every census 750 call on those dates is present as a row
      { const missing = C.contracts750.filter(c => LSS.find(l => l.iso === c.date) && !LSS.find(l => l.iso === c.date).rows.find(r => r.call === c.call));
        console.log(`AL tabulations in the Contractors tab: ${LSS.length}, ${LSS.reduce((a, l) => a + l.rows.length, 0)} contracts; census 750 calls missing ${missing.length}`);
        if (LSS.length !== 11 || LSS.some(l => l.kind !== "tab") || missing.length) { console.log("AL LETTING SAMPLES WRONG"); bidFail++; } }
      const dec5 = C.contracts750.filter(c => c.date === "2025-12-05").map(c => c.call), lb = dec.rows.map(r => r.call);
      // 3.8c: the Jan 30, 2026 tabulation — 35 contracts (the census's call count for that letting), 96 bids, every bidder listed
      const janCalls = new Set(); C.contracts750.forEach(c => { if (c.date === "2026-01-30") janCalls.add(c.call); });
      const janBids = jan.rows.reduce((a, r) => a + r.bidders.length, 0), janN = C.lettings.find(l => l.date === "2026-01-30").n;
      console.log(`AL Jan 30, 2026 tabulation: ${jan.rows.length} contracts (census says ${janN}), ${janBids} bids, max ${Math.max(...jan.rows.map(r => r.bidders.length))} bidders on one contract`);
      if (jan.rows.length !== 35 || janN !== 35 || janBids !== 96 || [...janCalls].some(c => !jan.rows.find(r => r.call === c))) { console.log("AL JAN 2026 TAB WRONG"); bidFail++; }
      const unmatched = dec5.filter(c => !lb.includes(c));
      const badRow = C.contracts750.filter(c => !c.id || !c.county || !c.date || !c.items.length || c.hw.length !== 3 || c.infra.length !== 3);
      console.log(`AL item census: ${lets} lettings, ${cons} contracts, ${C.contracts750.length} priced 750/756, ${L2.length} L2, ${lum} luminaire assemblies (${hm} high-mast); Dec 5 calls vs Low Bid Sheet ${unmatched.length ? "UNMATCHED " + unmatched.join(",") : "reconciled"}`);
      if (lets !== 18 || cons !== 363 || C.contracts !== 363 || C.contracts750.length !== 39 || L2.length !== 15 || lum !== 492 || hm !== 41 || unmatched.length || badRow.length || dec.rows.length !== 28) { console.log("AL ITEM CENSUS WRONG"); bidFail++; } } }
  console.log(bidFail ? `BID CATALOGUE: ${bidFail} failure(s)` : "bid catalogue: 8 states, 32 checklist rows cited, panels and calendars rendered, no bid-derived layer claimed — ACCEPTED");
  if (bidFail) process.exit(1);
}

if (!okC || !okL || !agree || noEv.length || layerFail) process.exit(1);
if (unread.length || noEvidence.length) process.exit(1);
