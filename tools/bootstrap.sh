#!/bin/sh
# Check interpreters before importing any Python catalog code.
catalog_tools=$(CDPATH= cd -- "${0%/*}" && pwd) || exit 1
catalog_seen=0
catalog_python=
catalog_probe() {
    [ -x "$1" ] || return 1
    catalog_seen=1
    "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 11)' </dev/null >/dev/null 2>&1
}
catalog_finish() {
    catalog_status=$1
    if [ "$catalog_status" -ne 0 ] && [ -z "${CI:-}${KREA2_CATALOG_NO_PAUSE:-}" ] && [ -t 0 ] && [ -t 2 ]; then
        printf '\nPress Enter to close this window.\n' >&2
        read -r catalog_reply
    fi
    exit "$catalog_status"
}
catalog_install() {
    case "$(/usr/bin/uname -s 2>/dev/null)" in
        Darwin) printf '%s\n' 'macOS: https://www.python.org/downloads/macos/' >&2 ;;
        *) printf '%s\n' 'Linux: https://docs.python.org/3/using/unix.html' 'Install Python 3.10+ with your distribution package manager, including its matching venv package.' >&2 ;;
    esac
    printf '%s\n' 'After installation, open this startup file again.' >&2
}
if [ -n "${KREA2_CATALOG_PYTHON:-}" ]; then
    if [ ! -f "$KREA2_CATALOG_PYTHON" ] || [ ! -x "$KREA2_CATALOG_PYTHON" ]; then
        printf '%s\n' '[PYTHON_PATH] KREA2_CATALOG_PYTHON is not an executable file. Correct or unset it.' >&2
        catalog_finish 12
    fi
    catalog_probe "$KREA2_CATALOG_PYTHON"
    catalog_status=$?
    if [ "$catalog_status" -eq 11 ]; then
        printf '%s\n' '[PYTHON_OLD] The specified Python is older than 3.10.' >&2
        catalog_install
        catalog_finish 11
    elif [ "$catalog_status" -ne 0 ]; then
        printf '%s\n' '[PYTHON_PATH] The specified Python could not run. Correct or unset KREA2_CATALOG_PYTHON.' >&2
        catalog_finish 12
    fi
    catalog_python=$KREA2_CATALOG_PYTHON
else
    catalog_ifs=$IFS
    IFS=:
    for catalog_dir in $PATH; do
        [ -n "$catalog_dir" ] || continue
        IFS=$catalog_ifs
        for catalog_name in python3 python python3.20 python3.19 python3.18 python3.17 python3.16 python3.15 python3.14 python3.13 python3.12 python3.11 python3.10; do
            if catalog_probe "$catalog_dir/$catalog_name"; then
                catalog_python=$catalog_dir/$catalog_name
                break
            fi
        done
        [ -z "$catalog_python" ] || break
        IFS=:
    done
    IFS=$catalog_ifs
    if [ -z "$catalog_python" ]; then
        if [ "$catalog_seen" -eq 1 ]; then
            printf '%s\n' '[PYTHON_OLD] No runnable Python 3.10+ was found among the installed candidates.' >&2
            catalog_status=11
        else
            printf '%s\n' '[PYTHON_MISSING] Python 3.10+ is not installed or is not on PATH.' >&2
            catalog_status=10
        fi
        catalog_install
        catalog_finish "$catalog_status"
    fi
fi
"$catalog_python" "$catalog_tools/launch_catalog.py" "$@"
catalog_finish $?
