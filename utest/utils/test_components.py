#  Copyright 2010 Nokia Siemens Networks Oyj
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

from robot.utils.asserts import assert_equals, assert_none

from robotide.utils.components import PopupMenuItems, PopupMenuItem


class Parent(object):

    def OnDoSomething(self):
        pass

    def OnDo(self):
        pass


class TestPopupMenuItems(unittest.TestCase):

    def test_initing_without_data(self):
        items = PopupMenuItems()
        assert_equals(len(items._items), 0)

    def test_initing_with_data(self):
        parent = Parent()
        items = PopupMenuItems(parent, ['Do Something', 'Do'])
        assert_equals(len(items._items), 2)

    def test_adding_data(self):
        parent = Parent()
        items = PopupMenuItems(parent, ['Do Something'])
        assert_equals(len(items._items), 1)
        items.add_menu_item(PopupMenuItem('Do', parent=parent))
        assert_equals(len(items._items), 2)
        def _test():
            pass
        items.add_menu_item(PopupMenuItem('Do', callable=_test))
        assert_equals(len(items._items), 3)
        assert_equals(items._items[-1].callable, _test)

    def test_adding_separator(self):
        items = PopupMenuItems()
        items.add_separator()
        assert_equals(len(items._items), 1)


class TestPopupMenuItem(unittest.TestCase):

    def test_creation_with_name_and_parent(self):
        parent = Parent()
        item = PopupMenuItem('Do Something', parent=parent)
        assert_equals(item.callable, parent.OnDoSomething)

    def test_creation_with_name_and_callable(self):
        def _test():
            pass
        item = PopupMenuItem('Do Something', _test)
        assert_equals(item.callable, _test)

    def test_creation_with_name_shortcut_in_name(self):
        parent = Parent()
        item = PopupMenuItem('Do\tCtrl-x', parent=parent)
        assert_equals(item.name, 'Do\tCtrl-x')
        assert_equals(item.callable, parent.OnDo)

    def test_creating_separator(self):
        item = PopupMenuItem('---')
        assert_equals(item.name, '---')
        assert_none(item.callable)


if __name__ == "__main__":
    unittest.main()