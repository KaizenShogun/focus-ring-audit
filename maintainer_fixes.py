#!/usr/bin/env python3
"""Measure candidate fixes for Bamboo and holiday.css with the same harness.

A fix nobody measured is an opinion. Each candidate is layered over the real stylesheet with
an `@import`, which is how it would arrive if the maintainer changed that line, and is measured
in BOTH themes: both sheets fail only in light, so a candidate that fixes light and sinks dark
is not a fix.

The shipped state is re-measured in the same batch (paired control). If the "before" does not
reproduce the published number, the "after" is worth nothing.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import measure  # noqa: E402

DARK_FLAG = "--blink-settings=preferredColorScheme=0"
BAMBOO = "https://cdn.jsdelivr.net/npm/bamboo.css@1.4.0/dist/bamboo.min.css"
HOLIDAY = "https://cdn.jsdelivr.net/npm/holiday.css@0.11.6"

# holiday: la lista de selectores de SU regla de foco, recortada a lo que hay en la página demo
H_SEL = ("button:focus,button:not([type]):focus,[type=\"text\"]:focus,input:not([type]):focus,"
         "textarea:focus,select:focus,summary:focus")

CASES = [
    # (hoja, etiqueta del candidato, css extra, qué elementos, en qué temas)
    (BAMBOO, "shipped", "", ("#lnk", "#inp", "#btn"), ("light", "dark")),
    (BAMBOO, "b-focus #5e81ac (nord10) en los dos temas",
     ":root{--b-focus:#5e81ac}", ("#lnk", "#inp", "#btn"), ("light", "dark")),
    (BAMBOO, "b-focus #4c566a (nord3) en los dos temas",
     ":root{--b-focus:#4c566a}", ("#btn",), ("light", "dark")),
    (BAMBOO, "b-focus por tema: #5e81ac claro / #88c0d0 oscuro",
     ":root{--b-focus:#5e81ac}@media(prefers-color-scheme:dark){:root{--b-focus:#88c0d0}}",
     ("#lnk", "#inp", "#btn"), ("light", "dark")),

    (HOLIDAY, "shipped", "", ("#inp", "#btn"), ("light", "dark")),
    (HOLIDAY, "anillo duro, mismo color (sin desenfoque)",
     "%s{box-shadow:0 0 0 .2rem var(--border-hover-color)!important}" % H_SEL,
     ("#inp", "#btn"), ("light", "dark")),
    (HOLIDAY, "light-border-hover-color #767676 (desenfoque intacto)",
     ":root{--light-border-hover-color:#767676}", ("#inp", "#btn"), ("light", "dark")),
    (HOLIDAY, "light-border-hover-color #595959 (desenfoque intacto)",
     ":root{--light-border-hover-color:#595959}", ("#inp", "#btn"), ("light", "dark")),
    (HOLIDAY, "anillo duro + #767676",
     ":root{--light-border-hover-color:#767676}"
     "%s{box-shadow:0 0 0 .2rem var(--border-hover-color)!important}" % H_SEL,
     ("#inp", "#btn"), ("light", "dark")),
]

_render = measure.render


def render_dark(html, args, png=None):
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


def sheet(url, extra):
    if not extra:
        return url
    return "data:text/css," + urllib.parse.quote('@import url("%s");\n%s' % (url, extra))


ap = argparse.ArgumentParser()
ap.add_argument("--tries", type=int, default=2)
ap.add_argument("--out", default="maintainer_fixes.json")
a = ap.parse_args()

args = argparse.Namespace(css=None, url=None, width=900, height=700, wait=9000)
label = {"#lnk": "link", "#inp": "text input", "#btn": "button"}
rows = []
for url, cand, extra, sels, themes in CASES:
    fw = "Bamboo" if url == BAMBOO else "holiday.css"
    print("== %s · %s" % (fw, cand))
    args.css = sheet(url, extra)
    for theme in themes:
        measure.render = _render if theme == "light" else render_dark
        for sel in sels:
            r = measure.measure_stable(args, sel, tries=a.tries)
            rows.append({"framework": fw, "candidate": cand, "extra_css": extra, "theme": theme,
                         "element": label[sel], "changed_px": r.get("changed_px"),
                         "max_contrast": r.get("max_contrast"), "px_at_3to1": r.get("px_at_3to1"),
                         "area_needed_approx": r.get("area_needed_approx"),
                         "aa_1411": r.get("aa_1411"), "stable": r.get("stable", True),
                         "error": r.get("error")})
            print("   %-5s %-11s changed=%-6s max=%-7s px>=3:1=%-6s %s%s"
                  % (theme, label[sel], r.get("changed_px"), r.get("max_contrast"),
                     r.get("px_at_3to1"), r.get("aa_1411", r.get("error")),
                     "" if r.get("stable", True) else "  [INESTABLE]"))
            sys.stdout.flush()
measure.render = _render

# ¿cuántas veces usa holiday la variable que propongo tocar? (cambiarla mueve también el hover)
src = urllib.request.urlopen(urllib.request.Request(
    "https://raw.githubusercontent.com/EvgenyOrekhov/holiday.css/master/dist/holiday.css",
    headers={"User-Agent": "focus-audit"}), timeout=60).read().decode()
usos = len(re.findall(r"var\(--border-hover-color\)", src))
print("\nholiday: var(--border-hover-color) usada %d veces en dist/holiday.css" % usos)

json.dump({"measured_utc": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
           "dark_flag": DARK_FLAG, "holiday_border_hover_uses": usos, "rows": rows},
          open(a.out, "w"), indent=1)
print("-> %s (%d filas)" % (a.out, len(rows)))
