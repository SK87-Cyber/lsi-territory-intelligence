# Kit notes — build 10.1b (the October refresh, Oct 26–27, 2026)

The original kit's parsers (parse_bidtabs.py, parse_tdot.py, parse_mdot.py, parse_gdot_tabs.py,
parse_kytc.py, parse_ardot.py, parse_aldot_year.py, parse_scdot_tabs.py, hwsplit.py, snapshot.py,
build_pdf.py, embed_geo.py, hover-check.js and the manifests) were NOT in the GitHub repo and were
not available this run. The scripts/ folder here holds the 10.1b rewrites, each re-proving the
original reconciliation gates on the new lettings; deltas/ holds every parsed letting in the
universal record shape, plus the award updates and the ALDOT STIP re-read. The logos and
geo-se.json were recovered from the Netlify 10.1a package (the built page embeds both).
**Owner action that prevents this next time: push the FULL kit zip to the repo.**
companion.pdf could not be regenerated (build_pdf.py not on hand) — the Netlify package ships the
10.1a edition.
