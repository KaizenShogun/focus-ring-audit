#!/usr/bin/env python3
"""Pico CSS in its dark theme, measured with the same harness as the light one.

The corpus is light-only. Reading the minified stylesheet turns up something the table
cannot show: in dark, `--pico-form-element-focus-color` stops being the opaque border
colour and becomes `var(--pico-primary-focus)` — the same translucent rgba that already
sinks the button. So the dark text input *should* fail too. It does not, and that is worth
a measurement rather than an argument.

Pico's dark theme lives behind `[data-theme=dark]` (and behind the media query), so asking
for the stylesheet is not enough: the attribute has to be on the `<html>` element. That is
the only thing that differs from measure.py here, so the numbers compare row for row with
the light ones.

    python3 _pico_dark.py            # -> pico_dark.json
"""
import argparse
import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import measure  # noqa: E402

CSS = "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.min.css"

measure.DEMO_PAGE = measure.DEMO_PAGE.replace(
    '<html lang="en">', '<html lang="en" data-theme="dark">')

ap = argparse.ArgumentParser()
ap.add_argument("--css", default=CSS)
ap.add_argument("--tries", type=int, default=2)
ap.add_argument("--out", default="pico_dark.json")
a = ap.parse_args()

args = argparse.Namespace(css=a.css, url=None, width=900, height=700, wait=9000)
rows = []
for name, sel in (("link", "#lnk"), ("text input", "#inp"), ("button", "#btn")):
    r = measure.measure_stable(args, sel, tries=a.tries)
    rows.append({"element": name, "selector": sel, "theme": "dark", "css": a.css,
                 "max_contrast": r.get("max_contrast"), "changed_px": r.get("changed_px"),
                 "px_at_3to1": r.get("px_at_3to1"), "aa_1411": r.get("aa_1411"),
                 "stable": r.get("stable", True)})
    print("%-11s max=%-7s changed=%-6s px>=3:1=%-6s %s%s"
          % (name, r.get("max_contrast"), r.get("changed_px"), r.get("px_at_3to1"),
             r.get("aa_1411", r.get("error")),
             "" if r.get("stable", True) else "  [UNSTABLE]"))
    sys.stdout.flush()
json.dump({"framework": "Pico CSS", "theme": "dark", "rows": rows},
          open(a.out, "w"), indent=1)
print("-> %s" % a.out)
