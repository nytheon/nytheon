"""Central configuration for the profile builder.

Holds every account detail, brand color, tech-stack icon and rendering
option used across the SVG generators, the README builder and the CLI.

All values are plain data so the module stays dependency-free and can be
imported by every part of the tool (including tests) without side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Brand palette (matches GitHub's dark theme so the profile blends in).
# ---------------------------------------------------------------------------
BG_COLOR: str = "#0d1117"
PANEL_COLOR: str = "#161b22"
BORDER_COLOR: str = "#30363d"
TEXT_COLOR: str = "#e6edf3"
MUTED_COLOR: str = "#8b949e"
GRID_COLOR: str = "#1c2128"
ACCENT_BLUE: str = "#58a6ff"
ACCENT_PURPLE: str = "#bc8cff"
ACCENT_GREEN: str = "#3fb950"
ACCENT_RED: str = "#d14836"
ACCENT_CYAN: str = "#26a5e4"

ACCENT_GRADIENT: Tuple[str, str, str] = (
    ACCENT_BLUE,
    ACCENT_PURPLE,
    ACCENT_GREEN,
)

# GitHub contribution level colors, darkest (none) to lightest (max).
LEVEL_COLORS: Tuple[str, ...] = (
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
)

FONT_MONO: str = "Consolas, Menlo, monospace"
FONT_SANS: str = "Segoe UI, -apple-system, sans-serif"


# ---------------------------------------------------------------------------
# Known GitHub language colours (used by the language bar renderer).
# Fall back to an accent colour for anything not listed here.
# ---------------------------------------------------------------------------
LANGUAGE_COLORS: Dict[str, str] = {
    "Python": "#3572A5",
    "C++": "#f34b7d",
    "C#": "#178600",
    "C": "#555555",
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "PHP": "#4F5D95",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Shell": "#89e051",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Dockerfile": "#384d54",
    "Jupyter Notebook": "#DA5B0B",
    "TeX": "#3D6117",
    "Markdown": "#083fa1",
    "JSON": "#292929",
    "YAML": "#cb171e",
    "Solidity": "#AA6746",
    "Batchfile": "#C1F12E",
    "Assembly": "#6E4C13",
}


def language_color(name: str) -> str:
    """Return a stable colour for a language name, falling back to an accent."""
    if name in LANGUAGE_COLORS:
        return LANGUAGE_COLORS[name]
    return ACCENT_GRADIENT[hash(name) % len(ACCENT_GRADIENT)]


# ---------------------------------------------------------------------------
# Profile configuration.
# ---------------------------------------------------------------------------
@dataclass
class ProfileConfig:
    """All user-specific values used when generating the profile."""

    username: str = "nytheon"
    display_name: str = "Nytheon"
    tagline: str = "AI Developer · NLP Engineer · Full-Stack Technologist"
    email: str = "henrik.weber63@gmail.com"
    telegram: str = "nytheon"
    location: str = ""
    github_url: str = "github.com/nytheon"
    founding_year: int = 2026

    # Lines shown by the animated typing effect (live readme-typing-svg).
    typing_lines: Tuple[str, ...] = (
        "Building intelligent systems",
        "Conversational AI & Agents",
        "NLP & Machine Learning",
        "Full-Stack Engineering",
    )

    # Free-form "about" paragraphs.
    about_paragraphs: Tuple[str, ...] = (
        "I am a passionate AI developer crafting intelligent systems that "
        "solve real-world problems - from natural language processing and "
        "conversational AI to full-stack products shipped end to end.",
        "I enjoy building from scratch, optimising existing systems and "
        "constantly learning what comes next.",
    )

    # Bullet points under "What I focus on".
    focus_areas: Tuple[Tuple[str, str], ...] = (
        ("Natural Language Processing", "language models, embeddings and text intelligence"),
        ("Conversational AI & Agents", "chat systems, tool use and streaming responses"),
        ("Machine Learning & Deep Learning", "training, evaluation and deployment"),
        ("Full-Stack Engineering", "from idea to a shipped product"),
    )

    # skillicons.dev icon slugs (real language / tool logos).
    tech_icons: Tuple[str, ...] = (
        "python", "cpp", "cs", "java", "js", "ts",
        "nodejs", "react", "html", "css", "tailwind",
        "fastapi", "docker", "postgres", "mysql",
        "mongodb", "redis", "git", "linux", "bash",
    )

    # External live-service knobs.
    stats_theme: str = "github_dark"
    language_layout: str = "compact"
    streak_theme: str = "github-dark-blue"
    graph_theme: str = "react-dark"

    # ------------------------------------------------------------------
    # Derived helpers.
    # ------------------------------------------------------------------
    def contact_items(self) -> List[Tuple[str, str, str, str]]:
        """Return (label, subtitle, url, colour) tuples for the contact row."""
        return [
            ("GMAIL", self.email, f"mailto:{self.email}", ACCENT_RED),
            ("TELEGRAM", f"@{self.telegram}", f"https://t.me/{self.telegram}", ACCENT_CYAN),
            ("GITHUB", self.github_url, f"https://{self.github_url}", ACCENT_BLUE),
        ]

    def typing_query(self) -> str:
        """URL-encode the typing lines into a single 'lines=' parameter."""
        from urllib.parse import quote_plus

        return quote_plus(";".join(self.typing_lines))

    def as_dict(self) -> Dict[str, object]:
        """Expose the config as a plain dictionary (for caching and logging)."""
        return {
            "username": self.username,
            "display_name": self.display_name,
            "tagline": self.tagline,
            "email": self.email,
            "telegram": self.telegram,
            "github_url": self.github_url,
            "location": self.location,
            "founding_year": self.founding_year,
            "typing_lines": list(self.typing_lines),
            "tech_icons": list(self.tech_icons),
            "stats_theme": self.stats_theme,
            "language_layout": self.language_layout,
            "streak_theme": self.streak_theme,
            "graph_theme": self.graph_theme,
        }
