#!/usr/bin/env python3
"""Is there one paste-in override that fixes the focus ring on every framework that fails?

A fix nobody measured is an opinion. This runs the same harness over each failing
(framework, element) pair from results.json: once as shipped, then once per candidate
override, layered on top of the real stylesheet exactly as a site owner would layer it.

The candidates differ on purpose. `solid` is the obvious one and will lose on a dark page
or against a same-coloured component; `dual` is the two-tone ring that is supposed to
survive any background. Neither carries `!important`, which is the point: read the README
for what that costs. To measure a candidate that does, hand it to try_fix.py:

    python3 fix_candidates.py --tries 2      # -> fixes.json
    python3 try_fix.py --css <url> --selector "#btn" \
        --fix 'button:focus-visible{outline:3px solid #005fcc !important;...}'
"""
import argparse
import json
import os
import sys
import urllib.parse

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import measure  # noqa: E402

SEL = ("a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,"
       "textarea:focus-visible,summary:focus-visible,[tabindex]:focus-visible,"
       "[role=button]:focus-visible")

CANDS = {
    "solid": "%s{outline:3px solid #005fcc;outline-offset:2px}" % SEL,
    "dual": "%s{outline:2px solid #000;outline-offset:2px;"
            "box-shadow:0 0 0 6px #fff,0 0 0 8px #000}" % SEL,
}


def sheet(url, extra):
    return "data:text/css," + urllib.parse.quote('@import url("%s");\n%s' % (url, extra))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results.json")
    ap.add_argument("--out", default="fixes.json")
    ap.add_argument("--tries", type=int, default=2)
    a = ap.parse_args()

    cands = dict(CANDS)
    d = json.load(open(a.results))
    targets = [r for r in d["rows"]
               if r.get("aa_1411") == "FAIL" or r.get("visible") is False]
    print("%d failing rows; trying %d candidates\n" % (len(targets), len(cands)))

    args = argparse.Namespace(css=None, url=None, width=900, height=700, wait=9000)
    out = []
    selmap = {"link": "#lnk", "text input": "#inp", "button": "#btn"}
    for t in targets:
        row = {"framework": t["framework"], "element": t["element"], "css": t["css"],
               "before": {"max_contrast": t.get("max_contrast"),
                          "px_at_3to1": t.get("px_at_3to1"),
                          "aa_1411": t.get("aa_1411"), "visible": t.get("visible")},
               "after": {}}
        for name, css in cands.items():
            args.css = sheet(t["css"], css)
            r = measure.measure_stable(args, selmap[t["element"]], tries=a.tries)
            row["after"][name] = {"max_contrast": r.get("max_contrast"),
                                  "px_at_3to1": r.get("px_at_3to1"),
                                  "aa_1411": r.get("aa_1411"),
                                  "stable": r.get("stable", True),
                                  "error": r.get("error")}
            print("%-13s %-11s %-9s max=%-7s px=%-6s %s%s"
                  % (t["framework"], t["element"], name, r.get("max_contrast"),
                     r.get("px_at_3to1"), r.get("aa_1411", r.get("error")),
                     "" if r.get("stable", True) else "  [UNSTABLE]"))
            sys.stdout.flush()
        out.append(row)
    json.dump({"candidates": cands, "rows": out}, open(a.out, "w"), indent=1)
    print("\n-> %s" % a.out)
    for name in cands:
        ok = sum(1 for r in out if r["after"][name].get("aa_1411") == "PASS")
        print("%-9s passes %d/%d" % (name, ok, len(out)))


if __name__ == "__main__":
    main()
