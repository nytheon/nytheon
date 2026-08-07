"""Unit tests for the profile builder.

Run with:  python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
import xml.dom.minidom

from profile_builder.config import ProfileConfig, language_color
from profile_builder.models import (
    CalendarWeek,
    ContributionCalendar,
    ContributionDay,
    LanguageStat,
    LiveData,
    Repository,
    UserStats,
)
from profile_builder import readme_builder, svg_assets, workflow
from profile_builder.workflow import build_workflow


def make_sample_data(followers: int = 18, repos: int = 5,
                     stars: int = 16, contributions: int = 4029) -> LiveData:
    """Build a fully-populated LiveData fixture for rendering tests."""
    stats = UserStats(
        followers=followers,
        public_repos=repos,
        total_stars=stars,
        avatar_url="https://avatars.githubusercontent.com/u/1",
        bio="AI developer",
    )
    week = CalendarWeek([
        ContributionDay(date=f"2026-01-0{i+1}", count=i, color="#26a641", weekday=i)
        for i in range(7)
    ])
    calendar = ContributionCalendar(total=contributions, weeks=[week] * 52)
    repositories = [
        Repository(name=f"repo-{i}", stars=i, primary_language="Python") for i in range(repos)
    ]
    languages = [
        LanguageStat(name="Python", bytes_count=4000),
        LanguageStat(name="TypeScript", bytes_count=3000),
        LanguageStat(name="HTML", bytes_count=2000),
        LanguageStat(name="CSS", bytes_count=1000),
    ]
    return LiveData(stats=stats, calendar=calendar, repositories=repositories,
                    languages=languages)


class TestXmlEscape(unittest.TestCase):
    def test_ampersand(self):
        self.assertEqual(svg_assets.xml_escape("A & B"), "A &amp; B")

    def test_angle_brackets(self):
        self.assertEqual(svg_assets.xml_escape("<tag>"), "&lt;tag&gt;")

    def test_quotes(self):
        self.assertEqual(svg_assets.xml_escape('a"b\'c'), "a&quot;b&apos;c")

    def test_plain_text_unchanged(self):
        self.assertEqual(svg_assets.xml_escape("hello world"), "hello world")


class TestFormatting(unittest.TestCase):
    def test_thousands(self):
        self.assertEqual(svg_assets.thousands(4029), "4,029")
        self.assertEqual(svg_assets.thousands(0), "0")
        self.assertEqual(svg_assets.thousands(1000000), "1,000,000")

    def test_language_color_known(self):
        self.assertEqual(language_color("Python"), "#3572A5")

    def test_language_color_fallback(self):
        color = language_color("NobodySpeaksThis")
        self.assertTrue(color.startswith("#"))
        self.assertEqual(len(color), 7)


class TestModels(unittest.TestCase):
    def test_contribution_calendar_totals(self):
        cal = make_sample_data().calendar
        # one fixture day has count 0, so 6 active days per week
        self.assertEqual(cal.active_days, 52 * 6)

    def test_top_languages_ordering(self):
        data = make_sample_data()
        top = data.top_languages(limit=2)
        self.assertEqual(top[0][0].name, "Python")
        self.assertGreater(top[0][1], top[1][1])

    def test_language_percent(self):
        lang = LanguageStat("Python", 5000)
        self.assertEqual(lang.percent_of(10000), 50.0)
        self.assertEqual(lang.percent_of(0), 0.0)

    def test_live_data_round_trip(self):
        data = make_sample_data()
        restored = LiveData.from_dict(data.to_dict())
        self.assertEqual(restored.stats.followers, data.stats.followers)
        self.assertEqual(restored.contributions, data.contributions)
        self.assertEqual(restored.language_dict(), data.language_dict())
        self.assertEqual(len(restored.repositories), len(data.repositories))


class TestSvgAssets(unittest.TestCase):
    def test_hero_banner_is_valid_xml(self):
        cfg = ProfileConfig()
        svg = svg_assets.build_hero_banner(cfg, make_sample_data())
        xml.dom.minidom.parseString(svg)  # raises on malformed XML
        self.assertIn("NYTHEON", svg)
        self.assertIn("4,029", svg)
        self.assertIn("18", svg)

    def test_divider_is_valid_xml(self):
        svg = svg_assets.build_divider()
        xml.dom.minidom.parseString(svg)

    def test_stat_cards_is_valid_xml(self):
        svg = svg_assets.build_stat_cards(ProfileConfig(), make_sample_data())
        xml.dom.minidom.parseString(svg)
        self.assertIn("REPOSITORIES", svg)

    def test_language_bars_are_valid_xml(self):
        svg = svg_assets.build_language_bars(make_sample_data().languages)
        xml.dom.minidom.parseString(svg)
        self.assertIn("Python", svg)

    def test_wrap_text(self):
        lines = svg_assets.wrap_text("word " * 40, width=20)
        self.assertTrue(all(len(line) <= 20 for line in lines))
        self.assertGreater(len(lines), 1)


class TestReadmeBuilder(unittest.TestCase):
    def setUp(self):
        self.cfg = ProfileConfig()
        self.data = make_sample_data()

    def test_uses_live_services(self):
        content = readme_builder.build_readme(self.cfg, self.data)
        self.assertNotIn("github-readme-stats.vercel.app", content)
        self.assertIn("skillicons.dev", content)
        self.assertIn("streak-stats.demolab.com", content)
        self.assertIn("github-readme-activity-graph.vercel.app", content)
        self.assertIn("img.shields.io", content)
        self.assertIn("komarev.com", content)
        self.assertIn("readme-typing-svg", content)

    def test_stats_and_langs_are_local_assets(self):
        content = readme_builder.build_readme(self.cfg, self.data)
        self.assertIn('src="assets/stats.svg"', content)
        self.assertIn('src="assets/langs.svg"', content)

    def test_no_unreliable_services(self):
        # github-readme-stats and github-profile-trophy are frequently
        # suspended; the README must not depend on them.
        content = readme_builder.build_readme(self.cfg, self.data)
        self.assertNotIn("github-readme-stats", content)
        self.assertNotIn("github-profile-trophy", content)

    def test_local_assets_are_generated(self):
        from tempfile import TemporaryDirectory
        import os
        with TemporaryDirectory() as root:
            written = readme_builder.write_assets(self.cfg, self.data, root)
            written_names = [os.path.basename(p) for p in written]
            for asset in ("banner.svg", "stats.svg", "langs.svg"):
                self.assertIn(asset, written_names)
                with open(os.path.join(root, "assets", asset),
                          encoding="utf-8") as fh:
                    xml.dom.minidom.parseString(fh.read())
        # no other local static assets should be referenced
        content = readme_builder.build_readme(self.cfg, self.data)
        for stale in ("tech.svg", "activity.svg", "contact.svg"):
            self.assertNotIn(f"assets/{stale}", content)

    def test_contains_all_sections(self):
        content = readme_builder.build_readme(self.cfg, self.data)
        for section in ("About Me", "Tech Stack", "GitHub Stats", "Connect with Me"):
            self.assertIn(section, content)

    def test_no_activity_svg(self):
        content = readme_builder.build_readme(self.cfg, self.data)
        self.assertNotIn("activity.svg", content)

    def test_typing_url_encodes_lines(self):
        url = readme_builder.typing_svg_url(self.cfg)
        self.assertIn("readme-typing-svg", url)
        self.assertIn("%3B", url)  # the ';' separator gets encoded

    def test_contact_buttons_present(self):
        content = readme_builder.build_readme(self.cfg, self.data)
        self.assertIn("mailto:", content)
        self.assertIn("t.me/nytheon", content)

    def test_footer_mentions_autorefresh(self):
        content = readme_builder.build_readme(self.cfg, self.data)
        self.assertIn("auto-refreshes daily", content)


class TestWorkflow(unittest.TestCase):
    def test_workflow_contains_required_keys(self):
        yaml_content = build_workflow(ProfileConfig())
        for fragment in (
            "name: refresh profile",
            "cron:",
            "actions/checkout@v4",
            "actions/setup-python@v5",
            "python -m unittest discover -s tests",
            "python -m profile_builder --root ..",
            "git push",
            "GITHUB_TOKEN",
        ):
            self.assertIn(fragment, yaml_content)

    def test_workflow_indentation_is_sane(self):
        yaml_content = build_workflow(ProfileConfig())
        lines = yaml_content.splitlines()
        self.assertTrue(lines[0].startswith("name:"))
        step_lines = [l for l in lines if l.startswith("      - name:")]
        self.assertGreaterEqual(len(step_lines), 4)

    def test_custom_cron(self):
        yaml_content = build_workflow(ProfileConfig(), cron="0 */6 * * *")
        self.assertIn("0 */6 * * *", yaml_content)

    def test_workflow_path(self):
        import os
        self.assertEqual(workflow.WORKFLOW_REL_PATH,
                         os.path.join(".github", "workflows", "profile.yml"))


class TestConfig(unittest.TestCase):
    def test_contact_items(self):
        cfg = ProfileConfig()
        items = cfg.contact_items()
        self.assertEqual(len(items), 3)
        self.assertTrue(items[0][1].startswith("henrik"))

    def test_as_dict_round_trip_keys(self):
        cfg = ProfileConfig()
        payload = cfg.as_dict()
        for key in ("username", "display_name", "tagline", "tech_icons"):
            self.assertIn(key, payload)


if __name__ == "__main__":
    unittest.main()
