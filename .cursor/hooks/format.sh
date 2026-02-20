#!/bin/bash
set -euo pipefail

input=$(cat)

file_path=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('file_path',''))" 2>/dev/null || echo "")

if [[ -z "$file_path" || ! "$file_path" == *.py ]]; then
    exit 0
fi

if command -v uv &>/dev/null; then
    uv run ruff format "$file_path" 2>/dev/null || true
    uv run ruff check --fix "$file_path" 2>/dev/null || true
    uv run isort "$file_path" 2>/dev/null || true
elif command -v ruff &>/dev/null; then
    ruff format "$file_path" 2>/dev/null || true
    ruff check --fix "$file_path" 2>/dev/null || true
    isort "$file_path" 2>/dev/null || true
fi

exit 0
