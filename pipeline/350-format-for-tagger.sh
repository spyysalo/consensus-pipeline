#!/bin/bash

# Format PubMed texts for JensenLab tagger.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

MODULEDIR="$SCRIPTDIR/../modules/pubmed"

INDIR="$SCRIPTDIR/../data/pubmed/db"

OUTDIR="$SCRIPTDIR/../data/pubmed/fortagger"

TOOLDIR="$SCRIPTDIR/../scripts"

inpath="$INDIR/pubmed.sqlite"

if [ ! -s "$inpath" ]; then
    echo "$SCRIPT:ABORT: $inpath not found"
    exit 1
fi

mkdir -p "$OUTDIR"

outpath="$OUTDIR/pubmed.fortagger.tsv"

if [ -s "$outpath" ]; then
    echo "$SCRIPT:$outpath exists, skipping ..."
    exit 0
fi

command="$TOOLDIR/formatfortagger.py"

python3 "$command" "$inpath" > "$outpath"

echo "SCRIPT:done." >&2
