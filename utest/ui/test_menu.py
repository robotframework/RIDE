import unittest
from robot.utils.asserts import assert_equals
from robotide.ui.menu import MenuBar


class MenuBarStub(MenuBar):
    def __init__(self):
        self._accelerators = []
        self._registered_names = {}

    def _get_name_with_accelerator(self, name):
        normalized = name.replace('&', '').upper()
        if normalized in self._registered_names:
            return self._registered_names[normalized]
        try:
            name = self._use_given_accelerator(name)
        except ValueError:
            name = self._generate_accelerator(name)
        self._registered_names[normalized] = name
        return name
    
    def _use_given_accelerator(self, name):
        index = name.find('&') + 1
        if 0 < index < len(name) and self._accelerator_is_free(name[index]):
            return name
        raise ValueError

    def _generate_accelerator(self, name):
        name = name.replace('&', '')
        for pos, char in enumerate(name):
            if self._accelerator_is_free(char):
                return '%s&%s' % (name[:pos], name[pos:])
        return name

    def _accelerator_is_free(self, char):
        char = char.upper()
        if char != ' ' and char not in self._accelerators:
            self._accelerators.append(char)
            return True
        return False


class TestGetNameWithAccelerator(unittest.TestCase):

    def setUp(self):
        self._mb = MenuBarStub()

    def _test(self, input, expected):
        assert_equals(self._mb._get_name_with_accelerator(input), expected)

    def test_use_first_free_char(self):
        self._test('File', '&File')
        self._test('Foo', 'F&oo')
        self._test('Foobar', 'Foo&bar')

    def test_case_insensitive(self):
        self._test('File', '&File')
        self._test('foo', 'f&oo')
        self._test('bar', '&bar')
        self._test('Barbi', 'B&arbi')

    def test_all_letters_taken(self):
        self._test('File', '&File')
        self._test('Open', '&Open')
        self._test('Foo', 'Foo')

    def test_space_is_not_used(self):
        self._test('File', '&File')
        self._test('Open', '&Open')
        self._test('Foo Bar', 'Foo &Bar')

    def test_free_given(self):
        self._test('&File', '&File')
        self._test('O&pen', 'O&pen')

    def test_non_free_given(self):
        self._test('&File', '&File')
        self._test('&Foo', 'F&oo')
        self._test('&Open', 'O&pen')
        self._test('F&oo Bar', 'Foo &Bar')
        self._test('&Fofo', 'Fofo')

    def test_get_same_acc_for_same_name(self):
        for name in 'F&ile', 'File', '&File', 'FI&LE', 'fil&e', 'file':
            self._test(name, 'F&ile')

    def test_ambersand_at_end_is_ignored(self):
        self._test('File&', '&File')
        

if __name__ == '__main__':
    unittest.main()
