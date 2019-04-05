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

if [[ -z $(find "$INDIR" -name '*.xml.gz') ]]; then
    echo "$SCRIPT:ABORT: no .xml.gz files found in $INDIR"
    exit 1
fi

missing=0
found=0
total=0
files=""
for f in $(find "$INDIR" -name '*.xml.gz' | sort); do
    o="$OUTDIR/$(basename "$f" .xml.gz).tar.gz"
    if [ -e "$o" ]; then
	echo "$SCRIPT:output exists for $(basename "$f")" >&2
	found=$((found+1))
    else
	echo "$SCRIPT:output for $(basename "$f") to do ..." >&2
	missing=$((missing+1))
	if [ "$files" == "" ]; then
	    files="$f"
	else
	    files="$files"$'\n'"$f"
	fi
    fi
    total=$((total+1))
done

echo "$SCRIPT:output exists for $found/$total ($missing/$total to do)"
if [ "$missing" -eq 0 ]; then
    echo "$SCRIPT:nothing to do, exiting."
    exit 0
fi

command="$MODULEDIR/extractTIABs.py"

echo "$SCRIPT:running \"$command\" with $PARALLEL_JOBS jobs on $missing files in $INDIR"

echo "$files" \
    | parallel --jobs $PARALLEL_JOBS python3 "$command" -a -z -o "$OUTDIR"
