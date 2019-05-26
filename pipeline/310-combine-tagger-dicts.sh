#!/bin/bash

# Download dictionary for JensenLab tagger.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CONFIGDIR="$SCRIPTDIR/../config"

# imports `dictionary` variable
source "$CONFIGDIR/tagger_config.sh"

MODULEDIR="$SCRIPTDIR/../modules/jensenlab-tools"

DICTDIR="$SCRIPTDIR/../data/tagger/${dictionary}_dict"

DICTS="${dictionary}_preferred.tsv ${dictionary}_names.tsv ${dictionary}_entities.tsv"

indicts=""
for d in $DICTS; do
    inpath="$DICTDIR/$d"
    if [ ! -s "$inpath" ]; then
	echo "$SCRIPT:ABORT:missing $inpath" >&2
    fi
    indicts="$indicts $inpath"
done

outpath="$DICTDIR/${dictionary}_combined.tsv"

if [ -s "$outpath" ]; then
    echo "$SCRIPT:$outpath exists, assuming complete and exiting." >&2
    exit 0
fi

command="$MODULEDIR/scripts/combinedicts.py"

echo "$SCRIPT:running \"$command\" on $DICTS in $DICTDIR with output to $outpath" >&2

python3 "$command" $indicts > "$outpath"
