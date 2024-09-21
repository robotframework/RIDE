#  Copyright 2023-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import pytest
import re
import unittest
from sys import version_info
from robotide.version import VERSION
from typing import Callable, Match, Pattern


""" Following code is copied from https://github.com/boromir674/semantic-version-check/ """

regex = re.compile(
    r'^(?P<major>0|[1-9]\d*)'
    r'\.'
    r'(?P<minor>0|[1-9]\d*)'
    r'(?:\.'
    r'(?P<patch>0|[1-9]\d*))?'
    r'(?P<alphabeta>[a|b][1-9])?'
    r'(?:\.'
    r'(?P<fix>0|[1-9]\d*))?'
    r'(?:-'
    r'(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
    r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
    r'(?:\+'
    r'(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
)


class RegExMatcher:
    @staticmethod
    def match(iregex: Pattern, string: str) -> Match:
        match_result = iregex.match(string)
        if not match_result:
            raise SemanticVersionFormatError(
                "Regex '{regex}' did not match string '{string}'".format(
                    regex=iregex.pattern, string=string
                )
            )
        return match_result


# Simple Adapter
class VersionCheck:
    def __init__(self, regex_matcher: Callable[[Pattern, str], Match]):
        self._regex_matcher = regex_matcher

    def __call__(self, string):
        return self._regex_matcher(regex, string)


class SemanticVersionFormatError(Exception):
    pass


# Simple callable
version_check = VersionCheck(RegExMatcher.match)


class VersionTestCase(unittest.TestCase):

    @staticmethod
    def test_version_is_string():
        assert isinstance(VERSION, str)

    @staticmethod
    @pytest.mark.skipif(version_info < (3,9,0), reason="Fails on Python < 3.9")
    def test_version_is_valid():
        clean_v = re.sub(r'dev.*$', '', VERSION)
        result = version_check(clean_v.removeprefix('v'))
        assert result


if __name__ == "__main__":
    unittest.main()
