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


def _lighten(hex_color, factor=0.35):
    """Blend a hex color toward white by `factor` (0=same, 1=white)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def render_donut_svg(totals, path="stats.svg", top_n=8):
    total = sum(totals.values())
    items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:top_n]

    width, height = 480, 300
    cx, cy, r, stroke = 130, 168, 82, 22
    circumference = 2 * math.pi * r
    gap = 5  # px gap between segments
    offset = 0

    gradients = []
    segments = []
    for i, (lang, val) in enumerate(items):
        pct = val / total
        length = max(pct * circumference - gap, 1)
        color = COLORS.get(lang, DEFAULT_COLOR)
        gid = f"grad{i}"
        gradients.append(
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0%" stop-color="{_lighten(color, 0.15)}"/>'
            f'<stop offset="100%" stop-color="{color}"/>'
            f'</linearGradient>'
        )
        segments.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
            f'stroke="url(#{gid})" stroke-width="{stroke}" stroke-linecap="butt" '
            f'stroke-dasharray="{length} {circumference - length}" '
            f'stroke-dashoffset="{-offset}" transform="rotate(-90 {cx} {cy})"/>'
        )
        offset += pct * circumference

    top_lang, top_val = items[0]
    top_pct = round(top_val / total * 100, 1)

    # Legend rows: colored dot, language name, right-aligned percentage
    row_h = 27
    legend_start = (height - (len(items) - 1) * row_h) / 2 - 4
    legend = ""
    for i, (lang, val) in enumerate(items):
        pct = round(val / total * 100, 1)
        color = COLORS.get(lang, DEFAULT_COLOR)
        y = legend_start + i * row_h
        legend += (
            f'<circle cx="286" cy="{y - 4}" r="5.5" fill="{color}"/>'
            f'<text x="302" y="{y}" class="legend-lang">{lang}</text>'
            f'<text x="452" y="{y}" class="legend-pct" text-anchor="end">{pct}%</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    {''.join(gradients)}
    <linearGradient id="cardBg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#f6f8fa"/>
    </linearGradient>
    <linearGradient id="cardBgDark" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#161b22"/>
      <stop offset="100%" stop-color="#0d1117"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000000" flood-opacity="0.12"/>
    </filter>
  </defs>
  <style>
    text {{ font-family: 'Segoe UI', -apple-system, system-ui, sans-serif; }}
    .card {{ fill: url(#cardBg); stroke: #e1e4e8; }}
    .title {{ fill: #24292f; font-size: 16px; font-weight: 700; letter-spacing: 0.2px; }}
    .subtitle {{ fill: #6e7781; font-size: 11px; }}
    .center-num {{ fill: #24292f; font-size: 26px; font-weight: 800; }}
    .center-label {{ fill: #6e7781; font-size: 11px; letter-spacing: 0.3px; }}
    .legend-lang {{ fill: #24292f; font-size: 13px; font-weight: 500; }}
    .legend-pct {{ fill: #57606a; font-size: 13px; font-weight: 600; }}
    .divider {{ stroke: #e1e4e8; }}
    @media (prefers-color-scheme: dark) {{
      .card {{ fill: url(#cardBgDark); stroke: #30363d; }}
      .title {{ fill: #e6edf3; }}
      .subtitle {{ fill: #8b949e; }}
      .center-num {{ fill: #e6edf3; }}
      .center-label {{ fill: #8b949e; }}
      .legend-lang {{ fill: #e6edf3; }}
      .legend-pct {{ fill: #b1bac4; }}
      .divider {{ stroke: #30363d; }}
    }}
  </style>
  <rect class="card" x="2" y="2" width="{width - 4}" height="{height - 4}" rx="16" filter="url(#shadow)"/>
  <text x="24" y="34" class="title">Most Used Languages</text>
  <text x="24" y="52" class="subtitle">across all repositories</text>
  <line class="divider" x1="24" y1="66" x2="{width - 24}" y2="66"/>
  {''.join(segments)}
  <text x="{cx}" y="{cy - 2}" text-anchor="middle" class="center-num">{top_pct}%</text>
  <text x="{cx}" y="{cy + 16}" text-anchor="middle" class="center-label">{top_lang.upper()}</text>
  {legend}
</svg>'''

    with open(path, "w") as f:
        f.write(svg)


if __name__ == "__main__":
    repos = get_repos()
    totals = get_language_totals(repos)
    render_donut_svg(totals)
    print("Wrote stats.svg")
