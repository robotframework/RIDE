

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

import unittest

from robotide.action.actioninfo import ActionInfoCollection
from nose.tools import assert_equal
from robotide.context import IS_MAC


def _check_mac(value, expected, expected_mac):
    if IS_MAC:
        assert_equal(value, expected_mac)
    else:
        assert_equal(value, expected)


class HandlerMock(object):

    def __init__(self, **handlers):
        self.handlers = handlers

    def __getattr__(self, name):
        return self.handlers[name]


class TestActionInfoCollection(unittest.TestCase):

    def test_create_entry(self):
        data = """ [File]
        Save | Save current suite or resource | Ctrl-S
        Huba | HubaBuba
        """
        handlers = HandlerMock(OnSave='save action', OnHuba='huba action')
        infos = ActionInfoCollection(data, handlers)
        assert_equal(infos[0].menu_name, 'File')
        assert_equal(infos[0].name, 'Save')
        assert_equal(infos[0].action, 'save action')
        assert_equal(infos[0].shortcut.value, 'Ctrl-S')
        _check_mac(infos[0].shortcut.printable, u'Ctrl-S', u'\u2303S')

        assert_equal(infos[1].menu_name, 'File')
        assert_equal(infos[1].name, 'Huba')
        assert_equal(infos[1].action, 'huba action')
        assert_equal(infos[1].shortcut.value, None)

    def test_create_entry_with_multi_shortcut(self):
        data = """ [Hopla]
        Huba (Alt-D or CtrlCmd-H) | HubaBuba
        """
        handlers = HandlerMock(OnHuba='huba action')
        infos = ActionInfoCollection(data, handlers)
        assert_equal(infos[0].menu_name, 'Hopla')
        _check_mac(infos[0].name, u'Huba  (Alt-D or Ctrl-H)', u'Huba  (\u2325D or \u2318H)')
        assert_equal(infos[0].action, 'huba action')
        assert_equal(infos[0].shortcut.value, None)


if __name__ == "__main__":
    unittest.main()
