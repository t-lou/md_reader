#!/usr/bin/env python3
"""
md2docx.py - Convert Markdown (e.g. answers copied from Copilot/Claude/Gemini)
into editable Word (.docx) documents, which you can then open in Word/LibreOffice,
tweak, and export to PDF.

Supports out of the box (via Pandoc):
  - Headings, bold/italic/strikethrough
  - Fenced & indented code blocks (with language-aware highlighting)
  - Tables (pipe tables / GFM tables)
  - LaTeX math: $inline$ and $$block$$ -> real, editable Word equations (OMML)
  - Images (local files or remote URLs) -> embedded in the docx
  - Links -> clickable hyperlinks

Requirements:
  - Python 3.7+
  - Pandoc installed and on PATH: https://pandoc.org/installing.html
      macOS:    brew install pandoc
      Ubuntu:   sudo apt install pandoc
      Windows:  winget install --id JohnMacFarlane.Pandoc
  - No Python packages required — this script only uses the standard library
    and shells out to the `pandoc` binary.

Usage:
  python md2docx.py answer.md
  python md2docx.py answer.md -o report.docx
  python md2docx.py chat1.md chat2.md chat3.md --outdir converted/
  python md2docx.py answer.md --reference-doc mystyle.docx

Tip (--reference-doc):
  Pandoc's default docx styling is plain. To control fonts/margins/heading
  colors/code-block appearance, create a .docx with the styles you want
  (Normal, Heading 1-3, Source Code) and pass it with --reference-doc.
  See: https://pandoc.org/MANUAL.html#option--reference-doc
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def normalize_latex_delimiters(text: str) -> str:
    """Rewrite \\( \\) and \\[ \\] LaTeX delimiters to $ $ / $$ $$ so Pandoc's
    tex_math_dollars extension recognizes them as math. Fenced code blocks
    (```...```) are left untouched so code containing literal backslashes
    isn't corrupted."""
    parts = re.split(r"(```.*?```)", text, flags=re.DOTALL)
    for i, part in enumerate(parts):
        if part.startswith("```"):
            continue  # leave code blocks as-is
        part = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", part, flags=re.DOTALL)
        part = re.sub(r"\\\((.*?)\\\)", r"$\1$", part, flags=re.DOTALL)
        parts[i] = part
    return "".join(parts)


def check_pandoc() -> None:
    if shutil.which("pandoc") is None:
        sys.exit(
            "Error: 'pandoc' was not found on your PATH.\n\n"
            "Install it first:\n"
            "  macOS:    brew install pandoc\n"
            "  Ubuntu:   sudo apt install pandoc\n"
            "  Windows:  winget install --id JohnMacFarlane.Pandoc\n"
            "  Other:    https://pandoc.org/installing.html\n"
        )


def convert(md_path: Path, out_path: Path, reference_doc: str = None) -> bool:
    original_text = md_path.read_text(encoding="utf-8")
    normalized_text = normalize_latex_delimiters(original_text)

    # Write the normalized text to a temp file *in the same directory* so
    # relative image paths in the markdown still resolve correctly.
    tmp_path = md_path.with_name(f".{md_path.stem}__normalized.md")
    tmp_path.write_text(normalized_text, encoding="utf-8")

    try:
        # gfm: matches the github-flavored markdown style Copilot/Claude/Gemini
        # output (tables, fenced code, autolinks) + tex_math_dollars for
        # $...$ / $$...$$ LaTeX (now including what were originally \( \) / \[ \])
        cmd = [
            "pandoc",
            str(tmp_path),
            "-f",
            "gfm+tex_math_dollars",
            "-t",
            "docx",
            "-o",
            str(out_path),
            "--resource-path",
            str(md_path.parent) or ".",
            "--standalone",
        ]
        if reference_doc:
            cmd += ["--reference-doc", reference_doc]

        result = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        tmp_path.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"  x FAILED: {md_path.name}")
        if result.stderr.strip():
            print(f"    {result.stderr.strip()}")
        return False

    print(f"  OK  {md_path.name}  ->  {out_path}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Markdown files to Word (.docx) via Pandoc.")
    parser.add_argument("inputs", nargs="+", help="One or more .md files to convert")
    parser.add_argument("-o", "--output", help="Output filename (only with a single input file)")
    parser.add_argument("--outdir", help="Directory to place converted .docx files in")
    parser.add_argument(
        "--reference-doc",
        help="Optional .docx template controlling fonts/styles/margins",
    )
    args = parser.parse_args()

    check_pandoc()

    inputs = [Path(p) for p in args.inputs]
    if args.output and len(inputs) > 1:
        sys.exit("Error: -o/--output only works with a single input file. Use --outdir for batches.")

    outdir = Path(args.outdir) if args.outdir else None
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)

    converted = 0
    for md_path in inputs:
        if not md_path.exists():
            print(f"  x NOT FOUND: {md_path}")
            continue
        if md_path.is_dir():
            print(f"  - SKIPPED (directory): {md_path}")
            continue
        if md_path.suffix.lower() != ".md":
            print(f"  - SKIPPED (not .md): {md_path}")
            continue

        if args.output:
            out_path = Path(args.output)
        elif outdir:
            out_path = outdir / (md_path.stem + ".docx")
        else:
            out_path = md_path.with_suffix(".docx")

        if convert(md_path, out_path, args.reference_doc):
            converted += 1

    print(f"\n{converted}/{len(inputs)} file(s) converted.")
    if converted:
        print("Open the .docx in Word/LibreOffice to review, then 'Save As PDF' when ready.")


if __name__ == "__main__":
    main()
