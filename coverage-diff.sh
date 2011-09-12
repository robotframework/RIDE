#!/bin/bash

coverage run --source src/ utest/run_utests.py
coverage annotate
hg diff -U 0 > to_be_commited.diff
python coverage_diff.py to_be_commited.diff
COVERAGE_EXIT=$?
rm `find src/ -name *.py,cover`
coverage erase
exit $COVERAGE_EXIT
