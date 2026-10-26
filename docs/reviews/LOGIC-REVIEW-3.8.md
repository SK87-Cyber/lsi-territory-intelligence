# Logic and interface review — after Build 3.8 (Sep 4, 2026)

**Owner's brief:** "The interface is getting very convoluted and doesn't look clean any more. Review the logic of what we are trying to accomplish and how it can be better — particularly now that you know what information we have. Clean up the sources. Make the logos more visible." Executed as **Build 3.8a** (an interface run; no milestone delivered, so a letter suffix per the naming rule). Owner registering the Bid Express account in parallel.

## 1. What the product holds now

Eight states carry the seven transferable layers (four at 7/7, four at 6/7 with the pipeline honestly absent). North Carolina carries all five bid-derived layers from a full year read at item level. Four states have a programmed-lighting pipeline read from the agency's own source (NC 14, AL 27, GA 15, KY 5 projects). Every state has an ownership model in one of four shapes, a decision body in one of four shapes, a territory map, a leadership chain and a contact table. As of 3.8 every state also has a bid-artifact catalogue and a letting calendar. That is a lot more than the interface was designed around in Phase 1, and the review's first finding is that the *page structure never caught up with the data*: things that were the whole product in Build 1.5 (the rules, the evidence ladders, the coverage matrix) were still sitting on the landing page in front of the briefing.

## 2. What was wrong, page by page

**The Overview was a 7,000-pixel wall.** Budget chart, a five-column regulatory table, the coverage matrix, the bid catalogue, six rules, two evidence ladders and a rule strip, in that order. A customer watching the owner open the page saw methodology before intelligence. There was no single place that said, per state, *what we know*.

**The hero repeated itself and misled.** "Hover a state for its headline" appeared three times (subtitle, a boxed hint, and the legend). The four headline tiles under the map presented North Carolina's contract count, lighting dollars and pipeline as if they were eight-state figures — three of four tiles were NC-only, labelled as the territory.

**State pages carried a noise tile.** The "What this model is built from" tile with twelve strike-through chips was inward-facing build status, not briefing material, and it took the most valuable slot on the page (beside the map).

**Contacts duplicated people.** Where a state's chain of command and its lighting-desk list named the same person (KY: Goodman, Ballinger; SC and MS likewise), the table printed them twice — once with no phone under "Statewide leadership" and once with the direct line under "Lighting, traffic & procurement". That is a logic defect, not a styling one: a reader could reasonably conclude the Secretary has no published line.

**The References page was a 13,000-pixel URL dump.** Full URLs printed as text, every row three lines, no way to find anything, and a boilerplate callout about "the production platform" that no reader needs.

**The logos were 52 and 36 pixels tall**, and the tagline beside them carried the build number, phase, milestone status, methodology version and research date in one run-on line.

**The Contractors tab** is NC-only data (the general-construction concentration) labelled as if it were territory-wide.

## 3. What changed in 3.8a

- **Brand bar:** logos at 84 px (Lighting Solutions of Alabama) and 60 px (Cooper); the tagline reduced to three short lines with the build number in muted text.
- **Hero:** one subtitle, one small hint, the legend. The four headline tiles now say territory-true things — combined programme size, 8 of 8 ownership models, programmed lighting projects across the states that publish them, and *one* state read at item level with its identified dollars — so nothing NC-only wears an eight-state label.
- **Overview = briefing.** New first section, **The territory at a glance**: one card per state with programme size, ownership shape and who buys, what is programmed, where the bid record stands, and the next scheduled letting. Then the budget chart and the regulatory comparison (the owner's own ask) — and nothing else.
- **New Method tab** (the old Roadmap tab, renamed, id unchanged): the coverage matrix, the bid catalogue, the six rules, the evidence ladders and the roadmap all live there. The product still states its method; it just doesn't lead with it.
- **State pages:** the chip tile is gone; a one-line "Model: 7/7 transferable · 0/5 bid-derived" plus **the next letting date** sits under the state header instead. The "not yet read" lighting tile now points at the catalogue below it with the confirmed-artifact count and the expected base rate. A **chain-of-command strip** (the original project brief asked for the DOT chain of command to be showcased) now heads the contacts section, drawn from the same `chain` rows the table uses. Contacts are **deduplicated by name**, keeping the row that carries the phone (SC 14→12, MS 13→11, KY 21→19 rows; no person lost).
- **Sources:** one compact row design shared by the References page and every state's sources panel — number badge, linked title, role and access date, domain only. The References page gained a **state filter and a search box**. Full URLs are on the links, never printed.
- **Contractors tab** relabelled "North Carolina · who builds, who buys".
- **Footer** cut to two lines. Panel summaries and meta text one size smaller.

Nothing was removed from the product; the methodology moved to the Method tab, and `verify.js` passes unchanged (plus the 3.8 block).

## 4. What the product should display next, given what it now knows

Ordered by value to a briefing, with what each needs.

1. **A cross-state programmed-lighting call list.** Four states' pipelines are already in the model (61 projects naming lighting; 34 lighting-only). The Overview should carry one table of *lighting-only* programmed projects across all four, sorted by construction year, with the state, the territory and its engineer. It is the earliest call list the public record can produce, and it is already data. *No owner input needed; recommend building it into 3.9 or as 3.8b.*
2. **The letting calendar as the retrieval schedule (milestone 2.3).** The strip on each state page is the seed: every tick is a date an agent should fetch the results and, two to four weeks later, the award artifact. Rendering "next letting" per state (done in 3.8a) is the first half; the second half is a table of *what to fetch, when, from where* per state — which §10 of the roadmap already holds in prose. *No owner input needed.*
3. **After Kentucky and Arkansas read: quantities and the price book before dollars.** The universal record captures every bidder's unit price and the quantities by class. For a lighting seller, "44 high-mast luminaires at 335–560 W and six 120-foot standards in twelve months" is a better sentence than "$1.4M identified" — it is the thing the specification conversation is about. The lighting tile should grow a quantities line, and a per-state price-book panel should join the research door. *Design decision at 3.10, once two states have rows.*
4. **The chain of command should carry verification age.** The strip now exists; Phase 5's staleness rule (active → stale at 120 days → unknown at 365) should tint the rungs. *Needs the owner's answer to the open question in §9: who verifies, on what cadence.*
5. **Presentation mode (Phase 8) is now cheap.** The glance cards, the state header line and the ownership panel are the flow; a toggle that hides the details panels and enlarges the map is a small run. *Owner call on priority.*
6. **Retire the Contractors tab into the NC page** once a second state has a letting record, or keep it as the "market context" page and populate it per state. Today it is one state's data at territory level in the nav. *Owner call.*

## 5. Decisions the owner is asked for

- The three-bar lighting tile (hardware / electrical infrastructure / work) vs today's identified-vs-product — still behind `LIGHTING_TILE_SPLIT`.
- Whether the Contractors tab stays in the nav or folds into North Carolina's page.
- Priority between the cross-state call list (item 1) and starting the Kentucky read (3.9). The call list is a half-run and needs no research; recommendation is to do it first so the Overview's briefing value lands before the next data layer.
