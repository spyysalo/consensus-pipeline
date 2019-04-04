#!/bin/bash

# Extract titles and abstracts from PubMed data.

set -euo pipefail

PARALLEL_JOBS=5

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

MODULEDIR="$SCRIPTDIR/../modules/pubmed"

INDIR="$SCRIPTDIR/../data/pubmed/original_data"

OUTDIR="$SCRIPTDIR/../data/pubmed/texts"

command="$MODULEDIR/extractTIABs.py"

echo "$SCRIPT:running \"$command\" with $PARALLEL_JOBS jobs on data in $INDIR"\
     >&2

find "$INDIR" -name '*.xml.gz' | sort \
     | parallel --jobs $PARALLEL_JOBS python3 "$command" -a -z -o "$OUTDIR"
