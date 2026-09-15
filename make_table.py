#!/usr/bin/env python3
"""Turn results.json into the markdown table that goes in the README."""
import json
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

STARS = {  # stars fetched 2026-09-14, for ordering only
    "Bootstrap 5": 174797,
    "Pico CSS": 16858,
    "Milligram": 10216,
    "water.css": 8647,
    "MVP.css": 5132,
    "Simple.css": 5011,
    "Sakura": 4388,
    "new.css": 4047,
    "LaTeX.css": 3479,
    "matcha.css": 1936,
    "Tacit": 1883,
    "Marx": 1709,
    "concrete.css": 634,
    "Bahunya": 312,
    "Bamboo": 280,
    "holiday.css": 159,
}


def cell(r):
    if r.get("error"):
        return "err"
    if not r.get("visible"):
        return "**none**"
    mark = "" if r["aa_1411"] == "PASS" else "**"
    return "%s%.2f:1%s" % (mark, r["max_contrast"], mark)


def main():
    d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results.json"))
    by = {}
    for r in d["rows"]:
        by.setdefault(r["framework"], {})[r["element"]] = r
    order = sorted(by, key=lambda n: -(STARS.get(n) or 0))

    def block(names, title):
        print("\n### %s\n" % title)
        print("| framework | ★ | link | text input | button | verdict (SC 1.4.11 AA) |")
        print("|---|--:|--:|--:|--:|---|")
        for n in names:
            rs = by[n]
            fails = [e for e in ("link", "text input", "button")
                     if rs.get(e, {}).get("aa_1411") == "FAIL" or rs.get(e, {}).get("visible") is False]
            v = "passes on all three" if not fails else "**fails on %s**" % ", ".join(fails)
            unstable = any(not rs[e].get("stable", True) for e in rs)
            # No repo, no link: a row pointing at a bare github.com is worse than plain text.
            repo = rs["link"].get("repo")
            label = "[%s](https://github.com/%s)" % (n, repo) if repo else n
            print("| %s | %s | %s | %s | %s | %s%s |"
                  % (label,
                     STARS.get(n) or "—",
                     cell(rs.get("link", {})), cell(rs.get("text input", {})),
                     cell(rs.get("button", {})), v, " ⚠ unstable" if unstable else ""))

    classless = [n for n in order if by[n]["link"]["classless"]]
    other = [n for n in order if not by[n]["link"]["classless"]]
    print("Measured %s, chromium headless, 900×700, default light scheme." % d["measured_utc"])
    block(classless, "Classless frameworks")
    block(other, "Reference points (class-based, not part of the claim)")

    nf = sum(1 for n in classless
             if any(by[n][e]["aa_1411"] == "FAIL" for e in by[n]))
    print("\n%d of %d classless frameworks fail SC 1.4.11 on at least one of the three elements."
          % (nf, len(classless)))


if __name__ == "__main__":
    main()
