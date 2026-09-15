#!/usr/bin/env python3
"""Controls for the harness: four stylesheets whose answer is known before we run them.

A sensor that cannot fail loudly is not a sensor. In particular C2 answers the question
the whole corpus depends on: does a programmatic .focus() match `:focus-visible` in this
browser? If it did not, every framework that styles `:focus-visible` (which is most of the
modern ones) would come out "no visible change" and the table would be a lie.

Expected, before running:
  C0 no stylesheet    -> the browser's own ring: visible, high contrast
  C1 :focus           -> visible, ~red on white, well over 3:1
  C2 :focus-visible   -> same as C1, IF programmatic focus matches focus-visible
  C3 outline:0        -> nothing changes at all
"""
import argparse
import json
import os
import sys
import urllib.parse

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import measure  # noqa: E402

SHEETS = {
    "C0 nothing":        "",
    "C1 :focus":         "a:focus,input:focus,button:focus{outline:6px solid #f00;outline-offset:2px}",
    "C2 :focus-visible": "a:focus-visible,input:focus-visible,button:focus-visible"
                         "{outline:6px solid #f00;outline-offset:2px}",
    "C3 outline:0":      "a:focus,input:focus,button:focus{outline:0}"
                         "a,input,button{border:0;background:#fff;color:#000}",
}


def data_uri(css):
    return "data:text/css," + urllib.parse.quote(css)


def main():
    args = argparse.Namespace(css=None, url=None, width=900, height=700, wait=8000)
    out = {}
    for name, css in SHEETS.items():
        args.css = data_uri(css) if css else data_uri("/*empty*/")
        rows = [measure.measure(args, s) for s in ("#lnk", "#inp", "#btn")]
        out[name] = rows
        print("== %s" % name)
        for r in rows:
            print("   %-6s %-7s changed=%-6s max=%-7s px>=3:1=%s"
                  % (r["selector"], r.get("visible"), r.get("changed_px"),
                     r.get("max_contrast"), r.get("px_at_3to1")))
    with open("controls.json", "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
