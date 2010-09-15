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

from robotide.editor.editordialogs import _Dialog
from robotide.editor.fieldeditors import ValueEditor
from robotide.validators import (TestCaseNameValidator, UserKeywordNameValidator,
                                 ArgumentsValidator)


class TestCaseNameDialog(_Dialog):
    _title = 'New Test Case'

    def _add_comment_editor(self, item):
        pass

    def _create_help(self):
        pass

    def _get_editors(self, name):
        value = name or ''
        return [ValueEditor(self, value, 'Name',
                            TestCaseNameValidator(self._controller))]

    def get_name(self):
        return _Dialog.get_value(self)[0]


class UserKeywordNameDialog(_Dialog):
    _title = 'New User Keyword'

    def _add_comment_editor(self, item):
        pass

    def _create_help(self):
        pass

    def _get_editors(self, name):
        value = name or ''
        return [ValueEditor(self, value, 'Name',
                            UserKeywordNameValidator(self._controller)),
                ValueEditor(self, '', 'Arguments', ArgumentsValidator())]

    def get_name(self):
        return _Dialog.get_value(self)[0]

    def get_args(self):
        return _Dialog.get_value(self)[1]

