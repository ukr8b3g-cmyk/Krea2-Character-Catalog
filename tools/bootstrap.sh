#!/bin/sh
catalog_tools=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
if [ -n "${KREA2_CATALOG_PYTHON:-}" ]; then
    catalog_python=$KREA2_CATALOG_PYTHON
elif command -v python3 >/dev/null 2>&1; then
    catalog_python=$(command -v python3)
elif command -v python >/dev/null 2>&1; then
    catalog_python=$(command -v python)
else
    printf '%s\n' 'Python 3.10+ is required. Install Python from https://www.python.org/downloads/ and reopen the catalog.' >&2
    exit 1
fi
exec "$catalog_python" "$catalog_tools/launch_catalog.py" "$@"
