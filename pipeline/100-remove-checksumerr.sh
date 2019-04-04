#!/bin/bash

# Remove PubMed data with checksum errors.

set -euo pipefail

SCRIPT="$(basename "$0")"

# https://stackoverflow.com/a/246128
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

DATADIR="$SCRIPTDIR/../data/pubmed/original_data"

if [ ! -d "$DATADIR" ]; then
    echo "$SCRIPT:$DATADIR does not exist, skip check"
    exit 0
fi

for f in $(find "$DATADIR" -name '*.xml.gz' | sort); do
    c="$f.md5"
    if [ ! -e "$c" ]; then
	echo "$SCRIPT:missing checksum $c, removing $f" >&2
	rm -f "$f"
    else
	md5=$(md5sum < $f | awk '{ print $1 }')
	ref=$(cat "$c" | perl -pe 's/.*=\s*(\S+).*/$1/')
	if [ "$md5" != "$ref" ]; then
	    echo "$SCRIPT:WARNING:checksums differ ($md5<>$ref), removing $f and $c" >&2
	    rm -f "$f"
	    rm -f "$c"
	else
	    echo "$SCRIPT:checksum OK for $f" >&2
	fi
    fi
done
