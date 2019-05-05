#!/bin/bash

# Download NCBI taxonomy data.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

OUTDIR="$SCRIPTDIR/../data/taxonomy"

RANK_OUTPUT="$OUTDIR/rank.tsv"

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

# Grab fields tax_id and rank from nodes.dmp
echo "$SCRIPT:storing ranks in $RANK_OUTPUT ..." >&2
cut -f 1,5 nodes.dmp > "$RANK_OUTPUT"

echo "$SCRIPT:done." >&2
