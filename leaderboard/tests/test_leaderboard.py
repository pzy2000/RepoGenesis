"""
Test suite for RepoGenesis Leaderboard website.

Validates HTML structure, CSS, JS, and JSON data files
following TDD best practices. Tests are written BEFORE implementation.
"""

import json
import os
import re
import unittest
from pathlib import Path
from html.parser import HTMLParser


# ====================================================================
# Constants
# ====================================================================

LEADERBOARD_DIR = Path(__file__).resolve().parent.parent
INDEX_HTML = LEADERBOARD_DIR / "index.html"
SUBMIT_HTML = LEADERBOARD_DIR / "submit.html"
MAIN_CSS = LEADERBOARD_DIR / "css" / "main.css"
LEADERBOARD_JS = LEADERBOARD_DIR / "js" / "leaderboard.js"
RESULTS_JSON = LEADERBOARD_DIR / "data" / "results.json"
LOGO_IMG = LEADERBOARD_DIR / "img" / "repogenesis.png"
SERVE_PY = LEADERBOARD_DIR / "serve.py"


# ====================================================================
# Helper: Simple HTML tag extractor
# ====================================================================

class HTMLTagCollector(HTMLParser):
    """Collects tags, attributes, and text content from HTML."""

    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs_map = {}  # tag -> [list of attr dicts]
        self.text_chunks = []
        self._current_tag = None

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attr_dict = dict(attrs)
        self.attrs_map.setdefault(tag, []).append(attr_dict)
        self._current_tag = tag

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.text_chunks.append(stripped)

    def has_tag_with_class(self, tag, cls):
        for attr_dict in self.attrs_map.get(tag, []):
            classes = attr_dict.get("class", "")
            if cls in classes.split():
                return True
        return False

    def has_tag_with_attr(self, tag, attr_name, attr_value=None):
        for attr_dict in self.attrs_map.get(tag, []):
            if attr_name in attr_dict:
                if attr_value is None or attr_dict[attr_name] == attr_value:
                    return True
        return False

    def has_text(self, text):
        for chunk in self.text_chunks:
            if text in chunk:
                return True
        return False


def parse_html(filepath):
    """Parse an HTML file and return an HTMLTagCollector."""
    collector = HTMLTagCollector()
    collector.feed(filepath.read_text(encoding="utf-8"))
    return collector


# ====================================================================
# Test: File existence
# ====================================================================

class TestFileStructure(unittest.TestCase):
    """All required files must exist."""

    def test_index_html_exists(self):
        self.assertTrue(INDEX_HTML.exists(), f"Missing: {INDEX_HTML}")

    def test_submit_html_exists(self):
        self.assertTrue(SUBMIT_HTML.exists(), f"Missing: {SUBMIT_HTML}")

    def test_main_css_exists(self):
        self.assertTrue(MAIN_CSS.exists(), f"Missing: {MAIN_CSS}")

    def test_leaderboard_js_exists(self):
        self.assertTrue(LEADERBOARD_JS.exists(), f"Missing: {LEADERBOARD_JS}")

    def test_results_json_exists(self):
        self.assertTrue(RESULTS_JSON.exists(), f"Missing: {RESULTS_JSON}")

    def test_logo_exists(self):
        self.assertTrue(LOGO_IMG.exists(), f"Missing: {LOGO_IMG}")

    def test_serve_py_exists(self):
        self.assertTrue(SERVE_PY.exists(), f"Missing: {SERVE_PY}")


# ====================================================================
# Test: JSON data structure
# ====================================================================

class TestResultsJSON(unittest.TestCase):
    """Validate data/results.json schema and content."""

    @classmethod
    def setUpClass(cls):
        with open(RESULTS_JSON, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_top_level_keys(self):
        """Must have three sub-frame keys."""
        self.assertIn("verified", self.data)
        self.assertIn("full", self.data)
        self.assertIn("verified_no_docker", self.data)

    def test_verified_is_list(self):
        self.assertIsInstance(self.data["verified"], list)

    def test_full_is_list(self):
        self.assertIsInstance(self.data["full"], list)

    def test_verified_no_docker_not_empty(self):
        self.assertGreater(len(self.data["verified_no_docker"]), 0)

    def test_verified_entry_schema(self):
        """Each verified entry must have required fields."""
        required = {"model", "category", "language", "pass_at_1", "ac", "dsr",
                     "org", "date"}
        for entry in self.data["verified"]:
            self.assertTrue(required.issubset(entry.keys()),
                            f"Missing keys in {entry.get('model', '?')}: "
                            f"{required - entry.keys()}")

    def test_full_entry_schema(self):
        required = {"model", "category", "language", "pass_at_1", "ac",
                     "org", "date"}
        for entry in self.data["full"]:
            self.assertTrue(required.issubset(entry.keys()),
                            f"Missing keys in {entry.get('model', '?')}")

    def test_verified_no_docker_entry_schema(self):
        required = {"model", "category", "language", "pass_at_1", "ac", "dsr",
                     "org", "date"}
        for entry in self.data["verified_no_docker"]:
            self.assertTrue(required.issubset(entry.keys()),
                            f"Missing keys in {entry.get('model', '?')}: "
                            f"{required - entry.keys()}")

    def test_category_values(self):
        """Category must be Agent, IDE, or CLI."""
        valid = {"Agent", "IDE", "CLI"}
        for tab in ("verified", "full", "verified_no_docker"):
            for entry in self.data[tab]:
                self.assertIn(entry["category"], valid,
                              f"Invalid category: {entry['category']}")

    def test_language_values(self):
        """Language must be Python or Java."""
        valid = {"Python", "Java"}
        for tab in ("verified", "full", "verified_no_docker"):
            for entry in self.data[tab]:
                self.assertIn(entry["language"], valid,
                              f"Invalid language: {entry['language']}")

    def test_ac_is_numeric(self):
        """AC must be a number between 0 and 100."""
        for tab in ("verified", "full", "verified_no_docker"):
            for entry in self.data[tab]:
                ac = entry["ac"]
                self.assertIsInstance(ac, (int, float))
                self.assertGreaterEqual(ac, 0)
                self.assertLessEqual(ac, 100)

    def test_verified_dsr_present(self):
        """Verified entries must have DSR as number or null."""
        for entry in self.data["verified"]:
            dsr = entry["dsr"]
            if dsr is not None:
                self.assertIsInstance(dsr, (int, float))
                self.assertGreaterEqual(dsr, 0)
                self.assertLessEqual(dsr, 100)

    def test_date_format(self):
        """Dates must be YYYY-MM-DD format."""
        date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for tab in ("verified", "full", "verified_no_docker"):
            for entry in self.data[tab]:
                self.assertRegex(entry["date"], date_re,
                                 f"Bad date: {entry['date']}")

    def test_verified_no_docker_entry_count(self):
        """Must have 72 entries (48 agent + 24 IDE)."""
        self.assertEqual(len(self.data["verified_no_docker"]), 72)

    def test_verified_no_docker_pass_at_1_present(self):
        """Each verified_no_docker entry must have pass_at_1 as number or null."""
        for entry in self.data["verified_no_docker"]:
            p = entry["pass_at_1"]
            if p is not None:
                self.assertIsInstance(p, (int, float),
                                     f"pass_at_1 must be numeric: {entry['model']}")
                self.assertGreaterEqual(p, 0)
                self.assertLessEqual(p, 100)

    def test_verified_no_docker_dsr_present(self):
        """Each verified_no_docker entry must have dsr as number or null."""
        for entry in self.data["verified_no_docker"]:
            d = entry["dsr"]
            if d is not None:
                self.assertIsInstance(d, (int, float),
                                     f"dsr must be numeric: {entry['model']}")
                self.assertGreaterEqual(d, 0)
                self.assertLessEqual(d, 100)

    def test_verified_no_docker_has_both_languages(self):
        """Must have entries for both Python and Java."""
        languages = {e["language"] for e in self.data["verified_no_docker"]}
        self.assertIn("Python", languages)
        self.assertIn("Java", languages)

    def test_verified_no_docker_has_agents_and_ides(self):
        """Must have both Agent and IDE category entries."""
        categories = {e["category"] for e in self.data["verified_no_docker"]}
        self.assertIn("Agent", categories)
        self.assertIn("IDE", categories)


# ====================================================================
# Test: index.html structure
# ====================================================================

class TestIndexHTML(unittest.TestCase):
    """Validate index.html has correct structure."""

    @classmethod
    def setUpClass(cls):
        cls.html = INDEX_HTML.read_text(encoding="utf-8")
        cls.parsed = parse_html(INDEX_HTML)

    def test_has_doctype(self):
        self.assertTrue(self.html.strip().startswith("<!DOCTYPE html"),
                        "Missing DOCTYPE")

    def test_has_title(self):
        self.assertIn("<title>", self.html)
        self.assertIn("RepoGenesis", self.html)

    def test_links_main_css(self):
        self.assertIn("css/main.css", self.html)

    def test_links_leaderboard_js(self):
        self.assertIn("js/leaderboard.js", self.html)

    def test_links_font_awesome(self):
        self.assertIn("font-awesome", self.html)

    # --- Sidebar ---
    def test_sidebar_exists(self):
        self.assertTrue(self.parsed.has_tag_with_class("aside", "sidebar") or
                        self.parsed.has_tag_with_class("nav", "sidebar") or
                        "sidebar" in self.html)

    def test_sidebar_has_logo_text(self):
        self.assertTrue(self.parsed.has_text("RepoGenesis"))

    def test_sidebar_has_leaderboards_link(self):
        self.assertIn("Leaderboards", self.html)

    def test_sidebar_benchmarks_section(self):
        """BENCHMARKS section title in sidebar."""
        self.assertTrue(
            "BENCHMARKS" in self.html or "Benchmarks" in self.html)

    def test_sidebar_about_section(self):
        """ABOUT section title in sidebar."""
        self.assertTrue("ABOUT" in self.html or "About" in self.html)

    def test_sidebar_about_links(self):
        """ABOUT section must have Paper, Docs, Contact, Citations, Press."""
        for label in ("Paper", "Docs", "Contact", "Citations", "Press"):
            self.assertIn(label, self.html,
                          f"Missing ABOUT link: {label}")

    def test_sidebar_submit_button(self):
        """Submit button must exist in sidebar."""
        self.assertIn("Submit", self.html)
        self.assertIn("submit.html", self.html)

    def test_sidebar_submit_styled(self):
        """Submit should have special styling (nav-link-submit class)."""
        self.assertIn("nav-link-submit", self.html)

    def test_sidebar_social_icons(self):
        """Footer should have GitHub icon."""
        self.assertIn("fa-github", self.html)

    def test_theme_toggle(self):
        """Theme toggle button must exist."""
        self.assertIn("theme-toggle", self.html)

    # --- Sidebar benchmark hash navigation ---
    def test_sidebar_benchmark_links_have_hash(self):
        """Sidebar benchmark links must use hash anchors for tab navigation."""
        self.assertIn("#verified", self.html)
        self.assertIn("#full", self.html)
        self.assertTrue(
            "#verified_no_docker" in self.html or
            "#no-docker" in self.html,
            "Missing hash anchor for Verified (Without Docker) tab")

    # --- Tabs ---
    def test_tab_verified(self):
        self.assertIn("Verified", self.html)

    def test_tab_full(self):
        self.assertIn("Full", self.html)

    def test_tab_verified_no_docker(self):
        """Tab for Verified (Without Docker)."""
        self.assertTrue(
            "Without Docker" in self.html or
            "without Docker" in self.html or
            "Without docker" in self.html or
            "No Docker" in self.html)

    def test_three_tab_buttons(self):
        """Must have exactly 3 tab buttons."""
        count = self.html.count("tab-button")
        self.assertGreaterEqual(count, 3,
                                f"Expected >= 3 tab-button occurrences, got {count}")

    # --- Table ---
    def test_table_exists(self):
        self.assertIn("<table", self.html)

    def test_table_header_model(self):
        self.assertIn("Model", self.html)

    def test_table_header_pass_at_1(self):
        self.assertTrue("Pass@1" in self.html or "Pass@1" in self.html)

    def test_table_header_ac(self):
        self.assertIn("AC", self.html)

    def test_table_header_dsr(self):
        self.assertIn("DSR", self.html)

    # --- Mobile ---
    def test_mobile_header(self):
        self.assertIn("mobile-header", self.html)

    def test_sidebar_overlay(self):
        self.assertIn("sidebar-overlay", self.html)


# ====================================================================
# Test: submit.html structure
# ====================================================================

class TestSubmitHTML(unittest.TestCase):
    """Validate submit.html has correct structure."""

    @classmethod
    def setUpClass(cls):
        cls.html = SUBMIT_HTML.read_text(encoding="utf-8")
        cls.parsed = parse_html(SUBMIT_HTML)

    def test_has_doctype(self):
        self.assertTrue(self.html.strip().startswith("<!DOCTYPE html"))

    def test_has_title(self):
        self.assertIn("Submit", self.html)
        self.assertIn("RepoGenesis", self.html)

    def test_links_main_css(self):
        self.assertIn("css/main.css", self.html)

    def test_submit_heading(self):
        """Must have 'Submit to RepoGenesis' heading."""
        self.assertTrue(
            "Submit to RepoGenesis" in self.html or
            "Submit to Repogenesis" in self.html)

    def test_submit_guidelines_text(self):
        """Must describe guidelines."""
        self.assertTrue(
            "guidelines" in self.html.lower() or
            "contributing" in self.html.lower() or
            "instructions" in self.html.lower())

    def test_evaluating_section(self):
        """Must have 'Evaluating on RepoGenesis' section."""
        self.assertTrue(
            "Evaluating on RepoGenesis" in self.html or
            "Evaluating" in self.html)

    def test_submit_to_leaderboard_section(self):
        """Must have 'Submit to Leaderboard' section."""
        self.assertIn("Submit to Leaderboard", self.html)

    def test_info_banner(self):
        """Must have an info banner."""
        self.assertIn("info-banner", self.html)

    def test_sidebar_present(self):
        """Same sidebar as index.html."""
        self.assertIn("sidebar", self.html)

    def test_sidebar_submit_active(self):
        """Submit link should be marked as active."""
        self.assertIn("active", self.html)

    def test_has_footer(self):
        """Must have a page footer."""
        self.assertIn("page-footer", self.html)

    def test_footer_copyright(self):
        self.assertTrue(
            "RepoGenesis" in self.html and
            ("2026" in self.html or "2025" in self.html))

    def test_github_link(self):
        """Must link to GitHub repo."""
        self.assertIn("github.com", self.html)


# ====================================================================
# Test: CSS structure
# ====================================================================

class TestMainCSS(unittest.TestCase):
    """Validate css/main.css has required rules."""

    @classmethod
    def setUpClass(cls):
        cls.css = MAIN_CSS.read_text(encoding="utf-8")

    def test_has_css_variables(self):
        self.assertIn(":root", self.css)

    def test_dark_theme_colors(self):
        """Dark theme must define bg and text colors."""
        self.assertIn("--bg-primary", self.css)
        self.assertIn("--text-primary", self.css)

    def test_light_theme(self):
        """Must have light-mode overrides."""
        self.assertIn("light-mode", self.css)

    def test_sidebar_styles(self):
        self.assertIn(".sidebar", self.css)

    def test_tab_button_styles(self):
        self.assertIn(".tab-button", self.css)

    def test_leaderboard_table_styles(self):
        self.assertIn(".leaderboard-table", self.css)

    def test_category_badge_styles(self):
        self.assertIn(".badge-agent", self.css)
        self.assertIn(".badge-ide", self.css)
        self.assertIn(".badge-cli", self.css)

    def test_submit_button_style(self):
        self.assertIn(".nav-link-submit", self.css)

    def test_mobile_responsive(self):
        self.assertIn("@media", self.css)

    def test_metric_value_styles(self):
        self.assertIn(".metric-value", self.css)

    def test_page_footer_styles(self):
        self.assertIn(".page-footer", self.css)

    def test_info_banner_styles(self):
        self.assertIn(".info-banner", self.css)


# ====================================================================
# Test: JavaScript structure
# ====================================================================

class TestLeaderboardJS(unittest.TestCase):
    """Validate js/leaderboard.js has required functionality."""

    @classmethod
    def setUpClass(cls):
        cls.js = LEADERBOARD_JS.read_text(encoding="utf-8")

    def test_fetches_results_json(self):
        """Must load data/results.json."""
        self.assertTrue(
            "results.json" in self.js or
            "data/" in self.js)

    def test_tab_switching_logic(self):
        """Must handle tab click events."""
        self.assertTrue(
            "tab" in self.js.lower() and
            ("click" in self.js.lower() or
             "addEventListener" in self.js.lower()))

    def test_render_table_function(self):
        """Must have a function to render table rows."""
        self.assertTrue(
            "render" in self.js.lower() or
            "buildTable" in self.js.lower() or
            "populateTable" in self.js.lower() or
            "createRow" in self.js.lower())

    def test_sorting_logic(self):
        """Must support column sorting."""
        self.assertTrue(
            "sort" in self.js.lower())

    def test_default_sort_is_pass_at_1_descending(self):
        """Default sort must be pass_at_1 descending so top results appear first."""
        self.assertIn("pass_at_1", self.js)
        # sortColumn initialised to "pass_at_1" and sortDirection to "desc"
        self.assertRegex(self.js, r'sortColumn\s*=\s*["\']pass_at_1["\']')
        self.assertRegex(self.js, r'sortDirection\s*=\s*["\']desc["\']')

    def test_theme_toggle_logic(self):
        """Must handle theme switching."""
        self.assertTrue(
            "theme" in self.js.lower() or
            "dark" in self.js.lower() or
            "light-mode" in self.js)

    def test_handles_three_tabs(self):
        """Must reference all three data keys."""
        self.assertIn("verified", self.js)
        self.assertIn("full", self.js)
        self.assertTrue(
            "verified_no_docker" in self.js or
            "verifiedNoDocker" in self.js or
            "no_docker" in self.js)

    def test_mobile_sidebar_toggle(self):
        """Must handle mobile sidebar open/close."""
        self.assertTrue(
            "sidebar" in self.js.lower() and
            ("open" in self.js.lower() or
             "toggle" in self.js.lower()))

    def test_filter_logic(self):
        """Must support filtering (category or language)."""
        self.assertTrue(
            "filter" in self.js.lower())

    def test_error_message_includes_server_hint(self):
        """Error message should guide user to run a local server."""
        self.assertTrue(
            "serve" in self.js.lower() or
            "server" in self.js.lower() or
            "python" in self.js.lower(),
            "Error message should hint at using a local server")

    def test_hash_navigation_support(self):
        """Must support hash-based tab navigation (e.g. #verified)."""
        self.assertTrue(
            "location.hash" in self.js or
            "hashchange" in self.js or
            "window.location.hash" in self.js,
            "Must support URL hash navigation for tabs")

    def test_updates_sidebar_active_state(self):
        """Must update sidebar nav-link active state on tab change."""
        js_lower = self.js.lower()
        self.assertTrue(
            ("nav-link" in self.js and "active" in self.js) or
            ("sidebar" in js_lower and "active" in js_lower),
            "Must update sidebar active state when switching tabs")


# ====================================================================
# Test: serve.py local server
# ====================================================================

class TestServePy(unittest.TestCase):
    """Validate serve.py local HTTP server script."""

    @classmethod
    def setUpClass(cls):
        cls.content = SERVE_PY.read_text(encoding="utf-8")

    def test_uses_http_server(self):
        """Must use Python's http.server module."""
        self.assertIn("http.server", self.content)

    def test_serves_leaderboard_dir(self):
        """Must change to leaderboard directory for serving."""
        self.assertTrue(
            "chdir" in self.content or
            "directory" in self.content.lower() or
            "__file__" in self.content,
            "Must serve from the leaderboard directory")

    def test_has_port_config(self):
        """Must define a port (default or configurable)."""
        self.assertTrue(
            "port" in self.content.lower() or
            "8000" in self.content or
            "PORT" in self.content,
            "Must have port configuration")

    def test_has_main_guard(self):
        """Must have if __name__ == '__main__' guard."""
        self.assertIn('__name__', self.content)
        self.assertIn('__main__', self.content)


# ====================================================================
# Test: Cross-file consistency
# ====================================================================

class TestCrossFileConsistency(unittest.TestCase):
    """Ensure files reference each other correctly."""

    def test_index_references_submit(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("submit.html", html)

    def test_submit_references_index(self):
        html = SUBMIT_HTML.read_text(encoding="utf-8")
        self.assertIn("index.html", html)

    def test_index_references_css(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("css/main.css", html)

    def test_submit_references_css(self):
        html = SUBMIT_HTML.read_text(encoding="utf-8")
        self.assertIn("css/main.css", html)

    def test_index_references_js(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("js/leaderboard.js", html)

    def test_index_references_logo(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn("img/repogenesis.png", html)

    def test_submit_references_logo(self):
        html = SUBMIT_HTML.read_text(encoding="utf-8")
        self.assertIn("img/repogenesis.png", html)

    def test_json_data_keys_match_js_tabs(self):
        """JS tab data keys should match JSON keys."""
        with open(RESULTS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        js = LEADERBOARD_JS.read_text(encoding="utf-8")
        for key in data.keys():
            self.assertIn(key, js,
                          f"JSON key '{key}' not referenced in JS")


# ====================================================================
# Test: Contact and Citations features
# ====================================================================

class TestContactAndCitations(unittest.TestCase):
    """Validate Contact mailto link and BibTeX citation modal in both HTML files."""

    @classmethod
    def setUpClass(cls):
        cls.index_html = INDEX_HTML.read_text(encoding="utf-8")
        cls.submit_html = SUBMIT_HTML.read_text(encoding="utf-8")

    # --- Contact mailto ---

    def test_index_contact_is_mailto(self):
        """index.html Contact link must use mailto: to pzy2000@sjtu.edu.cn."""
        self.assertIn("mailto:pzy2000@sjtu.edu.cn", self.index_html)

    def test_submit_contact_is_mailto(self):
        """submit.html Contact link must use mailto: to pzy2000@sjtu.edu.cn."""
        self.assertIn("mailto:pzy2000@sjtu.edu.cn", self.submit_html)

    # --- Citations modal presence ---

    def test_index_citations_modal_exists(self):
        """index.html must contain a BibTeX citations modal element."""
        self.assertTrue(
            "bibtex-modal" in self.index_html or
            "citations-modal" in self.index_html,
            "Missing BibTeX modal in index.html")

    def test_submit_citations_modal_exists(self):
        """submit.html must contain a BibTeX citations modal element."""
        self.assertTrue(
            "bibtex-modal" in self.submit_html or
            "citations-modal" in self.submit_html,
            "Missing BibTeX modal in submit.html")

    # --- BibTeX content ---

    def test_index_bibtex_has_key_fields(self):
        """index.html modal must contain the paper BibTeX key fields."""
        for field in ("peng2026", "RepoGenesis", "arXiv", "2601.13943"):
            self.assertIn(field, self.index_html,
                          f"Missing BibTeX field '{field}' in index.html")

    def test_submit_bibtex_has_key_fields(self):
        """submit.html modal must contain the paper BibTeX key fields."""
        for field in ("peng2026", "RepoGenesis", "arXiv", "2601.13943"):
            self.assertIn(field, self.submit_html,
                          f"Missing BibTeX field '{field}' in submit.html")

    # --- Modal CSS ---

    def test_css_has_modal_styles(self):
        """main.css must have styles for the BibTeX modal."""
        css = MAIN_CSS.read_text(encoding="utf-8")
        self.assertTrue(
            "bibtex-modal" in css or "citations-modal" in css,
            "Missing modal CSS rules in main.css")

    # --- JS wires up Citations link ---

    def test_index_citations_link_triggers_modal(self):
        """index.html Citations nav link must reference modal show logic."""
        self.assertTrue(
            "bibtex-modal" in self.index_html or
            "showCitations" in self.index_html or
            "citations-modal" in self.index_html,
            "Citations link in index.html does not open a modal")

    def test_submit_citations_link_triggers_modal(self):
        """submit.html Citations nav link must reference modal show logic."""
        self.assertTrue(
            "bibtex-modal" in self.submit_html or
            "showCitations" in self.submit_html or
            "citations-modal" in self.submit_html,
            "Citations link in submit.html does not open a modal")


# ====================================================================
# Test: Org Icon feature
# ====================================================================

class TestOrgIcons(unittest.TestCase):
    """Validate that org icons are correctly wired in data, CSS, and JS."""

    # Expected mapping: org name -> relative path from leaderboard root
    ORG_IMG_MAP = {
        "DeepCode": "figs/DeepCode.png",
        "ModelScope": "figs/modelscope-color.png",
        "MetaGPT": "figs/metagpt.png",
        "Alibaba": "figs/qwen-color.png",
        "Microsoft": "figs/githubcopilot.png",
        "Google": "figs/google.png",
        "Anysphere": "figs/cursor.png",
    }

    @classmethod
    def setUpClass(cls):
        with open(RESULTS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        cls.entries = data.get("verified_no_docker", [])
        cls.js = LEADERBOARD_JS.read_text(encoding="utf-8")
        cls.css = MAIN_CSS.read_text(encoding="utf-8")

    # --- results.json: org_img field present ---

    def test_all_entries_have_org_img_field(self):
        """Every entry in verified_no_docker must have an 'org_img' field."""
        missing = [
            e.get("model", "<unknown>")
            for e in self.entries
            if "org_img" not in e
        ]
        self.assertEqual(
            missing, [],
            f"Entries missing 'org_img': {missing[:5]}"
        )

    def test_org_img_paths_are_non_empty(self):
        """Every org_img value must be a non-empty string."""
        bad = [
            e.get("model", "<unknown>")
            for e in self.entries
            if not e.get("org_img")
        ]
        self.assertEqual(bad, [], f"Entries with empty org_img: {bad[:5]}")

    def test_org_img_files_exist(self):
        """Every org_img path must point to an existing file in the figs/ dir."""
        missing_files = []
        for e in self.entries:
            img_path = e.get("org_img", "")
            full_path = LEADERBOARD_DIR / img_path
            if not full_path.exists():
                missing_files.append(f"{e.get('model')} -> {img_path}")
        self.assertEqual(
            missing_files, [],
            f"Missing icon files: {missing_files[:5]}"
        )

    def test_org_img_mapping_is_correct(self):
        """Each org value must map to its expected org_img path."""
        wrong = []
        for e in self.entries:
            org = e.get("org", "")
            expected_img = self.ORG_IMG_MAP.get(org)
            actual_img = e.get("org_img", "")
            if expected_img and actual_img != expected_img:
                wrong.append(
                    f"{e.get('model')}: expected={expected_img}, got={actual_img}"
                )
        self.assertEqual(wrong, [], f"Wrong org_img mappings: {wrong[:5]}")

    def test_all_seven_orgs_present_in_data(self):
        """All 7 known orgs must appear in the entries."""
        orgs_in_data = {e.get("org") for e in self.entries}
        for org in self.ORG_IMG_MAP:
            self.assertIn(org, orgs_in_data, f"Org '{org}' not found in data")

    # --- CSS: .org-icon class styled properly ---

    def test_css_org_icon_has_width(self):
        """main.css .org-icon must define a width."""
        # Find .org-icon block
        import re
        match = re.search(r'\.org-icon\s*\{([^}]+)\}', self.css)
        self.assertIsNotNone(match, ".org-icon class not found in main.css")
        block = match.group(1)
        self.assertIn("width", block, ".org-icon must define width")

    def test_css_org_icon_has_height(self):
        """main.css .org-icon must define a height."""
        import re
        match = re.search(r'\.org-icon\s*\{([^}]+)\}', self.css)
        self.assertIsNotNone(match, ".org-icon class not found in main.css")
        block = match.group(1)
        self.assertIn("height", block, ".org-icon must define height")

    def test_css_org_icon_has_vertical_align(self):
        """main.css .org-icon must define vertical-align for inline alignment."""
        import re
        match = re.search(r'\.org-icon\s*\{([^}]+)\}', self.css)
        self.assertIsNotNone(match, ".org-icon class not found in main.css")
        block = match.group(1)
        self.assertIn("vertical-align", block,
                      ".org-icon must define vertical-align")

    # --- JS: renderCell for 'org' uses <img> with title and class ---

    def test_js_org_cell_renders_img_tag(self):
        """leaderboard.js renderCell for 'org' must produce an <img> element."""
        self.assertIn("<img", self.js,
                      "JS renderCell for org must use <img> tag")

    def test_js_org_cell_uses_org_img_field(self):
        """leaderboard.js renderCell for 'org' must reference entry.org_img."""
        self.assertIn("org_img", self.js,
                      "JS renderCell must reference entry.org_img")

    def test_js_org_cell_has_title_attribute(self):
        """leaderboard.js renderCell for 'org' img must include title attribute."""
        self.assertIn('title=', self.js,
                      "JS renderCell org img must include title= attribute")

    def test_js_org_cell_uses_org_icon_class(self):
        """leaderboard.js renderCell for 'org' img must use class='org-icon'."""
        self.assertIn("org-icon", self.js,
                      "JS renderCell org img must use class org-icon")


if __name__ == "__main__":
    unittest.main()
