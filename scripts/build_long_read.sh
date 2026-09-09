#!/usr/bin/env sh
# Run from any directory. Requires pandoc and pdflatex for the PDF.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
pandoc article/when_ai_does_the_work.md --standalone --embed-resources --resource-path=article --css=article/style.css -o article/when_ai_does_the_work.html
pandoc article/when_ai_does_the_work.md --standalone --resource-path=article --pdf-engine=pdflatex -V documentclass=article -V fontsize=11pt -V geometry:margin=24mm -V papersize=a4 -V linestretch=1.1 -V colorlinks=true -V linkcolor=black -V urlcolor=blue -H article/pdf_header.tex -o article/when_ai_does_the_work.pdf
