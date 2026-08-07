"""README.md assembly.

The generated profile README is built from *live* services where they are
reliable, and from locally generated assets where the public services
keep failing (stats + top languages). The daily GitHub Actions workflow
regenerates the local assets so they stay current while always loading:

- hero banner .... local SVG (regenerated daily by the workflow)
- stats .......... local SVG, baked from live API data every day
- languages ...... local SVG, baked from live API data every day
- typing effect .. readme-typing-svg.demolab.com
- badges ......... komarev.com + img.shields.io
- tech stack ..... skillicons.dev (real language / tool logos)
- streak ......... streak-stats.demolab.com
- activity ....... github-readme-activity-graph.vercel.app
- connect ........ img.shields.io buttons
"""

from __future__ import annotations

import os
from typing import List

from .config import ProfileConfig
from .models import LiveData
from .svg_assets import xml_escape

# ---------------------------------------------------------------------------
# Live service URL builders.
# ---------------------------------------------------------------------------
def typing_svg_url(cfg: ProfileConfig) -> str:
    """Animated typing effect (live)."""
    lines = cfg.typing_query()
    return (
        "https://readme-typing-svg.demolab.com/?font=Fira+Code&weight=600&pause=1200"
        f"&color=58A6FF&center=true&vCenter=true&width=660&lines={lines}"
    )


def views_badge(cfg: ProfileConfig) -> str:
    return (
        "https://komarev.com/ghpvc/?username="
        f"{cfg.username}&style=flat-square&label=PROFILE+VIEWS&color=58a6ff"
    )


def followers_badge(cfg: ProfileConfig) -> str:
    return (
        "https://img.shields.io/github/followers/"
        f"{cfg.username}?style=flat-square&label=FOLLOWERS&color=58a6ff"
    )


def stars_badge(cfg: ProfileConfig) -> str:
    return (
        "https://img.shields.io/github/stars/"
        f"{cfg.username}?style=flat-square&label=STARS&color=3fb950"
    )


def tech_stack_url(cfg: ProfileConfig) -> str:
    """skillicons.dev strip - the actual language logos."""
    return "https://skillicons.dev/icons?i=" + ",".join(cfg.tech_icons) + "&perline=10"


def streak_url(cfg: ProfileConfig) -> str:
    return (
        "https://streak-stats.demolab.com/?user="
        f"{cfg.username}&theme={cfg.streak_theme}&hide_border=true"
        "&background=0D1117&ring=58A6FF&fire=3FB950"
        "&currStreakLabel=E6EDF3&sideLabels=8B949E&dates=8B949E"
        "&currStreakNum=E6EDF3&sideNums=E6EDF3"
    )


def activity_graph_url(cfg: ProfileConfig) -> str:
    return (
        "https://github-readme-activity-graph.vercel.app/graph?username="
        f"{cfg.username}&theme={cfg.graph_theme}&bg_color=0d1117"
        "&hide_border=true&area=true&custom_title=Activity"
    )


def _shields_button(label: str, bg: str, logo: str) -> str:
    return (
        "https://img.shields.io/badge/"
        f"{label}-{bg}?style=for-the-badge&logo={logo}&logoColor=white"
    )


# ---------------------------------------------------------------------------
# Section builders.
# ---------------------------------------------------------------------------
def _header(cfg: ProfileConfig) -> List[str]:
    return [
        '<div align="center">',
        "",
        '  <img src="assets/banner.svg" width="100%" alt="Nytheon banner"/>',
        "",
        "  <br/><br/>",
        "",
        f"  <img src=\"{typing_svg_url(cfg)}\" alt=\"Typing effect\"/>",
        "",
        "  <br/>",
        "",
        "  <p>",
        f'    <img src="{views_badge(cfg)}" alt="Profile views"/>',
        f'    <img src="{followers_badge(cfg)}" alt="Followers"/>',
        f'    <img src="{stars_badge(cfg)}" alt="Stars"/>',
        "  </p>",
        "",
        "</div>",
        "",
    ]


def _about(cfg: ProfileConfig) -> List[str]:
    lines = ["---", "", "### About Me", "", ""]
    for paragraph in cfg.about_paragraphs:
        lines += [xml_escape(paragraph), ""]
    lines += ["**What I focus on**", ""]
    for title, detail in cfg.focus_areas:
        lines += [f"- **{xml_escape(title)}** - {xml_escape(detail)}"]
    lines.append("")
    return lines


def _tech(cfg: ProfileConfig) -> List[str]:
    return [
        "---",
        "",
        "### Tech Stack",
        "",
        '<div align="center">',
        "",
        f'  <img src="{tech_stack_url(cfg)}" alt="Tech stack logos"/>',
        "",
        "</div>",
        "",
    ]


def _stats(cfg: ProfileConfig) -> List[str]:
    return [
        "---",
        "",
        "### GitHub Stats",
        "",
        '<div align="center">',
        "",
        '  <img src="assets/stats.svg" width="100%" alt="GitHub stats"/>',
        "",
        "</div>",
        "",
        '<div align="center">',
        "",
        '  <img src="assets/langs.svg" width="100%" alt="Top languages"/>',
        "",
        "</div>",
        "",
        '<div align="center">',
        "",
        f'  <img src="{streak_url(cfg)}" alt="GitHub streak"/>',
        "",
        "</div>",
        "",
        '<div align="center">',
        "",
        f'  <img src="{activity_graph_url(cfg)}" alt="Activity graph"/>',
        "",
        "</div>",
        "",
    ]


def _connect(cfg: ProfileConfig) -> List[str]:
    items = cfg.contact_items()
    buttons: List[str] = ["---", "", "### Connect with Me", "", '<div align="center">', ""]
    for label, subtitle, url, _color in items:
        logo = label.lower()
        bg = {"GMAIL": "D14836", "TELEGRAM": "26A5E4", "GITHUB": "181717"}.get(label, "58a6ff")
        buttons.append(
            f'  <a href="{xml_escape(url)}">'
            f'<img src="{_shields_button(label, bg, logo)}" alt="{label}"/></a>'
        )
    buttons += ["", "</div>", ""]
    return buttons


def _footer(cfg: ProfileConfig) -> List[str]:
    return [
        '<div align="center">',
        "",
        f"  <sub>&copy; {cfg.founding_year} {cfg.display_name} - profile auto-refreshes daily via GitHub Actions</sub>",
        "",
        "</div>",
        "",
    ]


# ---------------------------------------------------------------------------
# Public entry points.
# ---------------------------------------------------------------------------
def build_readme(cfg: ProfileConfig, live: LiveData) -> str:
    """Assemble the full README markdown as a string."""
    sections: List[str] = []
    sections += _header(cfg)
    sections += _about(cfg)
    sections += _tech(cfg)
    sections += _stats(cfg)
    sections += _connect(cfg)
    sections += _footer(cfg)
    return "\n".join(sections).rstrip() + "\n"


def write_assets(cfg: ProfileConfig, live: LiveData, root: str) -> List[str]:
    """Write all generated asset files, returning the list of written paths.

    Local assets are regenerated by the daily workflow so the README always
    loads: banner (branding), stats + top languages (baked from live data
    because github-readme-stats.vercel.app keeps getting suspended).
    Everything else in the README is live and needs no files on disk.
    """
    from .svg_assets import build_divider, build_hero_banner, build_language_bars, build_stat_cards

    assets_dir = os.path.join(root, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    written = []
    banner_path = os.path.join(assets_dir, "banner.svg")
    with open(banner_path, "w", encoding="utf-8") as fh:
        fh.write(build_hero_banner(cfg, live))
    written.append(banner_path)

    divider_path = os.path.join(assets_dir, "divider.svg")
    with open(divider_path, "w", encoding="utf-8") as fh:
        fh.write(build_divider())
    written.append(divider_path)

    stats_path = os.path.join(assets_dir, "stats.svg")
    with open(stats_path, "w", encoding="utf-8") as fh:
        fh.write(build_stat_cards(cfg, live))
    written.append(stats_path)

    langs_path = os.path.join(assets_dir, "langs.svg")
    with open(langs_path, "w", encoding="utf-8") as fh:
        fh.write(build_language_bars(live.languages))
    written.append(langs_path)

    return written


def write_readme(cfg: ProfileConfig, live: LiveData, root: str) -> str:
    """Write README.md at the repo root, returning the generated content."""
    content = build_readme(cfg, live)
    readme_path = os.path.join(root, "README.md")
    with open(readme_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return content


def run(cfg: ProfileConfig, live: LiveData, root: str) -> None:
    """Generate every file that depends on live data."""
    write_assets(cfg, live, root)
    write_readme(cfg, live, root)
