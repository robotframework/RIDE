import unittest

from nose.tools import assert_equals

from robotide.widgets.popupmenu import PopupMenuItems, PopupMenuItem


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
        _test = lambda: None
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
        assert_equals(item.callable, None)


if __name__ == "__main__":
    unittest.main()
