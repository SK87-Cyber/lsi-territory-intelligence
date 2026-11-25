# November 2026 lettings refresh (Build 10.2k, read Nov 25, 2026)

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
