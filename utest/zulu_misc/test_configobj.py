# coding=utf-8
#  Copyright 2024-     Robot Framework Foundation
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

# This file was copied and modified from https://github.com/DiffSK/configobj tests

from __future__ import unicode_literals
import os
import re

from codecs import BOM_UTF8
from warnings import catch_warnings
from tempfile import NamedTemporaryFile

import pytest
import io

import configobj as co
from configobj import ConfigObj, flatten_errors, ReloadError, DuplicateError, MissingInterpolationOption, InterpolationLoopError, ConfigObjError
from configobj.validate import Validator, VdtValueTooSmallError


def cfg_lines(config_string_representation):
    """
    :param config_string_representation: string representation of a config
        file (typically a triple-quoted string)
    :type config_string_representation: str or unicode
    :return: a list of lines of that config. Whitespace on the left will be
        trimmed based on the indentation level to make it a bit saner to assert
        content of a particular line
    :rtype: str or unicode
    """
    lines = config_string_representation.splitlines()

    for idx, line in enumerate(lines):
        if line.strip():
            line_no_with_content = idx
            break
    else:
        raise ValueError('no content in provided config file: '
                         '{!r}'.format(config_string_representation))

    first_content = lines[line_no_with_content]
    if isinstance(first_content, bytes):
        first_content = first_content.decode('utf-8')
    ws_chars = len(re.search(r'^(\s*)', first_content).group(1))

    def yield_stringified_line():
        for line in lines:
            if isinstance(line, bytes):
                yield line.decode('utf-8')
            else:
                yield line


    return [re.sub(r'^\s{0,%s}' % ws_chars, '', line).encode('utf-8')
            for line in yield_stringified_line()]


@pytest.fixture
def cfg_contents(request):

    def make_file_with_contents_and_return_name(config_string_representation):
        """
        :param config_string_representation: string representation of a config
            file (typically a triple-quoted string)
        :type config_string_representation: str or unicode
        :return: a list of lines of that config. Whitespace on the left will be
            trimmed based on the indentation level to make it a bit saner to assert
            content of a particular line
        :rtype: basestring
        """

        lines = cfg_lines(config_string_representation)

        with NamedTemporaryFile(delete=False, mode='wb') as cfg_file:
            for line in lines:
                if isinstance(line, bytes):
                    cfg_file.write(line + os.linesep.encode('utf-8'))
                else:
                    cfg_file.write((line + os.linesep).encode('utf-8'))
        request.addfinalizer(lambda : os.unlink(cfg_file.name))

        return cfg_file.name

    return make_file_with_contents_and_return_name


def test_order_preserved():
    c = ConfigObj()
    c['a'] = 1
    c['b'] = 2
    c['c'] = 3
    c['section'] = {}
    c['section']['a'] = 1
    c['section']['b'] = 2
    c['section']['c'] = 3
    c['section']['section'] = {}
    c['section']['section2'] = {}
    c['section']['section3'] = {}
    c['section2'] = {}
    c['section3'] = {}

    c2 = ConfigObj(c)
    assert c2.scalars == ['a', 'b', 'c']
    assert c2.sections == ['section', 'section2', 'section3']
    assert c2['section'].scalars == ['a', 'b', 'c']
    assert c2['section'].sections == ['section', 'section2', 'section3']

    assert c['section'] is not c2['section']
    assert c['section']['section'] is not c2['section']['section']


"""" Test always fails in our setup
def test_options_deprecation():
    with catch_warnings(record=True) as log:
        ConfigObj(options={})

    # unpack the only member of log
    try:
        warning, = log
    except ValueError:
        assert len(log) == 1

    assert warning.category == DeprecationWarning
"""

def test_list_members():
    c = ConfigObj()
    c['a'] = []
    c['a'].append('foo')
    assert c['a'] == ['foo']


def test_list_interpolation_with_pop():
    c = ConfigObj()
    c['a'] = []
    c['a'].append('%(b)s')
    c['b'] = 'bar'
    assert c.pop('a') == ['bar']


def test_with_default():
    c = ConfigObj()
    c['a'] = 3

    assert c.pop('a') == 3
    assert c.pop('b', 3) == 3
    with pytest.raises(KeyError):
        c.pop('c')


def test_interpolation_with_section_names(cfg_contents):
    cfg = cfg_contents("""
item1 = 1234
[section]
    [[item1]]
    foo='bar'
    [[DEFAULT]]
        [[[item1]]]
        why = would you do this?
    [[other-subsection]]
    item2 = '$item1'""")
    c = ConfigObj(cfg, interpolation='Template')

    # This raises an exception in 4.7.1 and earlier due to the section
    # being found as the interpolation value
    repr(c)


def test_interoplation_repr():
    c = ConfigObj(['foo = $bar'], interpolation='Template')
    c['baz'] = {}
    c['baz']['spam'] = '%(bar)s'

    # This raises a MissingInterpolationOption exception in 4.7.1 and earlier
    repr(c)


class TestEncoding(object):
    @pytest.fixture
    def ant_cfg(self):
        return """
        [tags]
            [[bug]]
                translated = \U0001f41c
        """

    #issue #18
    def test_unicode_conversion_when_encoding_is_set(self, cfg_contents):
        cfg = cfg_contents(b"test = some string")

        c = ConfigObj(cfg, encoding='utf8')

        assert isinstance(c['test'], str)


    #issue #18
    def test_no_unicode_conversion_when_encoding_is_omitted(self, cfg_contents):
        cfg = cfg_contents(b"test = some string")

        c = ConfigObj(cfg)
        assert isinstance(c['test'], str)

    #issue #44
    def test_that_encoding_using_list_of_strings(self):
        cfg = [b'test = \xf0\x9f\x90\x9c']

        c = ConfigObj(cfg, encoding='utf8')

        assert isinstance(c['test'], str)

        assert c['test'] == '\U0001f41c'

    #issue #44
    def test_encoding_in_subsections(self, ant_cfg, cfg_contents):
        c = cfg_contents(ant_cfg)
        cfg = ConfigObj(c, encoding='utf-8')

        assert isinstance(cfg['tags']['bug']['translated'], str)

    #issue #44 and #55
    def test_encoding_in_config_files(self, request, ant_cfg):
        # the cfg_contents fixture is doing this too, but be explicit
        with NamedTemporaryFile(delete=False, mode='wb') as cfg_file:
            cfg_file.write(ant_cfg.encode('utf-8'))
        request.addfinalizer(lambda : os.unlink(cfg_file.name))

        cfg = ConfigObj(cfg_file.name, encoding='utf-8')
        assert isinstance(cfg['tags']['bug']['translated'], str)
        cfg.write()

@pytest.fixture
def testconfig1():
    """
    copied from the main doctest
    """
    return """\
    key1= val    # comment 1
    key2= val    # comment 2
    # comment 3
    [lev1a]     # comment 4
    key1= val    # comment 5
    key2= val    # comment 6
    # comment 7
    [lev1b]    # comment 8
    key1= val    # comment 9
    key2= val    # comment 10
    # comment 11
        [[lev2ba]]    # comment 12
        key1= val    # comment 13
        # comment 14
        [[lev2bb]]    # comment 15
        key1= val    # comment 16
    # comment 17
    [lev1c]    # comment 18
    # comment 19
        [[lev2c]]    # comment 20
        # comment 21
            [[[lev3c]]]    # comment 22
            key1 = val    # comment 23"""


@pytest.fixture
def testconfig2():
    return """\
        key1 = 'val1'
        key2 =   "val2"
        key3 = val3
        ["section 1"] # comment
        keys11 = val1
        keys12 = val2
        keys13 = val3
        [section 2]
        keys21 = val1
        keys22 = val2
        keys23 = val3

            [['section 2 sub 1']]
            fish = 3
    """


@pytest.fixture
def testconfig6():
    return b'''
        name1 = """ a single line value """ # comment
        name2 = \''' another single line value \''' # comment
        name3 = """ a single line value """
        name4 = \''' another single line value \'''
        [ "multi section" ]
        name1 = """
        Well, this is a
        multiline value
        """
        name2 = \'''
        Well, this is a
        multiline value
        \'''
        name3 = """
        Well, this is a
        multiline value
        """     # a comment
        name4 = \'''
        Well, this is a
        multiline value
        \'''  # I guess this is a comment too
    '''


@pytest.fixture
def a(testconfig1, cfg_contents):
    """
    also copied from main doc tests
    """
    return ConfigObj(cfg_contents(testconfig1), raise_errors=True)


@pytest.fixture
def b(testconfig2, cfg_contents):
    """
    also copied from main doc tests
    """
    return ConfigObj(cfg_contents(testconfig2), raise_errors=True)


@pytest.fixture
def i(testconfig6, cfg_contents):
    """
    also copied from main doc tests
    """
    return ConfigObj(cfg_contents(testconfig6), raise_errors=True)


def test_configobj_dict_representation(a, b, cfg_contents):

    assert a.depth == 0
    assert a == {
        'key2': 'val',
        'key1': 'val',
        'lev1c': {
            'lev2c': {
                'lev3c': {
                    'key1': 'val',
                    },
                },
            },
        'lev1b': {
            'key2': 'val',
            'key1': 'val',
            'lev2ba': {
                'key1': 'val',
                },
            'lev2bb': {
                'key1': 'val',
                },
            },
        'lev1a': {
            'key2': 'val',
            'key1': 'val',
            },
        }
    
    assert b.depth == 0
    assert b == {
        'key3': 'val3',
        'key2': 'val2',
        'key1': 'val1',
        'section 1': {
            'keys11': 'val1',
            'keys13': 'val3',
            'keys12': 'val2',
            },
        'section 2': {
            'section 2 sub 1': {
                'fish': '3',
                },
            'keys21': 'val1',
            'keys22': 'val2',
            'keys23': 'val3',
            },
        }

    t = cfg_lines("""
        'a' = b # !"$%^&*(),::;'@~#= 33
        "b" = b #= 6, 33
    """)
    t2 = ConfigObj(t)
    assert t2 == {'a': 'b', 'b': 'b'}
    t2.inline_comments['b'] = ''
    del t2['a']
    assert t2.write() == ['','b = b', '']


def test_behavior_when_list_values_is_false():
    c = '''
       key1 = no quotes
       key2 = 'single quotes'
       key3 = "double quotes"
       key4 = "list", 'with', several, "quotes"
       '''
    cfg = ConfigObj(cfg_lines(c), list_values=False)
    assert cfg == {
        'key1': 'no quotes',
        'key2': "'single quotes'",
        'key3': '"double quotes"',
        'key4': '"list", \'with\', several, "quotes"'
    }

    cfg2 = ConfigObj(list_values=False)
    cfg2['key1'] = 'Multiline\nValue'
    cfg2['key2'] = '''"Value" with 'quotes' !'''
    assert cfg2.write() == [
        "key1 = '''Multiline\nValue'''",
        'key2 = "Value" with \'quotes\' !'
    ]

    cfg2.list_values = True
    assert cfg2.write() == [
        "key1 = '''Multiline\nValue'''",
        'key2 = \'\'\'"Value" with \'quotes\' !\'\'\''
    ]


def test_flatten_errors(val, cfg_contents):
    config = cfg_contents("""
       test1=40
       test2=hello
       test3=3
       test4=5.0
       [section]
           test1=40
           test2=hello
           test3=3
           test4=5.0
           [[sub section]]
               test1=40
               test2=hello
               test3=3
               test4=5.0
    """)
    configspec = cfg_contents("""
       test1= integer(30,50)
       test2= string
       test3=integer
       test4=float(6.0)
       [section]
           test1=integer(30,50)
           test2=string
           test3=integer
           test4=float(6.0)
           [[sub section]]
               test1=integer(30,50)
               test2=string
               test3=integer
               test4=float(6.0)
       """)
    c1 = ConfigObj(config, configspec=configspec)
    res = c1.validate(val)
    assert flatten_errors(c1, res) == [([], 'test4', False), (['section'], 'test4', False), (['section', 'sub section'], 'test4', False)]
    res = c1.validate(val, preserve_errors=True)
    check = flatten_errors(c1, res)
    assert check[0][:2] == ([], 'test4')
    assert check[1][:2] == (['section'], 'test4')
    assert check[2][:2] == (['section', 'sub section'], 'test4')
    for entry in check:
        assert isinstance(entry[2], VdtValueTooSmallError)
        assert str(entry[2]) == 'the value "5.0" is too small.'


def test_unicode_handling():
    u_base = '''
    # initial comment
       # inital comment 2
    test1 = some value
    # comment
    test2 = another value    # inline comment
    # section comment
    [section]    # inline comment
       test = test    # another inline comment
       test2 = test2
    # final comment
    # final comment2
    '''

    # needing to keep line endings means this isn't a good candidate
    # for the cfg_lines utility method
    u = u_base.encode('utf_8').splitlines(True)
    u[0] = BOM_UTF8 + u[0]
    uc = ConfigObj(u)
    uc.encoding = None
    assert uc.BOM
    assert uc == {'test1': 'some value', 'test2': 'another value',
                  'section': {'test': 'test', 'test2': 'test2'}}
    uc = ConfigObj(u, encoding='utf_8', default_encoding='latin-1')
    assert uc.BOM
    assert isinstance(uc['test1'], str)
    assert uc.encoding == 'utf_8'
    assert uc.newlines == '\n'
    assert len(uc.write()) == 13
    uc['latin1'] = "This costs lot's of "
    a_list = uc.write()
    assert 'latin1' in str(a_list)
    assert len(a_list) == 14
    assert isinstance(a_list[0], bytes)
    assert a_list[0].startswith(BOM_UTF8)

    u = u_base.replace('\n', '\r\n').encode('utf-8').splitlines(True)
    uc = ConfigObj(u)
    assert uc.newlines == '\r\n'
    uc.newlines = '\r'
    file_like = io.BytesIO()
    uc.write(file_like)
    file_like.seek(0)
    uc2 = ConfigObj(file_like)
    assert uc2 == uc
    assert uc2.filename == None
    assert uc2.newlines == '\r'


class TestWritingConfigs(object):
    def test_validate(self, val):
        spec = [
            '# Initial Comment',
            '',
            'key1 = string(default=Hello)',
            '',
            '# section comment',
            '[section] # inline comment',
            '# key1 comment',
            'key1 = integer(default=6)',
            '# key2 comment',
            'key2 = boolean(default=True)',
            '# subsection comment',
            '[[sub-section]] # inline comment',
            '# another key1 comment',
            'key1 = float(default=3.0)'
        ]
        blank_config = ConfigObj(configspec=spec)
        assert blank_config.validate(val, copy=True)
        assert blank_config.dict() == {
            'key1': 'Hello',
            'section': {'key1': 6, 'key2': True, 'sub-section': {'key1': 3.0}}
        }
        assert blank_config.write() == [
            '# Initial Comment',
            '',
            'key1 = Hello',
            '',
            '# section comment',
            '[section]# inline comment',
            '# key1 comment',
            'key1 = 6',
            '# key2 comment',
            'key2 = True',
            '# subsection comment',
            '[[sub-section]]# inline comment',
            '# another key1 comment',
            'key1 = 3.0'
        ]

    def test_writing_empty_values(self):
        config_with_empty_values = [
            '',
            'key1 =',
            'key2 =# a comment',
        ]
        cfg = ConfigObj(config_with_empty_values)
        assert cfg.write() == ['', 'key1 = ""', 'key2 = ""# a comment']
        cfg.write_empty_values = True
        assert cfg.write() == ['', 'key1 = ', 'key2 = # a comment']


class TestUnrepr(object):
    def test_in_reading(self):
        config_to_be_unreprd = cfg_lines("""
            key1 = (1, 2, 3)    # comment
            key2 = True
            key3 = 'a string'
            key4 = [1, 2, 3, 'a mixed list']
        """)
        cfg = ConfigObj(config_to_be_unreprd, unrepr=True)
        assert cfg == {
            'key1': (1, 2, 3),
            'key2': True,
            'key3': 'a string',
            'key4': [1, 2, 3, 'a mixed list']
        }

        assert cfg == ConfigObj(cfg.write(), unrepr=True)

    def test_in_multiline_values(self, cfg_contents):
        config_with_multiline_value = cfg_contents('''
        k = \"""{
            'k1': 3,
            'k2': 6.0}\"""
        ''')
        cfg = ConfigObj(config_with_multiline_value, unrepr=True)
        assert cfg == {'k': {'k1': 3, 'k2': 6.0}}

    def test_with_a_dictionary(self):
        config_with_dict_value = ['k = {"a": 1}']
        cfg = ConfigObj(config_with_dict_value, unrepr=True)
        assert isinstance(cfg['k'], dict)

    def test_with_hash(self):
        config_with_a_hash_in_a_list = [
            'key1 = (1, 2, 3)    # comment',
            'key2 = True',
            "key3 = 'a string'",
            "key4 = [1, 2, 3, 'a mixed list#']"
        ]
        cfg = ConfigObj(config_with_a_hash_in_a_list, unrepr=True)
        assert cfg == {
            'key1': (1, 2, 3),
            'key2': True,
            'key3': 'a string',
            'key4': [1, 2, 3, 'a mixed list#']
        }


class TestValueErrors(object):
    def test_bool(self, empty_cfg):
        empty_cfg['a'] = 'fish'
        with pytest.raises(ValueError) as excinfo:
            empty_cfg.as_bool('a')
        assert str(excinfo.value) == 'Value "fish" is neither True nor False'
        empty_cfg['b'] = 'True'
        assert empty_cfg.as_bool('b') is True
        empty_cfg['b'] = 'off'
        assert empty_cfg.as_bool('b') is False

    def test_int(self, empty_cfg):
        for bad in ('fish', '3.2'):
            empty_cfg['a'] = bad
            with pytest.raises(ValueError) as excinfo:
                empty_cfg.as_int('a')
            assert str(excinfo.value).startswith('invalid literal for int()')

        empty_cfg['b'] = '1'
        assert empty_cfg.as_bool('b') is True
        empty_cfg['b'] = '3.2'

    def test_float(self, empty_cfg):
        empty_cfg['a'] = 'fish'
        with pytest.raises(ValueError):
            empty_cfg.as_float('a')

        empty_cfg['b'] = '1'
        assert empty_cfg.as_float('b') == 1
        empty_cfg['b'] = '3.2'
        assert empty_cfg.as_float('b') == 3.2



def test_error_types():
    # errors that don't have interesting messages
    test_value = 'what'
    for ErrorClass in (co.ConfigObjError, co.NestingError, co.ParseError,
                       co.DuplicateError, co.ConfigspecError,
                       co.RepeatSectionError):
        with pytest.raises(ErrorClass) as excinfo:
            # TODO: assert more interesting things
            # now that we're not using doctest
            raise ErrorClass(test_value)
        assert str(excinfo.value) == test_value

    for ErrorClassWithMessage, msg in (
        (co.InterpolationLoopError,
         'interpolation loop detected in value "{0}".'),
        (co.MissingInterpolationOption,
         'missing option "{0}" in interpolation.'),
    ):
        with pytest.raises(ErrorClassWithMessage) as excinfo:
            raise ErrorClassWithMessage(test_value)
        assert str(excinfo.value) == msg.format(test_value)

    # ReloadError is raised as IOError
    with pytest.raises(IOError):
        raise co.ReloadError()


class TestSectionBehavior(object):
    def test_dictionary_representation(self, a):

        n = a.dict()
        assert n == a
        assert n is not a

    def test_merging(self, cfg_contents):
        config_with_subsection = cfg_contents("""
            [section1]
            option1 = True
            [[subsection]]
            more_options = False
            # end of file
        """)
        config_that_overwrites_parameter = cfg_contents("""
            # File is user.ini
            [section1]
            option1 = False
            # end of file
        """)
        c1 = ConfigObj(config_that_overwrites_parameter)
        c2 = ConfigObj(config_with_subsection)
        c2.merge(c1)
        assert c2.dict() == {'section1': {'option1': 'False', 'subsection': {'more_options': 'False'}}}

    def test_walking_with_in_place_updates(self, cfg_contents):
            config = cfg_contents("""
                [XXXXsection]
                XXXXkey = XXXXvalue
            """)
            cfg = ConfigObj(config)
            assert cfg.dict() == {'XXXXsection': {'XXXXkey': 'XXXXvalue'}}
            def transform(section, key):
                val = section[key]
                newkey = key.replace('XXXX', 'CLIENT1')
                section.rename(key, newkey)
                if isinstance(val, str):
                    val = val.replace('XXXX', 'CLIENT1')
                    section[newkey] = val

            assert cfg.walk(transform, call_on_sections=True) == {
                'CLIENT1section': {'CLIENT1key': None}
            }
            assert cfg.dict() == {
                'CLIENT1section': {'CLIENT1key': 'CLIENT1value'}
            }


def test_reset_a_configobj():

    something = object()
    cfg = ConfigObj()
    cfg['something'] = something
    cfg['section'] = {'something': something}
    cfg.filename = 'fish'
    cfg.raise_errors = something
    cfg.list_values = something
    cfg.create_empty = something
    cfg.file_error = something
    cfg.stringify = something
    cfg.indent_type = something
    cfg.encoding = something
    cfg.default_encoding = something
    cfg.BOM = something
    cfg.newlines = something
    cfg.write_empty_values = something
    cfg.unrepr = something
    cfg.initial_comment = something
    cfg.final_comment = something
    cfg.configspec = something
    cfg.inline_comments = something
    cfg.comments = something
    cfg.defaults = something
    cfg.default_values = something
    cfg.reset()
    
    assert cfg.filename is None
    assert cfg.raise_errors is False
    assert cfg.list_values is True
    assert cfg.create_empty is False
    assert cfg.file_error is False
    assert cfg.interpolation is True
    assert cfg.configspec is None
    assert cfg.stringify is True
    assert cfg.indent_type is None
    assert cfg.encoding is None
    assert cfg.default_encoding is None
    assert cfg.unrepr is False
    assert cfg.write_empty_values is False
    assert cfg.inline_comments == {}
    assert cfg.comments == {}
    assert cfg.defaults == []
    assert cfg.default_values == {}
    assert cfg == ConfigObj()
    assert repr(cfg) == 'ConfigObj({})'


class TestReloading(object):
    @pytest.fixture
    def reloadable_cfg_content(self):
        content = '''
                test1=40
                test2=hello
                test3=3
                test4=5.0
                [section]
                    test1=40
                    test2=hello
                    test3=3
                    test4=5.0
                    [[sub section]]
                        test1=40
                        test2=hello
                        test3=3
                        test4=5.0
                [section2]
                    test1=40
                    test2=hello
                    test3=3
                    test4=5.0
            '''
        return content

    def test_handle_no_filename(self):
        for bad_args in ([io.BytesIO()], [], [[]]):
            cfg = ConfigObj(*bad_args)
            with pytest.raises(ReloadError) as excinfo:
                cfg.reload()
            assert str(excinfo.value) == 'reload failed, filename is not set.'

    def test_reloading_with_an_actual_file(self, request,
                                           reloadable_cfg_content,
                                           cfg_contents):

        with NamedTemporaryFile(delete=False, mode='wb') as cfg_file:
            cfg_file.write(reloadable_cfg_content.encode('utf-8'))
        request.addfinalizer(lambda : os.unlink(cfg_file.name))

        configspec = cfg_contents("""
            test1= integer(30,50)
            test2= string
            test3=integer
            test4=float(4.5)
            [section]
                test1=integer(30,50)
                test2=string
                test3=integer
                test4=float(4.5)
                [[sub section]]
                    test1=integer(30,50)
                    test2=string
                    test3=integer
                    test4=float(4.5)
            [section2]
                test1=integer(30,50)
                test2=string
                test3=integer
                test4=float(4.5)
            """)

        cfg = ConfigObj(cfg_file.name, configspec=configspec)
        cfg.configspec['test1'] = 'integer(50,60)'
        backup = ConfigObj(cfg_file.name)
        del cfg['section']
        del cfg['test1']
        cfg['extra'] = '3'
        cfg['section2']['extra'] = '3'
        cfg.reload()
        assert cfg == backup
        assert cfg.validate(Validator())


class TestDuplicates(object):
    def test_duplicate_section(self):
        cfg = '''
        [hello]
        member = value
        [hello again]
        member = value
        [ "hello" ]
        member = value
        '''
        with pytest.raises(DuplicateError) as excinfo:
            ConfigObj(cfg.splitlines(), raise_errors=True)
        assert str(excinfo.value) == 'Duplicate section name at line 6.'
    
    def test_duplicate_members(self):
        d = '''
        [hello]
        member=value
        [helloagain]
        member1=value
        member2=value
        'member1'=value
        ["andagain"]
        member=value
        '''
        with pytest.raises(DuplicateError) as excinfo:
            ConfigObj(d.splitlines(),raise_errors=True)
        assert str(excinfo.value) == 'Duplicate keyword name at line 7.'


class TestInterpolation(object):
    """
    tests various interpolation behaviors using config par
    """
    @pytest.fixture
    def config_parser_cfg(self):
        cfg = ConfigObj()
        cfg['DEFAULT'] = {
            'b': 'goodbye',
            'userdir': r'c:\\home',
            'c': '%(d)s',
            'd': '%(c)s'
        }
        cfg['section'] = {
            'a': r'%(datadir)s\\some path\\file.py',
            'b': r'%(userdir)s\\some path\\file.py',
            'c': 'Yo %(a)s',
            'd': '%(not_here)s',
            'e': '%(e)s',
        }
        cfg['section']['DEFAULT'] = {
            'datadir': r'c:\\silly_test',
            'a': 'hello - %(b)s',
        }
        return cfg

    @pytest.fixture
    def template_cfg(self, cfg_contents):
        interp_cfg = '''
        [DEFAULT]
        keyword1 = value1
        'keyword 2' = 'value 2'
        reference = ${keyword1}
        foo = 123

        [ section ]
        templatebare = $keyword1/foo
        bar = $$foo
        dollar = $$300.00
        stophere = $$notinterpolated
        with_braces = ${keyword1}s (plural)
        with_spaces = ${keyword 2}!!!
        with_several = $keyword1/$reference/$keyword1
        configparsersample = %(keyword 2)sconfig
        deep = ${reference}

            [[DEFAULT]]
            baz = $foo

            [[ sub-section ]]
            quux = '$baz + $bar + $foo'

                [[[ sub-sub-section ]]]
                convoluted = "$bar + $baz + $quux + $bar"
        '''
        return ConfigObj(cfg_contents(interp_cfg), interpolation='Template')

    def test_interpolation(self, config_parser_cfg):
        test_section = config_parser_cfg['section']
        assert test_section['a'] == r'c:\\silly_test\\some path\\file.py'
        assert test_section['b'] == r'c:\\home\\some path\\file.py'
        assert test_section['c'] == r'Yo c:\\silly_test\\some path\\file.py'

    def test_interpolation_turned_off(self, config_parser_cfg):
        config_parser_cfg.interpolation = False
        test_section = config_parser_cfg['section']
        assert test_section['a'] == r'%(datadir)s\\some path\\file.py'
        assert test_section['b'] == r'%(userdir)s\\some path\\file.py'
        assert test_section['c'] == r'Yo %(a)s'

    def test_handle_errors(self, config_parser_cfg):

        with pytest.raises(MissingInterpolationOption) as excinfo:
            print(config_parser_cfg['section']['d'])
        assert (str(excinfo.value) ==
                'missing option "not_here" in interpolation.')

        with pytest.raises(InterpolationLoopError) as excinfo:
            print(config_parser_cfg['section']['e'])
        assert (str(excinfo.value) ==
                'interpolation loop detected in value "e".')

    def test_template_interpolation(self, template_cfg):
        test_sec = template_cfg['section']
        assert test_sec['templatebare'] == 'value1/foo'
        assert test_sec['dollar'] == '$300.00'
        assert test_sec['stophere'] == '$notinterpolated'
        assert test_sec['with_braces'] == 'value1s (plural)'
        assert test_sec['with_spaces'] == 'value 2!!!'
        assert test_sec['with_several'] == 'value1/value1/value1'
        assert test_sec['configparsersample'] == '%(keyword 2)sconfig'
        assert test_sec['deep'] == 'value1'
        assert test_sec['sub-section']['quux'] == '123 + $foo + 123'
        assert (test_sec['sub-section']['sub-sub-section']['convoluted'] ==
                '$foo + 123 + 123 + $foo + 123 + $foo')


class TestQuotes(object):
    """
    tests what happens whn dealing with quotes
    """
    def assert_bad_quote_message(self, empty_cfg, to_quote, **kwargs):
        #TODO: this should be use repr instead of str
        message = 'Value "{0}" cannot be safely quoted.'
        with pytest.raises(ConfigObjError) as excinfo:
            empty_cfg._quote(to_quote, **kwargs)
        assert str(excinfo.value) == message.format(to_quote)

    def test_handle_unbalanced(self, i):
        self.assert_bad_quote_message(i, '"""\'\'\'')

    def test_handle_unallowed_newline(self, i):
        newline = '\n'
        self.assert_bad_quote_message(i, newline, multiline=False)

    def test_handle_unallowed_open_quote(self, i):
        open_quote = ' "\' '
        self.assert_bad_quote_message(i, open_quote, multiline=False)
        
    def test_handle_multiple_bad_quote_values(self):
        testconfig5 = '''
        config = "hello   # comment
        test = 'goodbye
        fish = 'goodbye   # comment
        dummy = "hello again
        '''
        with pytest.raises(ConfigObjError) as excinfo:
            ConfigObj(testconfig5.splitlines())
        assert len(excinfo.value.errors) == 4



def test_handle_stringify_off():
    c = ConfigObj()
    c.stringify = False

    with pytest.raises(TypeError) as excinfo:
        c['test'] = 1
    assert str(excinfo.value) == 'Value is not a string "1".'


class TestValues(object):
    """
    Tests specifics about behaviors with types of values
    """
    @pytest.fixture
    def testconfig3(self, cfg_contents):
        return cfg_contents("""
            a = ,
            b = test,
            c = test1, test2   , test3
            d = test1, test2, test3,
        """)

    def test_empty_values(self, cfg_contents):
        cfg_with_empty = cfg_contents("""
        k =
        k2 =# comment test
        val = test
        val2 = ,
        val3 = 1,
        val4 = 1, 2
        val5 = 1, 2, """)
        cwe = ConfigObj(cfg_with_empty)
        # see a comma? it's a list
        assert cwe == {'k': '', 'k2': '', 'val': 'test', 'val2': [],
                       'val3': ['1'], 'val4': ['1', '2'], 'val5': ['1', '2']}
        # not any more
        cwe = ConfigObj(cfg_with_empty, list_values=False)
        assert cwe == {'k': '', 'k2': '', 'val': 'test', 'val2': ',',
                       'val3': '1,', 'val4': '1, 2', 'val5': '1, 2,'}

    def test_list_values(self, testconfig3):
        cfg = ConfigObj(testconfig3, raise_errors=True)
        assert cfg['a'] == []
        assert cfg['b'] == ['test']
        assert cfg['c'] == ['test1', 'test2', 'test3']
        assert cfg['d'] == ['test1', 'test2', 'test3']

    def test_list_values_off(self, testconfig3):
        cfg = ConfigObj(testconfig3, raise_errors=True, list_values=False)
        assert cfg['a'] == ','
        assert cfg['b'] == 'test,'
        assert cfg['c'] == 'test1, test2   , test3'
        assert cfg['d'] == 'test1, test2, test3,'
        
    def test_handle_multiple_list_value_errors(self):
        testconfig4 = '''
        config = 3,4,,
        test = 3,,4
        fish = ,,
        dummy = ,,hello, goodbye
        '''
        with pytest.raises(ConfigObjError) as excinfo:
            ConfigObj(testconfig4.splitlines())
        assert len(excinfo.value.errors) == 4

        
        
def test_creating_with_a_dictionary():
    dictionary_cfg_content = {
        'key1': 'val1',
        'key2': 'val2',
        'section 1': {
            'key1': 'val1',
            'key2': 'val2',
            'section 1b': {
                'key1': 'val1',
                'key2': 'val2',
            },
        },
        'section 2': {
            'key1': 'val1',
            'key2': 'val2',
            'section 2b': {
                'key1': 'val1',
                'key2': 'val2',
            },
        },
        'key3': 'val3',
    }
    cfg = ConfigObj(dictionary_cfg_content)
    assert dictionary_cfg_content == cfg
    assert dictionary_cfg_content is not cfg
    assert dictionary_cfg_content == cfg.dict()
    assert dictionary_cfg_content is not cfg.dict()


class TestComments(object):
    @pytest.fixture
    def comment_filled_cfg(self, cfg_contents):
        return cfg_contents("""
            # initial comments
            # with two lines
            key = "value"
            # section comment
            [section] # inline section comment
            # key comment
            key = "value"

            # final comment
            # with two lines"""
        )

    def test_multiline_comments(self, i):

        expected_multiline_value = '\nWell, this is a\nmultiline value\n'
        assert i == {
            'name4': ' another single line value ',
            'multi section': {
                'name4': expected_multiline_value,
                'name2': expected_multiline_value,
                'name3': expected_multiline_value,
                'name1': expected_multiline_value,
            },
            'name2': ' another single line value ',
            'name3': ' a single line value ',
            'name1': ' a single line value ',
        }

    def test_starting_and_ending_comments(self, a, testconfig1, cfg_contents):

        filename = a.filename
        a.filename = None
        values = a.write()
        index = 0
        while index < 23:
            index += 1
            line = values[index-1]
            assert line.endswith('# comment ' + str(index))
        a.filename = filename

        start_comment = ['# Initial Comment', '', '#']
        end_comment = ['', '#', '# Final Comment']
        newconfig = start_comment + testconfig1.splitlines() + end_comment
        nc = ConfigObj(newconfig)
        assert nc.initial_comment == ['# Initial Comment', '', '#']
        assert nc.final_comment == ['', '#', '# Final Comment']
        assert nc.initial_comment == start_comment
        assert nc.final_comment == end_comment

    def test_inline_comments(self):
        c = ConfigObj()
        c['foo'] = 'bar'
        c.inline_comments['foo'] = 'Nice bar'
        assert c.write() == ['foo = bar # Nice bar']

    def test_unrepr_comments(self, comment_filled_cfg):
        c = ConfigObj(comment_filled_cfg, unrepr=True)
        assert c == { 'key': 'value', 'section': { 'key': 'value'}}
        assert c.initial_comment == [
            '', '# initial comments', '# with two lines'
        ]
        assert c.comments == {'section': ['# section comment'], 'key': []}
        assert c.inline_comments == {
            'section': '# inline section comment', 'key': ''
        }
        assert c['section'].comments == { 'key': ['# key comment']}
        assert c.final_comment == ['', '# final comment', '# with two lines']

    def test_comments(self, comment_filled_cfg):
        c = ConfigObj(comment_filled_cfg)
        assert c == { 'key': 'value', 'section': { 'key': 'value'}}
        assert c.initial_comment == [
            '', '# initial comments', '# with two lines'
        ]
        assert c.comments == {'section': ['# section comment'], 'key': []}
        assert c.inline_comments == {
            'section': '# inline section comment', 'key': None
        }
        assert c['section'].comments == { 'key': ['# key comment']}
        assert c.final_comment == ['', '# final comment', '# with two lines']



def test_overwriting_filenames(a, b, i):
    #TODO: I'm not entirely sure what this test is actually asserting
    filename = a.filename
    a.filename = 'test.ini'
    a.write()
    a.filename = filename
    assert a == ConfigObj('test.ini', raise_errors=True)
    os.remove('test.ini')
    b.filename = 'test.ini'
    b.write()
    assert b == ConfigObj('test.ini', raise_errors=True)
    os.remove('test.ini')
    i.filename = 'test.ini'
    i.write()
    assert i == ConfigObj('test.ini', raise_errors=True)
    os.remove('test.ini')


def test_interpolation_using_default_sections():
    c = ConfigObj()
    c['DEFAULT'] = {'a' : 'fish'}
    c['a'] = '%(a)s'
    assert c.write() == ['a = %(a)s', '[DEFAULT]', 'a = fish']
    

class TestIndentation(object):
    @pytest.fixture
    def max_tabbed_cfg(self):
        return ['[sect]', '    [[sect]]', '        foo = bar']

    def test_write_dictionary(self):
        assert ConfigObj({'sect': {'sect': {'foo': 'bar'}}}).write() == [
            '[sect]', '    [[sect]]', '        foo = bar'
        ]

    def test_indentation_preserved(self, max_tabbed_cfg):
        for cfg_content in (
            ['[sect]', '[[sect]]', 'foo = bar'],
            ['[sect]', '  [[sect]]', '    foo = bar'],
            max_tabbed_cfg
        ):
            assert ConfigObj(cfg_content).write() == cfg_content

    def test_handle_tabs_vs_spaces(self, max_tabbed_cfg):
        one_tab = ['[sect]', '\t[[sect]]', '\t\tfoo = bar']
        two_tabs = ['[sect]', '\t\t[[sect]]', '\t\t\t\tfoo = bar']
        tabs_and_spaces = [b'[sect]', b'\t \t [[sect]]',
                           b'\t \t \t \t foo = bar']

        assert ConfigObj(one_tab).write() == one_tab
        assert ConfigObj(two_tabs).write() == two_tabs
        assert ConfigObj(tabs_and_spaces).write() == [s.decode('utf-8') for s in tabs_and_spaces]
        assert ConfigObj(max_tabbed_cfg, indent_type=chr(9)).write() == one_tab
        assert ConfigObj(one_tab, indent_type='    ').write() == max_tabbed_cfg


class TestEdgeCasesWhenWritingOut(object):
    def test_newline_terminated(self, empty_cfg):
        empty_cfg.newlines = '\n'
        empty_cfg['a'] = 'b'
        collector = io.BytesIO()
        empty_cfg.write(collector)
        assert collector.getvalue() == b'a = b\n'

    def test_hash_escaping(self, empty_cfg):
        empty_cfg.newlines = '\n'
        empty_cfg['#a'] = 'b # something'
        collector = io.BytesIO()
        empty_cfg.write(collector)
        assert collector.getvalue() == b'"#a" = "b # something"\n'
        
        empty_cfg = ConfigObj()
        empty_cfg.newlines = '\n'
        empty_cfg['a'] = 'b # something', 'c # something'
        collector = io.BytesIO()
        empty_cfg.write(collector)
        assert collector.getvalue() == b'a = "b # something", "c # something"\n'

    def test_detecting_line_endings_from_existing_files(self):
        newlines = ('\r\n', '\n') if os.linesep != '\r\n' else ('\r\n',)
        for expected_line_ending in newlines:
            with open('temp', 'w') as h:
                h.write(expected_line_ending)
            c = ConfigObj('temp')
            assert c.newlines == expected_line_ending
            os.remove('temp')

    def test_writing_out_dict_value_with_unrepr(self):
        # issue #42
        cfg = [str('thing = {"a": 1}')]
        c = ConfigObj(cfg, unrepr=True)
        assert repr(c) == "ConfigObj({'thing': {'a': 1}})"
        assert c.write() == ["thing = {'a': 1}"]
