"""
PDF loader for Webb Schools documents.
Place PDF files in data/pdfs/ and run this script.

PDFs are extracted with pdfplumber (tables -> Markdown). Some documents have a
broken text layer that no extractor can recover (e.g. the course catalog's
course-offering grids use a symbol font whose glyphs map to random letters). For
those, drop a clean `*.md` next to the PDF in data/pdfs/ — a Markdown file whose
key words match a PDF (e.g. `..._course_catalog.md` ↔ `course_catalog_....pdf`)
replaces that PDF's extraction. HTML course-offering tables in the Markdown are
rendered as one self-describing line per course so retrieval works even when a
chunk doesn't carry the table header.
"""

import os
import re
import json
import html
import pdfplumber

PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs")
OUTPUT_DIR = os.environ.get(
    "DATA_DIR",
    os.path.join(os.path.dirname(__file__), "..", "data-store", "scraped"),
)


# --------------------------------------------------------------------------- #
# PDF extraction (pdfplumber)
# --------------------------------------------------------------------------- #
def _table_to_markdown(table):
    """Serialize a pdfplumber table (list of rows of cells) to a Markdown table."""
    rows = []
    for row in table or []:
        if row is None:
            continue
        cells = []
        for cell in row:
            text = "" if cell is None else str(cell)
            cells.append(text.replace("\n", " ").replace("|", r"\|").strip())
        if any(cells):
            rows.append(cells)
    if not rows:
        return ""
    ncols = max(len(r) for r in rows)
    rows = [(r + [""] * ncols)[:ncols] for r in rows]
    lines = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * ncols) + " |",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _extract_page(page):
    """Return a page's body text (excluding table regions) followed by each of
    its tables rendered as Markdown."""
    try:
        tables = page.find_tables()
    except Exception:
        tables = []

    if tables:
        bboxes = [t.bbox for t in tables]

        def _outside_tables(obj):
            try:
                cx = (obj["x0"] + obj["x1"]) / 2
                cy = (obj["top"] + obj["bottom"]) / 2
            except (KeyError, TypeError):
                return True
            return not any(
                x0 <= cx <= x1 and top <= cy <= bottom
                for (x0, top, x1, bottom) in bboxes
            )

        try:
            body = page.filter(_outside_tables).extract_text() or ""
        except Exception:
            body = page.extract_text() or ""
    else:
        body = page.extract_text() or ""

    blocks = []
    if body.strip():
        blocks.append(body.strip())
    for table in tables:
        try:
            markdown = _table_to_markdown(table.extract())
        except Exception:
            markdown = ""
        if markdown:
            blocks.append(markdown)
    return "\n\n".join(blocks)


def load_pdf(filepath):
    """Extract text and tables from a PDF file as Markdown-aware plain text."""
    pages = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            content = _extract_page(page)
            if content.strip():
                pages.append(content)
    return "\n\n".join(pages)


# --------------------------------------------------------------------------- #
# Clean Markdown overrides (HTML tables -> RAG-friendly text)
# --------------------------------------------------------------------------- #
_GRADE_COLS = {"9th", "10th", "11th", "12th"}
_TERM_COLS = {"sem1", "sem2", "semester1", "semester2", "year"}


def _doc_key(filename):
    """Key a document by its alphabetic words so an override matches its PDF even
    when the years / separators differ (course_catalog ↔ 2026-2027_course_catalog)."""
    stem = filename.rsplit(".", 1)[0].lower()
    words = [w for w in re.findall(r"[a-z]+", stem) if w not in {"output", "final"}]
    return frozenset(words) or frozenset({stem})


def _html_cells(row_html):
    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.S)
    return [html.unescape(re.sub(r"<[^>]+>", " ", c)).strip() for c in cells]


def _html_table_to_text(table_html):
    """Course-offering tables -> one self-describing line per course; other
    tables -> a Markdown table."""
    rows = [c for c in (_html_cells(r)
            for r in re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.S)) if c]
    if not rows:
        return ""
    header = rows[0]
    hnorm = [h.lower().replace(" ", "") for h in header]
    grade_idx = [i for i, h in enumerate(hnorm) if h in _GRADE_COLS]
    term_idx = [i for i, h in enumerate(hnorm) if h in _TERM_COLS]

    if grade_idx and term_idx:  # course-offering grid
        prereq_idx = next((i for i, h in enumerate(hnorm) if "prereq" in h), None)
        credit_idx = next((i for i, h in enumerate(hnorm) if "work" in h or "credit" in h), None)
        dept = header[0].strip()
        out = [f"{dept} course offerings (grades that may take each course and the term it runs):"]
        for r in rows[1:]:
            r = (r + [""] * len(header))[:len(header)]
            name = r[0].strip()
            if not name:
                continue
            seg = f"{name} ({dept.title()})"
            if credit_idx is not None and r[credit_idx].strip():
                seg += f" — {r[credit_idx].strip()} credit"
            if prereq_idx is not None and r[prereq_idx].strip():
                seg += f"; prerequisite: {r[prereq_idx].strip()}"
            grades = [header[i] for i in grade_idx if r[i].strip().upper() == "X"]
            terms = [header[i] for i in term_idx if r[i].strip().upper() == "X"]
            if grades:
                seg += f"; open to grades: {', '.join(grades)}"
            if terms:
                seg += f"; offered: {', '.join(terms)}"
            out.append(seg + ".")
        return "\n".join(out)

    # generic table -> Markdown
    ncol = max(len(r) for r in rows)
    rows = [(r + [""] * ncol)[:ncol] for r in rows]
    esc = lambda c: c.replace("|", r"\|")
    md = ["| " + " | ".join(esc(c) for c in rows[0]) + " |",
          "| " + " | ".join(["---"] * ncol) + " |"]
    for r in rows[1:]:
        md.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(md)


def _md_to_text(md):
    """Render a Markdown document, converting its HTML <table> blocks to text."""
    return re.sub(r"<table[^>]*>.*?</table>",
                  lambda m: _html_table_to_text(m.group(0)), md, flags=re.S)


# --------------------------------------------------------------------------- #
def load_all_pdfs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # A *.md override replaces the PDF whose key words it shares.
    overrides = {}
    for fn in sorted(os.listdir(PDF_DIR)):
        if fn.lower().endswith(".md"):
            with open(os.path.join(PDF_DIR, fn), encoding="utf-8") as f:
                overrides[_doc_key(fn)] = (fn, _md_to_text(f.read()))

    pdf_files = sorted(f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf"))
    if not pdf_files and not overrides:
        print(f"No PDF or .md files found in {PDF_DIR}")
        print("Place your Webb Schools PDFs there and run again.")
        return

    def _write(url, title, content, slug):
        out_path = os.path.join(OUTPUT_DIR, f"pdf_{slug}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"url": url, "title": title, "content": content}, f,
                      ensure_ascii=False, indent=2)
        print(f"  Saved: pdf_{slug}.json ({len(content)} chars)")

    for filename in pdf_files:
        slug = filename.replace(".pdf", "").replace(" ", "_").lower()
        key = _doc_key(filename)
        if key in overrides:
            src_fn, content = overrides.pop(key)
            print(f"Override: using {src_fn} instead of {filename}")
            _write(f"local://{src_fn}", src_fn.rsplit('.', 1)[0].replace('_', ' '), content, slug)
            continue
        print(f"Loading: {filename}")
        text = load_pdf(os.path.join(PDF_DIR, filename))
        if not text:
            print("  SKIP: no text extracted")
            continue
        _write(f"local://{filename}", filename.replace(".pdf", "").replace("_", " "), text, slug)

    # Overrides that didn't match any PDF become their own documents.
    for key, (src_fn, content) in overrides.items():
        slug = src_fn.rsplit(".", 1)[0].replace(" ", "_").lower()
        print(f"Override (standalone): {src_fn}")
        _write(f"local://{src_fn}", src_fn.rsplit('.', 1)[0].replace('_', ' '), content, slug)

    print(f"\nDone. Sources written to {OUTPUT_DIR}")


if __name__ == "__main__":
    load_all_pdfs()
