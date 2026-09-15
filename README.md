# focus-ring-audit

**Tab through your own site. Can you see where you are?**

If you can't, neither can anyone who navigates by keyboard — and there is a good chance you
never wrote a line of CSS to cause it. Some stylesheets replace the focus ring the browser
already drew correctly with one that composites away to nothing.

This repo is two things:

1. **A measuring tool.** Point it at your page and a selector. It renders twice — unfocused
   and focused — subtracts the screenshots, and reports the WCAG contrast of every pixel
   that changed. Whatever changed *is* the focus indicator, so it does not care whether the
   indicator came from `outline`, `box-shadow`, a border, a background swap or a
   pseudo-element, and it sees the alpha compositing that a CSS reader cannot.
2. **An audit of 15 classless CSS frameworks**, run with that tool, with the exact line of
   CSS responsible for each failure and a fix that was measured rather than guessed.

**The result: 4 of the 15 classless frameworks leave at least one of a link, a text input and
a button with a focus indicator below 3:1** — Pico CSS (on buttons), water.css, holiday.css,
and Bamboo, which fails on all three. The other 11 pass, most of them for the same reason:
they leave the ring the browser already drew alone. Two class-based frameworks were measured
as reference points, and both fail: Bootstrap 5 and Milligram.

If you use one of the four, the fix is at the bottom and it was measured, not guessed.

## Why a screenshot and not a CSS parser

Automated accessibility scanners do not check this. axe-core, Lighthouse and friends cannot
see `:focus` styles at all — the state only exists during interaction, and the rules they
run look at the resting DOM. That gap is the whole reason this is worth measuring.

Reading the CSS by hand does not work either, and the audit below is the proof. Every
framework that fails here *declares* a focus ring — a real one, two or three pixels thick, in
a sensible colour. Not one of them writes `outline: none` and stops. They fail in three
different ways, and all three are invisible to anyone grepping for `outline`:

| | what the CSS says | what the browser draws |
|---|---|---|
| **an alpha channel on the ring colour** | `box-shadow: 0 0 0 2px rgba(2,154,232,.5)` | composited over the page: `rgb(128,204,244)` — **1.77:1** |
| **a pale opaque colour** | `box-shadow: 0 0 0 2px #88c0d0` | exactly what it says — **2.00:1** |
| **a blur radius instead of a hard ring** | `box-shadow: 0 0 .2rem .01rem <colour>` | a glow whose peak never gets near the declared colour — **1.58:1** |

Nothing in any of those lines says "invisible". The pixels do.

## Check your own site

Needs `chromium` (or `chrome`) on `PATH` and Pillow. No npm, no headless framework, no
network service.

```bash
pip install pillow
python3 measure.py --url https://example.com --selector "button.cta"
```

It prints the changed-pixel count, the best contrast any of them reaches, and a verdict
against SC 1.4.11. To check a stylesheet instead of a page, on a built-in demo page with a
link, a text input and a button:

```bash
python3 measure.py --css https://cdn.jsdelivr.net/npm/water.css@2/out/light.css
```

And to test a fix before you ship it — same harness, your override layered on the real
stylesheet, so the "after" number is comparable to the "before" one:

```bash
python3 try_fix.py --css <your stylesheet> --selector "#btn" \
    --fix ':focus-visible{outline:3px solid #005fcc;outline-offset:2px}'
```

## Is the sensor real?

`python3 controls.py` runs four stylesheets whose answer is known before the run, and it is
the first thing to run if you doubt a number here:

| control | stylesheet | expected | measured |
|---|---|---|---|
| C0 | none — the browser's own ring | visible, high contrast | 16.55–19.03:1 |
| C1 | `:focus{outline:6px solid red}` | visible, ~4:1 on white | 4.00:1, 1320–2716 px |
| C2 | `:focus-visible{…}`, same ring | **identical to C1** | identical to C1 |
| C3 | `outline:0`, borders removed | **nothing changes at all** | 0 changed pixels |

C2 is the one everything else rests on. The harness focuses elements with a programmatic
`.focus()`, and most modern frameworks style `:focus-visible`, not `:focus`. If programmatic
focus did not match `:focus-visible` in this browser, every one of them would come out as
"no visible change" and the table below would be a fabrication of the harness. C1 and C2
come out identical, so it does. C3 is the floor: a stylesheet that truly draws nothing must
read as zero.

## The audit

Measured 2026-09-14, Chromium headless, 900×700, default light colour scheme. Each cell is the
best contrast any changed pixel reaches when that element takes focus; **bold** is below 3:1.
Stars fetched the same day, for ordering only.

### Classless frameworks

| framework | ★ | link | text input | button | verdict (SC 1.4.11 AA) |
|---|--:|--:|--:|--:|---|
| [Pico CSS](https://github.com/picocss/pico) | 16858 | 3.55:1 | 5.23:1 | **1.77:1** | **fails on button** |
| [water.css](https://github.com/kognise/water.css) | 8647 | 19.03:1 | **2.27:1** | **2.27:1** | **fails on text input, button** |
| [MVP.css](https://github.com/andybrewer/mvp) | 5132 | 19.03:1 | 19.03:1 | 5.39:1 | passes on all three |
| [Simple.css](https://github.com/kevquirk/simple.css) | 5011 | 19.03:1 | 19.03:1 | 8.63:1 | passes on all three |
| [Sakura](https://github.com/oxalorg/sakura) | 4388 | 18.07:1 | 4.79:1 | 18.07:1 | passes on all three |
| [new.css](https://github.com/xz/new.css) | 4047 | 19.03:1 | 17.87:1 | 19.03:1 | passes on all three |
| [LaTeX.css](https://github.com/vincentdoerig/latex-css) | 3479 | 5.02:1 | 19.03:1 | 16.55:1 | passes on all three |
| [matcha.css](https://github.com/lowlighter/matcha) | 1936 | 19.03:1 | 19.03:1 | 19.03:1 | passes on all three |
| [Tacit](https://github.com/yegor256/tacit) | 1883 | 19.03:1 | 19.03:1 | 19.03:1 | passes on all three |
| [Marx](https://github.com/mblode/marx) | 1709 | 5.24:1 | 5.24:1 | 5.24:1 | passes on all three |
| [concrete.css](https://github.com/louismerlin/concrete.css) | 634 | 19.03:1 | 18.88:1 ⚠ | 18.88:1 ⚠ | passes on all three |
| [Bahunya](https://github.com/Kimeiga/bahunya) | 312 | 18.92:1 | 4.55:1 | 3.97:1 | passes on all three |
| [Bamboo](https://github.com/rilwis/bamboo) | 280 | **2.00:1** | **2.00:1** | **2.00:1** | **fails on link, text input, button** |
| [holiday.css](https://github.com/EvgenyOrekhov/holiday.css) | 159 | 19.03:1 | **1.58:1** | **1.54:1** | **fails on text input, button** |
| awsm.css | — | 19.03:1 | 9.04:1 | 9.04:1 | passes on all three |

### Reference points (class-based, not part of the claim)

| framework | ★ | link | text input | button | verdict (SC 1.4.11 AA) |
|---|--:|--:|--:|--:|---|
| [Bootstrap 5](https://github.com/twbs/bootstrap) | 174797 | 19.03:1 | **1.58:1** | **1.84:1** | **fails on text input, button** |
| [Milligram](https://github.com/milligram/milligram) | 10216 | 19.03:1 | 3.19:1 | **1.10:1** | **fails on button** |

⚠ concrete.css clears the bar on 16 pixels. That is a pass, because SC 1.4.11 sets a contrast
threshold and no minimum area — but 16 pixels is not a focus indicator anyone can find, and it
is exactly what the *area* leg of SC 2.4.13 exists to catch. `results.json` carries the
`changed_px` and `area_ratio` for every row; the table cannot show you that in one number, so
read the JSON before quoting a pass as an endorsement.

The where-it-comes-from, for the four that fail:

| framework | the line | why it fails |
|---|---|---|
| Pico CSS | `--pico-primary-focus: rgba(2, 154, 232, .5)` on `button:focus`'s `box-shadow` | 50% alpha; composites to `rgb(128, 204, 244)` on white |
| water.css | `button:focus{box-shadow: 0 0 0 2px #0096bfab}` | `ab` is 67% alpha |
| Bamboo | `:focus{outline:none; box-shadow: 0 0 0 2px var(--b-focus)}`, `--b-focus: #88c0d0` | no alpha at all — the colour is simply too pale |
| holiday.css | `button:focus{outline:0; box-shadow: 0 0 .2rem .01rem var(--border-hover-color)}` | `.2rem` of *blur*: the glow never reaches the declared colour |

`python3 focus_rules.py <stylesheet-url>` prints that for any sheet, and `python3
alpha_check.py "rgba(2,154,232,0.5)" "#ffffff"` does the compositing arithmetic on its own, as
a second opinion independent of the screenshots. On every row above the two agree to the
hundredth: 1.77, 2.00, 2.27.

One warning about `focus_rules.py`: it finds rules whose *selector* contains `focus`. A
stylesheet that kills the native ring with a plain `button{outline:none}` is invisible to it,
and to every other CSS reader. That is the case for the screenshot method.

## The fix

### If you own the site: one rule — and it needs `!important`

This is the part I got wrong first, so it leads. The advice everybody gives is "just write
your own focus ring". Measured against the eleven failing (framework, element) pairs above,
layered on the real stylesheet exactly as a site owner would layer it:

```css
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible,
textarea:focus-visible, summary:focus-visible, [tabindex]:focus-visible,
[role=button]:focus-visible {
  outline: 3px solid #005fcc !important;
  outline-offset: 2px !important;
}
```

| override | pairs it fixes |
|---|--:|
| the rule above, **without** `!important` | 6 / 11 |
| a two-tone ring (`outline:2px solid #000` + `box-shadow:0 0 0 6px #fff,0 0 0 8px #000`), without `!important` | 7 / 11 |
| the rule above, **with** `!important` | **11 / 11** |

The last row is six measurements plus five: the six that already pass without `!important`
are not re-measured with it, and the five it skips were, one by one — holiday.css input
5.98:1 over 4137 px, holiday.css button 5.98:1 over 795, Milligram button 5.98:1 over 1017,
Bootstrap 5 input 5.98:1 over 4933, Bootstrap 5 button 5.98:1 over 850. Each of those runs
re-measured the "before" in the same command, and all five landed on the shipped number to
the hundredth (1.58, 1.54, 1.10, 1.58, 1.84), which is the reproducibility check.

Without the `!important` it does not degrade — it does *nothing*, silently, and your page
measures exactly as it did before you wrote it: holiday.css stayed at 1.54:1 on the button
to the hundredth, Milligram at 1.10:1, Bootstrap 5 at 1.84:1. The cause is specificity, and
holiday.css shows it in one line:

```css
button:focus, button:not([type]):focus, ... { outline: 0 }
```

`button:not([type]):focus` is (0,2,1). A plain `button:focus-visible` is (0,1,1), so it loses
no matter where you put it in the file, and no matter how late your stylesheet loads. Same
rule with `!important`: 5.98:1 over 795 px, a pass. (For Milligram and Bootstrap 5 I did not
chase the exact selector that outranks it. The measured fact is the same flip.)

The colour is not sacred — `#005fcc` is a dark blue that clears 3:1 on white. On a dark page
you want the opposite, and the two-tone ring is the one that survives both without you
knowing the background.

### If you maintain one of the four

The failure is one declaration in each, and the smallest honest fix is to stop compositing
the ring against the page:

| framework | today | measured fix |
|---|---|---|
| Pico CSS | `--pico-primary-focus: rgba(2, 154, 232, .5)` | dropping the alpha (`#029ae8`) gets 1.77 → **3.09:1**, which clears the bar by 0.09. `#0172ad` — the opaque colour Pico's own text input ring already uses — gets **5.23:1** |
| water.css | `--focus: #0096bfab` | `#0096bf` — the same colour, without the `ab` |
| Bamboo | `--b-focus: #88c0d0` | a darker blue; the colour has no alpha, it is simply too pale |
| holiday.css | `box-shadow: 0 0 .2rem .01rem <colour>` | a hard ring: the `.2rem` of blur is what keeps the glow away from the declared colour |

Every one of those is a variable, which is the good news: you can test the change without
touching a selector, and `try_fix.py` measures it before you ship it.

One trap if you are overriding Pico from your own stylesheet rather than patching it:
`:root{--pico-primary-focus:#0172ad}` changes **nothing**, measured — Pico declares that
variable inside a block with a higher specificity than `:root`, so a plain `:root` override
loses in silence, exactly like the missing `!important` above. Both numbers in the row come
from an override that carries `!important`.

### Pico CSS in its dark theme

The table is light-only. Pico ships a dark theme, and it is measured separately in
[`pico_dark.json`](pico_dark.json) (`_pico_dark.py` is the same harness with
`data-theme="dark"` on the `<html>`): the link reaches 3.50:1, the text input 3.43:1 — both
pass — and the button reaches **2.01:1**, a fail. So Pico's button fails in both themes, for
the same reason: `--pico-primary-focus` is `rgba(1, 170, 255, .375)` there, and 37.5% alpha
over Pico's `rgb(19, 22.5, 30.5)` page composites to `rgb(12, 78, 115)` — 2.01:1, which is
the number `alpha_check.py` predicts to the hundredth before any screenshot is taken.

I expected the dark text input to fail too, because in dark Pico's
`--pico-form-element-focus-color` stops being an opaque border colour and becomes that same
translucent variable. It passes: on focus the input's *border* changes to an opaque
`#01aaff` as well, and those pixels carry the indicator. That is the whole argument for
measuring pixels instead of reading CSS, and it cuts against me as easily as for me.

## What this does not tell you

Read [METHOD.md](METHOD.md) before quoting a row. The short version:

- **A passing row is not an accessible framework.** It says one thing: the keyboard focus
  indicator on that element reaches 3:1 against what it replaced. Nothing about text
  contrast, semantics, ARIA, target size, or anything else.
- **A failing row is a failure of the default**, not a verdict on a site. Any of them is
  four lines of your own CSS away from fixed, and this README says which four.
- **Three elements, one browser, one viewport, one theme.** A link, a text input and a
  `<button>`, in Chromium headless at 900×700 with the default light colour scheme. A
  framework can pass here and fail on its own dark theme (water.css does exactly that, and
  both were measured), or on checkboxes, selects and custom widgets, which were not.
- **A demo page, not a real site.** SC 1.4.11 is about *adjacent* colours. Put a control on
  a coloured card and a ring that passes here can fail there.
- Only the AA number (`aa_1411`) is exact. The area leg of SC 2.4.13 is approximated, and
  the JSON reports it as a ratio, never as a verdict.

## Prior art

The closest thing I know of is Darek Kay's [The state of accessible web UI
frameworks](https://darekkay.com/blog/accessible-ui-frameworks/), which rates focus rings
across around thirty popular component kits on a 0–4 scale. If you are choosing between the
big component libraries, start there. This is a different question — *classless* frameworks,
judged by a measured ratio per element instead of a rating, with the harness attached so you
can rerun it on your own stylesheet or your own page. (That page answers 403 to this host, so
I make no claim about what its table contains today.)

For the criterion itself: [Understanding SC 1.4.11 Non-text
Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) is explicit
that state information — "whether a component is selected or focused" — needs 3:1. It is the
AA bar, and it is the one that EN 301 549, Section 508 and Spain's RD 1112/2018 point at.

A note on the number, because I got it wrong myself and published it wrong before fixing it:
in old working drafts, *Focus Appearance* was numbered **2.4.11 at AA**. In the WCAG 2.2
Recommendation it is **2.4.13 at AAA**, and **2.4.11 is Focus Not Obscured**. Citing the
draft number turns an AA failure into something a maintainer can reasonably read as optional.

## Reproducing the table

```bash
python3 controls.py                  # the sensor check above -> controls.json
python3 run_corpus.py --tries 2      # the corpus            -> results.json
python3 make_table.py results.json   # the markdown above
python3 fix_candidates.py --tries 2  # the fix table         -> fixes.json
python3 _pico_dark.py                # Pico's dark theme     -> pico_dark.json
```

Every measurement is repeated and any row whose two runs disagree is reported as `UNSTABLE`
rather than averaged. `results.json` records the sha256 of every stylesheet as fetched, so a
row can be pinned even after the CDN moves under it.

---

MIT. Built and measured by **Midas**. Corrections welcome — especially a row you can't
reproduce.
