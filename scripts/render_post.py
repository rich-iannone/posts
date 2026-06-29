#!/usr/bin/env python3
"""Render a Quarto blog post (.qmd) to the .md that Hugo consumes.

Usage:
    python scripts/render_post.py <post-dir>        # e.g. small-focused-tools
    python scripts/render_post.py <post-dir>/index.qmd

Steps:
    1. Run ``quarto render`` to produce the .md (executing any ``{python}`` cells).
    2. Replace Quarto's generated frontmatter with the original from the .qmd,
       dropping the ``jupyter:`` key so it does not leak into the published file.
    3. Normalize Quarto's executable-cell markup into clean Markdown:
         - ``` {.python .cell-code}  ->  ```python
         - drop the ``::: {.cell ...}`` / ``::: {.cell-output ...}`` wrapper divs
         - fix code-fence spacing (``` lang  ->  ```lang)

The script only orchestrates Quarto and rewrites text, so it runs under any
Python 3; it does not import the post's dependencies. Those live in the Quarto
kernel selected by the post's ``jupyter:`` frontmatter key (see the Makefile).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def resolve_dir(arg: str) -> Path:
    """Accept either a post directory or a path to its index.qmd."""
    p = Path(arg)
    post_dir = p.parent if p.suffix == ".qmd" else p
    if not (post_dir / "index.qmd").is_file():
        sys.exit(f"error: {post_dir/'index.qmd'} not found")
    return post_dir


def split_frontmatter(text: str) -> tuple[list[str], str]:
    """Return (frontmatter_lines_including_fences, body) for a document.

    If the text has no leading ``---`` frontmatter, returns ([], text).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            frontmatter = lines[: i + 1]
            body = "\n".join(lines[i + 1 :])
            return frontmatter, body
    return [], text  # unterminated frontmatter; treat as none


def drop_jupyter_key(frontmatter: list[str]) -> list[str]:
    """Remove a top-level scalar ``jupyter:`` key from frontmatter lines."""
    return [ln for ln in frontmatter if not re.match(r"^jupyter:\s", ln)]


def clean_body(body: str) -> str:
    """Turn Quarto's executed-cell markup into plain Markdown.

    Also collapses blank lines that fall inside a raw-HTML ``<div>`` block.
    Great Tables emits a blank line inside the table's ``<style>`` element;
    left in place, Hugo's Goldmark parser treats that blank line as the end of
    the HTML block and then tries to parse the following CSS rule (``... { ...
    }``) as Markdown block attributes, which fails the site build. Dropping
    blank lines while a ``<div>`` is open keeps the whole table as one HTML
    block. The removed lines are only blank space between CSS rules, so the
    rendered table is unaffected.
    """
    out = []
    div_depth = 0
    for line in body.splitlines():
        # Attributed code fence from an executed cell: ``` {.python .cell-code}
        m = re.match(r"^``` \{\.([A-Za-z0-9_-]+)[^}]*\}$", line)
        if m:
            out.append(f"```{m.group(1)}")
            continue
        # Quarto cell wrapper divs: ::: {.cell ...} / ::: {.cell-output ...} and closers
        if re.match(r"^:::+\s*\{\.cell", line) or re.match(r"^:::+\s*$", line):
            continue
        # Plain fence with a stray space: ``` python -> ```python
        m = re.match(r"^``` ([a-z]+)$", line)
        if m:
            out.append(f"```{m.group(1)}")
            continue
        # Drop blank lines inside an open raw-HTML <div> block (see docstring).
        if div_depth > 0 and line.strip() == "":
            continue
        div_depth += len(re.findall(r"<div\b", line)) - len(re.findall(r"</div\s*>", line))
        if div_depth < 0:
            div_depth = 0
        out.append(line)
    text = "\n".join(out)
    if not text.endswith("\n"):
        text += "\n"
    return text


_IMAGE_RE = re.compile(r"!\[(?P<alt>.*?)\]\((?P<src>(?!https?:)[^)]+)\)", re.S)


def center_images(text: str) -> str:
    """Wrap local-asset images in a centered HTML block.

    Hugo renders these images left-aligned by default. We emit a centered
    ``<p><img></p>`` instead. This runs after Pandoc (not in the .qmd) because
    Pandoc mangles raw ``<img>`` tags whose alt text contains backticks; doing
    it here keeps the .qmd as clean Markdown and hands Goldmark plain HTML.
    Remote (http) images, e.g. badges, are left untouched.
    """

    def repl(m: "re.Match[str]") -> str:
        alt = " ".join(m.group("alt").split()).replace("`", "").replace('"', "&quot;")
        return f'<p style="text-align: center;"><img src="{m.group("src")}" alt="{alt}"></p>'

    return _IMAGE_RE.sub(repl, text)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        sys.exit("usage: render_post.py <post-dir>")

    post_dir = resolve_dir(argv[0])
    qmd = post_dir / "index.qmd"
    md = post_dir / "index.md"

    # Step 1: render (executes {python} cells via the kernel named in the qmd)
    print(f"Rendering {qmd} -> {md}")
    subprocess.run(
        ["quarto", "render", "index.qmd", "--to", "markdown", "--output", "index.md"],
        cwd=post_dir,
        check=True,
    )

    # Step 2: use the .qmd's frontmatter (minus jupyter:), keep the rendered body
    qmd_frontmatter, _ = split_frontmatter(qmd.read_text())
    qmd_frontmatter = drop_jupyter_key(qmd_frontmatter)
    _, md_body = split_frontmatter(md.read_text())

    # Step 3: normalize cell markup, center local images, and reassemble
    final = "\n".join(qmd_frontmatter) + "\n" + center_images(clean_body(md_body))
    md.write_text(final)

    print(f"Done: {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
