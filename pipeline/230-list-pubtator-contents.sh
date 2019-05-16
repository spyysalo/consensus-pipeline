#!/bin/bash

# List PubTator source data contents.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

MODULEDIR="$SCRIPTDIR/../modules/pubtator"

INDIR="$SCRIPTDIR/../data/pubtator/original_data"

OUTDIR="$SCRIPTDIR/../data/pubtator/contents"

inpath="$INDIR/bioconcepts2pubtator_offsets.gz"

if [ ! -s "$inpath" ]; then
    echo "$SCRIPT:ABORT: $inpath not found"
    exit 1
fi

mkdir -p "$OUTDIR"

outpath="$OUTDIR/pubtator.source.listing"

if [ -s "$outpath" ]; then
    echo "$SCRIPT:$outpath exists, skipping ..."
    exit 0
fi

command="$MODULEDIR/listpubtatorids.py"

echo "$SCRIPT:running \"$command\" on $inpath with output to $outpath" >&2

python3 "$command" "$inpath" > "$outpath"
