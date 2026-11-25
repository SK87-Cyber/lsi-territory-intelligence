# November 2026 lettings refresh (Builds 10.2k and 10.2l, read Nov 25, 2026)

Lettings added to the record with the refresh-oct26 tools:

| State | Letting | Contracts | Low bids | Lighting contracts | Lighting | Status |
|---|---|---|---|---|---|---|
| NC | Nov 17, 2026 | 11 | $572,426,274.53 | 2 | $6,016,242.00 | apparent (no Board record yet) |
| AR | Nov 4, 2026 | 19 | $196,802,399 | 3 | $3,102,011.51 | awarded (Awards List) |
| KY | Nov 19, 2026 | 18 | $29,310,659.09 | not yet priced | — | census level; item index shows lighting on 26-1133 and 26-1521 |
| TN | Nov 6, 2026 | 27 | $65,750,221.73 | 0 | $0 | awarded |

Tool changes: nc_itemc.py knows seven more bidder cities; nc_delta.py classes generic lighting items (5260/5265/5270) by what the
description names (painted light standard = pole; bridge conduit system, railing, formed opening = infrastructure).
Arkansas job 040904 was bid A+B: the parsed base bids were replaced by the contract amounts printed beside them before emitting.
Tennessee: tn_build.py (new) builds the delta from the Apparent Bid Results, Summary of Bids and Contract Awards; all 27 calls'
item extensions re-add to the printed TOTAL CONTRACT for every bidder.
Citation ids are zero-based positions in a state's sources list.

## Second batch (Build 10.2l)

| State | Letting | Contracts | Low bids | Lighting contracts | Lighting | Status |
|---|---|---|---|---|---|---|
| MS | Oct 27, 2026 | 15 | $347,282,838.00 | 3 | $4,844,880.55 | 14 awarded Nov 10, one rejected; one call has no tabulation posted |
| MS | Nov 24, 2026 | 11 | $61,305,960.72 | 1 | $5,730.00 | apparent; one call has no tabulation posted |
| AL | Aug 28, 2026 | 13 | $33,671,530.16 | 2 | $514,322.27 | awarded (posted tabulation) |
| SC | Nov 10, 2026 | 26 | $499,939,710.37 | not yet priced | — | census level until certified tabulations post |

Mississippi: Sep 22 and Sep 29 awards (Commission action Oct 13) applied. Project 108168301 (I-55, Madison) was rejected at the
Aug 25 letting and awarded on its Oct 27 re-let; its lighting is counted once, on the Oct 27 row (the Aug 25 row stays in `all`).
ms_emit_nov.py: a call with no posted tabulation is carried unread (cls UNKNOWN); a tabulation column with no bidder in the
checked results (irregular bid) is ignored.
Alabama: al_tab_parse.py (new) parses the Tabulation of Bids; all 13 contracts reconcile to the cent for every bidder.
al_emit_2026-08-28.py adds Section 751 (replace/remove roadway luminaire, replace pole wiring) to the lighting rule: first met on
20260828008, a lighting-only contract. Earlier lettings were not re-read for Section 751 items.
Alabama Sep 25 and Nov 6 are on the Low Bid Sheet only (no tabulation posted) and are not in the contract record.
