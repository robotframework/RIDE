#!/bin/bash

apidir=$(dirname $0)
epydoc="epydoc --config $apidir/epydoc.conf --css $apidir/epydoc.css"

if [[ $1 == '' ]]; then
    echo "Usage: $0 all"
    echo "   or: $0 <epydoc options>"
elif [[ $1 == 'all' ]]; then
    $epydoc --output $apidir $apidir/../../src/robotide
else
    $epydoc $@
fi
