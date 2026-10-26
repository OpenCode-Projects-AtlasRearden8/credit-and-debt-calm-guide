"""Tests for The Credit and Debt Calm Guide build.

Covers the markdown-to-HTML converter (unit level) and the whole site build
(end-to-end): page generation, navigation, internal links, anchors, required
attribution, worksheet printability, the scores diagram, and a scan for
secret-shaped strings.
"""

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

_spec = importlib.util.spec_from_file_location("cdcg_build", ROOT / "build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

# Pages required by the project spec, without which the guide is incomplete.
REQUIRED_PAGES = {
    "index",
    "01-pull-your-reports-safely",
    "02-dispute-errors-plain-letters",
    "03-freezes-beat-monitoring",
    "04-how-scores-work",
    "05-debt-payoff-order",
    "06-collector-call-scripts",
    "07-spotting-credit-and-debt-scams",
    "dispute-letter-templates",
    "worksheet-dispute-tracker",
    "worksheet-debt-payoff-plan",
    "worksheet-collector-call-log",
    "glossary",
}


class ConverterInlineTests(unittest.TestCase):
    def test_headings(self):
        self.assertEqual(build.md_to_html("# Hello"), '<h1 id="hello">Hello</h1>')
        self.assertEqual(build.md_to_html("## Sub part"), '<h2 id="sub-part">Sub part</h2>')

    def test_heading_slug_is_url_safe(self):
        out = build.md_to_html("## What's a 1099-C?")
        self.assertIn('id="whats-a-1099-c"', out)

    def test_paragraph(self):
        self.assertEqual(build.md_to_html("Just a normal line."), "<p>Just a normal line.</p>")

    def test_bold_italic_inline_code(self):
        out = build.md_to_html("A **bold**, *soft*, and `tick` moment.")
        self.assertEqual(
            out, "<p>A <strong>bold</strong>, <em>soft</em>, and <code>tick</code> moment.</p>"
        )

    def test_link_markdown_to_html(self):
        out = build.md_to_html("See [chapter](03-freezes-beat-monitoring.md) now.")
        self.assertIn('href="03-freezes-beat-monitoring.html"', out)
        self.assertNotIn(".md\"", out)

    def test_link_with_anchor(self):
        out = build.md_to_html("See [entry](glossary.md#avalance) next.")
        self.assertIn('href="glossary.html#avalance"', out)

    def test_external_link_gets_noopener(self):
        out = build.md_to_html("Look at [a site](https://example.com) here.")
        self.assertIn('target="_blank" rel="noopener"', out)

    def test_docs_asset_link_is_rewritten_to_site_root(self):
        out = build.md_to_html("![d](../assets/scores-diagram.svg)")
        self.assertIn('src="scores-diagram.svg"', out)
        self.assertNotIn("../assets/", out)

    def test_raw_html_is_escaped(self):
        out = build.md_to_html("<script>alert(1)</script>")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_code_span_contents_are_escaped_and_protected(self):
        out = build.md_to_html("Type `<b>x</b>` there.")
        self.assertIn("<code>&lt;b&gt;x&lt;/b&gt;</code>", out)


class ConverterBlockTests(unittest.TestCase):
    def test_horizontal_rule(self):
        self.assertEqual(build.md_to_html("---"), "<hr>")

    def test_fenced_code_block(self):
        md = "```text\nhello <world>\n```"
        out = build.md_to_html(md)
        self.assertIn("<pre><code", out)
        self.assertIn("hello &lt;world&gt;", out)

    def test_blockquote(self):
        out = build.md_to_html("> **Remember:** keep calm.")
        self.assertIn("<blockquote>", out)
        self.assertIn("<strong>Remember:</strong>", out)

    def test_unordered_list(self):
        out = build.md_to_html("- one\n- two\n- three")
        self.assertEqual(out.count("<li>"), 3)
        self.assertTrue(out.startswith("<ul>"))
        self.assertTrue(out.endswith("</ul>"))

    def test_ordered_list(self):
        out = build.md_to_html("1. one\n2. two")
        self.assertTrue(out.startswith("<ol>"))
        self.assertEqual(out.count("<li>"), 2)

    def test_task_list(self):
        out = build.md_to_html("- [ ] not yet\n- [x] done")
        self.assertIn('class="task"', out)
        self.assertIn('<input type="checkbox"> not yet', out)
        self.assertIn('<input type="checkbox" checked> done', out)

    def test_nested_list(self):
        out = build.md_to_html("- parent\n  - child A\n  - child B\n- second parent")
        self.assertIn("<ul>\n<li>parent\n<ul>", out)
        self.assertEqual(out.count("<li>child A</li>"), 1)
        self.assertEqual(out.count("<li>second parent</li>"), 1)

    def test_table(self):
        md = "| A | B |\n|---|---|\n| 1 | two words |"
        out = build.md_to_html(md)
        self.assertIn("<table>", out)
        self.assertIn("<th>A</th>", out)
        self.assertIn("<td>1</td>", out)
        self.assertIn("<td>two words</td>", out)

    def test_letter_block_preserved_verbatim(self):
        md = "```text\nDear Bureau:\n[BALANCE] is wrong.\n```"
        out = build.md_to_html(md)
        self.assertIn("[BALANCE] is wrong.", out)

    def test_unterminated_fence_is_robust(self):
        out = build.md_to_html("```js\nconst x = 1;")
        self.assertIn("const x = 1;", out)


class ContentCoverageTests(unittest.TestCase):
    def test_every_required_page_exists(self):
        docs = {p.stem for p in build.DOCS_DIR.glob("*.md")}
        self.assertTrue(REQUIRED_PAGES <= docs, REQUIRED_PAGES - docs)

    def test_page_order_is_registered(self):
        listed = {name[:-3] for name in build.PAGE_ORDER}
        docs = {p.stem for p in build.DOCS_DIR.glob("*.md")}
        self.assertEqual(listed, docs)

    def test_scores_diagram_asset_exists(self):
        self.assertTrue((build.ASSETS_DIR / "scores-diagram.svg").is_file())
        svg = (build.ASSETS_DIR / "scores-diagram.svg").read_text(encoding="utf-8")
        for expected in ("35%", "30%", "15%", "10%", "Payment history", "Amounts owed"):
            self.assertIn(expected, svg)

    def test_scores_diagram_referenced_in_scores_chapter(self):
        text = (build.DOCS_DIR / "04-how-scores-work.md").read_text(encoding="utf-8")
        self.assertIn("scores-diagram.svg", text)

    def test_companion_project_mentioned(self):
        text = "".join(p.read_text(encoding="utf-8") for p in build.DOCS_DIR.glob("*.md"))
        self.assertIn("subscription-audit-handbook", text)


class EndToEndBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "site"
        build.build(cls.out)
        cls.docs = {p.stem for p in build.DOCS_DIR.glob("*.md")}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_doc_has_html(self):
        for doc in self.docs:
            self.assertTrue((self.out / f"{doc}.html").is_file(), doc)

    def test_assets_copied(self):
        for name in ("style.css", "favicon.svg", "scores-diagram.svg"):
            self.assertTrue((self.out / name).is_file())

    def test_footer_copyright_exact(self):
        expected = "Copyright (c) 2026 Asdale Dynamics, LLC"
        for name in self.docs:
            html = (self.out / f"{name}.html").read_text(encoding="utf-8")
            self.assertIn(expected, html, name)

    def test_attribution_credit(self):
        for name in self.docs:
            html = (self.out / f"{name}.html").read_text(encoding="utf-8")
            self.assertIn("Asdale Dynamics, LLC", html, name)

    def test_titles_present(self):
        html = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn("<title>Welcome — start here | The Credit and Debt Calm Guide</title>", html)
        self.assertIn("The Credit and Debt Calm Guide", html)

    def test_nav_lists_all_pages(self):
        html = (self.out / "index.html").read_text(encoding="utf-8")
        for name in self.docs:
            self.assertIn(f'href="{name}.html"', html, name)

    def test_prev_next_only_at_ends(self):
        first = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('class="prev"', first)
        self.assertIn('class="next"', first)
        last = (self.out / "glossary.html").read_text(encoding="utf-8")
        self.assertIn('class="prev"', last)
        self.assertNotIn('class="next"', last)

    def test_print_button_on_worksheets_and_letters_only(self):
        printable = build.PRINTABLE_PAGES
        for name in self.docs:
            html = (self.out / f"{name}.html").read_text(encoding="utf-8")
            if name in printable:
                self.assertIn("Print this page", html, name)
            else:
                self.assertNotIn("print-button", html, name)

    def test_worksheets_have_checkboxes(self):
        for name in ("worksheet-dispute-tracker", "worksheet-debt-payoff-plan",
                     "worksheet-collector-call-log"):
            html = (self.out / f"{name}.html").read_text(encoding="utf-8")
            self.assertGreaterEqual(html.count('type="checkbox"'), 3, name)

    def test_letters_page_has_three_templates(self):
        text = (build.DOCS_DIR / "dispute-letter-templates.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("```text"), 3)

    def test_disclaimer_on_every_page(self):
        for name in self.docs:
            html = (self.out / f"{name}.html").read_text(encoding="utf-8")
            self.assertIn("education, not legal or financial advice", html, name)

    def test_diagram_embeds_and_resolves(self):
        html = (self.out / "04-how-scores-work.html").read_text(encoding="utf-8")
        self.assertIn('src="scores-diagram.svg"', html)
        self.assertNotIn("../assets/", html)

    def test_internal_links_resolve(self):
        id_pattern = re.compile(r'id="([^"]+)"')
        link_pattern = re.compile(r'href="([^"]+)"')
        pages = self.docs
        for name in pages:
            html = (self.out / f"{name}.html").read_text(encoding="utf-8")
            own_ids = {m.group(1) for m in id_pattern.finditer(html)}
            for href in {m.group(1) for m in link_pattern.finditer(html)}:
                if href.startswith("http") or href.startswith("style.css") or href == "favicon.svg":
                    continue
                target, _, frag = href.partition("#")
                if not target:
                    self.assertIn(frag, own_ids, f"{name} -> {href}")
                else:
                    target_name = target[:-5] if target.endswith(".html") else target
                    self.assertIn(target_name, pages, f"{name} -> {href}")
                    if frag:
                        target_html = (self.out / target).read_text(encoding="utf-8")
                        self.assertIn(f'id="{frag}"', target_html, f"{name} -> {href}")

    def test_images_resolve(self):
        src_pattern = re.compile(r'src="([^"]+)"')
        for name in self.docs:
            html = (self.out / f"{name}.html").read_text(encoding="utf-8")
            for src in {m.group(1) for m in src_pattern.finditer(html)}:
                if src.startswith("http"):
                    continue
                self.assertTrue((self.out / src).is_file(), f"{name} -> {src}")

    def test_no_duplicate_heading_ids(self):
        id_pattern = re.compile(r'id="([^"]+)"')
        for name in self.docs:
            html = (self.out / f"{name}.html").read_text(encoding="utf-8")
            ids = [m.group(1) for m in id_pattern.finditer(html)]
            self.assertEqual(len(ids), len(set(ids)), f"duplicate id in {name}")

    def test_no_unconverted_markdown_links(self):
        for name in self.docs:
            html = (self.out / f"{name}.html").read_text(encoding="utf-8")
            self.assertNotIn(".md)", html, name)
            self.assertNotIn('"../', html, name)

    def test_no_secret_shaped_strings(self):
        patterns = ["sk-", "AKIA", "ghp_", "xoxb-", "BEGIN PRIVATE KEY", "api_key"]
        sources = [p.read_text(encoding="utf-8") for p in build.DOCS_DIR.glob("*.md")]
        sources.append((ROOT / "build.py").read_text(encoding="utf-8"))
        sources.append((ROOT / "README.md").read_text(encoding="utf-8"))
        for source in sources:
            for pat in patterns:
                self.assertNotIn(pat, source, f"secret-like pattern {pat} found")

    def test_no_personal_data_shaped_strings(self):
        ssn_like = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
        for p in build.DOCS_DIR.glob("*.md"):
            self.assertIsNone(ssn_like.search(p.read_text(encoding="utf-8")), p.name)

    def test_license_exact_line(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2026 Asdale Dynamics, LLC", license_text)

    def test_readme_credits_llc(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Asdale Dynamics, LLC", readme)


if __name__ == "__main__":
    unittest.main()
