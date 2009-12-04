#!/bin/bash

start_dir=`pwd`
releasing_dir=$(dirname $0)

function commit {
    hg commit -m "$1"
    hg push
}

function update_version {
    python package.py version $1
    commit "version $1"
}

function create_tag {
    hg tag $1
    commit "$1 tag"
}

if [[ $1 == '' ]]; then
    echo "Usage: $0 <version>"
else
    cd $releasing_dir
    hg pull -u
    update_version "$1 final"
    create_tag $1
    python package.py sdist keep
    update_version trunk
    rm MANIFEST
    cd $start_dir
    echo Create Windows distribution with following commands:
    echo hg pull -u
    echo hg update $1
    echo python package.py wininst keep
    echo hg update
fi
