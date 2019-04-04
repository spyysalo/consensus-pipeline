#!/bin/bash

# Check checksums for PubMed data.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

INDIR="$SCRIPTDIR/../data/pubmed/original_data"

cd $INDIR

echo "$SCRIPT:checking checksums in $INDIR ..." >&2

set +e    # to allow for print output
if md5sum --check *.md5; then
    echo "$SCRIPT:all checksums OK in $INDIR" >&2
else
    echo "$SCRIPT:ABORT:checksum error(s) in $INDIR" >&2
    exit 1
fi
