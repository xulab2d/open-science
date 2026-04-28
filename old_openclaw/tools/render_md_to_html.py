#!/usr/bin/env python3
"""Render running Markdown project notes to a nice standalone HTML page using pandoc.

Why: Isaac requested MD be the forward-facing artifact and easily viewable in browser.

Usage:
  python3 tools/render_md_to_html.py --in out/running_md/shuai_mt43_dr911.md --out out/html/shuai_mt43_dr911.html
  python3 tools/render_md_to_html.py --dir out/running_md --out-dir out/html --index out/html/index.html
  python3 tools/render_md_to_html.py --in out/running_md/shuai_mt43_dr911.md --pdf out/pdf/shuai_mt43_dr911.pdf

Notes:
- Requires `pandoc` on PATH.
- Keeps relative image links working by preserving directory layout (HTML goes under out/html/; MD lives under out/running_md/; images typically under out/plots/).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

DEFAULT_CSS = """
:root {
  --bg: #0b0f14;
  --fg: #e6edf3;
  --muted: #9aa7b2;
  --link: #7ee787;
  --codebg: #111827;
  --border: #22303c;
  --maxw: 980px;
}
@media (prefers-color-scheme: light) {
  :root {
    --bg: #ffffff;
    --fg: #111827;
    --muted: #6b7280;
    --link: #047857;
    --codebg: #f3f4f6;
    --border: #e5e7eb;
  }
}
html, body { background: var(--bg); color: var(--fg); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; }
body { margin: 0; }
main { max-width: var(--maxw); margin: 0 auto; padding: 32px 20px 60px; }
h1, h2, h3 { line-height: 1.15; }
h1 { font-size: 32px; margin-top: 0; }
h2 { border-bottom: 1px solid var(--border); padding-bottom: 6px; margin-top: 32px; }
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
code, pre { background: var(--codebg); border: 1px solid var(--border); border-radius: 8px; }
code { padding: 2px 6px; }
pre { padding: 12px 14px; overflow-x: auto; }
blockquote { margin: 16px 0; padding: 10px 14px; border-left: 3px solid var(--border); color: var(--muted); }
table { border-collapse: collapse; }
img { max-width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--border); }
hr { border: 0; border-top: 1px solid var(--border); margin: 28px 0; }
.header { position: sticky; top: 0; backdrop-filter: blur(8px); background: color-mix(in srgb, var(--bg) 80%, transparent); border-bottom: 1px solid var(--border); }
.header-inner { max-width: var(--maxw); margin: 0 auto; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.badge { font-size: 12px; color: var(--muted); }
""".strip()

HTML_TEMPLATE = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>$title$</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <div class=\"header\">
    <div class=\"header-inner\">
      <div><a href=\"index.html\">OpenScience running notes</a></div>
      <div class=\"badge\">Rendered: $rendered_at$</div>
    </div>
  </div>
  <main>
  $body$
  </main>
</body>
</html>
""".strip()


def ensure_pandoc() -> None:
    if shutil.which("pandoc") is None:
        raise SystemExit("pandoc not found on PATH")


def render_one(md_path: Path, out_html: Path, out_dir_for_template: Path) -> None:
    ensure_pandoc()

    out_dir_for_template.mkdir(parents=True, exist_ok=True)
    template_path = out_dir_for_template / "template.html"
    css_path = out_dir_for_template / "style.css"
    template_path.write_text(HTML_TEMPLATE, encoding="utf-8")
    css_path.write_text(DEFAULT_CSS, encoding="utf-8")

    rendered_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")

    # pandoc will substitute $title$ from metadata title; fallback to filename.
    title = md_path.stem.replace("_", " ")

    cmd = [
        "pandoc",
        str(md_path),
        "--from=markdown+tex_math_dollars+tex_math_single_backslash+raw_html",
        "--to=html",
        f"--metadata=title:{title}",
        f"--metadata=rendered_at:{rendered_at}",
        f"--template={template_path}",
        "--standalone",
        "--mathjax",
        "--toc",
        "--toc-depth=3",
        "-o",
        str(out_html),
    ]

    out_html.parent.mkdir(parents=True, exist_ok=True)

    # Copy CSS alongside output HTML (avoid SameFileError when out_dir_for_template == out_html.parent)
    dst_css = out_html.parent / css_path.name
    if css_path.resolve() != dst_css.resolve():
        shutil.copy2(css_path, dst_css)

    subprocess.run(cmd, check=True)


def render_pdf(md_path: Path, out_pdf: Path) -> None:
    """Render PDF via pandoc -> LaTeX (pdflatex).

    Notes:
    - Requires a LaTeX install providing `pdflatex`.
    - Math is rendered by LaTeX (not MathJax).
    - Embedded HTML (e.g., <img ...>) may not carry over; prefer Markdown image syntax for PDF-critical figures.
    """
    ensure_pandoc()
    if not (shutil.which("xelatex") or shutil.which("lualatex") or shutil.which("pdflatex")):
        raise SystemExit("No LaTeX engine found (need xelatex, lualatex, or pdflatex)")

    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Use xelatex to avoid common Unicode issues (superscripts, degree signs, etc.)
    engine = "xelatex" if shutil.which("xelatex") else "lualatex" if shutil.which("lualatex") else "pdflatex"
    cmd = [
        "pandoc",
        str(md_path),
        "--from=markdown+tex_math_dollars+tex_math_single_backslash+raw_html",
        f"--pdf-engine={engine}",
        "-o",
        str(out_pdf),
    ]
    subprocess.run(cmd, check=True)


def write_index(html_paths: list[Path], index_path: Path) -> None:
    lines = [
        "# OpenScience running project notes (HTML)",
        "",
        "This is an auto-generated index. Source Markdown lives in `out/running_md/`.",
        "",
    ]
    for p in sorted(html_paths):
        rel = p.name
        lines.append(f"- [{p.stem}]({rel})")
    md = "\n".join(lines) + "\n"

    # Render the index markdown into html too
    tmp_md = index_path.with_suffix(".md")
    tmp_md.write_text(md, encoding="utf-8")
    render_one(tmp_md, index_path, index_path.parent)
    try:
        tmp_md.unlink()
    except Exception:
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", help="Input markdown file")
    ap.add_argument("--out", dest="out", help="Output html file")
    ap.add_argument("--dir", dest="dir", help="Input directory of md files")
    ap.add_argument("--out-dir", dest="out_dir", help="Output directory for html files")
    ap.add_argument("--index", dest="index", help="Write index.html here when using --dir")
    ap.add_argument("--pdf", dest="pdf", help="Output PDF file (optional; uses pandoc -> LaTeX -> pdflatex)")
    args = ap.parse_args()

    if args.inp and args.out:
        md_path = Path(args.inp)
        out_html = Path(args.out)
        render_one(md_path, out_html, out_html.parent)
        if args.pdf:
            render_pdf(md_path, Path(args.pdf))
        return

    if args.dir and args.out_dir:
        in_dir = Path(args.dir)
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        htmls: list[Path] = []
        for md_path in sorted(in_dir.glob("*.md")):
            out_html = out_dir / f"{md_path.stem}.html"
            render_one(md_path, out_html, out_dir)
            htmls.append(out_html)
        if args.index:
            write_index(htmls, Path(args.index))
        # optional pdf for each
        if args.pdf:
            pdf_dir = Path(args.pdf)
            pdf_dir.mkdir(parents=True, exist_ok=True)
            for md_path in sorted(in_dir.glob("*.md")):
                render_pdf(md_path, pdf_dir / f"{md_path.stem}.pdf")
        return

    raise SystemExit("Provide either --in/--out or --dir/--out-dir")


if __name__ == "__main__":
    main()
