#!/bin/bash

# Map serial IDs in JensenLab tagger to names and ontology/DB identifiers.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CONFIGDIR="$SCRIPTDIR/../config"

# imports `dictionary` variable
source "$CONFIGDIR/tagger_config.sh"

MODULEDIR="$SCRIPTDIR/../modules/jensenlab-tools"

INDIR="$SCRIPTDIR/../data/tagger/tagger_output"

inpath="$INDIR/pubmed.tagged.tsv"

if [ ! -s "$inpath" ]; then
    echo "$SCRIPT:ABORT:missing $inpath" >&2
    exit 1
fi

OUTDIR="$SCRIPTDIR/../data/tagger/tagger_output_mapped"

mkdir -p "$OUTDIR"

outpath="$OUTDIR/pubmed.tagged.tsv"

if [ -s "$outpath" ]; then
    echo "$SCRIPT:$outpath exists, assuming complete and exiting." >&2
    exit 0
fi

DICTDIR="$SCRIPTDIR/../data/tagger/${dictionary}_dict"

dictpath="$DICTDIR/${dictionary}_combined.tsv"

if [ ! -s "$dictpath" ]; then
    echo "$SCRIPT:ABORT:missing $dictpath" >&2
    exit 1
fi

command="$MODULEDIR/scripts/maptaggedids.py"

echo "$SCRIPT:running \"$command\" with dictionary $dictpath on $inpath with output to $outpath" >&2

python3 "$command" "$dictpath" "$inpath" > "$outpath"
