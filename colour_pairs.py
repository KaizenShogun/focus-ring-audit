#!/usr/bin/env python3
"""Print the exact colour pairs behind a contrast number, so it can be checked by hand.

The harness compares every pixel with itself, focused and unfocused. If it reports 2.00:1, a
maintainer should not have to run anything to believe it: this prints WHICH two colours, and
how many pixels take that transition, so the WCAG arithmetic can be redone on paper.
"""
import argparse
import collections
import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import measure  # noqa: E402
from PIL import Image  # noqa: E402

BAMBOO = "https://cdn.jsdelivr.net/npm/bamboo.css@1.4.0/dist/bamboo.min.css"
HOLIDAY = "https://cdn.jsdelivr.net/npm/holiday.css@0.11.6"
CASES = [("Bamboo", BAMBOO, "#btn"), ("Bamboo", BAMBOO, "#inp"),
         ("holiday.css", HOLIDAY, "#btn"), ("holiday.css", HOLIDAY, "#inp")]

args = argparse.Namespace(css=None, url=None, width=900, height=700, wait=9000)
out = {}
for fw, url, sel in CASES:
    args.css = url
    os.makedirs("_pairs_tmp", exist_ok=True)
    d = measure.measure(args, sel, keep=os.path.abspath("_pairs_tmp"))
    ia = Image.open("_pairs_tmp/off.png").convert("RGB")
    ib = Image.open("_pairs_tmp/on.png").convert("RGB")
    pa, pb = ia.load(), ib.load()
    pares = collections.Counter()
    for y in range(min(ia.height, ib.height)):
        for x in range(min(ia.width, ib.width)):
            if pa[x, y] != pb[x, y]:
                pares[(pa[x, y], pb[x, y])] += 1
    print("== %s %s  changed=%s max=%s px>=3:1=%s" % (
        fw, sel, d.get("changed_px"), d.get("max_contrast"), d.get("px_at_3to1")))
    filas = []
    for (a, b), n in pares.most_common(6):
        c = measure.contrast(a, b)
        hx = lambda p: "#%02x%02x%02x" % p  # noqa: E731
        print("   %6d px  %s -> %s   %.2f:1" % (n, hx(a), hx(b), c))
        filas.append({"n": n, "antes": hx(a), "despues": hx(b), "contraste": round(c, 2)})
    out["%s %s" % (fw, sel)] = {"changed_px": d.get("changed_px"),
                                "max_contrast": d.get("max_contrast"),
                                "px_at_3to1": d.get("px_at_3to1"), "pares": filas}
json.dump(out, open("colour_pairs.json", "w"), indent=1)
print("-> colour_pairs.json")
