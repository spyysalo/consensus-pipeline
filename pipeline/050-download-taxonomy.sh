#!/bin/bash

# Download NCBI taxonomy data.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

OUTDIR="$SCRIPTDIR/../data/taxonomy"

declare -a DMPFILES=(
    "nodes.dmp"
    "division.dmp"
    "merged.dmp"
    "delnodes.dmp"
)

missing=false
for d in "${DMPFILES[@]}"; do
    if [ ! -s "$OUTDIR/$d" ]; then
	echo "SCRIPT:$OUTDIR/$d not found, downloading ..." 2>&1
	missing=true
	break
    fi
done

if [ "$missing" = false ] ; then
    echo "$SCRIPT:found all files, exiting ..." >&2
    exit 0
fi

mkdir -p "$OUTDIR"

echo "$SCRIPT:creating temporary work directory ..." >&2
TMPDIR=`mktemp -d`

function rmtmp {      
  rm -rf "$TMPDIR"
}

trap rmtmp EXIT

cd "$TMPDIR"

echo "$SCRIPT:downloading taxdump.tar.gz from NCBI ..." >&2
wget 'ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz'

echo "$SCRIPT:unpacking taxdump.tar.gz ..." >&2
tar xvzf taxdump.tar.gz

for d in "${DMPFILES[@]}"; do
    echo "Copying $d to $OUTDIR ..." 2>&1
    cp "$d" "$OUTDIR"
done

echo "$SCRIPT:done." >&2
