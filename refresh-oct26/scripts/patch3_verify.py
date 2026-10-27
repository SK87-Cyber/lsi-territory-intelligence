#!/usr/bin/env python3
"""Stage 3: move verify.js's pinned expectations to the refreshed record.
Every change here is a deliberate re-pin of a published figure."""
v = open('work/verify.js', encoding='utf-8').read()

def rep(old, new, label):
    global v
    assert v.count(old) == 1, (label, v.count(old))
    v = v.replace(old, new)
    print('re-pinned:', label)

# NC: all seven lighting contracts confirmed (C205195 via the September 2026 Board minutes)
rep('if (aw.length !== 6) { console.log("NC AWARD COUNT WRONG — expected 6 after the April 2026 stamped Item C"); layerFail++; } }',
    'if (aw.length !== 7) { console.log("NC AWARD COUNT WRONG — expected 7 after the September 2026 Board minutes (C205195)"); layerFail++; } }', 'NC awards 6->7')

# AL pipeline: 27 -> 29 rows, 12 pure (Oct 26, 2026 STIP print)
rep('if (AP.length !== 27 || pure !== 12 || bad.length || wrongDiv.length) { console.log("AL PIPELINE WRONG"); layerFail++; } }',
    'if (AP.length !== 29 || pure !== 12 || bad.length || wrongDiv.length) { console.log("AL PIPELINE WRONG — expected 29 rows (Oct 26, 2026 STIP print), 12 pure"); layerFail++; } }', 'AL pipeline 27->29')

# KY calendar strip: 14 lettings in the record
rep('if (ticks !== 12) { console.log(`KY CALENDAR STRIP WRONG — expected 12 scheduled lettings, found ${ticks}`); bidFail++; } }',
    'if (ticks !== 14) { console.log(`KY CALENDAR STRIP WRONG — expected 14 lettings in the record, found ${ticks}`); bidFail++; } }', 'KY strip 12->14')

# LETSAMPLE: SC 11->13, KY 12->14
rep('const LSS = t.LETSAMPLE; if (!LSS.SC || LSS.SC.length !== 11 ||', 'const LSS = t.LETSAMPLE; if (!LSS.SC || LSS.SC.length !== 13 ||', 'LETSAMPLE SC 11->13')
rep('|| !LSS.KY || LSS.KY.length !== 12 ||', '|| !LSS.KY || LSS.KY.length !== 14 ||', 'LETSAMPLE KY 12->14')

# KY read: 14 lettings, 451 calls, 1,153 bids, 382 awarded, 28 lighting
rep('if (n !== 395 || K.contracts !== 395 || bids !== 1011 || awn !== 370 || allAw !== 370 || lit.length !== 24 || !lit.every(c => c.award === "awarded" && /\\{KY-\\d+\\}/.test(c.awardNote)) || !splitOk || K.lettings.length !== 12) { console.log("KY READ WRONG"); bidFail++; }',
    'if (n !== 451 || K.contracts !== 451 || bids !== 1153 || awn !== 382 || allAw !== 382 || lit.length !== 28 || !lit.every(c => c.award === "awarded" && /\\{KY-\\d+\\}/.test(c.awardNote)) || !splitOk || K.lettings.length !== 14) { console.log("KY READ WRONG"); bidFail++; }', 'KY read pins')
rep('console.log(`KY twelve lettings:', 'console.log(`KY fourteen lettings:', 'KY label')

# AR read: 10 lettings, 212 jobs, 646 bids, all awarded, 12 lighting; the census check excludes the two lettings outside its window
rep('const q = d => lit.reduce((a, c) => a + c.items.filter(it => it.section === "714" && it.desc.includes(d) && c.let !== "Aug 12, 2026").reduce((b, it) => b + it.qty, 0), 0);',
    'const q = d => lit.reduce((a, c) => a + c.items.filter(it => it.section === "714" && it.desc.includes(d) && c.let !== "Aug 12, 2026" && c.let !== "Sep 23, 2026").reduce((b, it) => b + it.qty, 0), 0);', 'AR census window')
rep('if (n !== 203 || A.contracts !== 203 || A.contractsRead !== 203 || bids !== 614 || awn !== 203 || lit.length !== 10 || !lit.every(c => c.award === "awarded" && /\\{AR-\\d+\\}/.test(c.awardNote)) || !splitOk || !census || A.lettings.length !== 9) { console.log("AR READ WRONG"); bidFail++; } } }',
    'if (n !== 212 || A.contracts !== 212 || A.contractsRead !== 212 || bids !== 646 || awn !== 212 || lit.length !== 12 || !lit.every(c => c.award === "awarded" && /\\{AR-\\d+\\}/.test(c.awardNote)) || !splitOk || !census || A.lettings.length !== 10) { console.log("AR READ WRONG"); bidFail++; } } }', 'AR read pins')
rep('console.log(`AR nine lettings:', 'console.log(`AR ten lettings:', 'AR label')

# AL read: 12 lettings, 233 contracts, 667 bids, 12 lighting; letting[11] = Jul 31, 2026
rep('if (n !== 222 || A.contracts !== 222 || A.contractsRead !== 222 || bids !== 628 || lit.length !== 12 || !lit.every(c => c.award === "awarded") || !A.all.every(c => c.award === "awarded") || !splitOk || miss.length || A.lettings.length !== 11 || A.lettings[0].iso !== "2025-07-25" || A.lettings[10].iso !== "2026-06-26") { console.log("AL READ WRONG"); bidFail++; } } }',
    'if (n !== 233 || A.contracts !== 233 || A.contractsRead !== 233 || bids !== 667 || lit.length !== 12 || !lit.every(c => c.award === "awarded") || !A.all.every(c => c.award === "awarded") || !splitOk || miss.length || A.lettings.length !== 12 || A.lettings[0].iso !== "2025-07-25" || A.lettings[11].iso !== "2026-07-31") { console.log("AL READ WRONG"); bidFail++; } } }', 'AL read pins')
rep('console.log(`AL eleven lettings:', 'console.log(`AL twelve lettings:', 'AL label')

# SC read: 13 lettings, 286 calls (264 read), 1,067 bids, 13 lighting, Aug 11 read 13, Oct 13 read 0
rep('const aug = S.lettings.find(l => l.iso === "2026-08-11");\n      if (n !== 245 || S.contracts !== 245 || S.contractsRead !== 225 || bids !== 908 || lit.length !== 11 || lit.some(c => c.award === "awarded") || !splitOk || S.lettings.length !== 11 || !aug || aug.read !== 0) { console.log("SC READ WRONG"); bidFail++; } } }',
    'const aug = S.lettings.find(l => l.iso === "2026-08-11"), oct = S.lettings.find(l => l.iso === "2026-10-13");\n      if (n !== 286 || S.contracts !== 286 || S.contractsRead !== 264 || bids !== 1067 || lit.length !== 13 || lit.some(c => c.award === "awarded") || !splitOk || S.lettings.length !== 13 || !aug || aug.read !== 13 || !oct || oct.read !== 0) { console.log("SC READ WRONG"); bidFail++; } } }', 'SC read pins')
rep('console.log(`SC eleven lettings:', 'console.log(`SC thirteen lettings:', 'SC label')

# TN read: 11 lettings, 412 calls (398 read), 1,116 bids, 399 awarded, 26 lighting, 14 unread
rep('if (n !== 386 || T.contracts !== 386 || T.contractsRead !== 373 || bids !== 1036 || awN !== 373 || lit.length !== 24 || l1.length !== 3 || !lit.every(c => c.award === "awarded") || !splitOk || !gate || T.lettings.length !== 10 || unread.length !== 13 || !unread.every(c => c.award === "rejected" || /PENDING/.test(c.note || "")) || ab.length !== 3) { console.log("TN READ WRONG"); bidFail++; }',
    'if (n !== 412 || T.contracts !== 412 || T.contractsRead !== 398 || bids !== 1116 || awN !== 399 || lit.length !== 26 || l1.length !== 3 || !lit.every(c => c.award === "awarded") || !splitOk || !gate || T.lettings.length !== 11 || unread.length !== 14 || !unread.every(c => c.award === "rejected" || /PENDING|resolved/.test(c.note || "")) || ab.length !== 3) { console.log("TN READ WRONG"); bidFail++; }', 'TN read pins')
rep('console.log(`TN ten lettings:', 'console.log(`TN eleven lettings:', 'TN label')
rep('const LSS = t.LETSAMPLE; if (!LSS.TN || LSS.TN.length !== 10 || LSS.TN.reduce((a, l) => a + l.rows.length, 0) !== 386) { console.log("TN LETSAMPLE WRONG"); bidFail++; } } }',
    'const LSS = t.LETSAMPLE; if (!LSS.TN || LSS.TN.length !== 11 || LSS.TN.reduce((a, l) => a + l.rows.length, 0) !== 412) { console.log("TN LETSAMPLE WRONG"); bidFail++; } } }', 'TN LETSAMPLE')

# MS read: 27 lettings, 184 calls, 676 bids, 158 awarded, 14 rejected; award lists now outstanding for Sep 22 / Sep 29
rep('if (n !== 170 || M.contracts !== 170 || M.contractsRead !== 170 || bids !== 616 || awN !== 146 || rej !== 12 || lit.length !== 6 || lit.filter(c => c.award === "awarded").length !== 5 || !splitOk || !gate || M.lettings.length !== 24 || !feb3 || feb3.read !== 17 || noaw.join(",") !== "2026-08-21,2026-08-25" || notLow !== 4) { console.log("MS READ WRONG"); bidFail++; }',
    'if (n !== 184 || M.contracts !== 184 || M.contractsRead !== 184 || bids !== 676 || awN !== 158 || rej !== 14 || lit.length !== 6 || lit.filter(c => c.award === "awarded").length !== 5 || lit.filter(c => c.award === "rejected").length !== 1 || !splitOk || !gate || M.lettings.length !== 27 || !feb3 || feb3.read !== 17 || noaw.join(",") !== "2026-09-22,2026-09-29" || notLow !== 4) { console.log("MS READ WRONG"); bidFail++; }', 'MS read pins')
rep('console.log(`MS twenty-four lettings:', 'console.log(`MS twenty-seven lettings:', 'MS label')
rep('const LSS = t.LETSAMPLE; if (!LSS.MS || LSS.MS.length !== 24 || LSS.MS.reduce((a, l) => a + l.rows.length, 0) !== 170) { console.log("MS LETSAMPLE WRONG"); bidFail++; } } }',
    'const LSS = t.LETSAMPLE; if (!LSS.MS || LSS.MS.length !== 27 || LSS.MS.reduce((a, l) => a + l.rows.length, 0) !== 184) { console.log("MS LETSAMPLE WRONG"); bidFail++; } } }', 'MS LETSAMPLE')

# freshness / diff block: totals move; last snapshot is 10.1a, so the diff against it is this refresh
rep('if (!first || !last || t.SNAPSHOTS.length < 8 || first.build !== "3.18" || !live.states.NC || live.total.lighting !== 130 || live.total.l2 !== last.total.l2) ok = false;',
    'if (!first || !last || t.SNAPSHOTS.length < 9 || first.build !== "3.18" || last.build !== "10.1a" || !live.states.NC || live.total.lighting !== 140 || live.total.l2 <= last.total.l2) ok = false;', 'freshness totals')
rep('const d0 = t.whatChanged(first, live), d1 = t.whatChanged(last, live);\n    if (d0.length < 5 || !d0.some(i => /Division channel/.test(i.text)) || !d0.some(i => /item shape/.test(i.text)) || !d0.some(i => /sources/.test(i.text))) ok = false;',
    'const d0 = t.whatChanged(first, live), d1 = t.whatChanged(last, live);\n    if (d0.length < 5 || !d0.some(i => /Division channel/.test(i.text)) || !d0.some(i => /item shape/.test(i.text)) || !d0.some(i => /sources/.test(i.text))) ok = false;\n    if (d1.length < 8 || !d1.some(i => /award/.test(i.kind))) { console.log("DIFF vs 10.1a EMPTY — the refresh should register"); ok = false; }', 'diff vs 10.1a')
# award queue: GA 2 stale + SC 13 unknown; a rejected contract is resolved and never queues
rep('const q = t.awardQueue(); if (q.some(r => r.st === "AL") || q.filter(r => r.st === "SC").length !== 11 || q.some(r => r.st === "SC" && r.cls !== "unknown") || !q.some(r => r.st === "GA" && r.cls === "stale")) ok = false;',
    'const q = t.awardQueue(); if (q.some(r => r.st === "AL") || q.some(r => r.st === "MS") || q.filter(r => r.st === "SC").length !== 13 || q.some(r => r.st === "SC" && r.cls !== "unknown") || !q.some(r => r.st === "GA" && r.cls === "stale") || q.length !== 15) ok = false;', 'award queue')

open('work/verify.js', 'w', encoding='utf-8').write(v)
print('verify.js re-pinned')
