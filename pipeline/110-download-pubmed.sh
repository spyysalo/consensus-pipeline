#!/bin/bash

# Download PubMed data.

set -euo pipefail

BASEURL="ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline"

# To download a sample of packages instead of everything, set STEP > 1
STEP=100

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

DATADIR="$SCRIPTDIR/../data/pubmed/original_data"

mkdir -p "$DATADIR"

for i in $(seq -w 1 "$STEP" 972); do
    # package
    r="pubmed19n0$i.xml.gz"
    url="$BASEURL/$r"
    if [ -e "$DATADIR/$r" ]; then
	echo "$SCRIPT:$DATADIR/$r exists, skipping ..." >&2
    else
	echo "$SCRIPT:downloading $url to $DATADIR ..." >&2
	wget -P "$DATADIR" "$url"
    fi
    # checksum
    r="pubmed19n0$i.xml.gz.md5"
    url="$BASEURL/$r"
    if [ -e "$DATADIR/$r" ]; then
	echo "$SCRIPT:$DATADIR/$r exists, skipping ..." >&2
    else
	echo "$SCRIPT:downloading $url to $DATADIR ..." >&2
	wget -P "$DATADIR" "$url"
    fi
done
