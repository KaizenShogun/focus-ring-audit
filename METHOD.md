# Method, and everything that could be wrong with it

## What is measured

Render the page twice with the same stylesheet: once with nothing focused, once with the
target element focused. Subtract the two screenshots pixel by pixel. **Whatever changed is
the focus indicator**, as a sighted keyboard user sees it.

That is the whole trick, and it is why the result does not depend on reading CSS. It does
not matter whether the indicator came from `outline`, `box-shadow`, `border`, a background
swap, a `::after`, or three of those at once. It does not matter whether the declared
colour is `#0096bf` if it was written `#0096bfab` and the browser composited away two
thirds of it before anyone saw it. The browser has already done all the compositing by the
time we look at the pixels.

For each changed pixel we compute the WCAG contrast ratio between its **before** and
**after** colour, and report how many pixels reach 3:1.

## The two criteria, and which number answers which

**SC 1.4.11 Non-text Contrast — AA, WCAG 2.1 and 2.2.** Its Understanding document says
state information, explicitly including "whether a component is … focused", needs 3:1
against adjacent colours. This is the AA bar. It is the one that appears in procurement
and in law (EN 301 549, Section 508, and in Spain RD 1112/2018, all of which point at
WCAG AA). **This is the verdict column.**

**SC 2.4.13 Focus Appearance — AAA, WCAG 2.2.** Asks for an indicator that is (a) at least
as large as a 2 CSS px perimeter of the component and (b) reaches 3:1 between the focused
and unfocused states of the same pixels.

Leg (b) and 1.4.11 compare the same pair of colours when the indicator's pixels were page
background before focus, so one measurement answers both. Leg (a) is reported as a ratio,
never as a verdict — see caveats.

A note on the number, because I got it wrong myself and published it wrong: in old working
drafts Focus Appearance was numbered **2.4.11 at AA**. In the Recommendation it is
**2.4.13 at AAA**, and **2.4.11 is Focus Not Obscured**. Citing the draft number turns an
AA failure into something a maintainer can reasonably read as optional.

## Controls (`controls.py`)

A sensor that cannot fail loudly is not a sensor. Four stylesheets whose answer is known
before the run:

| control | stylesheet | expected |
|---|---|---|
| C0 | none | the browser's own ring, high contrast |
| C1 | `:focus{outline:6px solid #f00}` | visible, ~4:1 on white |
| C2 | `:focus-visible{outline:6px solid #f00}` | identical to C1 |
| C3 | `:focus{outline:0}` with borders removed | nothing changes at all |

C2 is the one the whole corpus rests on. The harness focuses elements with a programmatic
`.focus()`, and **most modern frameworks style `:focus-visible`, not `:focus`**. If this
browser did not match `:focus-visible` on programmatic focus, every one of them would come
out as "no visible change" and the table would be a fabrication. C1 and C2 come out
byte-identical, so it does.

C3 is the floor: a stylesheet that truly draws nothing must read as zero changed pixels.

## Three things the harness imposes on the page

1. `padding` around the controls, so a ring drawn outside the border box is never clipped
   by the viewport edge.
2. `caret-color: transparent` on the text input. The blinking text cursor is not the
   input's focus indicator, and it changes ~15 px at 21:1 — enough, on its own, to rescue
   a stylesheet that draws nothing. Without this, C3's input scores 15 px above 3:1.
3. `transition: none; animation: none` on everything. **This is not cosmetic.** Pico CSS
   fades its focus styles in over 0.2s; without this the screenshot lands at an arbitrary
   point on that curve. The first run of this corpus reported Pico's text input as
   "max 1.00:1, no pixel reaches 3:1" and an immediately following run of the same command
   on the same stylesheet reported 5.23:1. Both numbers were real; one was caught mid-fade.
   WCAG is about the settled state.

Nothing else is imposed. In particular **no background colour is forced**, so a framework
that ships a dark page is measured on its own dark page.

Every measurement is then repeated (`--tries`, default 2) and any row whose two runs
disagree is reported as `UNSTABLE` rather than averaged into a number.

## Caveats — read these before quoting a row

- **Leg (a) of 2.4.13 is approximated.** The required area is computed as
  `(w+4)(h+4) - wh`, i.e. a full 2 px perimeter of the border box. A real ring drawn at an
  offset covers a slightly different area, so `area_ratio` between about 0.9 and 1.1 means
  "indistinguishable from the requirement by this method", not "borderline in the
  standard". Only `aa_1411` is exact.
- **One rendering, one browser, one viewport.** Chromium headless, 900×700, device pixel
  ratio 1, default (light) `prefers-color-scheme`. A framework can pass here and fail on
  its own dark theme — water.css does exactly that, and both were measured by hand.
- **Three elements.** A link, a text input and a `<button>`. A framework can be fine on
  these and broken on checkboxes, selects or custom widgets.
- **The demo page, not a real site.** A real page puts controls on coloured backgrounds,
  next to each other, inside cards. 1.4.11 is about adjacent colours, so a real site can
  fail where this passes.
- **A passing row is not an accessible framework.** It says one thing: the keyboard focus
  indicator on that element reaches 3:1 against what it replaced. Nothing about contrast
  of text, semantics, ARIA, target size or anything else.
- **A failing row is a failure of the default.** Any of these can be fixed in four lines of
  your own CSS, and the report for each failure says which four.

## Prior art

The closest thing I know of is Darek Kay's
[The state of accessible web UI frameworks](https://darekkay.com/blog/accessible-ui-frameworks/),
which rates focus rings across around thirty popular CSS UI frameworks on a 0–4 scale. It
is the better starting point if you are choosing between the big component kits. I could
not fetch the page from this host (it answers 403), so I make no claim about what its
table contains; this corpus is a different question — *classless* frameworks, judged by a
measured ratio per element rather than a rating, with the script attached so you can rerun
it on your own stylesheet or your own site.

Automated scanners are not prior art for this: axe-core and friends cannot see `:focus`
styles at all, because the state only exists during interaction. That gap is the reason
this is worth measuring.
