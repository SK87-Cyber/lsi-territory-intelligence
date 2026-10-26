# Milestone 3.2 research — Tennessee ownership, funding and decision layers
**Researched Sep 1, 2026. Build pending: the kit was not uploaded to this conversation. This file is the complete input for the template edit — fill `OWNERSHIP.TN` and `DECISION.TN` from it, append the sources to `STATES` TN, build 3.2.**

## The finding — the third ownership shape, confirmed

Tennessee is the **locally/utility-owned** state the roadmap predicted, but with a statutory spine Alabama lacks and a warrant gate North Carolina keeps for itself. Ownership is split by road class, and in every class the *maintenance and operation* burden lands on the local government:

1. **Statute.** TCA **54-5-206** authorizes municipalities to maintain and operate lighting systems on interstate highways **within their city limits, at the municipalities' expense**; the state commissioner prescribes the standards. MTAS (the UT Municipal Technical Advisory Service) reads it narrowly: the authority stops at the city boundary — a municipality has **no authority to pay for interstate lighting outside its limits**; outside municipalities, **counties may contract with the state** to operate interchange lighting (observed: a county paying for I-75 interchange lighting).

2. **Interstate mainline.** Where lighting is **determined to be warranted by the Traffic Engineering Office**, TDOT covers **100%** of installation cost — but only if **"the local maintaining agency agrees to maintain the installation"** (Traffic Design Manual, Roadway and Intersection Lighting chapter, §1.1.2).

3. **Interstate interchanges not under construction.** The local agency must submit a **written request** and fund **50% of the costs** when the project is programmed (§1.1.2; the Lighting Design Manual §1.3 states the same 50%).

4. **Non-interstate state highways.** TDOT **"generally does not replace or install new lighting."** Installation and maintenance **"are the responsibilities of the local governing agencies"** (Lighting Design Manual §1.3). Local agencies must **"agree to pay an appreciable percentage of, or wholly finance, the installation, maintenance and operation"** (§1.1.2). Requests route through the TDOT Utilities Office with funds submitted before letting.

5. **The utility half.** Local agencies are required to **coordinate with utility providers on maintenance operations** (§1.3.2) — in practice Tennessee municipalities operate street lighting through their municipal electric systems (TVA local power companies), which is what makes the shape "locally/utility owned" rather than merely "municipal".

## The decision layer — a third `DEC.kind`

Neither NC's standing committee nor AL's distributed case-by-case. Tennessee is a **warrant + agreement gate** (suggested kind: `"conditional"`):

- **Interstate mainline:** TDOT's **Traffic Engineering Office** determines warrant — but warrants **"do not obligate the agency to provide lighting"** (Lighting Design Manual §3.1), and nothing is built unless a local maintaining agency signs the maintenance agreement. Two keys, one lock.
- **Non-interstate:** the **local agency initiates** by request; **"all requests for roadway lighting installations on non-interstate highways will be reviewed and approved by the TDOT Traffic Services Manager"** (Lighting Design Manual §1.3); the rewrite chapter adds that **"the Design Division Director shall approve the installation or relocation of roadway lighting projects"** on state highways (§1.1.2).
- **Named people (published on TDOT's signal-and-lighting page, phones and emails printed on the page — not guessed):** Scott Pate, PE, Traffic Services Manager, 731-225-2277, Scott.Pate@tn.gov — *the named approver of non-interstate lighting requests*; Steve Bryan, PE, PTOE, Statewide Signal Engineer, 615-741-2152, Steve.Bryan@tn.gov. Lighting sits in the **Signal Design Section, Traffic Design Division**; the page's "Roadway Lighting" section is marked *Coming Soon*.

## The sales meaning (for the ownership panel's plain-language line)

The customer is the municipality (or its electric utility), in every class of road: even TDOT-built interstate lighting exists only where a city agreed to maintain it, and interchange relights need the city to bring half the money. The trigger points are the maintenance agreements themselves — a city already paying to operate interstate lighting is a named, findable account, and a warranted-but-unlit segment is a lead where the missing piece is a local agreement, not a state decision.

## Sources (for `STATES` TN `sources` — append only)

1. TDOT Lighting Design Manual (PDF) — https://www.tn.gov/content/dam/tn/tdot/traffic-engineering/TDOT%20Lighting%20Manual.pdf — §1.3 ownership/50% interchange/Traffic Services Manager approval; §3.1 warrants don't obligate.
2. TDOT Traffic Design Manual, "Roadway and Intersection Lighting" chapter (rewrite) — https://www.tn.gov/content/dam/tn/tdot/traffic-engineering/tdmanualrewrite/ROADWAY%20AND%20INTERSECTION%20LIGHTING.pdf — §1.1.2 funding/approval split; §1.3.2 utility coordination.
3. MTAS, "Maintenance and Operation of Street Lighting on Interstate Highways" — https://www.mtas.tennessee.edu/knowledgebase/maintenance-and-operation-street-lighting-interstate-highways — TCA 54-5-206 reading, city-limits boundary, county contract case.
4. TDOT Traffic Design (Signal & Lighting Design page) — https://www.tn.gov/tdot/traffic-design/signal-and-lighting-design.html — office, named contacts, "Roadway Lighting — Coming Soon".
5. (Older chapter, for the record) Traffic Design Manual Ch. 7 Highway Lighting, Dec 2007 — https://www.tdot.tn.gov/PublicDocuments/%5CDesignDivision%5Cassistant_engineer_design%5Cdesign%5Cv8%5CTraffic%20Design%20Manual%5CCHAPTER%207%20%E2%80%93%20ROADWAY%20LIGHTING.pdf — superseded by the rewrite; not fetched this run.

## §10.2c Tennessee release calendar — first observations, Sep 1, 2026

| Artifact | Where | Cadence | Tier | Note |
|---|---|---|---|---|
| STIP | tn.gov/tdot long-range planning, STIP/TIP page | 3-year cycle; FY 2023–2026 final (rev Feb 28, 2024) current, **FY 2026–2029 draft posted (rev Feb 5, 2026)**; amendments tracked on dedicated pages | 1 | Published as PDF documents |
| eSTIP | https://estip.app.tdot.tn.gov/ | Continuous | 1/2 | Queryable **JavaScript app** — returns an empty shell to a plain fetch; whether a REST/export endpoint exists behind it is unprobed. Pipeline layer stays UNKNOWN until it is. |
| Central lettings | tn.gov/tdot Construction Division, Bid Lettings pages | **~Every 6–8 weeks, seven in 2026** (Jan 9 special, Feb 6, Mar 20, May 8, Jun 26, Aug 14, Oct 2) — not monthly like NC | 1 dates / **3 documents** | Bid documents and addenda live on **Bid Express** — same Tier 3 wall as NC's Division channel. Bid work is paused anyway. |
| Lighting/design manuals | Traffic Design pages | Versioned, change rarely | 1 | Lighting Design Manual current; Traffic Design Manual mid-rewrite |
| Staff directory | Traffic Design pages | Continuous | 1 | Emails printed in page text — easier than NC's icon wall |

## What the build does with this (when the kit arrives)

- `OWNERSHIP.TN` from §§1–5 above, each claim keyed to its source.
- `DECISION.TN` with a new `kind: "conditional"` — render the two-key structure (state warrant + local agreement) rather than forcing NC's committee or AL's distributed shape. HANDOFF rule: a state that fits neither existing shape gets a new branch, never a forced fit.
- Coverage after this fills: TN at **6 of 7** transferable layers (pipeline UNKNOWN pending eSTIP probe), mirroring Alabama; assert in `verify.js`.
- ROADMAP: tick 3.2, add §10.2c, log the decision that TN's statutory basis (TCA 54-5-206) makes it the strongest ownership evidence of the three states — policy (NC), agreement practice (AL), statute + manual (TN).
