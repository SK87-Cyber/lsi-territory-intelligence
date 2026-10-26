# Research brief — alternative delivery (design-build, progressive design-build, CM/GC, P3) in one state DOT, and the lighting inside it

Read-only: WebSearch and WebFetch only. Sources allowed: the agency's own site (design-build / alternative delivery / innovative contracting pages, project pages, RFQ/RFP notices, award announcements, commission or board minutes, STIP), the legislature (the enabling statute), FHWA. Not allowed: trade press as the only source for a fact, contractor marketing pages as the only source for scope, guesses. Quote the agency's words. Where a fact is not in a primary source, return NOT FOUND.

Return ONLY a JSON object:
{
 "state": "XX",
 "authority": "the statute or rule that lets the DOT use design-build and other alternative delivery (name, section, year), and any cap on how many or how much — quote and cite",
 "program": "how the agency runs alternative delivery — the office or unit, its web page, the methods it uses (DB, PDB, CM/GC, P3), the typical procurement (RFQ → shortlist → RFP → best value), and where awards are published — quote and cite",
 "lightingRule": "who designs and selects lighting on a design-build job here — the design-builder's engineer of record, an agency lighting group review, the owner's (city/utility) sign-off — quote the RFP/technical-provisions language if any project publishes it, else NOT FOUND",
 "projects": [
   {"name": "", "id": "<agency project/contract id>", "method": "DB|PDB|CMGC|P3", "team": "<design-builder / developer as awarded, or shortlisted>", "value": "<contract value as published, with what it is: award, GMP, estimate>", "awarded": "<date, or 'advertised <date>' / 'RFQ <date>'>", "status": "<awarded | in design | under construction | RFP open | shortlisted | complete>", "lighting": "<the scope language that names lighting — quote; 'likely' is not allowed; NOT FOUND if the published scope does not mention lighting>", "lightingWhen": "<when lighting gets designed/bought on this job, if published: e.g. 'design complete 2027', else NOT FOUND>", "source_url": "", "source_title": "", "date_seen": "2026-09-07"}
 ],
 "sources": [["title","url","what it evidences"], ...]
}

Include every alternative-delivery highway project the agency has awarded since Jan 1, 2023 or lists as procured/advertised/programmed now (up to 12; prioritise interstate, interchange and freeway work, which is where roadway lighting rides). Lighting must be QUOTED from a published scope, RFP, fact sheet or project page — an interstate interchange without a published lighting mention is "NOT FOUND", not "likely".
