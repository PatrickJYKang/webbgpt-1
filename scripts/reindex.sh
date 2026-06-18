#!/usr/bin/env bash
#
# reindex.sh — re-extract PDFs and rebuild the ChromaDB vector index.
#
# Run this after changing PDF extraction logic or PDF content. It re-extracts
# data/pdfs/*.pdf, re-embeds the whole corpus with Gemini, and writes the index
# into the data-store submodule. A full rebuild is required because changing
# extraction changes the chunks, and build_index.py's resume mode would
# otherwise SKIP already-indexed PDFs by filename.
#
# Usage:
#   scripts/reindex.sh [--install] [--commit] [--skip-tests]
#     --install      pip install -r requirements.txt before running
#     --commit       commit & push the regenerated index (data-store + pointer)
#     --skip-tests   don't run tests/run_tests.py at the end
#   Env: PYTHON=python3.12 scripts/reindex.sh   # override the interpreter
#
set -euo pipefail

DO_INSTALL=0; DO_COMMIT=0; SKIP_TESTS=0
for arg in "$@"; do
  case "$arg" in
    --install)    DO_INSTALL=1 ;;
    --commit)     DO_COMMIT=1 ;;
    --skip-tests) SKIP_TESTS=1 ;;
    -h|--help)    echo "Usage: scripts/reindex.sh [--install] [--commit] [--skip-tests]"; exit 0 ;;
    *)            echo "Unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

# Always run from the repo root (this script lives in scripts/).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"

echo "==> Pre-flight checks"
command -v "$PY" >/dev/null 2>&1 || { echo "ERROR: '$PY' not found (set PYTHON=...)." >&2; exit 1; }

# 1. Source PDFs must be present (they're gitignored / local-only).
shopt -s nullglob; pdfs=(data/pdfs/*.pdf); shopt -u nullglob
if [ "${#pdfs[@]}" -eq 0 ]; then
  echo "ERROR: no PDFs found in data/pdfs/. Put the source PDFs there first." >&2
  exit 1
fi
echo "    PDFs:     ${#pdfs[@]} file(s) in data/pdfs/"

# 2. A Gemini API key is required for embeddings (.env or environment).
if [ ! -f .env ] && [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "ERROR: no .env and GEMINI_API_KEY unset — embeddings need a Gemini key." >&2
  exit 1
fi
echo "    API key:  $( [ -f .env ] && echo '.env present' || echo 'GEMINI_API_KEY set' )"

# 3. data-store submodule must be initialized (the index is written there).
if [ ! -e data-store/.git ]; then
  echo "    data-store not initialized — running 'git submodule update --init'"
  git submodule update --init data-store
fi

# 4. Dependencies.
if ! "$PY" -c 'import chromadb, pdfplumber; from google import genai' >/dev/null 2>&1; then
  if [ "$DO_INSTALL" -eq 1 ]; then
    echo "    Installing dependencies (requirements.txt)..."
    "$PY" -m pip install -r requirements.txt
  else
    echo "ERROR: missing deps. Run '$PY -m pip install -r requirements.txt' (or re-run with --install)." >&2
    exit 1
  fi
fi
echo "    Deps:     ok"

echo "==> [1/3] Extracting PDFs (pdfplumber, tables -> Markdown)"
"$PY" ingest/pdf_loader.py

echo "==> [2/3] Clearing old index and rebuilding"
rm -rf data-store/chroma_db
"$PY" rag/build_index.py

if [ "$SKIP_TESTS" -eq 1 ]; then
  echo "==> [3/3] Skipping tests (--skip-tests)"
else
  echo "==> [3/3] Running test suite"
  "$PY" tests/run_tests.py
fi

echo "==> Re-index complete."

if [ "$DO_COMMIT" -eq 1 ]; then
  echo "==> Publishing regenerated index"
  ( cd data-store && git add -A && git commit -m "Rebuild index: pdfplumber table extraction" && git push )
  git add data-store && git commit -m "Bump data-store (pdfplumber re-index)" && git push
else
  cat <<'EOF'

To publish the regenerated index (data-store is a submodule):

  cd data-store && git add -A && git commit -m "Rebuild index: pdfplumber table extraction" && git push && cd ..
  git add data-store && git commit -m "Bump data-store (pdfplumber re-index)" && git push

  (or re-run: scripts/reindex.sh --commit)
EOF
fi
