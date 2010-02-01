#!/bin/bash

gendir=$(dirname $0)
apidir=$(dirname $gendir)
epydoc="epydoc --config $gendir/epydoc.conf --css $gendir/epydoc.css"

if [[ $1 == '' ]]; then
    echo "Usage: $0 all"
    echo "   or: $0 <epydoc options>"
elif [[ $1 == 'all' ]]; then
    $epydoc --output $apidir $apidir/../../src/robotide
else
    $epydoc $@
fi
