# Lighting intelligence infrastructure

Established 2026-10-27 from Claude's complete Build 10.1b kit and the existing repository.
This infrastructure work is authorized separately from the roadmap's next research milestone.
The product build remains 10.1b: no research milestone or new evidence is claimed.

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

Normal rollback: revert the research/build commit in GitHub, rebuild and publish the earlier
validated source. A previously seen snapshot import is deliberately a no-op, so database
restoration requires importing a new release from the earlier source with a new release identity;
do not delete the immutable releases or versions. Retain GitHub source and original-kit archives
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
