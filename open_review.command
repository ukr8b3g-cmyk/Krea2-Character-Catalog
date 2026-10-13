#!/bin/sh
catalog_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
exec sh "$catalog_root/tools/bootstrap.sh" "$@"
