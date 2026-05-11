#!/usr/bin/env bash
# render-post.sh — Render a .qmd post to .md for the Posit Open Source blog.
#
# Usage: ./render-post.sh <post-dir>
#   e.g., ./render-post.sh great-docs-ten-things
#
# Steps:
#   1. Run quarto render to produce the .md
#   2. Replace the rendered frontmatter with the original from the .qmd
#   3. Fix code fence spacing (``` yaml → ```yaml)

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <post-dir>" >&2
    exit 1
fi

post_dir="$1"
qmd_file="$post_dir/index.qmd"
md_file="$post_dir/index.md"

if [[ ! -f "$qmd_file" ]]; then
    echo "Error: $qmd_file not found" >&2
    exit 1
fi

# Step 1: Render
echo "Rendering $qmd_file → $md_file"
(cd "$post_dir" && quarto render index.qmd --to markdown --output index.md)

# Step 2: Extract original frontmatter from .qmd and replace in .md
# Extract frontmatter (between first and second ---) from the .qmd
qmd_frontmatter=$(awk '
    /^---$/ { count++; if (count == 2) { print; exit }; print; next }
    count == 1 { print }
' "$qmd_file")

# Extract body (everything after the second ---) from the rendered .md
md_body=$(awk '
    /^---$/ { count++ }
    count >= 2 { if (count == 2 && /^---$/) { count++; next }; print }
' "$md_file")

# Write the cleaned .md
{
    echo "$qmd_frontmatter"
    echo "$md_body"
} > "$md_file"

# Step 3: Fix code fence spacing (``` lang → ```lang)
sed -i '' -E 's/^``` ([a-z]+)$/```\1/' "$md_file"

echo "Done: $md_file"
