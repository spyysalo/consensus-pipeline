#!/bin/bash

# Run JensenLab tagger on PubMed texts.

set -euo pipefail

# Set to "tagger" for the smaller tagger dictionary or "full" for the
# full dictionary.
dictionary="tagger"
#dictionary="full"

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

MODULEDIR="$SCRIPTDIR/../modules/jensenlab-tagger"

CONFIGDIR="$SCRIPTDIR/../config"

tagger="$MODULEDIR/tagcorpus"

if [ ! -e  "$tagger" ]; then
    echo "$SCRIPT:ABORT:missing $tagger (tagger not compiled?)" >&2
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
    --entities="$DICTDIR/tagger_entities.tsv" \
    --names="$DICTDIR/tagger_names.tsv" \
    --stopwords="$DICTDIR/tagger_global.tsv" \
    --autodetect \
    < "$inpath" \
    > "$outpath"
