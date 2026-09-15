#!/usr/bin/env python3
"""Independent arithmetic check: composite an rgba() over a background and give the ratio.

If the pixel the browser drew and the number this prints disagree, believe neither until
you know why. Used to confirm that the failing rings are failing because of their alpha,
not because of a quirk of the screenshot.

    python3 alpha_check.py "rgba(2,154,232,0.5)" "#ffffff"
"""
import re
import sys

import measure


def parse(c):
    c = c.strip()
    m = re.match(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)", c)
    if m:
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        return tuple(float(m.group(i)) for i in (1, 2, 3)), a
    h = c.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) == 8:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), int(h[6:8], 16) / 255.0
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), 1.0


def main():
    fg, a = parse(sys.argv[1])
    bg, _ = parse(sys.argv[2])
    out = tuple(round(a * fg[i] + (1 - a) * bg[i]) for i in range(3))
    print("%s over %s  ->  rgb%s   contrast vs background: %.2f:1"
          % (sys.argv[1], sys.argv[2], out, measure.contrast(out, bg)))


if __name__ == "__main__":
    main()
