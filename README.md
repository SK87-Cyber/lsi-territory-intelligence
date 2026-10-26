# Southeast DOT Lighting Intelligence

Market-intelligence portal tracking roadway lighting contracts across eight southeastern state DOTs (NC, SC, GA, AL, MS, TN, KY, AR). Built by Lighting Solutions of Alabama with Cooper Lighting Solutions.

Start with [HANDOFF.md](HANDOFF.md) (how the thing is made) and [ROADMAP.md](ROADMAP.md) §0 and §2 (what to do next).

## Layout

| Path | What it is |
|---|---|
| `template.html` | The entire site. **The only file you edit.** |
| `build.py` | Stamps the build number, embeds logos + geometry → `southeast-dot-lighting-intelligence-build-X.Y.html` |
| `verify.js` | Headless acceptance gate. Must pass before anything ships. |
| `HANDOFF.md` | Kit inventory, working loop, map of `template.html`, rules that survive every session. |
| `ROADMAP.md` | Milestone queue, current status, standing decisions. Updated last, every run. |
| `lsi-logo.png`, `cooper-logo.png` | Brand marks, at the repo root where `build.py` reads them (not yet committed — see below). |
| `dist/` | The built HTML for the current build, committed once per milestone. Never edited by hand. |
| `docs/research/` | Quote-and-cite research briefs that produced the data. |
| `docs/reviews/` | Logic reviews and accuracy passes. |
| `docs/ROADMAP-ARCHIVE.md` | Full run-by-run audit trail (append-only). |
| `docs/archive/` | Superseded handoff/roadmap versions. |

## Working loop

One conversation = one milestone. Build number = Phase.Milestone reached.

```
git pull
# edit template.html (surgical edits only)
python3 build.py X.Y --out dist
node verify.js dist/southeast-dot-lighting-intelligence-build-X.Y.html
# update ROADMAP.md and ROADMAP_STATUS in template.html
git add -A && git commit -m "Build X.Y: <milestone>" && git tag vX.Y
git push && git push --tags
```

## Not yet in this repo

The kit zip listed in HANDOFF.md §2 contains ~90 more files (the per-state parsers, `patch*.py`, `fund/`, `mfr/`, `bidx/`, `*_year.json`, `geo-se.json`, `snapshots.json`, the logos). Those lived only in the handoff zip and are not in project knowledge — add them from the latest kit zip when available. `build.py` needs the two logos beside it to run.
