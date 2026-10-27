#!/usr/bin/env python3
"""Probe word layout of a KYTC Unit Bid Tabulations page."""
import sys
import pdfplumber

path = sys.argv[1]
pages = [int(x) for x in sys.argv[2:]] or [0]
with pdfplumber.open(path) as pdf:
    for pno in pages:
        page = pdf.pages[pno]
        words = page.extract_words(keep_blank_chars=False)
        # group by y
        lines = {}
        for w in words:
            key = round(w['top'] / 3)
            lines.setdefault(key, []).append(w)
        print(f"=== page {pno} ===")
        for key in sorted(lines):
            ws = sorted(lines[key], key=lambda w: w['x0'])
            print(' | '.join(f"{w['text']}@{w['x0']:.0f}" for w in ws))
