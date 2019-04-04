#!/bin/bash

# Convert PubTator data into standoff and insert into DB.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

MODULEDIR="$SCRIPTDIR/../modules/pubtator"

INDIR="$SCRIPTDIR/../data/pubtator/original_data"
INFILE="$INDIR/bioconcepts2pubtator_offsets.gz"

OUTDIR="$SCRIPTDIR/../data/pubtator/db"

if [[ ! -e "$INFILE" ]]; then
    echo "$SCRIPT:ABORT: $INFILE not found"
    exit 1
fi

command="$MODULEDIR/convertpubtator.py"

echo "$SCRIPT:running \"$command\" on $INFILE" >&2

mkdir -p "$OUTDIR"

python3 "$command" -v -D -o "$OUTDIR/pubtator-original.sqlite" "$INFILE"
