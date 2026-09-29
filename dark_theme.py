#!/usr/bin/env python3
"""Measure a stylesheet's focus indicator in BOTH colour schemes.

The framework table in the README is the light theme. A sheet that ships a
`prefers-color-scheme: dark` block can pass in one theme and fail in the other, and Bamboo
and holiday.css both do exactly that — so the verdict is not publishable until both are
measured.

Dark is requested with `--blink-settings=preferredColorScheme=0`. That is the only flag found
that makes `matchMedia('(prefers-color-scheme: dark)').matches === true` without also turning
on Chrome's auto-darkening, which repaints the page and would measure something else.

Paired control: a sheet with no `prefers-color-scheme` block at all (Tacit), measured with the
flag and without it. If the flag alone moved a number, the dark column would mean nothing.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import urllib.request

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import measure  # noqa: E402

UA = "Mozilla/5.0 (compatible; focus-appearance-audit)"
DARK_FLAG = "--blink-settings=preferredColorScheme=0"

SHEETS = [
    ("Bamboo 1.4.0", "https://cdn.jsdelivr.net/npm/bamboo.css@1.4.0/dist/bamboo.min.css"),
    ("holiday.css 0.11.6", "https://cdn.jsdelivr.net/npm/holiday.css@0.11.6"),
    # control: sin @media prefers-color-scheme en toda la hoja
    ("CONTROL Tacit", "https://cdn.jsdelivr.net/gh/yegor256/tacit@gh-pages/tacit-css.min.css"),
]
ELEMENTS = [("#lnk", "link"), ("#inp", "text input"), ("#btn", "button")]

_render = measure.render


def render_dark(html, args, png=None):
    """measure.render con la bandera de tema oscuro metida en la línea de órdenes."""
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
        fh.write(html)
        path = fh.name
    cmd = [measure.chrome_bin(), "--headless=new", "--disable-gpu", "--no-sandbox",
           "--hide-scrollbars", "--force-device-scale-factor=1", DARK_FLAG,
           "--virtual-time-budget=%d" % args.wait,
           "--window-size=%d,%d" % (args.width, args.height)]
    cmd += ["--screenshot=" + png] if png else ["--dump-dom"]
    cmd.append("file://" + path)
    try:
        cp = subprocess.run(cmd, capture_output=True, timeout=args.wait / 1000 + 60)
        return cp.stdout.decode("utf-8", "replace")
    finally:
        os.unlink(path)


def fetch_meta(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    txt = body.decode("utf-8", "replace")
    return (hashlib.sha256(body).hexdigest()[:16], len(body),
            len(re.findall(r"prefers-color-scheme", txt)))


ap = argparse.ArgumentParser()
ap.add_argument("--tries", type=int, default=2)
ap.add_argument("--out", default="dark_theme.json")
a = ap.parse_args()

args = argparse.Namespace(css=None, url=None, width=900, height=700, wait=9000)
rows = []
for name, url in SHEETS:
    sha, nbytes, ndark = fetch_meta(url)
    print("== %s  %d bytes sha=%s  bloques prefers-color-scheme=%d" % (name, nbytes, sha, ndark))
    args.css = url
    for theme in ("light", "dark"):
        measure.render = _render if theme == "light" else render_dark
        for sel, label in ELEMENTS:
            r = measure.measure_stable(args, sel, tries=a.tries)
            rows.append({"framework": name, "css": url, "css_sha256_16": sha, "theme": theme,
                         "element": label, "selector": sel,
                         "component_px": r.get("component_px"),
                         "changed_px": r.get("changed_px"), "max_contrast": r.get("max_contrast"),
                         "median_contrast": r.get("median_contrast"),
                         "px_at_3to1": r.get("px_at_3to1"),
                         "area_needed_approx": r.get("area_needed_approx"),
                         "aa_1411": r.get("aa_1411"), "visible": r.get("visible"),
                         "stable": r.get("stable", True), "error": r.get("error")})
            print("   %-5s %-11s changed=%-6s max=%-7s px>=3:1=%-6s %s%s"
                  % (theme, label, r.get("changed_px"), r.get("max_contrast"),
                     r.get("px_at_3to1"), r.get("aa_1411", r.get("error")),
                     "" if r.get("stable", True) else "  [INESTABLE]"))
            sys.stdout.flush()
measure.render = _render
json.dump({"measured_utc": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
           "chromium": measure.chrome_bin(), "dark_flag": DARK_FLAG, "rows": rows},
          open(a.out, "w"), indent=1)
print("-> %s (%d filas)" % (a.out, len(rows)))
