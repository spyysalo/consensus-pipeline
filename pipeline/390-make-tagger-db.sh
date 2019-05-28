#!/bin/bash

# Insert JensenLab tagger output into DB as standoff.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

MODULEDIR="$SCRIPTDIR/../modules/jensenlab-tools"

TXTDIR="$SCRIPTDIR/../data/pubmed/fortagger/"

TAGDIR="$SCRIPTDIR/../data/tagger/tagger_output_mapped/"

txtpath="$TXTDIR/pubmed.fortagger.tsv"

if [ ! -s "$txtpath" ]; then
    echo "$SCRIPT:ABORT:missing $txtpath" >&2
    exit 1
fi

tagpath="$TAGDIR/pubmed.tagged.tsv"

if [ ! -s "$tagpath" ]; then
    echo "$SCRIPT:ABORT:missing $tagpath" >&2
    exit 1
fi

OUTDIR="$SCRIPTDIR/../data/tagger/db"

mkdir -p "$OUTDIR"

outpath="$OUTDIR/tagger.sqlite"

if [ -s "$outpath" ]; then
    echo "$SCRIPT:$outpath exists, assuming complete and exiting." >&2
    exit 0
fi

command="$MODULEDIR/scripts/tagged2standoff.py"

echo "$SCRIPT:running \"command\" on $txtpath and $tagpath with output to $outpath"

python3 "$command" -D "$outpath" "$txtpath" "$tagpath"
