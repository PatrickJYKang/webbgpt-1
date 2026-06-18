"""
PDF loader for Webb Schools documents.
Place PDF files in data/pdfs/ and run this script.

Uses pdfplumber so tables are extracted as structured rows and serialized to
Markdown, instead of being flattened into jumbled text (the way pypdf's plain
text extraction does). Table structure then survives chunking + embedding and
stays readable for the answer model. Body text outside tables is extracted
separately so a table's cells aren't also duplicated as garbled prose.
"""

import os
import json
import pdfplumber

PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs")
OUTPUT_DIR = os.environ.get(
    "DATA_DIR",
    os.path.join(os.path.dirname(__file__), "..", "data-store", "scraped"),
)


def _table_to_markdown(table):
    """Serialize a pdfplumber table (list of rows of cells) to a Markdown table."""
    rows = []
    for row in table or []:
        if row is None:
            continue
        cells = []
        for cell in row:
            text = "" if cell is None else str(cell)
            # Markdown table cells can't contain raw newlines or unescaped pipes.
            cells.append(text.replace("\n", " ").replace("|", r"\|").strip())
        if any(cells):  # drop fully-empty rows
            rows.append(cells)
    if not rows:
        return ""

    ncols = max(len(r) for r in rows)
    rows = [(r + [""] * ncols)[:ncols] for r in rows]  # pad ragged rows to width

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
            # Keep an object only if its center lies outside every table bbox,
            # so table cells aren't also pulled into the body text.
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


def load_all_pdfs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in {PDF_DIR}")
        print("Place your Webb Schools PDFs there and run again.")
        return

    for filename in pdf_files:
        filepath = os.path.join(PDF_DIR, filename)
        print(f"Loading: {filename}")
        text = load_pdf(filepath)
        if not text:
            print(f"  SKIP: no text extracted")
            continue

        slug = filename.replace(".pdf", "").replace(" ", "_").lower()
        output = {
            "url": f"local://{filename}",
            "title": filename.replace(".pdf", "").replace("_", " "),
            "content": text,
        }
        out_path = os.path.join(OUTPUT_DIR, f"pdf_{slug}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"  Saved: pdf_{slug}.json ({len(text)} chars)")

    print(f"\nDone. PDFs loaded into {OUTPUT_DIR}")


if __name__ == "__main__":
    load_all_pdfs()
