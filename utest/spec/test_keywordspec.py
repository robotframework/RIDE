#  Copyright 2008 Nokia Siemens Networks Oyj
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
import sys
import os

from robot.utils.asserts import assert_equals, assert_true
from robotide.spec import LibrarySpec

from resources import DATAPATH
sys.path.append(os.path.join(DATAPATH, 'libs'))


class TestLibrarySpec(unittest.TestCase):

    def test_opening_standard_library(self):
        spec = LibrarySpec('OperatingSystem', '')
        assert_true(len(spec.keywords))

    def test_opening_library_with_args(self):
        spec = LibrarySpec('ArgLib', ['arg value'])
        assert_equals(len(spec.keywords), 2)

    def test_importing_library_with_name(self):
        spec = LibrarySpec('ArgLib', ['val', 'WITH NAME', 'MyLib'])
        assert_equals(len(spec.keywords), 2)

    def test_importing_library_with_mutable_objects(self):
        spec = LibrarySpec('ArgLib', [[1,2], {1:3}])
        assert_equals(len(spec.keywords), 2)


    def test_reading_library_from_pythonpath(self):
        spec = LibrarySpec('TestLib', '')
        self._assert_keyword(spec.keywords[0], 'Testlib Keyword', args=False)
        exp_doc = 'This keyword requires one argument, has one optional argument'\
                    ' and varargs.\n\nThis is some more documentation'
        self._assert_keyword(spec.keywords[1], 'Testlib Keyword With Args',
                             exp_doc, exp_doc.splitlines()[0], args=False)

    def test_reading_library_with_relative_import_from_pythonpath(self):
        spec = LibrarySpec('sub/libsi.py', '')
        assert_equals(len(spec.keywords), 1)
        self._assert_keyword(spec.keywords[0], 'Libsi Keyword', args=False)

    def test_reading_library_from_xml(self):
        spec = LibrarySpec('LibSpecLibrary', '')
        assert_equals(len(spec.keywords), 3)
        exp_doc = 'This is kw documentation.\n\nThis is more docs.'
        self._assert_keyword(spec.keywords[0], 'Normal Keyword', exp_doc,
                             exp_doc.splitlines()[0], '[ foo ]')
        self._assert_keyword(spec.keywords[1], 'Attributeless Keyword')
        self._assert_keyword(spec.keywords[2], 'Multiarg Keyword',
                             args='[ arg1 | arg2=default value | *args ]')

    def test_reading_library_from_old_style_xml(self):
        spec = LibrarySpec('OldStyleLibSpecLibrary', '')
        assert_equals(len(spec.keywords), 3)
        exp_doc = 'This is kw documentation.\n\nThis is more docs.'
        self._assert_keyword(spec.keywords[0], 'Normal Keyword', exp_doc,
                             exp_doc.splitlines()[0], '[ foo ]')
        self._assert_keyword(spec.keywords[1], 'Attributeless Keyword')
        self._assert_keyword(spec.keywords[2], 'Multiarg Keyword',
                             args='[ arg1 | arg2=default value | *args ]')

    def _assert_keyword(self, kw, name, doc='', shortdoc='', args='[  ]'):
        assert_equals(kw.name, name)
        assert_equals(kw.doc, doc, repr(kw.doc))
        assert_equals(kw.shortdoc, shortdoc)
        if args:
            assert_equals(kw.args, args)


if __name__ == '__main__':
    unittest.main()
