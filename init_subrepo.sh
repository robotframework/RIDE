#!/bin/bash

less .hgsub | awk '{print $3; print $1}' | xargs hg clone
cd bundled/robotframework
less ../../.hgsubstate | awk '{print $1}' | xargs hg up
cd ../..
