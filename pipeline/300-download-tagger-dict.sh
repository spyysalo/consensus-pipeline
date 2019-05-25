#!/bin/bash

# Download dictionary for JensenLab tagger.

set -euo pipefail

# Set to "tagger" for the smaller tagger dictionary (300M download) or
# "full" for the full dictionary (1.7G download)
dictionary="tagger"
#dictionary="full"

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [ "$dictionary" == "tagger" ]; then
    url='http://download.jensenlab.org/tagger_dictionary.tar.gz'
elif [ "$dictionary" == "full" ]; then
    url='http://download.jensenlab.org/full_dictionary.tar.gz'
else
    echo "$SCRIPT: unknown dictionary $dictionary" >&2
    return 1
fi

OUTDIR="$SCRIPTDIR/../data/tagger/${dictionary}_dict"

missing=false
for d in "entities" "global" "groups" "names"; do
    path="$OUTDIR/${dictionary}_$d.tsv"
    if [ -s "$path" ]; then
	echo "$SCRIPT:found $path" >&2
    else
	echo "$SCRIPT:no $path, downloading ..." >&2
	missing=true
	break
    fi
done

if [ "$missing" = false ] ; then
    echo "$SCRIPT:found all files for $dictionary dictionary, exiting ..." >&2
    exit 0
fi
	
mkdir -p "$OUTDIR"

echo "$SCRIPT:creating temporary work directory ..." >&2
TMPDIR=`mktemp -d`

function rmtmp {      
    echo -n "$SCRIPT:deleting temporary directory ... " >&2
    rm -rf "$TMPDIR"
    echo "done." >&2
}

trap rmtmp EXIT

cd "$TMPDIR"

out=$(basename "$url")
echo "$SCRIPT:downloading $out from $url ..." >&2
wget "$url" -O "$out"

echo "$SCRIPT:unpacking $out to $OUTDIR ..." >&2
tar xvzf "$out" -C "$OUTDIR"

echo "$SCRIPT:done." >&2
