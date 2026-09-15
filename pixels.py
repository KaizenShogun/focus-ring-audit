#!/usr/bin/env python3
"""Dump the distinct (unfocused -> focused) colour pairs the focus state produces.

A verdict of "max contrast 1.00:1" is exactly the kind of number that should make you
check the sensor before you believe it, so this prints the pairs themselves: what colour
each changed pixel was, what it became, how many pixels did that, and the ratio.
"""
import argparse
import os
import sys
from collections import Counter

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import measure  # noqa: E402

from PIL import Image  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--css", required=True)
    ap.add_argument("--selector", required=True)
    ap.add_argument("--wait", type=int, default=8000)
    ap.add_argument("--keep", help="directory to keep off.png / on.png in")
    a = ap.parse_args()
    args = argparse.Namespace(css=a.css, url=None, width=900, height=700, wait=a.wait)

    outdir = a.keep or "."
    off, on = os.path.join(outdir, "off.png"), os.path.join(outdir, "on.png")
    measure.render(measure.build_page(args, None), args, off)
    measure.render(measure.build_page(args, a.selector), args, on)
    ia, ib = Image.open(off).convert("RGB"), Image.open(on).convert("RGB")
    pa, pb = ia.load(), ib.load()
    pairs = Counter()
    box = [10**6, 10**6, -1, -1]
    for y in range(min(ia.height, ib.height)):
        for x in range(min(ia.width, ib.width)):
            if pa[x, y] != pb[x, y]:
                pairs[(pa[x, y], pb[x, y])] += 1
                box = [min(box[0], x), min(box[1], y), max(box[2], x), max(box[3], y)]
    print("%d distinct colour pairs, %d changed px, bbox x%d..%d y%d..%d"
          % (len(pairs), sum(pairs.values()), box[0], box[2], box[1], box[3]))
    for (A, B), n in pairs.most_common(22):
        print("  %6d px  %-16s -> %-16s  %.2f:1" % (n, A, B, measure.contrast(A, B)))


if __name__ == "__main__":
    main()
