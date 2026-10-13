#!/bin/sh
catalog_root=$(CDPATH= cd -- "${0%/*}" && pwd) || exit 1
exec /bin/sh "$catalog_root/tools/bootstrap.sh" "$@"
