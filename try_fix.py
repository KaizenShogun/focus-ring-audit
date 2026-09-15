#!/usr/bin/env python3
"""Measure a framework, then measure it again with a proposed fix layered on top.

A fix nobody measured is an opinion. This imports the real stylesheet and appends the
override, so the "after" number comes from the same harness as the "before" one.

    python3 try_fix.py --css <url> --selector "#btn" \
        --fix ':root{--pico-primary-focus:#029ae8}'
"""
import argparse
import os
import sys
import urllib.parse

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import measure  # noqa: E402


def sheet(css_url, extra=""):
    return "data:text/css," + urllib.parse.quote('@import url("%s");\n%s' % (css_url, extra))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--css", required=True)
    ap.add_argument("--selector", action="append", required=True)
    ap.add_argument("--fix", action="append", default=[], help="CSS appended after the import")
    ap.add_argument("--wait", type=int, default=9000)
    ap.add_argument("--tries", type=int, default=2)
    a = ap.parse_args()

    args = argparse.Namespace(css=None, url=None, width=900, height=700, wait=a.wait)
    for label, extra in [("before", "")] + [("fix %d" % (i + 1), f) for i, f in enumerate(a.fix)]:
        args.css = sheet(a.css, extra)
        for sel in a.selector:
            r = measure.measure_stable(args, sel, tries=a.tries)
            print("%-8s %-6s max=%-7s px>=3:1=%-6s %s%s"
                  % (label, sel, r.get("max_contrast"), r.get("px_at_3to1"),
                     r.get("verdict", r.get("error")),
                     "" if r.get("stable", True) else "  [UNSTABLE]"))
        if extra:
            print("         via: %s" % extra)


if __name__ == "__main__":
    main()
