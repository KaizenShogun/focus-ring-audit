#!/usr/bin/env python3
"""Run measure.py over the framework corpus and write results.json.

One row per (framework, element). The stylesheet is loaded from the same CDN URL a person
would paste into their <head>, and its sha256 is recorded so the run can be pinned even
after the CDN moves.
"""
import argparse
import datetime
import hashlib
import json
import os
import sys
import urllib.request

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import measure  # noqa: E402

UA = "Mozilla/5.0 (compatible; focus-appearance-audit)"

# name, github repo (None = not found), CSS URL as a user would include it, classless?
CORPUS = [
    ("water.css",    "kognise/water.css",        "https://cdn.jsdelivr.net/npm/water.css@2/out/light.css", True),
    ("Pico CSS",     "picocss/pico",             "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.min.css", True),
    ("Simple.css",   "kevquirk/simple.css",      "https://cdn.jsdelivr.net/npm/simpledotcss@2/simple.css", True),
    ("Sakura",       "oxalorg/sakura",           "https://cdn.jsdelivr.net/npm/sakura.css/css/sakura.css", True),
    ("MVP.css",      "andybrewer/mvp",           "https://cdn.jsdelivr.net/npm/mvp.css", True),
    ("new.css",      "xz/new.css",               "https://cdn.jsdelivr.net/npm/@exampledev/new.css@1.1.2/new.min.css", True),
    ("awsm.css",     None,                       "https://cdn.jsdelivr.net/npm/awsm.css/dist/awsm.min.css", True),
    ("Bamboo",       "rilwis/bamboo",            "https://cdn.jsdelivr.net/npm/bamboo.css@1/dist/bamboo.min.css", True),
    ("Tacit",        "yegor256/tacit",           "https://cdn.jsdelivr.net/gh/yegor256/tacit@gh-pages/tacit-css.min.css", True),
    ("Bahunya",      "Kimeiga/bahunya",          "https://cdn.jsdelivr.net/gh/Kimeiga/bahunya/dist/bahunya.min.css", True),
    ("LaTeX.css",    "vincentdoerig/latex-css",  "https://cdn.jsdelivr.net/npm/latex.css/style.min.css", True),
    ("concrete.css", "louismerlin/concrete.css", "https://cdn.jsdelivr.net/npm/concrete.css", True),
    ("Marx",         "mblode/marx",              "https://cdn.jsdelivr.net/npm/marx-css/css/marx.min.css", True),
    ("matcha.css",   "lowlighter/matcha",        "https://cdn.jsdelivr.net/npm/@lowlighter/matcha/dist/matcha.css", True),
    ("holiday.css",  None,                       "https://cdn.jsdelivr.net/npm/holiday.css@0.11.2", True),
    # class-based, kept as reference points, not as part of the classless table
    ("Milligram",    "milligram/milligram",      "https://cdn.jsdelivr.net/npm/milligram@1/dist/milligram.min.css", False),
    ("Bootstrap 5",  "twbs/bootstrap",           "https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css", False),
]

ELEMENTS = [("#lnk", "link"), ("#inp", "text input"), ("#btn", "button")]


def sha_of(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    return hashlib.sha256(body).hexdigest()[:16], len(body), r.geturl()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="substring: run just the frameworks matching it")
    ap.add_argument("--out", default="results.json")
    ap.add_argument("--wait", type=int, default=8000)
    ap.add_argument("--tries", type=int, default=2,
                    help="repeat each measurement N times; disagreement is reported, not averaged")
    a = ap.parse_args()

    args = argparse.Namespace(css=None, url=None, width=900, height=700, wait=a.wait)
    rows = []
    for name, repo, url, classless in CORPUS:
        if a.only and a.only.lower() not in name.lower():
            continue
        sha, nbytes, final = sha_of(url)
        args.css = url
        for sel, label in ELEMENTS:
            r = measure.measure_stable(args, sel, tries=a.tries)
            r.update({"framework": name, "repo": repo, "css": url, "classless": classless,
                      "element": label, "css_sha256_16": sha, "css_bytes": nbytes,
                      "css_resolved": final})
            rows.append(r)
            print("%-13s %-11s %-6s %s%s" % (name, label, r.get("max_contrast"),
                                             r.get("verdict", r.get("error")),
                                             "" if r.get("stable", True) else "  [UNSTABLE]"))
            sys.stdout.flush()
    payload = {"measured_utc": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
               "chromium": measure.chrome_bin(), "viewport": [args.width, args.height],
               "rows": rows}
    with open(a.out, "w") as fh:
        json.dump(payload, fh, indent=1)
    print("\n-> %s (%d rows)" % (a.out, len(rows)))


if __name__ == "__main__":
    main()
