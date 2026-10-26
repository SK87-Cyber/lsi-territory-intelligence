# Code, logic and interface review — after Build 3.13 (Sep 5, 2026)

**Owner's brief:** "Run a code review of everything up to this point — logic review, math and understanding of product; search for errors and ways to improve; think through the cleanness and minimalist nature of the platform — still congested." Executed as **Build 3.13a** (a review run; no milestone delivered, so a letter suffix per the naming rule). Method: the template's script was executed headlessly with every rendered page captured; every `{ST-n}` token was resolved against the sources arrays; the three item-level parsers were re-run against the raw text with their reconciliation re-derived independently; the built page was screenshotted tab by tab at 1300 px.

## 1. The verdict in one paragraph

The product's arithmetic is sound where it is computed from one registry — the $37.1M of identified lighting is the same number on the hero, the glance cards, the state tiles and the read panels, and GA's 8,286 luminaires reconcile from the item rows. The defects were of three kinds: **parsers that proved less than the page claimed** (Georgia's "reconciled" meant the tabulation's own totals matched its ranking, not that the parsed rows summed to them — and 83 contracts did not, because prices in alternate sections were being handed to the wrong bidder); **text written for one state leaking onto another** (the bid-record panel told a Georgia reader "no letting in this state has been read", the tile said "not a twelve-month set yet" under a full year, the hero tooltip showed UNKNOWN for a state with $30M identified); and **stale prose** left from earlier builds. All of the first two kinds are fixed in 3.13a and now guarded by `verify.js`; the aesthetic findings are partly applied (below) and partly left as decisions.

## 2. Defects found and fixed in 3.13a

**Parsers (the integrity layer).**
- *Georgia prices in alternate sections landed on bidder 1.* `parse_gdot_tabs.py` zipped prices left-to-right; a section priced by only the second bidder was attributed to the first. Fixed by placing each price under the nearest "Ext Amount" column edge, as the Kentucky parser already did. Then the parsed rows were summed per column and compared to the printed Contract Grand Totals for the first time: 83 of 325 disagreed, most because line numbers repeat across sections (rows were keyed by line only) and lump-sum markers can be multi-digit `(5123)`. After those fixes **324 of 325 reconcile to the cent**; the one exception (B3CBA2502799-0, a Dec 2025 bridge with no lighting) is GDOT's own rows disagreeing with GDOT's own totals, and it now publishes as UNKNOWN. None of the 36 lighting contracts moved; the figures survived because no lighting item sat in an alternate, which is luck, not proof — hence the gate.
- *Reconciliation is now a gate, not a flag.* Both `ga_build.py` and `ky_build.py` set `cls = UNKNOWN` for any contract whose items do not sum to its total, carry `reconciled` and the residual into `YEAR[id].all`, and `verify.js` fails if a classed contract is unreconciled or the read count drifts. HANDOFF's rule ("a contract that does not reconcile does not publish") had been stated but not implemented.
- *Kentucky's tolerance.* The cent-rounding bound (0.005 × Σ quantity) is mathematically right but could reach $40,794 on a large contract; it is now capped at 0.02 % of the bid. All 363 still reconcile; the largest residual is $619 on a $50.4M bid, and the page says so instead of "to the cent".
- *Kentucky project numbers were lost.* The regex caught "Project Type:" before "Project FBP 5239(023)"; every KY row on the Contractors tab read "Type: GRADE & DRAIN…". Fixed; 395 rows now carry the project number.
- *Split classes made consistent across GA and KY.* Trenching and open-cut are electrical infrastructure (conduit installation), not work; removal, relocation, reinstallation and maintenance are work in both states (Georgia had counted "RELOCATE AND RE-INSTALL" as infrastructure and its work bucket read $0.00; it is $77,540); "INSTALL LUMINAIRE POLE" is work, not hardware. KY's work bucket fell from $993,630 to $252,799.
- *Loop wire (04830) is a signal detector,* not lighting electrical; removed from the shared range. KY identified lighting moves from $5,375,866 to **$5,372,878**. Fused connector kits were already demoted in 3.10.
- *Georgia April 2026:* two lighting contracts had read "Not awarded — absent from the announcement" because only the supplements are on file. They now read "Apparent — absent from the 2 announcement files supplied; the main announcement may be missing", with the cite.

**Rendering (one registry, one truth).**
- The bid-record panel no longer tells a read state it has not been read; the lighting tile says "a full letting year; a channel rate, not a state rate" when the year record is full; the hero tooltip, hero strip parenthetical, glance card and state head all read from `YEAR[id]` for any state, and the "contracts read" figure is now the item-level count (GA 324 of 325 let; KY 363 of 395) with the rate computed on it.
- The glance card distinguishes "no future date posted · last recorded Jun 26, 2026" (AL, SC, MS) from "dates not yet recorded". The calendar note counts only the dates inside the twelve months drawn.
- The call list's "already let" match now runs against every year record (GA, KY, NC), not only the Alabama census; the pipeline tile no longer asserts "not been let yet".
- The `{KY-33}` citation on the Kentucky dictionary pointed past the end of the sources array and rendered as nothing; corrected, and `verify.js` now resolves every token in the file (79 distinct, 0 unresolved).
- Twenty-odd stale sentences replaced ("no letting outside North Carolina has been read", "next: 3.9 Kentucky", the NC-only buyers callout printed on GA/KY, GA_DICT "from the June and July tabulations", "Type 3" luminaires, "PI" as the project label on Kentucky rows, tooltip dollars to nine decimals).

**verify.js.** Gains: a global cite-token check; the reconciliation-gate check per year record; the NC page in the NaN/zero scan; a check that no read state's bid-record panel denies the read. Still open (see §4): scanning the Overview/Contractors/Method output, parsing the numbers in BIDSRC prose against `YEAR`, and asserting `LETSAMPLE` equals `YEAR.all`.

## 3. The interface — what "congested" is, specifically

Screenshots at 1300 px: Overview 7,900 px tall, a state page 6,000, Method 8,250, Contractors 4,400 with everything collapsed. The state page above the fold is the right shape (header, map, four tiles, then one open panel). What congests it:

1. **Three panels open by default** — the territory legend, the ownership panel and the pipeline — each long. The legend duplicates the map. *Applied in 3.13a: the territory legend is collapsed by default on every state (its summary line still names the count and the hover hint).*
2. **Citation runs.** A read panel opened with fourteen bracketed numbers in a row, twice. *Applied: four or more consecutive citations render as one span, `[92–108, 14 sources]`, with the full list on hover.*
3. **Tile prose.** Each tile carries a two-line explanatory sentence under its number; four tiles, eight sentences, before any panel. *Not applied — a decision (§5): shorten to one clause each, or move the sentence to a hover.*
4. **The ownership panel is a wall** — prose, a four-card strip, a "what this means for selling" callout, a two-column gate table. It is the most valuable panel on the page and the hardest to scan. *Not applied — proposal: keep the four cards and the callout open; fold the prose and the gate table under "the full rule".*
5. **Stat tiles that answer methodology, not the rep.** CR1/CR3/HHI on the Contractors tab; "Model: 7/7 transferable · 5/5 bid-derived" in every state header. Both are honest and both belong on the Method tab. *Not applied — decision.*
6. **Overview order.** Glance cards → call list → budget chart → regulatory table. The budget chart repeats the glance cards' programme figures; the regulatory table is the owner's own ask and stays. *Proposal: drop the budget chart from the Overview (it lives on each state tile).*

## 4. Deferred defects (real, not fixed this run)

- Chain-of-command rungs with two names ("Mike Hancock · Jeremy C. Slinker") are dropped from the contacts table while the strip says every name is in the table. Fix: split on " · " in `buildContacts`.
- `censusPanel` is Alabama-literal in a generic name; `renderCompetition` writes NC content into a hidden node that is copied by `innerHTML`, with unbalanced `<details>` tags that only work because the HTML parser forgives them.
- `GA_LETS` and `KY_LETS` duplicate `YEAR.GA.all` / `YEAR.KY.all` (≈245 KB); derive `LETSAMPLE[id]` at load instead.
- Dead code: `covCard`, `coverage()`, the zoom scaffolding from 1.7a, `const tip=gt`.
- `parse_gdot_awards.py` defaults an unrecognised status to "awarded"; add an explicit `unknown` and fail on it.
- The per-state price book (every bidder's unit price is in `items[]`) is captured and never rendered — the single most useful unbuilt view for a lighting seller (the spec conversation is about what a Type 3 LED luminaire or an 80-ft high-mast pole went for, by state). Recommend it as the next interface milestone after Arkansas.

## 5. Decisions the owner is asked for

- Tile prose: one clause per tile, or keep the sentences.
- Ownership panel: fold the prose and gate table under a "full rule" toggle, keeping the cards and the selling callout open.
- Move "Model: 7/7 · 5/5" and the concentration stats (CR1/CR3/HHI) to the Method tab, leaving the heat map and the district table on Contractors.
- Drop the budget chart from the Overview.
- Build the price book (per state, per item class, low / high / weighted across the year's bidders) as milestone 3.14, ahead of or behind Arkansas.
