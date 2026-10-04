#!/usr/bin/env python3
"""Set the porthole release shown next to the GitHub link in every page's top bar.

    /usr/bin/python3 scripts/set-version.py v0.2.0

porthole is released as Helm chart tags (chart-vX.Y.Z, appVersion X.Y.Z), so
the badge shows vX.Y.Z and links to the chart-vX.Y.Z tag.

Static on purpose: no GitHub API call from visitors' browsers (rate limits,
a third-party request on every page view, and a blank badge when it fails).
Idempotent — re-running with the same version changes nothing.
"""
import glob
import re
import sys

if len(sys.argv) != 2 or not re.fullmatch(r"v\d+\.\d+\.\d+", sys.argv[1]):
    sys.exit("usage: set-version.py vX.Y.Z")
version = sys.argv[1]
badge = (f'<a href="https://github.com/bcollard/porthole/releases/tag/chart-{version}" class="nav-version" '
         f'target="_blank" rel="noopener" title="Latest release">{version}</a>')

github = re.compile(r'(<a href="https://github\.com/bcollard/porthole" class="nav-github"[^>]*>.*?</a>)'
                    r'(\s*<a [^>]*class="nav-version"[^>]*>[^<]*</a>)?', re.S)
# Stamp the stylesheet with the release too: HTML and CSS are served with a
# 10-minute cache, so a deploy that changes both can otherwise pair new markup
# with the old stylesheet for a while.
css = re.compile(r'href="/styles\.css(\?v=[^"]*)?"')

changed = 0
for path in sorted(glob.glob("*.html")):
    src = open(path, encoding="utf-8").read()
    out, _ = github.subn(lambda m: m.group(1) + "\n    " + badge, src, count=1)
    out = css.sub(f'href="/styles.css?v={version}"', out)
    if out != src:
        open(path, "w", encoding="utf-8").write(out)
        changed += 1
print(f"{version}: updated {changed} page(s)")
