#!/bin/bash

# Run JensenLab tagger on PubMed texts.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CONFIGDIR="$SCRIPTDIR/../config"

# imports `dictionary` variable
source "$CONFIGDIR/tagger_config.sh"

MODULEDIR="$SCRIPTDIR/../modules/jensenlab-tagger"

tagger="$MODULEDIR/tagcorpus"

if [ ! -e  "$tagger" ]; then
    echo "$SCRIPT:ABORT:missing $tagger (tagger not compiled?)" >&2
    exit 1
fi

INDIR="$SCRIPTDIR/../data/pubmed/fortagger"

inpath="$INDIR/pubmed.fortagger.tsv"

if [ ! -s "$inpath" ]; then
    echo "$SCRIPT:ABORT:missing $inpath" >&2
    exit 1
fi

OUTDIR="$SCRIPTDIR/../data/tagger/tagger_output"

mkdir -p "$OUTDIR"

outpath="$OUTDIR/pubmed.tagged.tsv"

if [ -s "$outpath" ]; then
    echo "$SCRIPT:$outpath exists, assuming complete and exiting." >&2
    exit 0
fi

DICTDIR="$SCRIPTDIR/../data/tagger/${dictionary}_dict"

for d in "entities" "global" "groups" "names"; do
    path="$DICTDIR/${dictionary}_$d.tsv"
    if [ ! -s "$path" ]; then
	echo "$SCRIPT:ABORT:missing $path" >&2
	exit 1
    fi
done

"$tagger" \
    --types="$CONFIGDIR/consensus_types.tsv" \
    --entities="$DICTDIR/${dictionary}_entities.tsv" \
    --names="$DICTDIR/${dictionary}_names.tsv" \
    --stopwords="$DICTDIR/${dictionary}_global.tsv" \
    --autodetect \
    < "$inpath" \
    > "$outpath"
