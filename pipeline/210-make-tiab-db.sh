#!/bin/bash

# Insert PubMed titles and abstracts into DB.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

MODULEDIR="$SCRIPTDIR/../modules/pubmed"

INDIR="$SCRIPTDIR/../data/pubmed/texts"

OUTDIR="$SCRIPTDIR/../data/pubmed/db"

if [[ -z $(find "$INDIR" -name '*.tar.gz') ]]; then
    echo "$SCRIPT:ABORT: no .tar.gz files found in $INDIR"
    exit 1
fi

dbpath="$OUTDIR/pubmed.sqlite"

if [ -s "$dbpath" ]; then
    echo "$SCRIPT:$dbpath exists, assuming complete and exiting."
    exit 0
fi

command="$MODULEDIR/scripts/makedb.py"

echo "$SCRIPT:running \"$command\" on data in $INDIR" >&2

mkdir -p "$OUTDIR"

find "$INDIR" -name '*.tar.gz' | sort \
    | xargs python3 "$command" "$dbpath"
