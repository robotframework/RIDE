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

from robotide.widgets.popupmenu import PopupMenuItems, PopupMenuItem


class Parent(object):

    def OnDoSomething(self):
        pass

    def OnDo(self):
        pass


class TestPopupMenuItems(unittest.TestCase):

    def test_initing_without_data(self):
        items = PopupMenuItems()
        assert len(items._items) == 0

    def test_initing_with_data(self):
        parent = Parent()
        items = PopupMenuItems(parent, ['Do Something', 'Do'])
        assert len(items._items) == 2

    def test_adding_data(self):
        parent = Parent()
        items = PopupMenuItems(parent, ['Do Something'])
        assert len(items._items) == 1
        items.add_menu_item(PopupMenuItem('Do', parent=parent))
        assert len(items._items) == 2
        _test = lambda: None
        items.add_menu_item(PopupMenuItem('Do', ccallable=_test))
        assert len(items._items) == 3
        assert items._items[-1].callable == _test

    def test_adding_separator(self):
        items = PopupMenuItems()
        items.add_separator()
        assert len(items._items) == 1


class TestPopupMenuItem(unittest.TestCase):

    def test_creation_with_name_and_parent(self):
        parent = Parent()
        item = PopupMenuItem('Do Something', parent=parent)
        assert item.callable == parent.OnDoSomething

    def test_creation_with_name_and_callable(self):
        def _test():
            pass
        item = PopupMenuItem('Do Something', _test)
        assert item.callable == _test

    def test_creation_with_name_shortcut_in_name(self):
        parent = Parent()
        item = PopupMenuItem('Do\tCtrl-x', parent=parent)
        assert item.name == 'Do\tCtrl-x'
        assert item.callable == parent.OnDo

    def test_creating_separator(self):
        item = PopupMenuItem('---')
        assert item.name == '---'
        assert item.callable == None


if __name__ == "__main__":
    unittest.main()
