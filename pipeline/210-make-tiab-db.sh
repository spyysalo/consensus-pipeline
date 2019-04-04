#!/bin/bash

# Insert titles and abstracts into db.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

MODULEDIR="$SCRIPTDIR/../modules/pubmed"

INDIR="$SCRIPTDIR/../data/pubmed/texts"

OUTDIR="$SCRIPTDIR/../data/pubmed/db"

command="$MODULEDIR/scripts/makedb.py"

if [[ -z $(find "$INDIR" -name '*.tar.gz') ]]; then
    echo "$SCRIPT:ABORT: no .tar.gz files found in $INDIR"
    exit 1
fi

echo "Running \"$command\" on data in $INDIR" >&2

mkdir -p "$OUTDIR"

find "$INDIR" -name '*.tar.gz' \
    | xargs python3 "$command" "$OUTDIR/pubmed.sqlite"
