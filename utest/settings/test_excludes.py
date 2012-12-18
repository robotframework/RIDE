import os
from os.path import sep
import tempfile
import unittest
from robotide.preferences.excludes import Excludes

class TestExcludes(unittest.TestCase):

    def setUp(self):
        self.exclude = Excludes(directory=tempfile.gettempdir())
        self.file_path = self.exclude._exclude_file_path

    def tearDown(self):
        if hasattr(self, 'file_path') and os.path.exists(self.file_path):
            os.remove(self.file_path)

    def test_update_excludes(self):
        self.exclude.update_excludes(['foo'])
        self.assertTrue(self.exclude.contains(_join('foo', 'bar')))

    def test_update_excludes_with_separator(self):
        self.exclude.update_excludes(['foo' + sep])
        self.assertTrue(self.exclude.contains(_join('foo')))
        self.assertTrue(self.exclude.contains('foo'))

    def test_updating_excludes_does_not_repeat_path(self):
        self.exclude.update_excludes(['foo'])
        self.exclude.update_excludes(['foo' + sep])
        self.assertTrue(self.exclude.contains(_join('foo', 'bar')))
        self.assertEqual(len(self.exclude._get_excludes()), 1)

    def test_updating_excludes_does_not_repeat_almost_similar_paths(self):
        data = os.path.join('foo', 'bar')
        self.exclude.update_excludes([data])
        self.exclude.update_excludes([data + os.path.sep])
        self.assertTrue(self.exclude.contains(_join('foo', 'bar')))

    def test_contains_when_there_is_no_path(self):
        self.assertFalse(self.exclude.contains(None))

    def test_remove_path(self):
        excludes = [_join('foo'), _join('bar', 'baz'), _join('qux'), _join('quux', 'corge')]
        removed = [_join('bar', 'baz'), _join('quux', 'corge')]
        self.exclude.update_excludes(excludes)
        self.assertTrue(all([self.exclude.contains(e) for e in excludes]))
        self.exclude.remove_path(removed[0])
        self.assertFalse(self.exclude.contains(removed[0]))
        self.exclude.remove_path(removed[1])
        self.assertFalse(self.exclude.contains(removed[1]))

    def test_when_exclude_file_points_to_directory(self):
        dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(dir, 'excludes'))
        self.exclude = Excludes(dir)
        del self.file_path # not created nor used in this test
        self.assertRaises(NameError, self.exclude._get_exclude_file, 'w')

    def test_star_path_pattern(self):
        self.exclude.update_excludes([_join('foo', '*', 'bar'), _join('*', 'splat')])
        self.assertTrue(self.exclude.contains('foo/baz/bar'))
        self.assertTrue(self.exclude.contains('foo/quu/qux/bar'))
        self.assertTrue(self.exclude.contains('/corge/splat/doom.txt'))

    def test_question_mark_path_pattern(self):
        self.exclude.update_excludes([_join('foo', '?ar')])
        self.assertTrue(self.exclude.contains('foo/bar'))
        self.assertTrue(self.exclude.contains('foo/dar'))
        self.assertFalse(self.exclude.contains('foo/ggar'))

    def test_char_sequence_path_pattern(self):
        self.exclude.update_excludes([_join('foo', '[bz]ar')])
        self.assertTrue(self.exclude.contains('foo/bar'))
        self.assertTrue(self.exclude.contains('foo/zar'))
        self.assertFalse(self.exclude.contains('foo/gar'))

    def test_char_sequence_not_in_path_pattern(self):
        self.exclude.update_excludes([_join('foo', '[!bz]ar')])
        self.assertFalse(self.exclude.contains('foo/bar'))
        self.assertFalse(self.exclude.contains('foo/zar'))
        self.assertTrue(self.exclude.contains('foo/gar'))

def _join(*args):
    return os.path.join(*args) + sep
