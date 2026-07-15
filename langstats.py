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

    cx, cy, r, stroke = 110, 110, 80, 24
    circumference = 2 * math.pi * r
    offset = 0
    segments = []
    for lang, val in items:
        pct = val / total
        length = pct * circumference
        color = COLORS.get(lang, DEFAULT_COLOR)
        segments.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
            f'stroke="{color}" stroke-width="{stroke}" '
            f'stroke-dasharray="{length} {circumference - length}" '
            f'stroke-dashoffset="{-offset}" transform="rotate(-90 {cx} {cy})"/>'
        )
        offset += length

    legend = ""
    for i, (lang, val) in enumerate(items):
        pct = round(val / total * 100, 1)
        color = COLORS.get(lang, DEFAULT_COLOR)
        y = 30 + i * 22
        legend += (
            f'<rect x="240" y="{y}" width="12" height="12" fill="{color}"/>'
            f'<text x="258" y="{y + 11}" font-size="13" font-family="sans-serif">'
            f'{lang} {pct}%</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="420" height="220">
{''.join(segments)}
{legend}
</svg>'''

    with open(path, "w") as f:
        f.write(svg)


if __name__ == "__main__":
    repos = get_repos()
    totals = get_language_totals(repos)
    render_donut_svg(totals)
    print("Wrote stats.svg")
