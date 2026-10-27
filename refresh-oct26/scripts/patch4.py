#!/usr/bin/env python3
"""Stage 4: calStrip dynamic window (records now exceed twelve months) + the
remaining verify re-pins (recurrence, altdel ladder total, financial join,
accuracy pass, AL letting samples)."""
import sys
sys.path.insert(0, 'scripts')

# ---- template: calStrip window follows the record ----
T = 'work/template.html'
tpl = open(T, encoding='utf-8').read()
def rep(s, old, new, label):
    assert s.count(old) == 1, (label, s.count(old))
    print('edited:', label)
    return s.replace(old, new)

tpl = rep(tpl, '  ticks=ticks.filter(t=>t.d);\n  const maxLit=Math.max(1,...ticks.map(t=>t.lit||0));\n  const cells=[]; for(let i=0;i<12;i++){',
 '  ticks=ticks.filter(t=>t.d);\n  const nMo=Math.max(12, 1+Math.max(11,...ticks.map(t=>(t.d.y-y0)*12+(t.d.mo-m0))));  /* 10.1b: the record outgrew twelve months — the strip follows it */\n  const maxLit=Math.max(1,...ticks.map(t=>t.lit||0));\n  const cells=[]; for(let i=0;i<nMo;i++){',
 'calStrip window')
tpl = rep(tpl, '<div class="calstrip">${cells.join("")}</div>',
 '<div class="calstrip" style="grid-template-columns:repeat(${nMo},1fr)">${cells.join("")}</div>', 'calStrip grid')
tpl = rep(tpl, 'const inWin=ticks.filter(t=>{ const k=(t.d.y-y0)*12+(t.d.mo-m0); return k>=0&&k<12; }).length; return inWin?inWin+" letting date"+(inWin===1?"":"s")+" in the twelve months shown"',
 'const inWin=ticks.filter(t=>{ const k=(t.d.y-y0)*12+(t.d.mo-m0); return k>=0&&k<nMo; }).length; return inWin?inWin+" letting date"+(inWin===1?"":"s")+" in the "+(nMo===12?"twelve":nMo)+" months shown"', 'calStrip caption')
open(T, 'w', encoding='utf-8').write(tpl)

# ---- verify re-pins ----
v = open('work/verify.js', encoding='utf-8').read()
def repv(old, new, label):
    global v
    assert v.count(old) == 1, (label, v.count(old))
    v = v.replace(old, new)
    print('re-pinned:', label)

# NC strip check already compares ticks to lettings.length — passes once the window grows. KY strip pin set to 14 earlier.
repv('const exp = { GA: 40, TN: 112, SC: 117, AL: 10, MS: 13, KY: 29, AR: 6, NC: 4 }; const got = {};',
     'const exp = { GA: 40, TN: 117, SC: 136, AL: 11, MS: 13, KY: 29, AR: 7, NC: 4 }; const got = {};', 'recurrence register')
repv('const cal = pages.find(h => /Bid Express calendar, read/.test(h) && /<th>Kind<\\/th>/.test(h)) || "";',
     'const cal = pages.find(h => /letting pages, read/.test(h) && /<th>Kind<\\/th>/.test(h)) || "";', 'calendar page regex')
repv('|| !t.BX_UPCOMING.TN || t.BX_UPCOMING.TN[0].date !== "2026-10-02" ||',
     '|| !t.BX_UPCOMING.TN || t.BX_UPCOMING.TN[0].date !== "2026-11-06" ||', 'BX TN next date')
repv('|| Math.round(lad) !== 74892576) { console.log("ALTDEL WRONG"', '|| Math.round(lad) !== 76491266) { console.log("ALTDEL WRONG"', 'altdel ladder total')
repv('const exp = { AL: [3, 24, true], GA: [0, 15, true], NC: [0, 14, true], SC: [0, 3, true], MS: [0, 2, true], AR: [0, 0, true], KY: [0, 0, false], TN: [0, 0, false] }; const got = {};',
     'const exp = { AL: [3, 26, true], GA: [0, 15, true], NC: [0, 14, true], SC: [0, 3, true], MS: [0, 2, true], AR: [0, 0, true], KY: [0, 0, false], TN: [0, 0, false] }; const got = {};', 'AL pipe join 24->26 carried')
repv('if (nC !== 130 || bad || rowsAll.length !== 130 || keep50 !== 112 ||', 'if (nC !== 140 || bad || rowsAll.length !== 140 || keep50 !== 121 ||', 'accuracy 130->140, keep50 112->121')
repv('if (LSS.length !== 11 || LSS.some(l => l.kind !== "tab") || missing.length) { console.log("AL LETTING SAMPLES WRONG"); bidFail++; } }',
     'if (LSS.length !== 12 || LSS.some(l => l.kind !== "tab") || missing.length) { console.log("AL LETTING SAMPLES WRONG"); bidFail++; } }', 'AL LETS 11->12')
# GA lettings layer: stale only the owner can clear (Bid Express login) — reported like an overdue award, never refused
repv('if (f.cls === "stale") (f.layer === "Awards" ? awardStale : stale).push(s.id + ":" + f.layer); }); });',
     'if (f.cls === "stale") ((f.layer === "Awards" || (s.id === "GA" && f.layer === "Lettings read")) ? awardStale : stale).push(s.id + ":" + f.layer); }); });   /* 10.1b: GA\'s letting artifacts exist only behind the owner\'s Bid Express login — reported, not refused, like an overdue award */', 'GA lettings stale reported not refused')
open('work/verify.js', 'w', encoding='utf-8').write(v)
print('patch4 done')
