SOUTHEAST DOT LIGHTING INTELLIGENCE — NETLIFY PRODUCTION PACKAGE (build 10.1, Sep 7, 2026)

What is in here
  site/index.html      the portal — one self-contained file (map geometry, data, logos embedded); no build step, no server code
  site/companion.pdf   the nine-page presentation companion, built from the same data
  site/founder-brief.pdf  the four-page plain-English briefing
  site/_headers        noindex + basic security headers (the site is meant to be shared by link, not found by search)
  site/robots.txt      disallow all crawlers
  site/404.html        sends any bad URL back to the portal
  netlify.toml         publish directory and headers

How to deploy (two minutes)
  1. Sign in at app.netlify.com → Sites → "Add new site" → "Deploy manually".
  2. Drag the "site" folder onto the drop zone. Netlify publishes it at a random *.netlify.app address.
  3. Site settings → Domain management to give it a name (e.g. territory.lightingsolutionsal.com) or keep the netlify.app address.
  4. To restrict who can open it: Site settings → Access & security → Password protection (a Netlify paid feature) — otherwise share the link privately; it is noindexed.

To update
  Replace site/index.html with the next build's HTML (and the PDFs), re-drag the folder. Nothing else changes.

Notes
  The portal reads nothing from the network at run time; everything it shows is inside index.html. Freshness lights are computed
  from the viewer's clock against the dates in the record, so they turn on their own as time passes — a new read is still a new build.
