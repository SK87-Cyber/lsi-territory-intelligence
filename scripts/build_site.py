"""Build and verify before creating the Netlify entry point; no network or secrets."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    version = (ROOT / "BUILD").read_text().strip()
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    # Never leave an old entry point after a failed build.
    (out / "index.html").unlink(missing_ok=True)
    subprocess.run([sys.executable, "build.py", version, "--out", str(out)], cwd=ROOT, check=True)
    built = out / f"southeast-dot-lighting-intelligence-build-{version}.html"
    subprocess.run([os.getenv("NODE", "node"), "scripts/export_data.cjs", str(built), str(out / "snapshot.json")], cwd=ROOT, check=True)
    # One verified build, three entry points. The redesign is the main page; the classic layout is kept
    # beside it as the fallback. The two differ by one attribute on <html>.
    html = built.read_text(encoding="utf-8")
    marker = '<html lang="en">'
    if html.count(marker) != 1:
        raise SystemExit("expected exactly one html tag to mark the redesign")
    redesign = html.replace(marker, '<html lang="en" data-ui="next">', 1)
    (out / "index.html").write_text(redesign, encoding="utf-8")
    for name, page in (("classic", html), ("next", redesign)):
        folder = out / name
        folder.mkdir(exist_ok=True)
        (folder / "index.html").write_text(page, encoding="utf-8")
    print(f"Verified Netlify entry point: {out / 'index.html'}")

if __name__ == "__main__":
    main()
