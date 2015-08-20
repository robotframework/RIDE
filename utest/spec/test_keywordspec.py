import unittest
import sys
import os

from nose.tools import assert_equals

from resources import DATAPATH
from robotide.context import LIBRARY_XML_DIRECTORY
from robotide.spec.xmlreaders import SpecInitializer
from robotide.utils import overrides

sys.path.append(os.path.join(DATAPATH, 'libs'))


class TestLibrarySpec(unittest.TestCase):

    def _spec(self, name):
        return SpecInitializer().init_from_spec(name)

    def test_reading_library_from_xml(self):
        kws = self._spec('LibSpecLibrary')
        assert_equals(len(kws), 3)
        exp_doc = 'This is kw documentation.\n\nThis is more docs.'
        self._assert_keyword(kws[0], 'Normal Keyword', exp_doc,
                             exp_doc.splitlines()[0], '[ foo ]')
        self._assert_keyword(kws[1], 'Attributeless Keyword')
        self._assert_keyword(kws[2], 'Multiarg Keyword',
                             args='[ arg1 | arg2=default value | *args ]')

    def test_reading_library_from_old_style_xml(self):
        kws = self._spec('OldStyleLibSpecLibrary')
        assert_equals(len(kws), 3)
        exp_doc = 'This is kw documentation.\n\nThis is more docs.'
        self._assert_keyword(kws[0], 'Normal Keyword', exp_doc,
                             exp_doc.splitlines()[0], '[ foo ]')
        self._assert_keyword(kws[1], 'Attributeless Keyword')
        self._assert_keyword(kws[2], 'Multiarg Keyword',
                             args='[ arg1 | arg2=default value | *args ]')

    def _assert_keyword(self, kw, name, doc='', shortdoc='', args='[  ]'):
        assert_equals(kw.name, name)
        assert_equals(kw.doc, doc, repr(kw.doc))
        assert_equals(kw.shortdoc, shortdoc)
        if args:
            assert_equals(kw.args, args)


class MockedSpecInitializer(SpecInitializer):

    def __init__(self, directories=None, pythonpath_return_value='pythonpath',
                 directory_mapping=None):
        self._pythonpath_return_value = pythonpath_return_value
        if directory_mapping is None:
            directory_mapping = {LIBRARY_XML_DIRECTORY: 'directory'}
        self._directory_mapping = directory_mapping
        self.initialized_from_pythonpath = False
        self.initialized_from_xml_directory = False
        SpecInitializer.__init__(self, directories)

    @overrides(SpecInitializer)
    def _find_from_library_xml_directory(self, directory, name):
        assert(name == 'name')
        self.directory = directory
        return self._directory_mapping.get(directory, None)

    @overrides(SpecInitializer)
    def _find_from_pythonpath(self, name):
        assert(name == 'name')
        return self._pythonpath_return_value

    @overrides(SpecInitializer)
    def _init_from_specfile(self, specfile, name):
        if not specfile:
            return None
        self.initialized_from_pythonpath = (specfile == 'pythonpath')
        self.initialized_from_xml_directory = (specfile == 'directory')
        return 'OK'


class TestSpecInitializer(unittest.TestCase):

    def test_pythonpath_is_preferred_before_xml_directory(self):
        specinitializer = MockedSpecInitializer()
        self.assertEquals('OK', specinitializer.init_from_spec('name'))
        self.assertTrue(specinitializer.initialized_from_pythonpath)
        self.assertFalse(specinitializer.initialized_from_xml_directory)

    def test_default_directory_is_always_used(self):
        specinitializer = MockedSpecInitializer(pythonpath_return_value=None)
        self.assertEquals('OK', specinitializer.init_from_spec('name'))
        self.assertFalse(specinitializer.initialized_from_pythonpath)
        self.assertTrue(specinitializer.initialized_from_xml_directory)
        self.assertEquals(specinitializer.directory, LIBRARY_XML_DIRECTORY)

    def test_not_finding_correct_file(self):
        specinitializer = MockedSpecInitializer(
            pythonpath_return_value=None, directory_mapping={})
        self.assertEquals(None, specinitializer.init_from_spec('name'))
        self.assertFalse(specinitializer.initialized_from_pythonpath)
        self.assertFalse(specinitializer.initialized_from_xml_directory)

    def test_finding_from_given_directory(self):
        specinitializer = MockedSpecInitializer(
            directories=['my_dir'], pythonpath_return_value=None,
            directory_mapping={'my_dir': 'directory'})
        self.assertEquals('OK', specinitializer.init_from_spec('name'))
        self.assertFalse(specinitializer.initialized_from_pythonpath)
        self.assertTrue(specinitializer.initialized_from_xml_directory)
        self.assertEquals(specinitializer.directory, 'my_dir')
