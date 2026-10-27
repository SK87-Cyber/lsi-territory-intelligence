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
    shutil.copyfile(built, out / "index.html")
    print(f"Verified Netlify entry point: {out / 'index.html'}")

if __name__ == "__main__":
    main()
