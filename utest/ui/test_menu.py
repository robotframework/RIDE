import unittest


from robot.utils.asserts import assert_equals

from robotide.ui.menu import MenuBar

class TestGetNameWithAccelerator(unittest.TestCase):

    def test_get_name_with_accelerator(self):
        menu = TestMenuBar()
        assert_equals(menu._get_name_with_accelerator('Foo'), '&Foo')
        assert_equals(menu._get_name_with_accelerator('Foo2'), 'F&oo2')
        assert_equals(menu._get_name_with_accelerator('foo3'), 'foo&3')
        assert_equals(menu._get_name_with_accelerator('fo'), 'fo')
        assert_equals(menu._get_name_with_accelerator('Open'), 'O&pen')

    def test_remove_prv_amp(self):
        menu = TestMenuBar()
        assert_equals(menu._get_name_with_accelerator('&Open'), '&Open')
        assert_equals(menu._get_name_with_accelerator('B&ar'), '&Bar')


class TestMenuBar(MenuBar):

    def __init__(self):
        self._accelerators = []