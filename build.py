#!/usr/bin/env python3
"""Build the Southeast DOT Lighting Intelligence site from template.html.

Usage:  python3 build.py 1.6          -> writes southeast-dot-lighting-intelligence-build-1.6.html
        python3 build.py 1.6 --out /mnt/user-data/outputs

The template never contains the logos; it contains two placeholders,
__LSI_B64__ and __COOPER_B64__, which this script replaces with base64 PNGs.
Edit template.html, never the built file.
"""
import base64, sys, os, re

here = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
build = args[0] if args else None
out_dir = here
if "--out" in sys.argv:
    out_dir = sys.argv[sys.argv.index("--out") + 1]

tpl = open(os.path.join(here, "template.html"), encoding="utf-8").read()
assert tpl.count("__LSI_B64__") == 1 and tpl.count("__COOPER_B64__") == 1, "template placeholders missing"

if build:
    # stamp the build number everywhere it appears
    tpl = re.sub(r"Build \d+\.\d+[a-z]?", f"Build {build}", tpl)

geo_path = os.path.join(here, "geo-se.json")
if os.path.exists(geo_path):
    geo = open(geo_path, encoding="utf-8").read().strip()
    print(f"embedding geo-se.json ({os.path.getsize(geo_path):,} bytes) - map renders offline")
else:
    geo = "null"
    print("no geo-se.json - the built page will load boundaries from the CDN")
assert tpl.count("__GEO_JSON__") == 1, "geometry placeholder missing"
tpl = tpl.replace("__GEO_JSON__", geo)

lsi = base64.b64encode(open(os.path.join(here, "lsi-logo.png"), "rb").read()).decode()
coop = base64.b64encode(open(os.path.join(here, "cooper-logo.png"), "rb").read()).decode()
html = tpl.replace("__LSI_B64__", lsi).replace("__COOPER_B64__", coop)

name = f"southeast-dot-lighting-intelligence-build-{build}.html" if build else "southeast-dot-lighting-intelligence.html"
path = os.path.join(out_dir, name)
os.makedirs(out_dir, exist_ok=True)
open(path, "w", encoding="utf-8").write(html)
print(f"wrote {path} ({len(html):,} bytes)")
