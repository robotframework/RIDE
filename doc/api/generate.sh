#!/bin/bash

apidir=$(dirname $0)
config=$apidir/epydoc.conf

if [[ $1 == '' ]]; then
    echo "Usage: $0 all"
    echo "   or: $0 <epydoc options>"
elif [[ $1 == 'all' ]]; then
    epydoc --config $config --output $apidir $apidir/../../src/robotide
else
    epydoc --config $config $@
fi
