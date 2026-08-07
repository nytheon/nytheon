"""SVG asset generators.

Only the *branding* graphics are rendered as local SVG files - the hero
banner and small decorative dividers. All live data (stat cards, language
chart, streak, activity) is served by external real-time services and is
assembled by :mod:`readme_builder`.

The banner generator receives the fetched :class:`models.LiveData` so the
numbers shown inside it (followers, contributions, repo count) stay in
sync every time the daily GitHub Actions job regenerates the profile.
"""

from __future__ import annotations

import random
import textwrap
from typing import List, Sequence, Tuple

from .config import (
    ACCENT_BLUE,
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_GRADIENT,
    ACCENT_PURPLE,
    ACCENT_RED,
    BG_COLOR,
    BORDER_COLOR,
    FONT_MONO,
    GRID_COLOR,
    MUTED_COLOR,
    PANEL_COLOR,
    TEXT_COLOR,
    language_color,
)
from .models import LanguageStat, LiveData

BANNER_WIDTH = 1400
BANNER_HEIGHT = 340


# ---------------------------------------------------------------------------
# Low-level helpers.
# ---------------------------------------------------------------------------
def xml_escape(value: str) -> str:
    """Escape a string for safe embedding inside an XML/SVG document."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def thousands(value: int) -> str:
    """Format an integer with thousands separators, e.g. 4029 -> '4,029'."""
    return f"{value:,}"


def _linear_gradient(gid: str, stops: Sequence[Tuple[float, str]]) -> str:
    """Build a horizontal linear-gradient <linearGradient> definition."""
    parts = []
    for offset, color in stops:
        parts.append(f'<stop offset="{offset}" stop-color="{color}"/>')
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">'
        f'{"".join(parts)}</linearGradient>'
    )


def _radial_gradient(gid: str, color: str, opacity: float) -> str:
    return (
        f'<radialGradient id="{gid}" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/>'
        f"</radialGradient>"
    )


def _grid_pattern(gid: str, size: int = 44) -> str:
    return (
        f'<pattern id="{gid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
        f'<path d="M {size} 0 L 0 0 0 {size}" fill="none" stroke="{GRID_COLOR}" stroke-width="1"/>'
        f"</pattern>"
    )


# ---------------------------------------------------------------------------
# Hero banner.
# ---------------------------------------------------------------------------
def _banner_particles(count: int = 16, seed: int = 7) -> List[str]:
    """Generate animated floating particles for the hero banner background."""
    rng = random.Random(seed)
    pieces = []
    for index in range(count):
        x = rng.randint(60, BANNER_WIDTH - 60)
        y = rng.randint(40, BANNER_HEIGHT - 50)
        radius = rng.randint(2, 5)
        duration = round(rng.uniform(6.0, 13.0), 1)
        drift = rng.randint(40, 120)
        grad = f"p{index % 2}"
        pieces.append(
            f'<circle cx="{x}" cy="{y}" r="{radius}" fill="url(#{grad})">'
            f'<animate attributeName="cy" values="{y};{y - drift};{y}" '
            f'dur="{duration}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.12;0.7;0.12" '
            f'dur="{duration}s" repeatCount="indefinite"/>'
            f"</circle>"
        )
    return pieces


def _banner_chip(x: int, y: int, label: str, value: str, color: str) -> str:
    """A small stat chip rendered inside the hero banner."""
    width = 60 + len(label) * 8 + len(value) * 9
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="30" rx="15" fill="{PANEL_COLOR}" '
        f'stroke="{color}" stroke-opacity="0.5"/>'
        f'<circle cx="{x + 18}" cy="{y + 15}" r="4" fill="{color}"/>'
        f'<text x="{x + 30}" y="{y + 20}" font-family="{FONT_MONO}" font-size="13" '
        f'fill="{TEXT_COLOR}">{xml_escape(value)} {xml_escape(label)}</text>'
    )


def build_hero_banner(cfg, live: LiveData, width: int = BANNER_WIDTH,
                      height: int = BANNER_HEIGHT) -> str:
    """Render the animated hero banner with live stat chips baked in."""
    from .config import ProfileConfig  # type-check only

    assert isinstance(cfg, ProfileConfig)

    particles = "\n".join(_banner_particles())
    chip_followers = _banner_chip(
        0, 0, "FOLLOWERS", thousands(live.stats.followers), ACCENT_BLUE,
    )
    chip_repos = _banner_chip(
        0, 0, "REPOS", thousands(live.stats.public_repos), ACCENT_PURPLE,
    )
    chip_contrib = _banner_chip(
        0, 0, "CONTRIBUTIONS", thousands(live.contributions), ACCENT_GREEN,
    )

    # Position chips in the lower band of the banner, right aligned.
    chips_x = width - 430
    chips_y = height - 60
    chips = "\n".join(
        s.replace('x="0" y="0"', f'x="{chips_x + offset}" y="{chips_y}"')
        for offset, s in enumerate([chip_followers, chip_repos, chip_contrib])
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    {_linear_gradient("bg", [(0.0, BG_COLOR), (1.0, "#10161f")])}
    {_linear_gradient("accent", [(0.0, ACCENT_BLUE), (0.5, ACCENT_PURPLE), (1.0, ACCENT_GREEN)])}
    {_linear_gradient("titlefill", [(0.0, TEXT_COLOR), (0.55, "#ffffff"), (1.0, MUTED_COLOR)])}
    {_radial_gradient("p0", ACCENT_BLUE, 0.9)}
    {_radial_gradient("p1", ACCENT_PURPLE, 0.9)}
    {_radial_gradient("glow1", ACCENT_BLUE, 0.28)}
    {_radial_gradient("glow2", ACCENT_PURPLE, 0.22)}
    {_grid_pattern("grid")}
  </defs>
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <rect width="{width}" height="{height}" fill="url(#grid)"/>
  <circle cx="{width - 120}" cy="30" r="260" fill="url(#glow1)"/>
  <circle cx="120" cy="{height}" r="240" fill="url(#glow2)"/>
  {particles}
  <rect x="70" y="52" width="96" height="96" rx="20" fill="{PANEL_COLOR}" stroke="url(#accent)" stroke-width="2">
    <animate attributeName="stroke-opacity" values="1;0.4;1" dur="4s" repeatCount="indefinite"/>
  </rect>
  <text x="118" y="122" text-anchor="middle" font-family="{FONT_MONO}" font-size="48" font-weight="700" fill="url(#accent)">{xml_escape(cfg.display_name[0])}</text>
  <text x="196" y="128" font-family="{FONT_MONO}" font-size="46" font-weight="700" fill="url(#titlefill)" letter-spacing="6">{xml_escape(cfg.display_name.upper())}</text>
  <text x="198" y="176" font-family="{FONT_MONO}" font-size="20" fill="{MUTED_COLOR}" letter-spacing="5">{xml_escape(cfg.tagline.upper())}</text>
  <rect x="198" y="200" width="320" height="3" rx="1.5" fill="url(#accent)">
    <animate attributeName="width" values="120;320;120" dur="5s" repeatCount="indefinite"/>
  </rect>
  <text x="198" y="270" font-family="{FONT_MONO}" font-size="17" fill="{ACCENT_BLUE}" opacity="0.85" letter-spacing="2">{xml_escape(cfg.github_url)}</text>
  <text x="198" y="300" font-family="{FONT_MONO}" font-size="14" fill="{ACCENT_GREEN}" opacity="0.9" letter-spacing="1">BUILDING INTELLIGENT SYSTEMS</text>
  {chips}
  <text x="{width - 40}" y="{height - 16}" text-anchor="end" font-family="{FONT_MONO}" font-size="12" fill="{BORDER_COLOR}" letter-spacing="2">LAST UPDATED {xml_escape(live.fetched_at[:10])}</text>
</svg>
"""


# ---------------------------------------------------------------------------
# Divider.
# ---------------------------------------------------------------------------
def build_divider(width: int = 1400, seed: int = 3) -> str:
    """A thin decorative divider used to separate README sections."""
    rng = random.Random(seed)
    dots = []
    for index in range(9):
        x = 560 + index * 35
        color = ACCENT_GRADIENT[index % len(ACCENT_GRADIENT)]
        dots.append(
            f'<circle cx="{x}" cy="30" r="3" fill="{color}">'
            f'<animate attributeName="r" values="2;4;2" dur="2.6s" '
            f'begin="{index * 0.25}s" repeatCount="indefinite"/>'
            f"</circle>"
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="60" viewBox="0 0 {width} 60">
  <rect width="{width}" height="60" fill="{BG_COLOR}"/>
  <rect x="430" y="29" width="520" height="1" fill="{BORDER_COLOR}"/>
  {chr(10).join(dots)}
</svg>
"""


# ---------------------------------------------------------------------------
# Stat cards (offline fallback).
# ---------------------------------------------------------------------------
def build_stat_cards(cfg, live: LiveData) -> str:
    """Render a four-card stats strip (used when offline generation is wanted)."""
    cards: List[Tuple[str, str, str]] = [
        ("REPOSITORIES", thousands(live.stats.public_repos), ACCENT_BLUE),
        ("FOLLOWERS", thousands(live.stats.followers), ACCENT_PURPLE),
        ("STARS EARNED", thousands(live.stats.total_stars), ACCENT_GREEN),
        ("CONTRIBUTIONS", thousands(live.contributions), ACCENT_RED),
    ]
    card_w, card_h, gap = 320, 140, 24
    total_width = len(cards) * card_w + (len(cards) - 1) * gap
    x0 = (1400 - total_width) // 2
    pieces = []
    for index, (label, value, color) in enumerate(cards):
        x = x0 + index * (card_w + gap)
        pieces.append(
            f'<g>'
            f'<rect x="{x}" y="40" width="{card_w}" height="{card_h}" rx="16" '
            f'fill="{PANEL_COLOR}" stroke="{BORDER_COLOR}"/>'
            f'<rect x="{x}" y="40" width="5" height="{card_h}" rx="2.5" fill="{color}"/>'
            f'<text x="{x + card_w / 2}" y="105" text-anchor="middle" '
            f'font-family="{FONT_MONO}" font-size="34" font-weight="700" fill="{TEXT_COLOR}">{value}</text>'
            f'<text x="{x + card_w / 2}" y="145" text-anchor="middle" '
            f'font-family="{FONT_MONO}" font-size="13" letter-spacing="3" fill="{MUTED_COLOR}">{label}</text>'
            f"</g>"
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="220" viewBox="0 0 1400 220">
  <rect width="1400" height="220" fill="{BG_COLOR}"/>
  {chr(10).join(pieces)}
</svg>
"""


# ---------------------------------------------------------------------------
# Language bars (offline fallback).
# ---------------------------------------------------------------------------
def build_language_bars(languages: Sequence[LanguageStat], limit: int = 6) -> str:
    """Render horizontal language bars with real GitHub language colours."""
    total = sum(l.bytes_count for l in languages) or 1
    top = sorted(languages, key=lambda l: l.bytes_count, reverse=True)[:limit]
    bar_w = 760
    x0 = (1400 - bar_w) // 2
    y = 70
    parts = [
        f'<text x="700" y="44" text-anchor="middle" font-family="{FONT_MONO}" '
        f'font-size="20" font-weight="700" letter-spacing="4" fill="{TEXT_COLOR}">MOST USED LANGUAGES</text>'
    ]
    for lang in top:
        pct = round(lang.bytes_count / total * 100.0, 1)
        color = language_color(lang.name)
        bar_width = max(4.0, (bar_w - 170) * pct / 100.0)
        parts.append(
            f'<text x="{x0}" y="{y}" font-family="{FONT_MONO}" font-size="14" '
            f'fill="{MUTED_COLOR}">{xml_escape(lang.name)}</text>'
            f'<rect x="{x0 + 170}" y="{y - 11}" width="{bar_w - 170}" height="10" rx="5" fill="{PANEL_COLOR}"/>'
            f'<rect x="{x0 + 170}" y="{y - 11}" width="{bar_width}" height="10" rx="5" fill="{color}">'
            f'<animate attributeName="width" values="4;{bar_width}" dur="1.1s" repeatCount="1" fill="freeze"/>'
            f"</rect>"
            f'<text x="{x0 + bar_w + 16}" y="{y}" text-anchor="end" '
            f'font-family="{FONT_MONO}" font-size="14" fill="{TEXT_COLOR}">{pct:.0f}%</text>'
        )
        y += 42
    height = max(240, y + 60)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="{height}" viewBox="0 0 1400 {height}">
  <rect width="1400" height="{height}" fill="{BG_COLOR}"/>
  {chr(10).join(parts)}
</svg>
"""


# ---------------------------------------------------------------------------
# Text helpers (used by readme builder).
# ---------------------------------------------------------------------------
def wrap_text(text: str, width: int = 78) -> List[str]:
    """Wrap a paragraph to a fixed column width."""
    return textwrap.wrap(text, width=width, break_long_words=True)
