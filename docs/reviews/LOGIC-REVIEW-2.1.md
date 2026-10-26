# Logic review — is this thing sound, and is the bid layer earning its place?

**Requested by the owner, September 1, 2026, at build 2.1.** Scope: (1) whether the bid structure is an appropriate category in the overlay, or a road toward something that cannot be built; (2) whether the North Carolina data is too convoluted or half-proportional to support decisions; (3) which features to tweak, streamline, or remove. This is a review, not a build — nothing below has been changed yet.

---

## 1. The verdict on the bid layer

**It is a sound category with the wrong job description.** Nothing unbuildable was built. The risk was never the data — it was what the data might be *used for*.

**What the bid read is, honestly.** It is complete within its channel: all fifteen Central lettings of the year, every item list read, every letting reconciled to NCDOT's printed totals to the cent. It is not sloppy work. But it is one channel of two — the fourteen Division offices let their own contracts up to $5M each behind a login, and small relighting and retrofit jobs are exactly the work that fits under $5M. So the channel we cannot see is plausibly where most *lighting* work lives, and we cannot bound its size. **As a market-size instrument, the bid read is structurally incomplete no matter how well it is executed.** Your "half proportional" instinct is correct, and no amount of additional Central reading fixes it.

**What the bid read actually bought — once.** It proved the base rate: 7 of 134 contracts, 0.09% of the dollars, nearly all product value in two high-mast interchange packages. That finding forced the question *why*, and the answer was the Roadway Lighting Policy — NCDOT funds lighting only on freeways and interchanges; everything else is municipal money that never enters a DOT letting. **The bid read was diagnostic scaffolding. It produced one load-bearing insight, the ownership model now carries that insight, and the scaffolding does not need to stay up.** The pause decision was right; this review's finding is stronger — the bid layer's job going forward is *evidence sampling* (validate a new state's ownership model with one letting-year read, maybe), never *market measurement*.

**One logic defect found: the competition layer measures the wrong market.** HHI 460, CR1 10.5%, the contractor-by-Division heat map — these are computed across all 134 winners of general roadway construction: paving, grading, bridges. Cooper does not compete with Blythe Construction. Blythe is a potential **customer** — primes buy luminaires to fulfil contracts. The year's product dollars went through exactly two accounts: APAC Atlantic/Smith Rowe JV ($370,650, C205012) and Blythe Development ($117,934, C205195). Ninety-nine point six percent of the year's product, two buyers. That is the decision-relevant competition fact, and the current tab buries it under concentration statistics for a market you are not in. **Recommendation: reframe "Who wins the work" as "Who buys product," listing the lighting-contract primes as target accounts, and demote the general-construction HHI to labelled context.**

## 2. What genuinely cannot be built — from public data

Three parts of the original vision cannot come from public sources, and pretending otherwise would be the "road to something that can't be built":

1. **Manufacturer share (Phase 7).** NCDOT specifies performance, publishes no approved-product list, and records the installed brand nowhere public. In states like this, the Cooper-versus-competitors picture can only come from **Cooper's own submittal and PO history**. Cooper is your partner — this is an ask, not a research project. Phase 7 should be re-scoped as partner-data integration, with public QPL evidence used only in states that publish one.
2. **Customer heat maps (your original brief).** A map of *your* customers requires *your* sales records. Public data can show who buys product from DOT work (see above — two accounts); it cannot show LSI's book of business. This is buildable — as an import of your own data in the workflow phase, not as research.
3. **Full bid visibility.** Blocked by a login, not by a law. Bid Express is a standard vendor account any legitimate business can register. **This is the single highest-leverage unblock in the project:** one account likely opens the Division channel in NC and several other states at once. Recommended as an owner action whenever the bid question is reopened.

A fourth, smaller gap: five of the seven lighting contracts still read "apparent" only because three Board minutes PDFs (Dec 2025, Apr 2026, Jun 2026) exceed what this tool can retrieve. Supplying those three files closes the year's award record in one run.

## 3. The North Carolina page — keep, rework, remove

Measured at build 2.1: eleven sections, ~2,240 words, 14 tables, 133 rows, roughly six screens. The top screen (map + tiles) works as a briefing. Below it, decision value and density are badly matched:

| Section | Determination |
|---|---|
| Map, tiles, Division legend | **Keep** — this is the briefing |
| Who pays / who decides | **Keep, first among sections** — the most decision-relevant panel on the page |
| Leadership & contacts | **Keep** |
| Twelve months of lettings | **Keep the finding, shrink the body** — headline figures and the seven lighting contracts; full letting detail belongs in the research file |
| Programmed pipeline | **Keep** — the strongest forward-looking layer, complete within its source |
| Whose product goes in (M5) | **Keep** — short, prevents wrong assumptions |
| Sources | **Keep** (collapsed) |
| Recent lettings — June through August | **Remove as a section.** It is a build artifact: those three lettings are inside the twelve-month set. Its contract tables move to the research file; nothing is deleted from the record |
| Who wins the work | **Rework** → "Who buys product" (two named accounts); general HHI moves to labelled context |
| The other channel — Division lettings | **Shrink to a note** — it is a caveat, not a section |
| Dictionary & capture methodology | **Demote** behind one "full research file" door |

Net effect: eleven sections become about six, fourteen tables become about six, and every figure keeps its citation. Same treatment for the Competition tab: keep the Division activity table (which you asked for) and the buyer view; demote the general-construction concentration. `ROADMAP.md` (69 KB) wants the same pass — steering summary up front, archive below.

## 4. Why this matters right now

The state page shape is what the next seven states inherit. Done before state two, this is one restructuring run. Done after, it is eight. The layer split (2.1) makes the restructure cheap: sections are already gated by layer, so moving them behind a research-file door does not touch the data.

## 5. Recommended sequence

1. **Briefing pass** — the keep/rework/remove table above, one run.
2. **You supply three minutes PDFs** — closes the award record; or we drop the amber "apparent" noise from the briefing view.
3. **State two on the transferable seven** — ownership policy first, per the standing decision.
4. **When the bid question reopens:** a Bid Express account, and the bid layer returns as a one-time base-rate sample per state, never a standing pipeline.
5. **Phase 7 re-scoped** as Cooper partner-data integration; **customer heat maps** scoped as an LSI data import.

Nothing reviewed here is unbuildable. Two things were being asked of data that cannot answer them — market size from one channel, and competition from a market you don't sell into — and both have honest replacements that use data already in hand.
