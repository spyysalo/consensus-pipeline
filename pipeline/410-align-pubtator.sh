#!/bin/bash

# Align PubTator annotations to PubMed texts.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

MODULEDIR="$SCRIPTDIR/../modules/annalign"

PUBMEDDIR="$SCRIPTDIR/../data/pubmed/db"

PUBTATORDIR="$SCRIPTDIR/../data/pubtator/db"

sourcedb="$PUBTATORDIR/pubtator-original.sqlite"

if [ ! -s "$sourcedb" ]; then
    echo "$SCRIPT:ABORT: $sourcedb not found"
    exit 1
fi

aligndb="$PUBMEDDIR/pubmed.sqlite"

if [ ! -s "$aligndb" ]; then
    echo "$SCRIPT:ABORT: $aligndb not found"
    exit 1
fi

outdb="$PUBTATORDIR/pubtator-aligned.sqlite"

if [ -s "$outdb" ]; then
    echo "$SCRIPT:$outdb exists, assuming complete and exiting."
    exit 0
fi

command="$MODULEDIR/annalign.py"

echo "$SCRIPT:running \"$command\" on $sourcedb and $aligndb"

python3 "$command" -t -D "$sourcedb" "$sourcedb" "$aligndb" -o "$outdb"
