#!/usr/bin/env python3
"""Build the static HTML site for The Credit and Debt Calm Guide.

Converts the Markdown files in docs/ into a self-contained static HTML site
in site/. Uses only the Python standard library - no installs needed.

Usage:
    python3 build.py            # build into ./site
    python3 build.py --out DIR  # build somewhere else (used by tests)

Copyright (c) 2026 Asdale Dynamics, LLC - MIT License
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
ASSETS_DIR = ROOT / "assets"
DEFAULT_OUT = ROOT / "site"

SITE_TITLE = "The Credit and Debt Calm Guide"
SITE_TAGLINE = "Credit repair without the fear, explained like a friend would."
SITE_DESCRIPTION = (
    "A calm, plain-English manual for steady credit repair: pull your own "
    "reports safely, dispute errors in plain letters, freeze your credit, "
    "understand how scores work, and pay down debt at a pace that respects "
    "math and morale. From Asdale Dynamics, LLC."
)
COPYRIGHT = "Copyright (c) 2026 Asdale Dynamics, LLC"

# Explicit page order: index first, then numbered chapters in number order,
# then the short extras (letters, worksheets, glossary) in a curated order.
PAGE_ORDER = [
    "index.md",
    "01-pull-your-reports-safely.md",
    "02-dispute-errors-plain-letters.md",
    "03-freezes-beat-monitoring.md",
    "04-how-scores-work.md",
    "05-debt-payoff-order.md",
    "06-collector-call-scripts.md",
    "07-spotting-credit-and-debt-scams.md",
    "dispute-letter-templates.md",
    "worksheet-dispute-tracker.md",
    "worksheet-debt-payoff-plan.md",
    "worksheet-collector-call-log.md",
    "glossary.md",
]

# Pages that get the print button (worksheets and the letter templates).
PRINTABLE_PAGES = {
    "dispute-letter-templates",
    "worksheet-dispute-tracker",
    "worksheet-debt-payoff-plan",
    "worksheet-collector-call-log",
}


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Turn heading text into a stable URL anchor id."""
    text = unicodedata.normalize("NFKD", text)
    text = text.replace("'", "").replace("\u2019", "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "section"


def strip_inline(text: str) -> str:
    """Remove markdown inline markers, for use in titles/anchors."""
    return re.sub(r"[*`_]", "", text).strip()


def ordered_docs() -> list[Path]:
    """Return the docs' markdown files in the curated PAGE_ORDER."""
    by_name = {p.name: p for p in DOCS_DIR.glob("*.md")}
    missing = [n for n in PAGE_ORDER if n not in by_name]
    extra = sorted(set(by_name) - set(PAGE_ORDER))
    if missing or extra:
        raise RuntimeError(
            f"PAGE_ORDER does not match docs/: missing={missing} unlisted={extra}"
        )
    return [by_name[name] for name in PAGE_ORDER]


# --------------------------------------------------------------------------
# Inline markdown: code spans, links, bold, italics
# --------------------------------------------------------------------------

CODE_SPAN = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?![\w*])")

_EXTERNAL_LINK = re.compile(r"^https?://", re.I)
_MD_LINK = re.compile(r"^(?!//)([A-Za-z0-9._/-]+)\.md(#[A-Za-z0-9-]*)?$")
_DOCS_ASSET = re.compile(r"^\.\./assets/(.+)$")


def _rewrite_link(url: str) -> str:
    """Rewrite links so they work from the flat generated site.

    - `chapter.md` / `chapter.md#anchor`  -> `chapter.html` / `chapter.html#anchor`
    - `../assets/x` -> `x` (assets are copied to the site root)
    """
    m = _MD_LINK.match(url)
    if m:
        return f"{m.group(1)}.html{m.group(2) or ''}"
    m = _DOCS_ASSET.match(url)
    if m:
        return m.group(1)
    return url


def inline(text: str) -> str:
    """Convert inline markdown (code, links, images, bold, italics) to HTML."""
    text = html.escape(text, quote=False)

    # Pull code spans out first so their contents are never further processed.
    placeholders: list[str] = []

    def _stash(m: re.Match) -> str:
        # Contents were already html-escaped above; stash them verbatim.
        placeholders.append(f"<code>{m.group(1)}</code>")
        return f"\x00CODE{len(placeholders) - 1}\x00"

    text = CODE_SPAN.sub(_stash, text)

    def _link(m: re.Match) -> str:
        label, url = m.group(1), m.group(2)
        url = _rewrite_link(url)
        if _EXTERNAL_LINK.match(url):
            return f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'
        return f'<a href="{url}">{label}</a>'

    def _img(m: re.Match) -> str:
        alt, src = m.group(1), _rewrite_link(m.group(2))
        return f'<img src="{src}" alt="{alt}">'

    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", _img, text)
    text = LINK.sub(_link, text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = ITALIC.sub(r"<em>\1</em>", text)

    # Restore code spans last (their contents were already escaped).
    def _restore(m: re.Match) -> str:
        return placeholders[int(m.group(1))]

    text = re.sub(r"\x00CODE(\d+)\x00", _restore, text)
    return text


# --------------------------------------------------------------------------
# Block markdown: headings, paragraphs, lists, tables, quotes, fences
# --------------------------------------------------------------------------

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
HR = re.compile(r"^\s{0,3}((-\s*){3,}|(\*\s*){3,}|(_\s*){3,})$")
FENCE = re.compile(r"^(?:\s{0,3})(`{3,}|~{3,})\s*(\S*)\s*$")
UL_ITEM = re.compile(r"^(\s*)([-*+])\s+(.*)$")
OL_ITEM = re.compile(r"^(\s*)(\d{1,3})[.)]\s+(.*)$")
TASK_ITEM = re.compile(r"^\[([ xX])\]\s+(.*)$")
QUOTE = re.compile(r"^>")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)+\|?\s*$")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def list_item(line: str):
    """Return (kind, text, indent) for a list item line, else (None, None, 0)."""
    m = UL_ITEM.match(line)
    if m:
        return "ul", m.group(3), len(m.group(1))
    m = OL_ITEM.match(line)
    if m:
        return "ol", m.group(3), len(m.group(1))
    return None, None, 0


def _is_block_start(line: str, lines: list[str], i: int) -> bool:
    if not line.strip():
        return True
    if FENCE.match(line) or HEADING.match(line) or HR.match(line):
        return True
    if QUOTE.match(line.lstrip()):
        return True
    kind, _, ind = list_item(line)
    if kind and ind < 4:
        return True
    if "|" in line and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1].strip()):
        return True
    return False


def parse_list(lines: list[str], i: int, indent: int):
    """Parse a (possibly nested) list starting at lines[i], whose first item
    sits at column `indent`. Returns (html, next_index)."""
    kind = lines[i].lstrip()[:1]
    kind = "ol" if kind.isdigit() else "ul"
    parts: list[dict] = []

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                k, _, ind = list_item(lines[j])
                if k and ind >= indent:
                    i = j
                    continue
            break

        k, text, ind = list_item(line)
        if k is None or ind < indent:
            break
        if ind > indent:
            # A nested list after a blank line: attach to previous item.
            if not parts:
                break
            sub_html, i = parse_list(lines, i, ind)
            parts[-1]["sub"].append(sub_html)
            continue
        if k != kind:
            break  # different list type at same level -> let caller handle

        i += 1
        task = None
        tm = TASK_ITEM.match(text)
        if tm and kind == "ul":
            task = tm.group(1).lower() == "x"
            text = tm.group(2)
        item = {"text": text, "task": task, "sub": []}
        parts.append(item)

        # Consume indented continuation / nested-list lines for this item.
        sub_lines = []
        while i < len(lines) and lines[i].strip() and _indent(lines[i]) > indent:
            sub_lines.append(lines[i])
            i += 1
        if sub_lines:
            if list_item(sub_lines[0])[0]:
                sub_html, _unused = parse_list(sub_lines, 0, _indent(sub_lines[0]))
                item["sub"].append(sub_html)
            else:
                item["sub"].append(
                    "<p>" + inline(" ".join(s.strip() for s in sub_lines)) + "</p>"
                )

    tag = "ul" if kind == "ul" else "ol"
    out = []
    for p in parts:
        if p["task"] is not None:
            checked = " checked" if p["task"] else ""
            inner = f'<input type="checkbox"{checked}> {inline(p["text"])}'
            cls = ' class="task"'
        else:
            inner = inline(p["text"])
            cls = ""
        if p["sub"]:
            inner += "".join("\n" + s for s in p["sub"])
        out.append(f"<li{cls}>{inner}</li>")
    return f"<{tag}>\n" + "\n".join(out) + f"\n</{tag}>", i


def parse_table(lines: list[str], i: int):
    header = [c.strip() for c in _split_row(lines[i])]
    i += 2  # skip header line + separator line
    rows = []
    while i < len(lines) and "|" in lines[i] and lines[i].strip():
        rows.append([c.strip() for c in _split_row(lines[i])])
        i += 1
    th = "".join(f"<th>{inline(c)}</th>" for c in header)
    body_rows = []
    for row in rows:
        tds = "".join(f"<td>{inline(c)}</td>" for c in row)
        body_rows.append(f"<tr>{tds}</tr>")
    return (
        "<table>\n<thead><tr>" + th + "</tr></thead>\n<tbody>\n"
        + "\n".join(body_rows) + "\n</tbody>\n</table>"
    ), i


def _split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # Allow escaped pipes: \| keeps cells intact.
    line = line.replace("\\|", "\x01")
    cells = [c.replace("\x01", "|") for c in line.split("|")]
    return cells


def blockquote_block(lines: list[str], i: int):
    buf = []
    while i < len(lines) and lines[i].lstrip().startswith(">"):
        buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
        i += 1
    inner = md_to_html("\n".join(buf))
    return "<blockquote>\n" + inner + "\n</blockquote>", i


def fenced_block(lines: list[str], i: int):
    m = FENCE.match(lines[i])
    fence, info = m.group(1), m.group(2)
    i += 1
    buf = []
    while i < len(lines) and not FENCE.match(lines[i]):
        buf.append(lines[i])
        i += 1
    if i < len(lines):
        i += 1  # consume the closing fence
    lang = re.sub(r"[^A-Za-z0-9-]", "", info)
    cls = f' class="language-{lang}"' if lang else ""
    code = html.escape("\n".join(buf))
    return f"<pre><code{cls}>{code}</code></pre>", i


def md_to_html(md: str) -> str:
    """Convert a Markdown document (the subset used in docs/) to HTML."""
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        if FENCE.match(line):
            block, i = fenced_block(lines, i)
            out.append(block)
            continue

        m = HEADING.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            anchor = slugify(strip_inline(text))
            out.append(f'<h{level} id="{anchor}">{inline(text)}</h{level}>')
            i += 1
            continue

        if HR.match(line):
            out.append("<hr>")
            i += 1
            continue

        if line.lstrip().startswith(">"):
            block, i = blockquote_block(lines, i)
            out.append(block)
            continue

        if "|" in line and i + 1 < n and TABLE_SEP.match(lines[i + 1].strip()):
            block, i = parse_table(lines, i)
            out.append(block)
            continue

        k, _, ind = list_item(line)
        if k and ind < 4:
            block, i = parse_list(lines, i, ind)
            out.append(block)
            continue

        buf = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not _is_block_start(lines[i], lines, i):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")

    return "\n".join(out)


# --------------------------------------------------------------------------
# Site assembly
# --------------------------------------------------------------------------

def first_h1(md: str) -> str | None:
    for line in md.split("\n"):
        m = HEADING.match(line)
        if m and len(m.group(1)) == 1:
            return strip_inline(m.group(2))
    return None


def read_pages() -> list[dict]:
    paths = ordered_docs()
    pages = []
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        body = md_to_html(raw)
        title = first_h1(raw) or f"Untitled ({path.stem})"
        nav_label = "Start here" if path.stem == "index" else re.sub(
            r"^(\d+[\s-]+|worksheet-)", "", title
        ).strip()
        pages.append({
            "src": path.name,
            "slug": path.stem,
            "html_name": path.stem + ".html",
            "title": title,
            "nav_label": nav_label,
            "body": body,
        })
    return pages


def render_page(page: dict, pages: list[dict], index: int) -> str:
    nav_items = []
    for p in pages:
        current = ' aria-current="page"' if p["slug"] == page["slug"] else ""
        nav_items.append(
            f'<li><a href="{p["html_name"]}"{current}>{html.escape(p["nav_label"])}</a></li>'
        )

    prev_html = ""
    if index > 0:
        p = pages[index - 1]
        prev_html = (
            f'<a class="prev" href="{p["html_name"]}">'
            f'<span class="dir">Previous</span>{html.escape(p["nav_label"])}</a>'
        )
    next_html = ""
    if index + 1 < len(pages):
        p = pages[index + 1]
        next_html = (
            f'<a class="next" href="{p["html_name"]}">'
            f'<span class="dir">Next</span>{html.escape(p["nav_label"])}</a>'
        )

    print_row = ""
    if page["slug"] in PRINTABLE_PAGES:
        print_row = (
            '<div class="print-row">'
            '<button class="print-button" onclick="window.print()">Print this page</button>'
            '<span class="hint">or press Ctrl+P (Cmd+P on a Mac)</span></div>'
        )

    title_esc = html.escape(page["title"])
    nav = "\n".join(nav_items)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{SITE_DESCRIPTION}">
<title>{title_esc} | {SITE_TITLE}</title>
<link rel="icon" href="favicon.svg">
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="wrap">
<header class="site-header">
<p class="kicker">Asdale Dynamics, LLC &middot; Beginner Guides</p>
<h1 class="site-title"><a href="index.html">{SITE_TITLE}</a></h1>
<p class="tagline">{SITE_TAGLINE}</p>
</header>
<nav class="site-nav" aria-label="Chapters">
<ul>
{nav}
</ul>
</nav>
<article>
{print_row}
{page["body"]}
</article>
<nav class="prevnext" aria-label="Adjacent chapters">
{prev_html}{next_html}
</nav>
<footer class="site-footer">
<p>{SITE_TITLE} is written and built by Asdale Dynamics, LLC. {COPYRIGHT}.</p>
<p>This guide is education, not legal or financial advice. Licensed under the
MIT License. This site is plain static HTML: no analytics, no cookies, no
tracking, and it works offline.</p>
</footer>
</div>
</body>
</html>
"""


def build(out_dir: Path = DEFAULT_OUT) -> list[str]:
    """Build the site into out_dir and return the list of files written."""
    out_dir = Path(out_dir).resolve()
    if out_dir in (Path("/"), ROOT):
        raise ValueError(f"Refusing to build into unsafe location: {out_dir}")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    pages = read_pages()
    written: list[str] = []
    for idx, page in enumerate(pages):
        target = out_dir / page["html_name"]
        target.write_text(render_page(page, pages, idx), encoding="utf-8")
        written.append(page["html_name"])

    if ASSETS_DIR.exists():
        for asset in ASSETS_DIR.iterdir():
            if asset.is_file():
                shutil.copy2(asset, out_dir / asset.name)
                written.append(asset.name)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the guide's static site.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output directory (default: site/)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    files = build(out_dir)
    print(f"Built {len(files)} files into {out_dir}/")
    for f in files:
        print(f"  {f}")


if __name__ == "__main__":
    main()
