#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
CATALOG="$SCRIPT_DIR/../config/tools.json"
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

case "${1:-}" in
--dry-run)
    printf 'DEPRECATED: install-tools.sh; use: be tools plan with an explicit selector\n' >&2
    shift
    exec "$python_bin" "$SCRIPT_DIR/tool_catalog.py" --catalog "$CATALOG" plan "$@"
    ;;
--install)
    printf 'DEPRECATED: install-tools.sh; use: be tools install with an explicit selector\n' >&2
    shift
    exec "$python_bin" "$SCRIPT_DIR/tool_catalog.py" --catalog "$CATALOG" install "$@"
    ;;
--help | -h)
    exec "$python_bin" "$SCRIPT_DIR/tool_catalog.py" --help
    ;;
"")
    exec "$python_bin" "$SCRIPT_DIR/tool_catalog.py" --help
    ;;
*)
    exec "$python_bin" "$SCRIPT_DIR/tool_catalog.py" --catalog "$CATALOG" "$@"
    ;;
esac
