#!/bin/bash

# List PubMed DB contents.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

INDIR="$SCRIPTDIR/../data/pubmed/db"

OUTDIR="$SCRIPTDIR/../data/pubmed/contents"

inpath="$INDIR/pubmed.sqlite"

if [ ! -s "$inpath" ]; then
    echo "$SCRIPT:ABORT: $inpath not found"
    exit 1
fi

mkdir -p "$OUTDIR"

outpath="$OUTDIR/pubmed.sqlite.listing"

if [ -s "$outpath" ]; then
    echo "$SCRIPT:$outpath exists, skipping ..."
else
    command="$SCRIPTDIR/../scripts/lssqlite.py"
    echo "$SCRIPT:running \"$command\" on $inpath with output to $outpath" >&2
    python3 "$command" "$inpath" > "$outpath"
fi

inpath="$outpath"
outpath="$OUTDIR/pubmed.sqlite.listing.ids"

if [ -s "$outpath" ]; then
    echo "$SCRIPT:$outpath exists, skipping ..."
else
    echo "$SCRIPT:processing $inpath with output to $outpath" >&2
    egrep '\.txt' < "$inpath" | perl -pe 's/\.txt//' > "$outpath"
fi

echo "SCRIPT:done." >&2
