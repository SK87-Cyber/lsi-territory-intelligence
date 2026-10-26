# Roadmap — revision 8 (Sep 5, 2026)

**What changed in this revision.** The roadmap is now organized by version. **Version 1.0** is the current build line and closes when Phase 3 closes. **Version 2.0** begins at that point and is everything the platform needs to be a continuously updating briefing tool: the living layer, the derived views, and three trimmed essentials from the old overlays (funding dates, recurring contracts, spec editions). Everything else that was in Phases 6–9 of revision 6 — the financial overlay, contractor-side contacts, the local channel, meeting mode, scheduled alerts — is parked under **Later** by owner decision, to be discussed when 2.0 is in hand. Milestone rule unchanged: one conversation delivers one milestone, and a refresh run is a milestone.

---

## Version 1.0 — Prove it, scale it (current build line)

### 0 · Foundation & source registry — met
Ships: this website, Methodology v2.2, the numbered source registry, evidence classifications (L1–L4, M1–M5), real Census boundaries, personnel-versioning rules.
Done when: every figure traces to a numbered reference, the map renders with no network, and the leadership directory is transcribed person by person. — Met. Open by choice: the active-roads geometry layer (needed by 2.0's corridor view, 5.9).

### 1 · North Carolina end-to-end proof of concept — complete, build 1.11
Unchanged. Fifteen Central lettings, 134 contracts, two independent classifications agreeing on 134 of 134; the Division channel documented and login-gated; every rate labelled a Central-letting rate.

### 2 · Common data platform — 2 of 6 milestones
Ships: normalized tables with event sourcing; the state adapter; the acquisition model in both halves.
Done when: a second state can be added with zero schema changes, with the seven transferable layers populated and the bid-derived five left empty without breaking a view — and a refresh run can update any state without touching render code.
Milestones: 2.1 the layer split ✓ · 2.2 the briefing pass ✓ · 2.3 the acquisition model — bid-artifact half shipped in 3.8; the retrieval half is specified as the 2.0 refresh run (4.1) · 2.4 normalized tables and event sourcing — required by 4.6 · 2.5 the state adapter — one file per DOT · 2.6 the contract record — the 3.8 schema (every bidder's line, quantities, award and availability dates, three-way lighting split) made the only shape a read may write.

### 3 · Eight-state rollout and the bid reads — build 3.13
Ships: each state's ownership and funding model, decision-maker, pipeline and contacts from its own record; then item-level bid reads in the order the catalogue set.
Milestones: 3.1–3.7 the eight states ✓ · 3.8 the bid catalogue ✓ · 3.9 Georgia (fourteen lettings) ✓ · 3.10 Kentucky (twelve) ✓ · 3.13 the generic competition record ✓ · **3.11 Arkansas** — the control read · **3.12 the four-state decision** — with NC, GA, KY and AR read, decide per remaining state (TN, MS, SC, AL) between a full year and a one-letting base-rate sample; record the decision and its reason on the state page · **3.14 the design-build read** — RFP scope and technical provisions for lighting on alternative-delivery projects, classified L3, listed with the DB team as buyer; closes the `LUMP` blind spot honestly.
Done when: every state's page explains who owns, funds and approves lighting from its own sources; no comparative metric publishes across incompatible denominators; every state carries either a full-year read or a labelled sample. **This is the close of Version 1.0.**

---

## Version 2.0 — Keep it true (starts at the close of Phase 3)

Pre-flight, one conversation: confirm the GA and KY reads stored every bidder's line and the quantities to the 2.6 schema. If they did, Phase 5's arithmetic views are one build each; if not, two re-reads precede Phase 5.

### 4 · The living layer
Ships: the machinery that makes the product true on a Tuesday, not only on build day.
Milestones:
- **4.1 the refresh run** — a standing milestone type: for each state on its own cadence (KY monthly Thursday, AR eight a year, SC second Tuesday, NC third Tuesday, TN six-to-eight weeks, MS/GA/AL as recorded), fetch the new letting, read it to the contract record, diff the pipeline, write the run to ROADMAP §2. No template change inside a refresh run. Expect two to three conversations a month across eight states, permanently.
- **4.2 freshness** — every figure carries *as-of* and *next expected* from its source's cadence; a source past next-expected shows STALE and fails the build after a grace period.
- **4.3 the award sweep** — a queue of every contract in `apparent` with the date its state's award artifact should exist (TN 2–4 weeks, MS Commission ratification ~3, KY Awards Committee monthly, AR Awards List, NC next Board, GA Bid Review Committee); cleared by the refresh run; nothing leaves `apparent` any other way.
- **4.4 contract lifecycle** — let → awarded → availability/NTP → in construction → complete, with availability from the award artifact and construction status where a DOT publishes it.
- **4.5 the opportunity record** — one entity: pipeline project → letting → award → prime → installer (from 5.3) → DOT contact → product classes and quantities → lifecycle stage → next action date → outcome (contacted, quoted, won, lost).
- **4.6 what changed** — the panel each build opens with: new lighting-bearing contracts, awards confirmed, pipeline moves, contact changes, stale sources. Depends on 2.4.
- **4.7 source health** — every registered source re-resolved and re-parsed each run; dictionaries versioned to spec editions.
Done when: a refresh run completes in one conversation with no template edit, every figure states its own age, and no contract is shown awarded that the sweep did not confirm.

### 5 · Derived intelligence
Ships: the views that are arithmetic on the contract record once three or more states are read. Every view publishes its *n* and its caveat, or does not publish.
Milestones, in the order a rep uses them:
- **5.1 the price book** — per state and year, every bidder's unit price on every lighting item class; labelled *installed price at the prime — a ceiling and benchmark, never a manufacturer price*; validated against ARDOT's weighted averages.
- **5.2 the submittal window** — letting → award → availability lag per state; a dated *call before* on every confirmed lighting contract.
- **5.3 the installer layer** — electrical subcontractors from published subcontractor listings and DBE commitments; repeat installers across eight states as named firms. Firm names only — contacts are the rep's phone call.
- **5.4 dispersion and participation** — spread on lighting items against paving, and bidder counts on lighting contracts against the letting average; only where the tab carries every bidder.
- **5.5 estimate variance** — engineer's estimate against low bid on lighting items where a state prints item-level estimates.
- **5.6 the calendar** — the 3.8 letting strip with fiscal-year and federal-fiscal-year boundaries **and the funding decision dates** (Kentucky's biennial budget, next in the 2028 session; STIP amendment windows; state program rounds) drawn on the same axis; a calendar until a second state-year exists, then a seasonality finding. *(Absorbs the old financial-overlay phase.)*
- **5.7 product mix, spec-to-product fit and spec editions** — mounting heights, wattages, CCT and controls by state from item descriptions; each state's LED specification (warranty, LM-79/80, BUG, CCT, dimming, networked controls) beside the classes bid; **spec edition and date recorded per state and re-read only when an edition changes**; QPL evidence where published; eligibility ≠ installed, always. *(Absorbs the old manufacturer-evidence phase — public record only; no market-share view will ever publish.)*
- **5.8 retrofit rate** — relight against install-only against decommission per state.
- **5.9 propensity scoring** — share of interchange, widening, bridge and preservation contracts that carried lighting per state, applied to every pipeline project as a lighting likelihood with its base rate; corridor view needs the Phase 0 geometry.
- **5.10 relight forecasting** — install-year inventories where public (Georgia first) turned into renewal windows.
- **5.11 recurring contracts** — maintenance, relamping, IDIQ, annual-needs and design-services contracts with incumbent, expiration, options and next expected solicitation, seeded from the 3.8 catalogue; built only where a state publishes its contract records. *(The old recurring-contracts phase, right-sized: two to three conversations.)*
Done when: each view is on the page with its n and caveat; the propensity score shows on every pipeline project in states with a full-year read; the calendar shows every state's next letting and next funding decision; and the opportunity record links to a recurring contract wherever one exists. **This is the close of Version 2.0.**

---

## Later — parked by owner decision, Sep 5, 2026

Not scheduled, not estimated, not on the site. To be discussed once 2.0 is in hand.
- Financial overlay proper — reported allocations, carry-forward snapshots, value-basis tooltips.
- Contractor-side contacts — estimators and purchasing at primes and installers.
- The local channel — agreement-derived city accounts in the five locally-owned states and their procurement portals. Depends on whether LSA sells to cities at all.
- Meeting / executive mode — the curated flow walking the opportunity record.
- Scheduled alerts and digests — the 4.6 panel on a timer with delivery.
- Active-roads geometry beyond what 5.9's corridor view needs.

---

### Sequencing note
Version 2.0 opens with the pre-flight schema check, then 4.1 the first refresh run, then the award sweep and freshness, because every later conversation should run inside the refresh discipline rather than bolt it on. Rough size from build 3.13: Version 1.0 remainder 5–7 conversations; Version 2.0 roughly 8–10 for Phase 4 plus ~7 arithmetic and ~6 research conversations for Phase 5, plus the standing refresh tax of two to three a month.
