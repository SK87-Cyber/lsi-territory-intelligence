# Milestone 3.8 research — the bid layer, catalogued across eight states
**Researched Sep 3–4, 2026. Build pending: the kit was not uploaded to this conversation. This file is the complete input for the 3.8 build — it fixes the universal contract-record schema, catalogues each state's bid artifacts against the four-item checklist, and proposes the roadmap re-cut (3.8 catalogue → 3.9 Kentucky → 3.10 Arkansas). Nothing below has been built.**

Owner decision this file executes: "Georgia first, bids after" (Sep 2) — the bid/contractor layer reopens, designed from all eight states' evidence, with NC's read as the reference adapter. Planning conversation of Sep 3 set the frame: the bid layer is an **evidence and quantities layer, never a market-size instrument**; the ownership model sets each state's expected base rate; every figure carries a channel label.

---

## 1. The four-item checklist — what a state needs before an item read can publish

A state's DOT lettings can be read for lighting only when all four exist publicly. A state missing one gets a labelled partial, never a verdict.

| # | Requirement | Why | NC reference |
|---|---|---|---|
| 1 | **Machine-readable item-level bid tabs** — every contract in the letting, ideally every bidder | Without items there is no classification; without all bidders there is no price dispersion | XLS bid tabs (Tier 2, owner download); PDF truncates |
| 2 | **A pay-item scheme with a lighting section** in the state spec book / item master | The structural half of the classifier (code family or spec section) needs something to test against | Division 14, sections 1400–1413, codes 5000–5299 |
| 3 | **An award artifact** — the state's equivalent of NCDOT's stamped Item C | Apparent ≠ awarded (rule 3) | Item C stamped AWARDED, or Board minutes |
| 4 | **A printed contract total per bidder** | Completeness anchor: item rows summed by bidder must equal it, or the read does not publish | Item C totals; all 134 reconcile to the cent |

Plus, for every state: the **second channel** (below-threshold / district lettings) and its access; the **false-friend class** to exclude; **on-call / maintenance lighting contracts** spotted (Phase 6 material); the **letting calendar** for the annual time-graph view.

## 2. The universal contract record (schema for `YEAR[id]` in every state)

Fixed here so the Kentucky read (3.9) is built to it from line one. Every field NC already carries survives; five are new (marked ★).

```
contract: {
  id, letting_date, call, state, channel ("central"|"district"|"local-let"),
  county[], territory (Division/District/Region label), tip_or_project_no,
  title, project_type ★ (agency's own type string — feeds propensity scoring later),
  bidders: n (from the award artifact, not the tabs), low_bidder, low_amt, est, diff_pct,
  award: {status: "apparent"|"awarded"|"rejected", artifact, date ★, availability_date ★, completion},
  cls: "L1"|"L2"|"L3"|"LUMP"|"None"|"UNKNOWN",
  lighting: {
    identified,                        // everything lighting, at the low bidder
    split: {hardware, infrastructure, work} ★,   // poles/luminaires/drive units/cabinets · conduit/feeder/JB/foundations/service · remove/relocate/reinstall
    range: [min,max] across bidders,   // only if all bidders' items are in the tab
    quantities: [{class, qty, unit, wattage?, mount_ht?}] ★,   // "44 high-mast luminaires 335–560W", "6 × 120' standards"
    items: [{line, code, section, desc, qty, unit, prices:{bidder: unit_price}}] ★  // keep EVERY bidder's line — price book, dispersion
  },
  evidence (with {ST-n} citation tokens), exclusions_applied[]
}
```

Display consequence (owner decision pending): the lighting tile shows **one total with three component bars** (hardware / electrical infrastructure / work) in place of identified-vs-product, plus a quantities line and a channel label. `product` (NC's current figure) equals `split.hardware` and is kept for continuity.

Derived views this schema unlocks without further research (from the Sep 3 planning list): per-state lighting price book (unit prices by item class, year, state); price dispersion on lighting items vs the contract; submittal window (letting → award → availability lag); retrofit rate (remove+install vs install-only); lighting propensity by `project_type`; annual letting-calendar strips per state.

## 3. The catalogue — eight states against the checklist

Observed Sep 3, 2026 unless marked. "◐" = exists but not yet confirmed by a read; "✗" = not public; "?" = unprobed.

### 3.1 Kentucky — KYTC · **anchor state for 3.9** · checklist 4/4 ✓

| Item | Finding |
|---|---|
| Tabs | **`Unit Bid Tabulations.pdf`** per letting at `transportation.ky.gov/Construction-Procurement/Publications/YYYY-MM-DD/`. **Item-level, every bidder** (columns Bidder1…Bidder12 with continuation blocks), engineer's estimate and % vs estimate, bidder count, Contid, county, District, SYP item no., completion time — all printed per contract. Whole letting readable in one fetch (May 21, 2021 sample: ~37 calls). Text-extractable; no code column printed — item **descriptions are standardised** (KYTC item master), so the dictionary keys on description + the KYTC bid-item code list (Tier 1, "Bid Item Quantities" on the procurement page). |
| Lighting section | Observed in the tab itself (Call 103, Oldham Co., May 2021): `POLE 40 FT MTG HT`, `BRACKET 4/6/8/10 FT`, `POLE BASE`, `TRANSFORMER BASE`, `LED LUMINAIRE` (9 @ $1,500), `WIRE-NO. 6/8/12`, `REMOVE LIGHTING` — a clean, self-contained lighting item family. Spec section number to be taken from the **2026 Standard Specifications** (effective Jan 2026 letting) — do not assert from memory. |
| Award artifact | `Letting Results.pdf` (contract-level, all bidders, engineer's estimate) posted bid day; **results updated "Award" / "Reject" after the Awards Committee** (Contractor's Guide, 3/27/2025). ◐ Confirm whether the Award/Reject flag lives on the letting web page (SharePoint) or a revised PDF — one check at 3.9 start. |
| Completeness anchor | `Total Bid` per bidder printed at the foot of every contract ✓ |
| Calendar | **Monthly, Thursdays** — 2026: Jan 29, Feb 19, Mar 26 (revised from Mar 19), Apr 23, May 21, Jun 25, Jul 23, Aug 20, Sep 24, Oct 22, Nov 19, Dec 10. **2027 already published** (Jan 28 … Dec 9). Advertisement ~3 weeks prior (federal) / 1 week (state). |
| Second channel | District-let / maintenance purchase orders — ? unprobed. State-owned model means the central letting *should* carry most lighting; verify with the read. |
| False friend | Navigational (marine) lighting — already recorded from HB 533. Also `INSTALL LED BEACON`, `INSTALL PEDESTRIAN HEAD-LED`, `INSTALL LED SIGNAL` (signal heads, not roadway lighting). |
| Expected base rate | **Highest of the eight** — KYTC installs and maintains its own lighting (KTC-17-23); $5.30M enacted in HB 533. If the read finds little, the dictionary is wrong. |

### 3.2 Arkansas — ARDOT · **control state for 3.10** · checklist 4/4 ✓

| Item | Finding |
|---|---|
| Tabs | **`Bid Tabulation Summary`** PDF per letting session (AM/PM) at `media.ark.org/ardot/<Mon>-YY-Bid-Tabs[_AM|_PM].pdf`, indexed at ardot.gov → Program Management → Bid Tabulations. **Item-level, every bidder, with ARDOT's own six-digit item codes** (spec section = first three digits: `714728 REMOVE AND REINSTALL ROADWAY LIGHTING`, `708451 ELECTRICAL CONDUCTORS FOR LUMINAIRES`, `710004 NON-METALLIC CONDUIT`). Prints contract ID, counties, route/section, contract description, rank table with % of low, A+C (cost-plus-time) flag where used. Archive **back to 2010**. Engineer's estimate **not** printed (some editions titled "without Estimates"). |
| Lighting section | **Section 714 = roadway lighting; 708 = conductors; 710 = conduit** (observed in the Aug 12, 2026 tab, Call 040). Full item list in the ARDOT Standard Specifications (Tier 1). |
| Award artifact | **Awards Lists** page — per-letting PDF (`<Mon>-DD-YYYY-Letting-Awards-List.pdf`) printing contractor, amount, and status incl. `ALL BIDS REJECTED` / `NO BIDS RECEIVED`; indexed back to 2001 (roadmap §10.2i). Also **Apparent Bid Results** on letting day. |
| Completeness anchor | Section subtotals per bidder + rank-table base bid ✓ |
| Calendar | **Eight lettings in 2026**: Jan 21, Mar 4, Apr 8, May 20, Jun 24, Aug 12, Sep 23, Nov 4 — roughly six-week spacing, some split AM/PM. Ads and plans 4 weeks prior. |
| Bonus | **Weighted Average Prices** page — ARDOT publishes unit-price averages itself; the price-book view (§2) can be validated against it. |
| False friend | `604096 PORTABLE CONSTRUCTION LIGHTING` (temporary, by the day) — the ARDOT twin of NC's §1413. |
| Expected base rate | Low — request state; ARDOT lets illumination only inside its own projects. A low finding *confirms* the ownership model. |

### 3.3 Georgia — GDOT · checklist 3/4 ✓, tabs gated (free account)

| Item | Finding |
|---|---|
| Tabs | **Since Oct 13, 2023 a BidX.com account is required to view GDOT bid tabulations** (GDOT Office of Engineering Services guide, rev. 4/29/2025: "Do not try to create anything other than a **free** account"). Tabs are item-level, all bidders, exportable CSV/TSV from BidX. → **Tier 3, but zero-cost**; the single account also opens NC's Division channel, TN and SC (see §5). |
| Lighting section | GDOT spec book has a dedicated highway-lighting section and electrical sections (numbers to be confirmed from the current spec book at read time — not asserted). Airfield lighting is the known false friend (3.3). |
| Award artifact | Awards/Rejections/Deferrals announcements after the Bid Review Committee (Construction Bidding Administration). Apparent low announced on letting day. |
| Completeness anchor | BidX tab carries bid totals per bidder ✓ (once accessed) |
| Calendar | Monthly letting practice (roadmap §10.2e) — record exact 2026 dates at first retrieval. |
| Second channel | Local-let (LAP) projects — GDOT's LAP manual notes lighting projects specifically route Contract IDs through OFM; a sidewalk/lighting enhancement channel exists outside central lettings. |
| Expected base rate | Moderate-high — the standing **LUMP SUM INTERCHANGE/ROADWAY LIGHTING** line and Lighting Design Services contract mean the DOT buys lighting annually. |

### 3.4 Tennessee — TDOT · checklist ◐, item depth to confirm

| Item | Finding |
|---|---|
| Tabs | Per-letting page at `tn.gov/tdot/tdot-construction-division/bid-lettings/<year>-bid-lettings/<date>-letting.html` carries **Apparent Bid Results** (letting day), **Summary of Bids** (~2–4 weeks later) and **Contract Awards**. The Summary of Bids PDF appears to list bidders item-by-item (Dec 6, 2024 sample) — ◐ **item depth and all-bidder coverage to be confirmed by one read**. Full tabs and addenda live on **Bid Express** (Tier 3, same account as GA). Also a public "Recent Bidders List (Bid Quotes)". |
| Lighting section | TDOT Standard Specifications lighting section and item numbering — to be read at 3.x, not asserted. |
| Award artifact | **`Contract Awards`** PDF per letting (e.g., Oct 3, 2025 letting → awards posted 10/22/25; Nov 7 → 12/02/25) — a **2–4 week letting-to-award lag**, the first observed value for the submittal-window derivation. |
| Completeness anchor | Contract totals in Apparent Bid Results / Summary of Bids ✓ |
| Calendar | ~every 6–8 weeks, seven in 2026 (roadmap §10.2c). |
| Expected base rate | Low-moderate — TDOT builds interstate lighting only where a local agency agrees to maintain; the tab read should show interchange packages and little else. |

### 3.5 Mississippi — MDOT · checklist ◐, strong award artifact

| Item | Finding |
|---|---|
| Tabs | Letting folders at `mdot.ms.gov/bidsystem_data/YYYYMMDD/LETDOCS/`: `…NoticeToContractors.pdf` (with **"Advanced INFORMATION ONLY Items and Quantities" per call — item codes in MDOT's section-letter form, e.g. `618-A001`, `907-618-A001`**), `…AsReadBidResults.pdf` (contract-level, all bidders, **STATE ESTIMATE printed**), `…BidAwards.pdf`. ◐ Item-level tabs with bidder unit prices: probe the same LETDOCS folder for a tabulation file; otherwise Bid Express (Tier 3). |
| Lighting section | MDOT item codes carry the spec section as the prefix — the lighting section number to be taken from the MDOT Standard Specifications at read time. |
| Award artifact | **`BidAwards.pdf`** — prints `AWARDED` per contract with the date the **Commission ratified** the Director's award authorization (e.g., bids Jul 23, 2020 → ratified Aug 11, 2020) and a `POSTPONED, WITHDRAWN, REJECTED` block. **The cleanest award statement after Kentucky's** — and a fixed ~2–3 week lag. |
| Completeness anchor | As-Read totals per bidder ✓ |
| Calendar | Lettings observed Feb 24, Mar 24, Apr 10, 2026 (plus May 28, 2025; May 17, 2024) — **not a fixed monthly Friday**; record the 2026 set at first retrieval. |
| Expected base rate | Low — statute puts in-city lighting on the municipality; MDOT builds lighting as project scope on its own system (roundabouts, interchanges). |

### 3.6 South Carolina — SCDOT · checklist 4/4 ✓ (confirmed Sep 4, 2026)

| Item | Finding |
|---|---|
| Tabs | **`info2.scdot.org/bidtabulations`** — public, browsed by letting year → date → contract, one tabulation per contract (PDF). **Tabs omit rejected and no-bid contracts** (recorded 3.6), so the apparent-bids file, not the tab index, is the census of what let. Full bid files on Bid Express (Tier 3); the **Construction Extranet** (proposals, plans, "Bids as Received") needs a free registration. ◐ Per-contract item depth / all-bidder coverage to confirm by one read. |
| Contract-level results | **`Apparent Bids for Letting of <date>`** PDF at `info2.scdot.org/bidsreceived/apparentbids/` — generated by Bid Express: call order, proposal no., counties, every bidder with bidder ID and total, "(n apparent bids)" per contract. Bid totals are posted "immediately after bids are opened" (Notice to Contractors, May 12, 2026). |
| Lighting section | SCDOT spec book lighting section — to be read at 3.x, not asserted. LED packages inside design-build megaprojects will read `LUMP`. |
| Award artifact | Awards follow the apparent-bids posting; exact artifact name ◐ (Contract Administration Office, 803-737-1750, publishes it — locate at first retrieval). |
| Completeness anchor | Bidder totals in the Apparent Bids file ✓ |
| Calendar | **Monthly, second Tuesday, 2:00:59 PM** (SCDOT Bids Received page); special lettings vary. Observed: Oct 8, 2024; Jan 9, 2024; May 12, 2026. |
| Expected base rate | Low — permit state; lighting on state ROW is installed and maintained by a governmental body or utility. Design-build is the structural blind spot here more than anywhere. |

### 3.7 Alabama — ALDOT · checklist ◐ (least confirmed this run)

| Item | Finding |
|---|---|
| Tabs | ALDOT's letting site (`alletting.dot.state.al.us`) publishes letting results and **bid tabulations** publicly (third-party resource index lists "ALDOT Bid Tabulations" and an annual "Low Bid Tabulations" compendium). ◐ **Three search passes (Sep 3–4) surfaced only aggregators, never the primary page** — the letting site is script-rendered like the STIP portal (§10.2b), so the format check (per-project PDF vs letting-wide; all bidders or low only) is a **Tier 2 owner click**: open the letting site, screenshot one letting's results and one bid tab. |
| Lighting section | ALDOT maintains a **"Unique Pay Item List"** (Construction Information page, Tier 1) — the item master to key the dictionary on; lighting section number from the Standard Specifications at read time. Rail-crossing flashers are the known false friend (3.2d). |
| Award artifact | ALDOT posts awards after bid review (news releases state "pending bid review and award"); exact artifact ◐. |
| Calendar | Monthly letting practice (§10.2b) — 2026 dates to record. |
| Expected base rate | Low-moderate — agreement model, but the STIP already shows 27 roadway-lighting projects ($22.4M pure-lighting scope), so the DOT lettings will carry interchange relights. |

### 3.8 North Carolina — NCDOT · reference adapter, checklist 4/4 (Central), Division channel Tier 3

Unchanged from Phase 1: XLS bid tabs (Tier 2), Division 14 dictionary, stamped Item C / Board minutes, Item C totals; monthly third-Tuesday lettings; Division channel (<$5M) behind Bid Express since 2018. NC's `parse_bidtabs.py` is the template for each state's parser; only its dictionary and column map change.

## 4. Cross-state readings

- **Every state's central letting is publicly readable at item level except Georgia's (free account) — and the two anchors (KY, AR) are the two most complete artifacts in the territory**: every bidder, every item, one file per letting, deep archives (AR to 2010; KY publications back at least to 2021). NC's XLS-behind-a-viewer problem is the exception, not the rule.
- **Award lag is observable and short**: TN 2–4 weeks, MS ~2–3 weeks (Commission ratification), KY after a monthly Awards Committee, NC the following month's Board. This is the "submittal window" derivation's raw material — one date pair per contract.
- **Item-code schemes fall into two kinds**: printed code with spec-section prefix (AR six-digit; MS section-letter; NC ten-digit) vs description-only tabs keyed to a separate item master (KY). The classifier's structural test needs a per-state adapter either way; the naming test and exclusion list transfer as a method.
- **Every state has a temporary-lighting false friend** (NC §1413 Portable Lighting; AR 604096 Portable Construction Lighting; KY portable/temp signal items; expect the same in TN/GA/AL/MS/SC). Plus the state-specific classes already logged: camera mounts (NC), rail flashers (AL), airfield (GA), navigational (KY).
- **Bid Express (free tier) unlocks four states at once**: GA tabs, TN full tabs, SC bid documents, NC Division channel. Registration is the roadmap's §10.3 item 3 and the pause condition is met — **recommend registering before 3.9 so Kentucky's below-threshold channel can be checked in the same run.**
- Commercial aggregators (e.g., DOTestimate) cover all eight states' tabs and unit-price history. Noted as a paid Tier 3 shortcut for the price book; **not a source for the product** — every published figure still traces to the agency's own artifact.

## 5. Proposed roadmap re-cut (for ROADMAP.md §2c in the build conversation)

- **3.8 — Catalogue and schema** (this file → template): add a `BIDSRC[id]` registry (tabs artifact, item scheme, award artifact, anchor, cadence, channel-2 access, false friends) rendered in §10 and on each state page's acquisition panel; add the contract-record schema to HANDOFF §5 as the standard for every future read; add the three-bar lighting tile behind a feature flag (owner decision). **Delivered when:** every state page states its bid-artifact status against the four-item checklist, and HANDOFF carries the schema.
- **3.9 — Kentucky, one letting year** at item level from `Unit Bid Tabulations.pdf`: build the KYTC dictionary from the item master + spec section; two-classifier adjudication; completeness reconciliation to `Total Bid`; award flags from the Awards Committee record; quantities and all-bidder prices captured to the schema. **Delivered when:** the coverage matrix shows KY with bid-derived layers and `verify.js` reconciles every contract.
- **3.10 — Arkansas, one letting year** from the Bid Tabulation Summaries + Awards Lists: the control read (request state). **Delivered when:** AR reconciles and the KY-vs-AR base-rate comparison is on the Overview with channel labels.
- **Then decide** (three states: NC, KY, AR) whether TN/GA/AL/MS/SC get a full year each or a one-letting base-rate sample — the logic review's recommendation for locally-owned states stands until evidence says otherwise.
- **Letting-calendar view** (owner pick "#7"): twelve-month strip per state — every letting a tick, lighting-bearing lettings filled and sized by identified value, green once awarded; fiscal-year and federal-FY boundaries annotated; pipeline construction years as a band. First year labelled a calendar, not a seasonality finding. Can ship with 3.8 for NC/KY/AR dates already in hand (KY 2026–27, AR 2026, NC 2025–26).

## 6. Open probes (agent work, not owner downloads)

1. KY: where the Award/Reject flag is published (web list vs PDF); KYTC bid-item code list URL; 2026 Standard Specifications lighting section number.
2. TN: Summary of Bids item depth; TDOT lighting section number.
3. MS: whether LETDOCS carries an item-level tabulation file; MDOT lighting section number.
4. AL: primary bid-tabulations page and format; award artifact name — **now a Tier 2 owner click** (the site does not surface to search or plain fetch).
5. SC: award artifact name; per-contract tab item depth (tab index and apparent-bids file confirmed Sep 4).
6. GA/TN/SC/NC-Division: **owner registers the free Bid Express account** (Tier 3; one action, four states).

## Sources (for `STATES` sources — append only, per state)

**KY:** KYTC Construction Procurement — Contractor's Guide (3/27/2025), `transportation.ky.gov/Construction-Procurement/Documents/KYTC Construction Procurement--Contractors Guide.pdf` · Unit Bid Tabulations, letting of 5/21/2021, `…/Publications/2021-05-21/Unit Bid Tabulations.pdf` · Letting Results, 2/19/2026, `…/Publications/2026-02-19/Letting Results.pdf` · 2026 Letting Schedule (rev. 1/13/2026) and 2027 Letting Schedule, `…/Construction-Procurement/Documents/Letting Schedule.pdf`.
**AR:** ARDOT Bid Tabulations index, `ardot.gov/divisions/program-management/construction-contract-development/construction-contractors/bid-tabulations/` · Bid Tabulation Summary, letting of 8/12/2026, `media.ark.org/ardot/Aug-26-Bid-Tabs.pdf` · 2026 Letting Schedule, `media.ark.org/ardot/Letting-Schedule_2026.pdf` · Awards List, letting of 5/18/2022, `media.ark.org/ardot/May-18-2022-Letting-Awards-List.pdf` · Weighted Average Prices page (same index).
**GA:** GDOT OES, "Finding Bid Tabulations on BidX" (rev. 4/29/2025), `dot.ga.gov/PartnerSmart/DesignManuals/EngineeringServices/Finding Tabulation of Bids on BidX.pdf` · GDOT LAP Manual ch. 10.
**TN:** TDOT Bid Lettings, `tn.gov/tdot/tdot-construction-division/bid-lettings.html` and the Oct 3 / Nov 7, 2025 letting pages · Summary of Bids, 12/6/2024 letting.
**MS:** MDOT bidsystem_data LETDOCS — Notice to Contractors (5/28/2025, 5/17/2024), As Read Bid Results (3/24/2015), Bid Awards (7/23/2020, 1/15/2021).
**SC:** SCDOT Bids Received page, `info2.scdot.org/bidsreceived` · Bid Tabulations index, `info2.scdot.org/bidtabulations` · Apparent Bids for Letting of Oct 8, 2024, `info2.scdot.org/bidsreceived/apparentbids/10082024 apparent bids.pdf` · Notice to Contractors, May 12, 2026, `info2.scdot.org/currentletting/ConstructionDocs/05122026 Notice to Contractors.pdf`.
**AL:** ALDOT Construction Information page (Unique Pay Item List), `dot.state.al.us/publications/Construction/ConstructionInformation.html` — primary tab page to be cited after the owner click.
