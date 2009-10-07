#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

import wx

from robotide.validators import TestCaseNameValidator, UserKeywordNameValidator


class _NameDialog(wx.TextEntryDialog):

    def __init__(self, datafile, test_or_uk=None):
        initial_value = test_or_uk and test_or_uk.name or ''
        wx.TextEntryDialog.__init__(self, None, '', self._title, initial_value)
        for child in self.GetChildren():
            if isinstance(child, wx.TextCtrl):
                if self._validator_class:
                    child.SetValidator(self._validator_class(datafile))
                self._text_ctrl = child

    def get_value(self):
        return self._text_ctrl.GetValue()


class TestCaseNameDialog(_NameDialog):
    _validator_class = TestCaseNameValidator
    _title = 'Test Case Name'


class UserKeywordNameDialog(_NameDialog):
    _validator_class = UserKeywordNameValidator
    _title = 'User Keyword Name'

