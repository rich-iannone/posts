#!/usr/bin/env bash
# render-post.sh — Render a .qmd post to .md for the Posit Open Source blog.
#
# Thin wrapper kept for backwards compatibility. The canonical implementation
# is scripts/render_post.py, driven by the Makefile (`make`, `make setup`).
#
# Usage: ./render-post.sh <post-dir>
#   e.g., ./render-post.sh great-docs-ten-things

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <post-dir>" >&2
    exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/scripts/render_post.py" "$1"
