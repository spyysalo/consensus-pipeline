#!/bin/bash

# Convert PubTator data into standoff and insert into DB.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

MODULEDIR="$SCRIPTDIR/../modules/pubtator"

INDIR="$SCRIPTDIR/../data/pubtator/original_data"
INFILE="$INDIR/bioconcepts2pubtator_offsets.gz"
IDDIR="$SCRIPTDIR/../data/pubmed/contents"
IDFILE="$IDDIR/pubmed.sqlite.listing.ids"

OUTDIR="$SCRIPTDIR/../data/pubtator/db"

if [[ ! -e "$INFILE" ]]; then
    echo "$SCRIPT:ABORT: $INFILE not found"
    exit 1
fi

if [[ ! -e "$IDFILE" ]]; then
    echo "$SCRIPT:ABORT: $IDFILE not found"
    exit 1
fi

dbpath="$OUTDIR/pubtator-original.sqlite"

if [ -s "$dbpath" ]; then
    echo "$SCRIPT:$dbpath exists, assuming complete and exiting."
    exit 0
fi

command="$MODULEDIR/convertpubtator.py"

echo "$SCRIPT:running \"$command\" on $INFILE" >&2

mkdir -p "$OUTDIR"

python3 "$command" --verbose --ids "$IDFILE" --retype-nominal --database \
	--output "$dbpath" "$INFILE"
