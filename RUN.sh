#!/bin/bash

# Pipeline driver script.

set -euo pipefail

# https://stackoverflow.com/a/246128
BASEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

SCRIPTDIR="$BASEDIR/pipeline"

for script in $(find "$SCRIPTDIR" -maxdepth 1 -name '[0-9]*.sh' | sort); do
    br=$(basename "$0")
    bs=$(basename "$script")
    echo
    echo "---------- $br: RUNNING $bs ----------" >&2
    echo
    "$script"
done

echo
echo "---------- $br: DONE ----------" >&2
echo
