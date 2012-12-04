#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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

import unittest
from robotide.testsearch.testsearch import _preprocess_input

class TestTextPreprocesser(unittest.TestCase):

    def test_adds_stars(self):
        self.assertEqual(_preprocess_input('word'), '*word*')

    def test_adds_stars_to_multiple_words(self):
        self.assertEqual(_preprocess_input('foo bar'), '*foo* *bar*')

    def test_does_nothing_to_empty_string(self):
        self.assertEqual(_preprocess_input(''), '')

    def test_adds_no_stars_if_star_is_present(self):
        self.assertEqual(_preprocess_input('foo*'), 'foo*')


if __name__ == '__main__':
    unittest.main()
