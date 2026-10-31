"""Build the printable manual and drawing set from the HTML pages.

Requires Google Chrome (or Chromium) and `pip install pypdf`.

    python tools/build_pdfs.py            # writes manual/OBS-10-manual.pdf and drawings/OBS-10-drawings.pdf
    python tools/build_pdfs.py --png      # also refreshes manual/png and drawings/png previews

Each HTML page sets its own @page size, so every page prints at its true size
(manual pages are US Letter at 96 px/in, so the 1:1 hardware page prints actual size).
"""
import argparse, glob, os, shutil, subprocess, sys, tempfile
from pypdf import PdfWriter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = next((c for c in ("google-chrome", "chromium", "chromium-browser", "chrome") if shutil.which(c)), None)


def chrome(args):
    if not CHROME:
        sys.exit("Chrome/Chromium not found on PATH")
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--virtual-time-budget=4000", *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def size_of(html):
    import re
    m = re.search(r"@page\{size:(\d+)px (\d+)px", open(html, encoding="utf-8").read())
    return int(m.group(1)), int(m.group(2))


def build(pages, out_pdf, png=False, png_dir=None):
    writer = PdfWriter()
    if png and png_dir:
        os.makedirs(png_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for i, p in enumerate(pages):
            pdf = os.path.join(tmp, f"{i:03d}.pdf")
            url = "file://" + os.path.abspath(p)
            chrome(["--no-pdf-header-footer", f"--print-to-pdf={pdf}", url])
            writer.append(pdf)
            if png:
                w, h = size_of(p)
                name = os.path.splitext(os.path.basename(p))[0] + ".png"
                chrome([f"--window-size={w},{h}", "--force-device-scale-factor=1.5",
                        f"--screenshot={os.path.join(png_dir or os.path.dirname(p), name)}", url])
    with open(out_pdf, "wb") as f:
        writer.write(f)
    print("wrote", os.path.relpath(out_pdf, ROOT), f"({len(pages)} pages)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--png", action="store_true"); a = ap.parse_args()
    build(sorted(glob.glob(f"{ROOT}/manual/pages/*.html")), f"{ROOT}/manual/OBS-10-manual.pdf", a.png, f"{ROOT}/manual/png")
    build(sorted(glob.glob(f"{ROOT}/drawings/src/*.html")), f"{ROOT}/drawings/OBS-10-drawings.pdf", a.png, f"{ROOT}/drawings/png")
