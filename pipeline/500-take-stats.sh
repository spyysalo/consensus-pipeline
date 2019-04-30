#!/bin/bash

# Take annotation statistics.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

OUTDIR="$SCRIPTDIR/../data/stats"

TOOLDIR="$SCRIPTDIR/../scripts"

declare -a DBDIRS=(
    "$SCRIPTDIR/../data/pubtator/db"
)

mkdir -p "$OUTDIR"

command="$TOOLDIR/standoffstats.py"

for d in "${DBDIRS[@]}"; do
    for f in $(find "$d" -name '*.sqlite'); do
	o="$OUTDIR/$(basename "$f" .sqlite).txt"
	if [ -s "$o" ]; then
	    echo "$SCRIPT:$(basename "$o") exists, skip $(basename "$f")" >&2
	else
	    echo "$SCRIPT:running \"$command\" on $f"
	    python3 "$command" "$f" -t 100 > $o
	fi
    done
done
