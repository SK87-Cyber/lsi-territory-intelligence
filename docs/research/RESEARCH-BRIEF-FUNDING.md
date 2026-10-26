# Research brief — how one state DOT's money is planned and allocated (public record only)

You are researching ONE state for a briefing tool. Read-only: WebSearch and WebFetch only. Quote the agency's or the statute's own words; never infer. Where you cannot find a fact in a primary source (the DOT, the legislature, the governor's budget office, the state constitution or code, FHWA), return the literal string NOT FOUND for that field — never a guess, never a secondary-source paraphrase presented as primary. Prefer the most recent document (FY 2026-27 / FY 2027 cycle). Every quoted fact must carry the URL it came from and the document's date or fiscal year.

Return ONLY a JSON object with these keys (strings unless noted). Keep each string under 60 words; quotations in double quotes inside the string with the source URL after them in square brackets.

{
 "state": "XX",
 "revenue": "where the DOT's money comes from — the dedicated state revenues by name (fuel tax rate/basis, vehicle fees, sales/use tax shares, other), the federal-aid share, bonds/debt policy. Quote and cite.",
 "revenueLaw": "the statute or constitutional provision that dedicates those revenues (name, year, section). Quote and cite.",
 "appropriator": "who appropriates or authorizes the DOT's spending and in what instrument — annual or biennial appropriations act, the commission's own budget, a governor's budget — with the current instrument's name, number and fiscal year. Quote and cite.",
 "cycle": "the fiscal year (start month) and whether the budget is annual or biennial; when the budget is typically enacted.",
 "planningInstrument": "the document that lists the projects the DOT will build (STIP, Work Program, Highway Plan, ten-year plan, Statewide Transportation Improvement Program), its horizon in years, who adopts it, and how often it is updated. Quote and cite.",
 "allocationRule": "how the capital money is divided geographically or by category — a statutory formula (percentages), a scoring system, a commission's discretion, a board's programme — with the rule's name and the shares. Quote and cite.",
 "decisionBody": "the body that puts a project into the programme and later awards the contract — legislature, commission, board, director — how its members are chosen, and what vote or instrument commits money (minute order, board resolution, enacted statute, director's authority). Quote and cite.",
 "figureMeaning": "what the state's headline figure (given below) actually is — the document it comes from, its status (enacted law / adopted programme / agency request / legislative recommendation / derived), and what it includes and excludes (federal funds in or out; debt service; local aid; capital vs operating). Quote and cite.",
 "lightingLine": "whether any published budget, programme or plan document carries a lighting line, category or programme (for example an annual lump-sum lighting programme, a highway plan lighting item, a maintenance lighting category). Quote the line and cite, or NOT FOUND.",
 "sources": [ ["title", "url", "what it evidences"], ... ]   // every URL you used, 3–8 entries
}

The headline figure the product currently shows for this state, and the document it is read from, are given in the task message. Confirm or correct it against the source and say so in figureMeaning.
