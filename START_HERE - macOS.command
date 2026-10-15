#!/bin/sh
catalog_home=$(CDPATH= cd -- "${0%/*}" && pwd) || exit 1
catalog_app="$catalog_home/app"
[ -f "$catalog_app/tools/bootstrap.sh" ] || catalog_app="$catalog_home"
if [ ! -f "$catalog_app/tools/bootstrap.sh" ]; then
    printf '%s\n' 'Catalog files are missing. Extract the complete ZIP and keep the app folder beside this startup file.' >&2
    if [ -z "${CI:-}${KREA2_CATALOG_NO_PAUSE:-}" ] && [ -t 0 ] && [ -t 2 ]; then printf 'Press Enter to close.\n' >&2; read -r catalog_reply; fi
    exit 2
fi
exec /bin/sh "$catalog_app/tools/bootstrap.sh" "$@"
