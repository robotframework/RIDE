#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

import os
import wx

from robotide import robotapi, utils


class _AbstractValidator(wx.Validator):
    """Implements methods to keep wxPython happy and some helper methods."""

    def Clone(self):
        return self.__class__()

    def TransferFromWindow(self):
        return True

    def TransferToWindow(self):
        return True

    def Validate(self, win):
        value = self.Window.Value
        error = self._validate(value)
        if error:
            self._show_error(error)
            return False
        return True

    def _show_error(self, message, title="Validation Error"):
        ret = wx.MessageBox(message, title, style=wx.ICON_ERROR)
        self._set_focus_to_text_control(self.Window)
        return ret

    def _set_focus_to_text_control(self, ctrl):
        ctrl.SetFocus()
        ctrl.SelectAll()


class TimeoutValidator(_AbstractValidator):

    def _validate(self, value):
        time_tokens = utils.split_value(value)
        if not time_tokens:
            return None
        timestr = time_tokens[0]
        try:
            secs = utils.timestr_to_secs(timestr)
            if secs <= 0:
                raise ValueError("Timestring must be over zero")
            time_tokens[0] = utils.secs_to_timestr(secs)
        except ValueError as err:
            if '${' not in timestr:
                return str(err)
        self._set_window_value(utils.join_value(time_tokens))
        return None

    def _set_window_value(self, value):
        self.Window.SetValue(value)


class ArgumentTypes(object):
    SCALAR, DEFAULT, LIST, DICT = range(1, 5)


class ArgumentsValidator(_AbstractValidator):

    def _validate(self, args_str):
        try:
            types = [self._get_type(arg)
                     for arg in utils.split_value(args_str)]
        except ValueError as e:
            return "Invalid argument syntax '%s'" % str(e)  # DEBUG  was arg
        return self._validate_argument_order(types)

    def _get_type(self, arg):
        if robotapi.is_scalar_var(arg):
            return ArgumentTypes.SCALAR
        elif robotapi.is_scalar_var(arg.split("=")[0]):
            return ArgumentTypes.DEFAULT
        elif robotapi.is_list_var(arg):
            return ArgumentTypes.LIST
        elif robotapi.is_dict_var(arg):
            return ArgumentTypes.DICT
        else:
            raise ValueError(arg)  # py3

    def _validate_argument_order(self, types):
        prev = ArgumentTypes.SCALAR
        for t in types:
            if t < prev:
                return ("List and scalar arguments must be before named and "
                        "dictionary arguments")
            prev = t
        return None


class NonEmptyValidator(_AbstractValidator):

    def __init__(self, field_name):
        _AbstractValidator.__init__(self)
        self._field_name = field_name

    def Clone(self):
        return self.__class__(self._field_name)

    def _validate(self, value):
        if not value:
            return "%s cannot be empty" % self._field_name
        return None


class SuiteFileNameValidator(NonEmptyValidator):

    def __init__(self, field_name, is_dir_type):
        NonEmptyValidator.__init__(self, field_name)
        self._is_dir_type = is_dir_type

    def Clone(self):
        return self.__class__(self._field_name, self._is_dir_type)

    def _validate(self, value):
        validity = NonEmptyValidator._validate(self, value)
        if not self._is_dir_type() and not validity:
            if value.lower() == '__init__':
                return "Invalid suite file name \"%s\"" % value
        return validity


class DirectoryExistsValidator(_AbstractValidator):

    def _validate(self, value):
        if not os.path.isdir(value):
            return "Chosen directory must exist"
        return None


class NewSuitePathValidator(_AbstractValidator):

    def _validate(self, value):
        path = os.path.normpath(value)
        if os.path.exists(path):
            return "Target file or directory must not exist"
        parentdir, filename = os.path.split(path)
        if "__init__" in filename:
            parentdir = os.path.dirname(parentdir)
        if not os.path.exists(parentdir):
            return "Parent directory must exist"
        return None


class _NameValidator(_AbstractValidator):

    def __init__(self, controller, orig_name=None):
        _AbstractValidator.__init__(self)
        self._controller = controller
        self._orig_name = orig_name

    def Clone(self):
        return self.__class__(self._controller, self._orig_name)

    def _validate(self, name):
        if self._orig_name is not None and utils.eq(
                name, self._orig_name, ignore=['_']):
            return ''
        return self._validation_method(name).error_message


class TestCaseNameValidator(_NameValidator):
    @property
    def _validation_method(self):
        return self._controller.validate_test_name


class UserKeywordNameValidator(_NameValidator):
    @property
    def _validation_method(self):
        return self._controller.validate_keyword_name


class ScalarVariableNameValidator(_NameValidator):
    @property
    def _validation_method(self):
        return self._controller.validate_scalar_variable_name


class ListVariableNameValidator(_NameValidator):
    @property
    def _validation_method(self):
        return self._controller.validate_list_variable_name


class DictionaryVariableNameValidator(_NameValidator):
    @property
    def _validation_method(self):
        return self._controller.validate_dict_variable_name
