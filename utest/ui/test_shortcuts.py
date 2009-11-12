import unittest 

from robotide.ui.shortcuts import parse_shortcut

import wx


class TestShortcutParsing(unittest.TestCase):
    

    def test_single_character(self):
        for shortcut, expected in [('A', (wx.ACCEL_NORMAL, 65)),
                                   ('DEL', (wx.ACCEL_NORMAL, wx.WXK_DELETE)),
                                   ('DELETE', (wx.ACCEL_NORMAL, wx.WXK_DELETE))]:
            self.assertEquals(parse_shortcut(shortcut), expected)

    def test_control_key_and_one_character(self):
        for shortcut, expected in [('Ctrl-A', (wx.ACCEL_CTRL, 65)),
                                   ('Shift-DEL', (wx.ACCEL_SHIFT, wx.WXK_DELETE)),
                                   ('Alt-DELETE', (wx.ACCEL_ALT, wx.WXK_DELETE))]:
            self.assertEquals(parse_shortcut(shortcut), expected)

    def test_two_control_keys_and_one_character(self):
        for shortcut, expected in [('Ctrl-Alt-A', (wx.ACCEL_CTRL+wx.ACCEL_ALT, 65)),
                                   ('Shift-Ctrl-DEL', (wx.ACCEL_SHIFT+wx.ACCEL_CTRL, wx.WXK_DELETE)),
                                   ('Alt-Cmd-DELETE', (wx.ACCEL_ALT+wx.ACCEL_CMD, wx.WXK_DELETE))]:
            self.assertEquals(parse_shortcut(shortcut), expected)

    def test_invalid_character(self):
        self.assertRaises(AttributeError, parse_shortcut, 'FooBar')

if __name__ == '__main__':
    unittest.main()
