# Lighting intelligence infrastructure

Established 2026-10-27 from Claude's complete Build 10.1b kit and the existing repository.
This infrastructure work is authorized separately from the roadmap's next research milestone.
The product build remains 10.1b: no research milestone or new evidence is claimed.

## Verified production connection — 2026-10-27

- Live site: https://lightingintelligencelayer.netlify.app/ — Build 10.1b published from GitHub.
- Infrastructure PR: https://github.com/SK87-Cyber/lsi-territory-intelligence/pull/1 — merged after both verification runs passed.
- Initial database import: https://github.com/SK87-Cyber/lsi-territory-intelligence/actions/runs/40542048855 — 2,859 records; private schema and RLS checks passed.
- The lighting database secret is saved in this repository. PanelMade remains separate.

## Connected components

- GitHub `SK87-Cyber/lsi-territory-intelligence`: complete source, recovered logos and geometry,
  refresh parsers, parsed deltas, immutable migrations and workflow definitions.
- Netlify `lightingintelligencelayer`: builds `main` using `netlify.toml`. The build generates
  a self-contained `dist/index.html` only after the existing acceptance gate succeeds.
- Dedicated Supabase project `lsi-territory-intelligence` (`jzfteehjkzxdzgisaxrf`, Ohio):
  server-side evidence store in the private `lsi` schema. Separate from PanelMade.
- GitHub Actions secret `LSI_DATABASE_URL`: the project's TLS session-pooler URI.
  No credentials belong in source, Netlify's browser bundle, exported snapshots, or chat.

## What runs

1. Every push/PR runs the existing research acceptance gate, then tests import idempotence,
   change history, transaction rollback, and private-schema access against disposable Postgres.
2. Pushes to `main` and manual dispatch of **Publish validated database snapshot** rebuild
   the site, apply versioned migrations, import validated records, and run access checks.
   The import is one transaction and is serialized with a database advisory lock.
3. Netlify builds the same committed source independently. A failed build retains the last
   successful deployment. Supabase unavailability does not make the static briefing disappear.
4. **Daily source review queue** runs at 11:30 UTC (07:30 Eastern daylight time / 06:30 standard).
   It checks at most sixteen government URLs with HEAD requests, no redirect following,
   a 15-second request timeout and a one-second spacing; non-government/login-gated sources
   remain manual. It calculates dated-layer review deadlines and stores observations in Supabase.
   Its Markdown/JSON report is available in the Actions summary and 90-day artifacts.

Source-health checks do NOT download full documents, parse new lettings, mark facts verified,
change QPL status, or turn apparent bids into awards. Changed artifacts still need a reconciled,
cited research update committed to the repository. Georgia/Bid Express remains owner-gated.
GitHub's scheduler can run late; this is not a guaranteed real-time monitor.

## Persistent data and recovery

`lsi.releases` stores complete immutable imported JSON snapshots with build, source hash and git
revision. `record_versions` retains every distinct historical payload. `records` is the current
projection; `change_events` records additions, changes and removals. Original data is preserved
even when a record leaves the current projection. Typed views expose contract money as decimal
values and keep the source payload alongside it. Missing values remain null.

The export includes states, numbered sources, available contracts, projects, dated public contacts,
manufacturer evidence, ownership, freshness dates, year registries and historical summaries.
The NC YEAR registry does not supply the same all-contract list as the other states: its full
published year registry is retained, but absent per-contract records are not manufactured.
Artifact HTTP retrieval time and the research's actual as-of date are different concepts.

Normal site rollback: revert the research/build commit in GitHub, rebuild and publish the earlier
validated source. For database rollback, run `python scripts/restore_snapshot.py <release-hash>`
from an authorized server with `LSI_DATABASE_URL`. It appends a dated recovery release from the
stored snapshot and restores the current projection while retaining every old version and event.
An ordinary repeated import remains a no-op. Retain GitHub source and original-kit archives
independently of Supabase. The free Supabase project is not a substitute for an independent backup.

All tables have RLS. `anon` and `authenticated` have no schema or table access. No public read
policy, email login, user-management flow, or service-role key is needed in the static site.
Adding a live/private workflow UI later requires an explicit access design and a new migration.

## First connection / credential rotation

Supabase > Connect > Direct > Session pooler > URI. Insert the actual database password
(percent-encoded if necessary), and include `sslmode=require`. Save the complete value as the
GitHub repository Actions secret `LSI_DATABASE_URL`. Run the database publishing workflow and
check both the import summary and private-schema smoke result. Never run integration tests
against this production database. On rotation, update the same secret and rerun publishing.

## Updating the research

Read HANDOFF.md and ROADMAP.md first. Add source references append-only. Use the state-specific
parser; preserve its reconciliation gate. Review changed facts, awards and manufacturer eligibility.
Update `template.html` surgically, then BUILD/ROADMAP_STATUS only if a research build changes.
Run `npm run build` and `npm test`; commit the complete source and let CI deploy it.
Do not hand-edit `dist/index.html` or independently edit current database facts: the committed,
reviewed research remains the publication authority. A daily health check is a review queue,
not a promise that all underlying research updates itself automatically.

## Verifier note — 2026-10-29

`verify.js` compared local-time page dates against UTC test dates (`toISOString()`), so the people-ledger SLA
boundary tests flipped between 8 pm Eastern and midnight. It now uses local calendar dates throughout
(`localISO`), matching the page. CI runs in UTC and was unaffected; evening local runs were.
`freshness.next` in the snapshot is clock-derived (documented in `scripts/export_data.cjs`), so a push after a
letting date passes records a small, accurate change event for that state; it is not a research change.

## Scheduled retrieval — added 2026-11-15

**Weekly scheduled retrieval** (`.github/workflows/retrieval.yml`, `scripts/retrieve.py`) runs Mondays at 10:17 UTC on a
GitHub-hosted runner. It lists what six public sources have posted and records what is new or changed since the last run:

| Source key | What is listed |
|---|---|
| `nc-lettings` | Newest 300 files in each of the 14 Division letting libraries, Central Letting and the 12 Month Tentative Letting Library |
| `al-procurement` | ALDOT Procurement Office notices and awarded master agreements |
| `ky-contracts` | Every open Transportation agreement (vendor and term; the service does not list titles) |
| `ky-payments` | Payment count and total, current and prior fiscal year, for four lighting and electrical vendors |
| `ga-pay-estimates` | Per contract, how many pay estimates are posted and the newest |
| `tn-progress-payments` | Whether a progress-payment file is posted for each Tennessee lighting contract in the record, and its date |

It reads listings only. It does not open bid documents, mark anything verified, change a research record or publish to the
site. The first run for a source records a baseline and raises no events. After that each new or changed item is a row in
`lsi.watch_events` (private), flagged `lighting` when its title or vendor names lighting. The public run summary shows
counts only. Read the queue with:
`select recorded_at,source,action,lighting,payload from lsi.watch_events where not reviewed order by recorded_at desc`.

Not yet covered: Kentucky pay estimates per contract, the North Carolina vendor portal (needs a page token), and the
browser-only sources in the source registry. Tennessee's folder name for 2026 contracts is unconfirmed, so those report
as not posted until one is found.

### Letting pages — added 2026-11-25

Six more sources list each state's own letting page, so a new letting, its results and its tabulations are flagged the
week they post:

| Source key | What is listed |
|---|---|
| `ky-lettings` | Letting dates, and the documents of the three newest lettings (results, bid item index, addenda, withdrawals) |
| `tn-lettings` | Per-letting pages for this year and next, and the files of the three newest (apparent results, summary of bids, awards) |
| `sc-lettings` | Apparent-bid files on the Bids Received page |
| `ms-lettings` | Every advertised call with its project description (MDOT's letting feed), and the letting dates |
| `al-lettings` | The current letting's files, the newest low bid sheet, and this year's tabulations of bids |
| `ar-lettings` | Apparent bid results, awards lists and bid tabulations |

Georgia is not covered: its tabulations sit behind a Bid Express login. tn.gov refuses some automated requests; the job
retries, and a refused sub-page is picked up the following week. Flagging a letting is not reading it: lighting dollars
still reach the site only through a reviewed read of the bid tabulations.
