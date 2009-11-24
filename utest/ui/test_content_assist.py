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

from robot.utils.asserts import assert_equals

from robotide.utils.contentassist import ContentAssistPopup

from resources import PYAPP_REFERENCE as _ # Needed to allow importing wx
import wx # Needs to be after robotide and PYAPP_REFERENCE import


class TestIsVariableRegexp(unittest.TestCase):

    def setUp(self):
        self.popup = ContentAssistPopup(wx.Frame(None))

    def test_variable_in_beginning(self):
        for comb in ['$', '@', '${', '@{', '${foo', '@{vari}']:
            assert_equals(self.popup._get_variable_start_index(comb), 0)

    def test_variable_in_the_middle(self):
        for comb, exp_ind in [('foo${', 3), ('${foo}@{bar', 6), ('${}text${', 7)]:
            assert_equals(self.popup._get_variable_start_index(comb), exp_ind)
    
    def test_no_variable_found(self):
        for comb in ['', 'foo' 'some text %']:
            assert_equals(self.popup._get_variable_start_index(comb), -1)


if __name__ == '__main__':
    unittest.main()
