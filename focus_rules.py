#!/usr/bin/env python3
"""Print the declarations a stylesheet applies on :focus / :focus-visible.

The measurement says a focus indicator fails. This says which lines wrote it, so the
report can name the fix instead of waving at the file.
"""
import re
import sys
import urllib.request

UA = "Mozilla/5.0 (compatible; focus-appearance-audit)"


def rules(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        sel, body = m.group(1).strip(), m.group(2).strip()
        if "focus" in sel:
            out.append((" ".join(sel.split()), " ".join(body.split())))
    return out


def var_defs(css, names):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    hits = {}
    for n in names:
        for m in re.finditer(re.escape(n) + r"\s*:\s*([^;}]+)", css):
            hits.setdefault(n, []).append(m.group(1).strip())
    return hits


def main():
    url = sys.argv[1]
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        css = r.read().decode("utf-8", "replace")
    rs = rules(css)
    names = set()
    for sel, body in rs:
        print("%s {\n    %s\n}" % (sel, body.replace("; ", ";\n    ")))
        names.update(re.findall(r"var\(\s*(--[\w-]+)", body))
    if names:
        print("\n-- variables used above --")
        for n, vals in var_defs(css, sorted(names)).items():
            print("%-28s %s" % (n, "  |  ".join(dict.fromkeys(vals))[:220]))


if __name__ == "__main__":
    main()
