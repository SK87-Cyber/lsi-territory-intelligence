#!/usr/bin/env python3
"""Presentation companion PDF, built from the site's own data objects.

The numbers are extracted from the built HTML (see the node one-liner in HANDOFF
section 9) into pdfdata.json, so the leave-behind and the portal cannot drift apart.

Usage:  python3 build_pdf.py pdfdata.json <build> [--out DIR]
"""
import json, sys, os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, Image, KeepTogether)

NAVY = colors.HexColor("#003B73"); BLUE = colors.HexColor("#005CAB")
GOLD = colors.HexColor("#F2C230"); SLATE = colors.HexColor("#5A6B7B")
LINE = colors.HexColor("#D6E0EA"); PAPER2 = colors.HexColor("#F6F9FC")
GREEN = colors.HexColor("#1E7B45"); AMBER = colors.HexColor("#B7791F")

S = dict(
    title=ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=27, leading=31, textColor=NAVY, spaceAfter=6),
    sub=ParagraphStyle("s", fontName="Helvetica", fontSize=12, leading=17, textColor=SLATE),
    h1=ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=NAVY, spaceBefore=4, spaceAfter=7),
    h2=ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=BLUE, spaceBefore=9, spaceAfter=4),
    body=ParagraphStyle("b", fontName="Helvetica", fontSize=9.6, leading=14, textColor=colors.HexColor("#1B2A38"), spaceAfter=5),
    small=ParagraphStyle("sm", fontName="Helvetica", fontSize=8.2, leading=11, textColor=SLATE),
    cell=ParagraphStyle("c", fontName="Helvetica", fontSize=8.2, leading=10.6),
    cellb=ParagraphStyle("cb", fontName="Helvetica-Bold", fontSize=8.2, leading=10.6, textColor=NAVY),
)


def money(v, dp=0):
    return "$" + format(round(v, dp), ",." + str(dp) + "f")


def tbl(rows, widths, header=True, align=None, size=8.2):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [("FONTSIZE", (0, 0), (-1, -1), size),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, LINE),
            ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, PAPER2]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header:
        cmds += [("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                 ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                 ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    for c, a in (align or {}).items():
        cmds.append(("ALIGN", (c, 0), (c, -1), a))
    t.setStyle(TableStyle(cmds))
    return t


def stat_row(items, width):
    lab = ParagraphStyle("lab", fontName="Helvetica", fontSize=7.2, leading=9.5, textColor=SLATE)
    big = ParagraphStyle("big", fontName="Helvetica-Bold", fontSize=15, leading=18)
    note = ParagraphStyle("note", fontName="Helvetica", fontSize=7.2, leading=9.5, textColor=SLATE)
    cells = [[[Paragraph(k.upper(), lab), Spacer(1, 2),
               Paragraph(f'<font color="{col}">{v}</font>', big), Spacer(1, 1),
               Paragraph(n, note)] for k, v, n, col in items]]
    t = Table(cells, colWidths=[width / len(items)] * len(items))
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.4, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
                           ("BACKGROUND", (0, 0), (-1, -1), PAPER2), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def build(data, build_no, out_dir):
    W = LETTER[0] - 1.1 * inch
    path = os.path.join(out_dir, f"southeast-dot-lighting-intelligence-companion-{build_no}.pdf")
    doc = SimpleDocTemplate(path, pagesize=LETTER, leftMargin=0.55 * inch, rightMargin=0.55 * inch,
                            topMargin=0.55 * inch, bottomMargin=0.6 * inch,
                            title="Southeast DOT Lighting Intelligence — presentation companion",
                            author="Lighting Solutions of Alabama")
    y, comp, div, pipe = data["year"], data["comp"], data["divact"], data["pipeline"]
    ident = sum(c["l2"] for c in y["lighting"]); prod = sum(c["product"] for c in y["lighting"])
    awarded = sum(c["l2"] for c in y["lighting"] if c.get("award") == "awarded")
    here = os.path.dirname(os.path.abspath(__file__))

    def footer(canv, d):
        canv.saveState()
        canv.setStrokeColor(LINE); canv.setLineWidth(0.5)
        canv.line(0.55 * inch, 0.5 * inch, LETTER[0] - 0.55 * inch, 0.5 * inch)
        canv.setFont("Helvetica", 7.4); canv.setFillColor(SLATE)
        canv.drawString(0.55 * inch, 0.36 * inch,
                        "Lighting Solutions of Alabama, in partnership with Cooper Lighting Solutions"
                        f"  ·  Build {build_no}  ·  Research through September 4, 2026")
        canv.drawRightString(LETTER[0] - 0.55 * inch, 0.36 * inch, f"{canv.getPageNumber()}")
        canv.restoreState()

    st = []
    # ---- cover ----
    logos = []
    for f, w in (("lsi-logo.png", 2.0), ("cooper-logo.png", 1.7)):
        p = os.path.join(here, f)
        if os.path.exists(p):
            from reportlab.lib.utils import ImageReader
            iw, ih = ImageReader(p).getSize()
            logos.append(Image(p, width=w * inch, height=w * inch * ih / iw))
    if len(logos) == 2:
        lt = Table([[logos[0], logos[1]]], colWidths=[W * 0.5, W * 0.5])
        lt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
        st += [lt, Spacer(1, 26)]
    st += [Paragraph("Southeast DOT Lighting Intelligence", S["title"]),
           Paragraph("Where the money is, where the lighting work is, who wins it, and who to call — "
                     "across eight state Departments of Transportation.", S["sub"]), Spacer(1, 18),
           stat_row([("Contracts read at item level", f"{y['contracts']}", f"North Carolina, {y['span']}", "#003B73"),
                     ("Low bids examined", f"${y['lowBids']/1e9:.2f}B", "every Central letting in the year", "#003B73"),
                     ("Lighting identified", money(ident), f"{money(prod)} of it product", "#B7791F"),
                     ("Programmed ahead", f"{len(pipe)}", "projects naming lighting, not yet let", "#003B73")], W),
           Spacer(1, 18),
           Paragraph("What you are looking at", S["h1"]),
           Paragraph("This is a market-intelligence platform, not a brochure. Every figure in it was read out of a "
                     "public artifact — a bid tabulation, a Board of Transportation award record, a published "
                     "improvement programme — and carries a numbered source. Where something has not been read, it "
                     "says UNKNOWN rather than guessing. North Carolina is complete to item level for a full year; "
                     "the other seven states carry verified budget, territory, leadership and — as of build 3.7 — their "
                     "own ownership and decision models, with their letting surveys still to run.", S["body"]),
           Paragraph("The seven questions it answers", S["h2"])]
    qs = ["Where is the money?", "Where is the lighting?", "Who wins it?", "Who decides?",
          "What is coming next?", "When does the incumbent turn over?",
          "What do we actually know about Cooper versus competing manufacturers?"]
    st += [tbl([[Paragraph(f"<b>{i+1}</b>", S["cell"]), Paragraph(q, S["cell"])] for i, q in enumerate(qs)],
               [0.32 * inch, W - 0.32 * inch], header=False)]

    # ---- rules ----
    st += [PageBreak(), Paragraph("The rules this runs on", S["h1"]),
           Paragraph("Six rules decide what this platform is allowed to say. They exist because a number that cannot "
                     "be defended in front of a customer is worse than no number at all. They are how it is built, "
                     "not a policy anyone has to countersign.", S["body"])]
    rules = [("No manufactured geography",
              "A territory total is the identified, programmed value of projects located there — never a district's share of a state budget."),
             ("No manufactured lighting dollars",
              "Lighting money comes from priced Division 14 pay items in real contracts, never a percentage of a DOT budget. Scope with no separable price never enters a dollar total."),
             ("Apparent is not awarded",
              "A low bid stays apparent until the Board's own record says the contract was awarded. The two are never summed together."),
             ("No manufactured manufacturer share",
              "Meeting a specification is not being installed. Until submittal or acceptance evidence exists the manufacturer is UNKNOWN — as it is for every contract today."),
             ("No manufactured people",
              "A vacancy stays vacant, and an email is never guessed from a naming pattern even an obvious one."),
             ("Every figure traces to a numbered source",
              "Anything not yet read says so in plain words rather than being left blank or quietly rounded to zero.")]
    # these are how the platform is built, not a policy anyone countersigns
    st += [tbl([[Paragraph(f"<b>{i+1}</b>", S["cellb"]), Paragraph(f"<b>{t}.</b> {d}", S["cell"])]
                for i, (t, d) in enumerate(rules)], [0.3 * inch, W - 0.3 * inch], header=False)]

    st += [Spacer(1, 12), Paragraph("How the classifier was tested", S["h2"]),
           Paragraph(f"Every one of the {data['classtest']['contracts']} contracts was classified twice by methods "
                     "sharing no logic — one reading the pay-item code, one reading only the item description. Both "
                     "disagreements found a real defect in the rules, and both were fixed: shared electrical now needs "
                     "a lighting-specific item beside it, and lighting items coded outside Division 14 are now caught. "
                     f"The two methods now agree on all {data['classtest']['agree']}. That is agreement after "
                     "adjudication, not an out-of-sample accuracy claim — the next twelve months are the first real test.",
                     S["body"])]

    # ---- eight states ----
    st += [PageBreak(), Paragraph("The eight-state picture", S["h1"]),
           Paragraph("Different budget objects, labelled by basis and never blended. Programme size is context for "
                     "how much roadway work a state lets — it is not a lighting figure.", S["body"])]
    rows = [["State", "Agency", "Programme", "Basis", "Territories"]]
    for s in sorted(data["states"], key=lambda x: -x["budget"]):
        rows.append([Paragraph(f"<b>{s['name']}</b>", S["cellb"]), Paragraph(s["agency"], S["cell"]),
                     Paragraph(f"${s['budget']:.2f}B", S["cell"]), Paragraph(s["basis"], S["cell"]),
                     Paragraph(s["geo"], S["cell"])])
    st += [tbl(rows, [1.05 * inch, 0.75 * inch, 0.75 * inch, W - 4.15 * inch, 1.6 * inch])]

    # ---- NC year ----
    st += [PageBreak(), Paragraph("North Carolina — a full year, read line by line", S["h1"]),
           stat_row([("Lettings", f"{len(y['lettings'])}", y["span"], "#003B73"),
                     ("Contracts", f"{y['contracts']}", "every item list read", "#003B73"),
                     ("Carried lighting", f"{len(y['lighting'])}", f"{len(y['lighting'])/y['contracts']*100:.1f}% of contracts", "#B7791F"),
                     ("Identified", money(ident), f"{money(awarded)} confirmed awarded", "#B7791F"),
                     ("Product", money(prod), "poles, luminaires, controls", "#B7791F")], W),
           Spacer(1, 10),
           Paragraph(f"Across ${y['lowBids']/1e9:.2f} billion of low bids and {y['contracts']} contracts, "
                     f"{len(y['lighting'])} carried any Division 14 lighting at all — "
                     f"{ident/y['lowBids']*100:.3f}% of the money. Of the {money(ident)} identified, {money(prod)} buys "
                     "product; the rest is conduit, feeder, junction boxes and relocation labour. Two contracts hold "
                     "almost all of the product value. The practical read: roadway-lighting product in North Carolina "
                     "arrives in a small number of high-mast packages a year, not spread across the programme — which "
                     "is why the programmed pipeline matters more than watching every letting.", S["body"]),
           Paragraph("The contracts that carried lighting", S["h2"])]
    rows = [["Contract", "Where", "Letting", "Low bidder", "Identified", "Product", "Status"]]
    for c in y["lighting"]:
        rows.append([Paragraph(f"<b>{c['id']}</b><br/><font size=7 color='#5A6B7B'>{c.get('tip') or '—'}</font>", S["cell"]),
                     Paragraph(f"{c['county']}<br/><font size=7 color='#5A6B7B'>Div {c['div']}</font>", S["cell"]),
                     Paragraph(c["let"], S["cell"]), Paragraph(c["low"], S["cell"]),
                     Paragraph(f"<b>{money(c['l2'])}</b>", S["cell"]), Paragraph(money(c["product"]), S["cell"]),
                     Paragraph(f"<font color='{'#1E7B45' if c.get('award')=='awarded' else '#B7791F'}'>"
                               f"{'Awarded' if c.get('award')=='awarded' else 'Apparent'}</font>", S["cell"])])
    st += [tbl(rows, [0.78 * inch, 0.82 * inch, 0.7 * inch, W - 4.48 * inch, 0.78 * inch, 0.7 * inch, 0.7 * inch],
               align={4: "RIGHT", 5: "RIGHT"})]

    # ---- ownership and the decision body ----
    st += [PageBreak(), Paragraph("Who pays for lighting, and who decides it goes in", S["h1"]),
           Paragraph("Before any bid data exists, one policy decides whether roadway lighting can appear in an NCDOT "
                     "contract at all. It is the single most useful page in this document, because it explains every "
                     "number in the rest of it.", S["body"]),
           stat_row([("NCDOT builds and maintains", "Interchanges", "and continuous fully controlled-access sections", "#003B73"),
                     ("The test", "Priority Index", "vs. a Base Index, reviewed every two years", "#003B73"),
                     ("Everywhere else", "Municipal", "the town pays, or agrees to maintain", "#003B73")], W),
           Spacer(1, 10),
           Paragraph("NCDOT constructs and maintains lighting only at interchanges and along continuous sections of "
                     "fully controlled-access roadway that meet its criteria, tested by a Priority Index measured "
                     "against a Base Priority Index. Elsewhere a municipality must reimburse the full design and "
                     "construction cost or agree to maintain and operate the system \u2014 and where a local government "
                     "fails to maintain a system it agreed to operate, the Department withholds a portion of that "
                     "government\u2019s Powell Bill funds equal to the cost of maintaining it.", S["body"]),
           Paragraph(f"<b>This is why the year looks the way it does.</b> Only {len(y['lighting'])} of {y['contracts']} "
                     "Central contracts carried lighting, and nearly all the product value sat in two high-mast "
                     "packages, both at freeway locations. That is not a thin sample; it is the policy working exactly "
                     "as written. <b>NCDOT-funded lighting is effectively an interchange and freeway product line.</b> "
                     "Surface-street lighting is usually municipal money \u2014 a different customer, a different budget "
                     "cycle, and it never appears in an NCDOT letting at all when the town builds it under an "
                     "encroachment.", S["body"]),
           Paragraph("The body that decides \u2014 the Roadway Lighting Committee", S["h2"]),
           Paragraph("An Electrical Engineer completes a lighting evaluation report; the Lighting and Electrical Team "
                     "Lead submits it; the Committee reviews it alongside Division comments and makes the final "
                     "decision on whether lighting goes into the roadway contract. Seven voting members, chaired by "
                     "the State Roadway Design Engineer.", S["body"])]
    seats = [["Seat on the Committee", "Who holds it", "Reachable"],
             ["State Roadway Design Engineer \u2014 Chair", "Steve T. Smallwood, PE", "stsmallwood1@ncdot.gov \u00b7 (919) 707-6342"],
             ["Lighting and Electrical Team Lead", "Greg Hall", "rghall@ncdot.gov \u00b7 (919) 707-6247"],
             ["Roadway Design Specialty Functions Group Lead", "Michael D. Lindgren, PE", "mdlindgren@ncdot.gov \u00b7 (919) 707-6207"],
             ["Director of Field Support", "Troy B. Brooks, PE", "tbbrooks2@ncdot.gov \u00b7 (919) 707-2509"],
             ["Director of Technical Services", "Not yet named", "seat named in the policy; person not verified"],
             ["State Traffic Safety Engineer", "Not yet named", "seat named in the policy; person not verified"],
             ["Director of Planning and Programming", "Not yet named", "seat named in the policy; person not verified"],
             ["FHWA Operations Engineer (observer)", "Not yet named", "seat named in the policy; person not verified"]]
    rows = [seats[0]] + [[Paragraph(a, S["cell"]),
                          Paragraph(f"<b>{b}</b>" if not b.startswith("Not yet") else f"<font color='#B7791F'>{b}</font>", S["cell"]),
                          Paragraph(f"<font size=7.4>{c}</font>", S["cell"])] for a, b, c in seats[1:]]
    st += [tbl(rows, [W - 4.05 * inch, 1.55 * inch, 2.5 * inch]),
           Spacer(1, 8),
           Paragraph("<b>Four of the seven voting seats are already in the contact list in this document, chair "
                     "included.</b> The decision to put lighting into an NCDOT contract is made by a named, standing "
                     "committee \u2014 not by a Division office, and not by the contractor who installs it. Influence "
                     "happens before the letting, at the evaluation-report stage, through the Lighting and Electrical "
                     "Team Lead. The four unnamed seats are the next people to identify.", S["body"])]

    # ---- the ownership layer across the territory (four shapes, from the page's own registries) ----
    own = data.get("ownership") or {}
    if own.get("AL") and own.get("TN"):
        st += [Spacer(1, 14), Paragraph("The same layer across the territory — eight states, four shapes", S["h2"]),
               stat_row([("North Carolina", "Policy", "a warrant test and a standing committee decide", "#003B73"),
                         ("Alabama · Mississippi · Arkansas", "Distributed", "case-by-case — city by city; split at the city line under an elected commission; by local request", "#003B73"),
                         ("Tennessee · Georgia · South Carolina", "Two-key", "a state approval plus a local owner — warrant, signed commitment, or photometric permit gate", "#003B73"),
                         ("Kentucky", "State-owned", "KYTC installs and maintains; the project list is enacted as law", "#003B73")], W),
               Spacer(1, 8)]
        for sid, nm in [("AL","Alabama"),("TN","Tennessee"),("GA","Georgia"),("SC","South Carolina"),("MS","Mississippi"),("AR","Arkansas"),("KY","Kentucky")]:
            if own.get(sid) and own[sid].get("digest"):
                st += [Paragraph(f"<b>{nm} — who buys:</b> " + own[sid]["digest"][0] + ". " + own[sid]["digest"][1], S["body"])]
        st += [Paragraph("The rule this proves, now applied across the whole territory: read the ownership and funding model "
                         "before anything else. It explains what the letting record will and will not show, and it "
                         "names the true customer — the municipality in most of the territory so far, and in "
                         "Kentucky, uniquely, the DOT itself.", S["body"])]

    # ---- pipeline ----
    st += [PageBreak(), Paragraph("What is coming — the programmed pipeline", S["h1"]),
           Paragraph(f"Every project in North Carolina's adopted 2026–2035 improvement programme whose scope names "
                     f"lighting, plus what the Board has funded since the programme snapshot. {len(pipe)} projects across "
                     f"{len(set(p['div'] for p in pipe))} of the 14 Divisions. Counted, never valued: the figure is the "
                     "whole project's programmed cost, not a lighting value.", S["body"])]
    order = {"pure": 0, "component": 1, "crosswalk": 2}
    label = {"pure": "Lighting is the scope", "component": "Lighting named in scope", "crosswalk": "Crosswalk beacon"}
    rows = [["Project", "Where", "Scope", "Stage", "Type"]]
    for p in sorted(pipe, key=lambda x: (order.get(x["kind"], 9), -x.get("cost", 0))):
        rows.append([Paragraph(f"<b>{p['tip']}</b>", S["cellb"]),
                     Paragraph(f"{p['county']}<br/><font size=7 color='#5A6B7B'>Div {p['div']}</font>", S["cell"]),
                     Paragraph(p["what"], S["cell"]),
                     Paragraph(f"{p.get('year','—')}<br/><font size=7 color='#5A6B7B'>{money(p.get('cost',0))}</font>", S["cell"]),
                     Paragraph(label.get(p["kind"], p["kind"]), S["cell"])])
    st += [tbl(rows, [0.72 * inch, 0.78 * inch, W - 3.9 * inch, 0.85 * inch, 1.05 * inch], size=7.6)]

    # ---- competition ----
    st += [PageBreak(), Paragraph("Who wins the work", S["h1"]),
           stat_row([("Contractors winning", f"{comp['winners']}", f"across {comp['contracts']} contracts", "#003B73"),
                     ("Largest single share", f"{comp['cr1']}%", f"of ${comp['total']/1e9:.2f}B", "#003B73"),
                     ("Top three combined", f"{comp['cr3']}%", "CR3", "#003B73"),
                     ("Concentration", f"{comp['hhi']}", "HHI — unconcentrated", "#1E7B45")], W),
           Spacer(1, 8),
           Paragraph(f"{comp['winners']} contractors took the {comp['contracts']} contracts and the largest holds "
                     f"{comp['cr1']}%. An HHI of {comp['hhi']} is an unconcentrated market by any standard reading — "
                     "there is no incumbent to displace at state level, and a bid is decided contract by contract. "
                     "Concentration is a Division story instead. This measures who <i>wins</i>, not who bids: the "
                     "letting spreadsheets carry itemised prices for at most four bidders per contract, so bidder "
                     "counts come from the Board's own record and are not claimed here.", S["body"]),
           Paragraph("Largest winners across the year", S["h2"])]
    rows = [["Contractor", "Contracts", "Value won", "Divisions", "Carried lighting"]]
    for c in comp["contractors"][:12]:
        rows.append([Paragraph(f"<b>{c['name']}</b>", S["cellb"]), Paragraph(str(c["n"]), S["cell"]),
                     Paragraph(f"${c['val']/1e6:.1f}M", S["cell"]), Paragraph(str(len(c["divs"])), S["cell"]),
                     Paragraph(f"{c['lit']} · {money(c['litval'])}" if c["lit"] else "—", S["cell"])])
    st += [tbl(rows, [W - 4.0 * inch, 0.75 * inch, 0.95 * inch, 0.8 * inch, 1.5 * inch],
               align={1: "CENTER", 2: "RIGHT", 3: "CENTER"})]

    # ---- divisions ----
    st += [PageBreak(), Paragraph("Territory reference — 14 Highway Divisions", S["h1"]),
           Paragraph("Activity over the twelve months, with the engineer who runs each Division. <b>Award not captured</b> "
                     "means the Board's award statement for that letting could not be retrieved — not that the contract "
                     "is known to be unawarded.", S["body"])]
    rows = [["Div", "Division Engineer", "Contracts", "Value", "Awarded", "Not captured", "Lighting", "Largest winner"]]
    for d in sorted(div, key=lambda k: -div[k]["val"]):
        v = div[d]; g = data["geoNC"][int(d) - 1]; b = comp["byDiv"].get(d, {})
        rows.append([Paragraph(f"<b>{d}</b>", S["cellb"]),
                     Paragraph(f"{g[1]}<br/><font size=7 color='#5A6B7B'>{g[2]}</font>", S["cell"]),
                     Paragraph(str(v["n"]), S["cell"]), Paragraph(f"${v['val']/1e6:.1f}M", S["cell"]),
                     Paragraph(f"<font color='#1E7B45'>{v['aw']}</font>", S["cell"]),
                     Paragraph(f"<font color='#B7791F'>{v['out']}</font>", S["cell"]),
                     Paragraph(money(v["litval"]) if v["lit"] else "—", S["cell"]),
                     Paragraph(f"{b.get('top','—')}<br/><font size=7 color='#5A6B7B'>{b.get('topShare','')}%</font>", S["cell"])])
    st += [tbl(rows, [0.3 * inch, 1.5 * inch, 0.6 * inch, 0.72 * inch, 0.62 * inch, 0.75 * inch, 0.8 * inch,
                      W - 5.29 * inch], size=7.4,
               align={2: "CENTER", 3: "RIGHT", 4: "CENTER", 5: "CENTER", 6: "RIGHT"})]

    # ---- who to call ----
    st += [PageBreak(), Paragraph("Who to call", S["h1"]),
           Paragraph("Verified against the NCDOT directory on August 31, 2026 — every address read off the page one "
                     "by one, never derived from a pattern. That matters here: the Lighting Team Lead is "
                     "<b>rghall@</b>, not the ghall@ an obvious rule would produce.", S["body"])]
    rows = [["", "Name", "Role", "Phone", "Email"]]
    for r in data["contacts"]:
        mail = r[4] if r[4] and r[4] != "dir" else "not yet transcribed"
        rows.append([Paragraph(f"<font size=7 color='#5A6B7B'>{r[0]}</font>", S["cell"]),
                     Paragraph(f"<b>{r[1]}</b>", S["cellb"]), Paragraph(r[2], S["cell"]),
                     Paragraph(r[3], S["cell"]), Paragraph(mail, S["cell"])])
    st += [tbl(rows, [0.85 * inch, 1.35 * inch, W - 5.5 * inch, 1.1 * inch, 1.6 * inch], size=7.4)]

    st += [Spacer(1, 14), Paragraph("What is not yet known", S["h2"]),
           Paragraph("The manufacturer on every contract. NCDOT's LED luminaire specification is written entirely as "
                     "performance requirements — it names no manufacturer and publishes no approved-product list — so "
                     "no public artifact in the letting chain says whose luminaire goes on the pole. The product "
                     "<i>classes</i> are known exactly (185W and 285W light-standard luminaires; 335W to 560W high mast; "
                     "3000K; ten-year warranty), and across the year that is 44 high-mast luminaires and one light "
                     "standard. This platform is built from the public record only, so that is where the question "
                     "rests: in a state that publishes no approved-product list, the manufacturer stays UNKNOWN, and "
                     "any share view built on less would be invented.", S["body"])]

    doc.build(st, onFirstPage=footer, onLaterPages=footer)
    return path


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.dirname(os.path.abspath(__file__))
    p = build(json.load(open(args[0])), args[1] if len(args) > 1 else "dev", out)
    print(f"wrote {p} ({os.path.getsize(p):,} bytes)")
