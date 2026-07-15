"""
Generates a donut-style SVG of language usage across all repos
(including private ones) using the GitHub API, then saves it as stats.svg.

Requires env var GH_TOKEN with a PAT that has 'repo' scope.
"""

import os
import math
import requests

USERNAME = os.environ["GH_USERNAME"]
TOKEN = os.environ["GH_TOKEN"]
HEADERS = {"Authorization": f"token {TOKEN}"}

COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "C++": "#f34b7d", "R": "#198CE7", "HTML": "#e34c26", "CSS": "#563d7c",
    "Jupyter Notebook": "#DA5B0B", "Shell": "#89e051",
}
DEFAULT_COLOR = "#858585"


def get_repos():
    repos, page = [], 1
    while True:
        r = requests.get(
            "https://api.github.com/user/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "affiliation": "owner"},
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def get_language_totals(repos):
    totals = {}
    for repo in repos:
        r = requests.get(repo["languages_url"], headers=HEADERS)
        r.raise_for_status()
        for lang, bytes_ in r.json().items():
            totals[lang] = totals.get(lang, 0) + bytes_
    return totals


def render_donut_svg(totals, path="stats.svg", top_n=8):
    total = sum(totals.values())
    items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:top_n]

    width, height = 440, 220
    cx, cy, r, stroke = 110, 110, 78, 20
    circumference = 2 * math.pi * r
    gap = 6  # px gap between segments
    offset = 0
    segments = []
    for i, (lang, val) in enumerate(items):
        pct = val / total
        length = max(pct * circumference - gap, 1)
        color = COLORS.get(lang, DEFAULT_COLOR)
        segments.append(
            f'<circle class="seg" cx="{cx}" cy="{cy}" r="{r}" fill="none" '
            f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
            f'stroke-dasharray="{length} {circumference - length}" '
            f'stroke-dashoffset="{-offset}" transform="rotate(-90 {cx} {cy})" '
            f'style="animation-delay:{i * 120}ms"/>'
        )
        offset += pct * circumference

    top_lang, top_val = items[0]
    top_pct = round(top_val / total * 100, 1)

    legend = ""
    for i, (lang, val) in enumerate(items):
        pct = round(val / total * 100, 1)
        color = COLORS.get(lang, DEFAULT_COLOR)
        y = 46 + i * 22
        legend += (
            f'<circle cx="248" cy="{y - 4}" r="6" fill="{color}"/>'
            f'<text x="262" y="{y}" class="legend-lang">{lang}</text>'
            f'<text x="420" y="{y}" class="legend-pct" text-anchor="end">{pct}%</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    text {{ font-family: 'Segoe UI', -apple-system, system-ui, sans-serif; }}
    .card {{ fill: #ffffff; stroke: #e1e4e8; }}
    .title {{ fill: #24292f; font-size: 15px; font-weight: 600; }}
    .center-num {{ fill: #24292f; font-size: 22px; font-weight: 700; }}
    .center-label {{ fill: #6e7781; font-size: 11px; }}
    .legend-lang {{ fill: #24292f; font-size: 13px; }}
    .legend-pct {{ fill: #6e7781; font-size: 13px; }}
    .seg {{
      filter: drop-shadow(0 1px 2px rgba(0,0,0,0.15));
      opacity: 0;
      animation: fade-in 0.5s ease-out forwards;
    }}
    @keyframes fade-in {{ to {{ opacity: 1; }} }}
    @media (prefers-color-scheme: dark) {{
      .card {{ fill: #0d1117; stroke: #30363d; }}
      .title {{ fill: #e6edf3; }}
      .center-num {{ fill: #e6edf3; }}
      .center-label {{ fill: #8b949e; }}
      .legend-lang {{ fill: #e6edf3; }}
      .legend-pct {{ fill: #8b949e; }}
    }}
  </style>
  <rect class="card" x="1" y="1" width="{width - 2}" height="{height - 2}" rx="14"/>
  <text x="20" y="28" class="title">Most Used Languages</text>
  {''.join(segments)}
  <text x="{cx}" y="{cy - 4}" text-anchor="middle" class="center-num">{top_pct}%</text>
  <text x="{cx}" y="{cy + 14}" text-anchor="middle" class="center-label">{top_lang}</text>
  {legend}
</svg>'''

    with open(path, "w") as f:
        f.write(svg)


if __name__ == "__main__":
    repos = get_repos()
    totals = get_language_totals(repos)
    render_donut_svg(totals)
    print("Wrote stats.svg")
