#!/bin/bash

# Download PubTator data.

set -euo pipefail

BASEURL="ftp://ftp.ncbi.nlm.nih.gov/pub/lu/PubTator/"
FILENAME="bioconcepts2pubtator_offsets.gz"

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

OUTDIR="$SCRIPTDIR/../data/pubtator/original_data"

mkdir -p "$OUTDIR"

url="$BASEURL/$FILENAME"
if [ -e "$OUTDIR/$FILENAME" ]; then
    echo "$SCRIPT:$OUTDIR/$FILENAME exists, skipping ..." >&2
else
    echo "$SCRIPT:downloading $url to $OUTDIR ..." >&2
    wget -P "$OUTDIR" "$url"
    echo "$SCRIPT:calculating checksum ..." >&2
    md5sum < "$OUTDIR/$FILENAME" > "$OUTDIR/$FILENAME.md5"
fi

echo "$SCRIPT:done." >&2
