#!/usr/bin/env python3
"""Measure a keyboard focus indicator in pixels, and check it against WCAG.

The idea is deliberately dumb, which is why it works: render the page twice — once with
nothing focused, once with the target element focused — and subtract the two screenshots.
Whatever changed *is* the focus indicator, as a person sees it. It does not matter whether
it came from `outline`, `box-shadow`, `border`, a background swap or a `::after`; and the
alpha compositing that hides "4px rings" that are really a 25% tint is already done by the
browser before we look.

Two criteria are in play, and they are not the same one:

  SC 1.4.11 Non-text Contrast (AA, WCAG 2.1+). Its Understanding document is explicit that
  state information — "whether a component is selected or focused" — needs 3:1 against
  adjacent colours. This is the AA bar, and it is the one that matters legally.

  SC 2.4.13 Focus Appearance (AAA, WCAG 2.2). Asks that some area of the indicator
  (a) be at least as large as a 2 CSS px thick perimeter of the unfocused component, and
  (b) reach 3:1 between the focused and unfocused states of those same pixels.
  (It was numbered 2.4.11 in old working drafts. In the Recommendation, 2.4.11 is Focus
  Not Obscured. Quoting the draft number is a real mistake — "AAA" reads as optional.)

When an indicator's pixels were background before focus, (b) and 1.4.11 compare the same
pair of colours, so one number answers both. That is the number this script reports.

So we report, for the changed pixels: how many there are, how many reach 3:1, and the
required area. Requirement (b) is measured exactly. Requirement (a) is an approximation —
see CAVEATS in the README before quoting it.

Usage:
    python3 measure.py --url https://example.com --selector "button.cta"
    python3 measure.py --css https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css

The second form renders a small built-in page (a link, a text input, a button) with that
stylesheet, which is how the framework table in the README was produced.

Requires: chromium (or chrome) on PATH, and Pillow. No npm, no headless framework.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

try:
    from PIL import Image
except ImportError:
    sys.exit("needs Pillow:  pip install pillow")

UA = "Mozilla/5.0 (compatible; focus-appearance-audit)"

# No background is forced here on purpose: a framework that ships a dark page must be
# measured on its own dark page. We impose exactly three things.
#
#  1. Room around the controls, so an outline drawn outside the box is never clipped.
#  2. A transparent caret on the text input. The blinking text cursor is not the input's
#     focus indicator and it changes ~15 px at 21:1 — enough to rescue a stylesheet that
#     in fact draws nothing at all. Control C3 in controls.py is that artifact, isolated.
#  3. No transitions and no animations. This one is not cosmetic: Pico CSS transitions its
#     focus styles over 0.2s, and without this the screenshot lands at a random point on
#     that curve. The first run of this corpus reported Pico's text input as "max 1.00:1,
#     nothing reaches 3:1" and a re-run of the same command reported 5.23:1. Both were the
#     same stylesheet; one was caught mid-fade. WCAG is about the settled state, and a
#     sensor that answers differently on two identical runs is not measuring anything.
DEMO_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="__CSS__">
<style>.wrap{padding:60px}#inp{caret-color:transparent!important}
*,*::before,*::after{transition:none!important;animation:none!important}</style>
</head><body><div class="wrap">
<p><a id="lnk" href="#x">an example link</a></p>
<p><input id="inp" type="text" class="form-control pure-input uk-input" value="text"></p>
<p><button id="btn" class="btn btn-primary button pure-button uk-button uk-button-default">Continue</button></p>
</div>__SCRIPT__</body></html>"""

SCRIPT = """<script>window.addEventListener("load",function(){
  var sel = %s;
  if (sel) { var e = document.querySelector(sel); if (e) e.focus(); }
  %s
});</script>"""

GEOM = ("var g=document.querySelector(%s);"
        "if(g){var r=g.getBoundingClientRect();"
        "document.body.insertAdjacentHTML('beforeend','<pre data-geom=\"'+"
        "[r.width,r.height].join(',')+'\"></pre>');}")


def chrome_bin():
    for c in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
        p = shutil.which(c)
        if p:
            return p
    sys.exit("no chromium/chrome found on PATH")


def build_page(args, focus_selector, want_geom_for=None):
    """Return the HTML to render: either the demo page or the real page with a <base>."""
    extra = GEOM % json.dumps(want_geom_for) if want_geom_for else ""
    script = SCRIPT % (json.dumps(focus_selector) if focus_selector else "null", extra)
    if args.css:
        return DEMO_PAGE.replace("__CSS__", args.css).replace("__SCRIPT__", script)
    req = urllib.request.Request(args.url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
        ct = r.headers.get("Content-Type", "")
    m = re.search(r"charset=([\w-]+)", ct)
    html = raw.decode(m.group(1) if m else "utf-8", "replace")
    if not re.search(r"<base\b", html, re.I):
        html = re.sub(r"(<head[^>]*>)", r'\1<base href="%s">' % args.url, html, count=1, flags=re.I)
    if re.search(r"</body>", html, re.I):
        return re.sub(r"</body>", script + "</body>", html, count=1, flags=re.I)
    return html + script


def render(html, args, png=None):
    """Screenshot to `png` (or dump the DOM if png is None). Returns the DOM text."""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
        fh.write(html)
        path = fh.name
    cmd = [chrome_bin(), "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
           "--force-device-scale-factor=1", "--virtual-time-budget=%d" % args.wait,
           "--window-size=%d,%d" % (args.width, args.height)]
    cmd += ["--screenshot=" + png] if png else ["--dump-dom"]
    cmd.append("file://" + path)
    try:
        cp = subprocess.run(cmd, capture_output=True, timeout=args.wait / 1000 + 60)
        return cp.stdout.decode("utf-8", "replace")
    finally:
        os.unlink(path)


def _lum(px):
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(px[0]) + 0.7152 * f(px[1]) + 0.0722 * f(px[2])


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def measure(args, selector, keep=None):
    with tempfile.TemporaryDirectory() as td:
        off = os.path.join(keep or td, "off.png") if keep else os.path.join(td, "off.png")
        on = os.path.join(keep or td, "on.png") if keep else os.path.join(td, "on.png")
        render(build_page(args, None), args, off)
        render(build_page(args, selector), args, on)
        dom = render(build_page(args, None, want_geom_for=selector), args)
        g = re.search(r'data-geom="([\d.]+),([\d.]+)"', dom)
        w, h = (float(g.group(1)), float(g.group(2))) if g else (None, None)
        if not (os.path.exists(off) and os.path.exists(on)):
            return {"selector": selector, "error": "screenshot failed"}
        ia = Image.open(off).convert("RGB")
        ib = Image.open(on).convert("RGB")
        pa, pb = ia.load(), ib.load()
        changed = []
        for y in range(min(ia.height, ib.height)):
            for x in range(min(ia.width, ib.width)):
                if pa[x, y] != pb[x, y]:
                    changed.append(contrast(pa[x, y], pb[x, y]))
    out = {"selector": selector, "component_px": [w, h] if w else None,
           "changed_px": len(changed)}
    if not changed:
        out.update({"visible": False, "verdict": "FAIL 2.4.7 — no visible change on focus"})
        return out
    changed.sort()
    at3 = sum(1 for c in changed if c >= 3.0)
    need = round((w + 4) * (h + 4) - w * h) if w else None
    out.update({
        "visible": True,
        "max_contrast": round(changed[-1], 2),
        "median_contrast": round(changed[len(changed) // 2], 2),
        "px_at_3to1": at3,
        "area_needed_approx": need,
    })
    # The AA verdict is the exact one: it needs only the contrast of the changed pixels.
    out["aa_1411"] = "FAIL" if at3 == 0 else "PASS"
    # The AAA area leg is an approximation and is reported as a ratio, never as a verdict.
    # `need` assumes a full 2 px perimeter of the border box; a real ring drawn at an
    # offset covers slightly more or less, so 0.9-1.1 means "indistinguishable from the
    # requirement with this method", not "borderline in the standard".
    out["area_ratio"] = round(at3 / need, 2) if need else None
    if at3 == 0:
        out["verdict"] = "FAIL 1.4.11 AA — the focus state changes %d px and not one reaches 3:1" % len(changed)
    else:
        out["verdict"] = "PASS 1.4.11 AA — %d px at >=3:1, up to %.2f:1" % (at3, changed[-1])
    return out


def measure_stable(args, selector, tries=2):
    """Measure `tries` times and refuse to report a number the harness cannot repeat."""
    runs = [measure(args, selector) for _ in range(tries)]
    key = lambda r: (r.get("visible"), r.get("px_at_3to1"), r.get("max_contrast"))  # noqa: E731
    out = runs[0]
    out["stable"] = all(key(r) == key(runs[0]) for r in runs)
    if not out["stable"]:
        out["runs"] = [key(r) for r in runs]
        out["verdict"] = "UNSTABLE across %d runs — %s" % (tries, out["runs"])
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="page to test")
    src.add_argument("--css", help="stylesheet URL to test against the built-in demo page")
    p.add_argument("--selector", action="append",
                   help="CSS selector of the element to focus (repeatable)")
    p.add_argument("--width", type=int, default=900)
    p.add_argument("--height", type=int, default=700)
    p.add_argument("--wait", type=int, default=12000, help="virtual time budget, ms")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args()

    selectors = args.selector or (["#lnk", "#inp", "#btn"] if args.css else None)
    if not selectors:
        p.error("--selector is required with --url")

    results = [measure(args, s) for s in selectors]
    if args.json:
        print(json.dumps(results, indent=1))
    else:
        for r in results:
            print("%-10s %s" % (r["selector"], r.get("verdict", r.get("error"))))
            if r.get("visible"):
                print("           changed %d px · max %.2f:1 · median %.2f:1 · %d px >= 3:1"
                      % (r["changed_px"], r["max_contrast"], r["median_contrast"], r["px_at_3to1"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
