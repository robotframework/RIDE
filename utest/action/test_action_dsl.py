import unittest

from robotide.action.actioninfo import ActionInfoCollection
from nose.tools import assert_equals
from robotide.context import IS_MAC


def _check_mac(value, expected, expected_mac):
    if IS_MAC:
        assert_equals(value, expected_mac)
    else:
        assert_equals(value, expected)


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
        assert_equals(infos[0].menu_name, 'File')
        assert_equals(infos[0].name, 'Save')
        assert_equals(infos[0].action, 'save action')
        assert_equals(infos[0].shortcut.value, 'Ctrl-S')
        _check_mac(infos[0].shortcut.printable, u'Ctrl-S', u'\u2303S')

        assert_equals(infos[1].menu_name, 'File')
        assert_equals(infos[1].name, 'Huba')
        assert_equals(infos[1].action, 'huba action')
        assert_equals(infos[1].shortcut.value, None)

    def test_create_entry_with_multi_shortcut(self):
        data = """ [Hopla]
        Huba (Alt-D or CtrlCmd-H) | HubaBuba
        """
        handlers = HandlerMock(OnHuba='huba action')
        infos = ActionInfoCollection(data, handlers)
        assert_equals(infos[0].menu_name, 'Hopla')
        _check_mac(infos[0].name, u'Huba  (Alt-D or Ctrl-H)', u'Huba  (\u2325D or \u2318H)')
        assert_equals(infos[0].action, 'huba action')
        assert_equals(infos[0].shortcut.value, None)


if __name__ == "__main__":
    unittest.main()
