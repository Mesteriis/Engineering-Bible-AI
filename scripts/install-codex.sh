#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python_bin="${ENGINEERING_BIBLE_PYTHON:-}"
if [[ -z "$python_bin" ]]; then
    if command -v python3.11 >/dev/null 2>&1; then
        python_bin=python3.11
    else
        python_bin=python3
    fi
fi
if ! command -v "$python_bin" >/dev/null 2>&1; then
    echo "Python interpreter not found: $python_bin" >&2
    exit 1
fi
"$python_bin" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else "Python 3.11+ is required")'
exec "$python_bin" "$script_dir/install_codex.py" "$@"
