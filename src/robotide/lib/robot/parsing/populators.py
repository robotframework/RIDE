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

import os

from multiprocessing import shared_memory
from robotide.lib.compat.parsing import language
from robotide.lib.robot.errors import DataError
from robotide.lib.robot.model import SuiteNamePatterns
from robotide.lib.robot.output import LOGGER
from robotide.lib.robot.utils import get_error_message, unic

from .datarow import DataRow
from .tablepopulators import (SettingTablePopulator, VariableTablePopulator,
                              TestTablePopulator, KeywordTablePopulator,
                              CommentsTablePopulator, NullPopulator)
# from .htmlreader import HtmlReader
from .tsvreader import TsvReader
from .robotreader import RobotReader
from .restreader import RestReader


READERS = {'tsv': TsvReader, 'rst': RestReader, 'rest': RestReader,
           'txt': RobotReader, 'robot': RobotReader}  # Removed 'html':HtmlReader, 'htm':HtmlReader, 'xhtml':HtmlReader,

# Hook for external tools for altering ${CURDIR} processing
PROCESS_CURDIR = True


def store_language(lang: list):
    assert lang is not None
    # Shared memory to store language definition
    try:
        sharemem = shared_memory.ShareableList(['en'], name="language")
    except FileExistsError:  # Other instance created file
        sharemem = shared_memory.ShareableList(name="language")
    sharemem[0] = lang[0]


class NoTestsFound(DataError):
    pass


class FromFilePopulator(object):
    _populators = {'setting': SettingTablePopulator,
                   'settings': SettingTablePopulator,
                   'variable': VariableTablePopulator,
                   'variables': VariableTablePopulator,
                   'test case': TestTablePopulator,
                   'test cases': TestTablePopulator,
                   'task': TestTablePopulator,
                   'tasks': TestTablePopulator,
                   'keyword': KeywordTablePopulator,
                   'keywords': KeywordTablePopulator,
                   'comments': CommentsTablePopulator}

    def __init__(self, datafile, tab_size=2, lang=None):
        self._datafile = datafile
        self._populator = NullPopulator()
        self._curdir = self._get_curdir(datafile.directory)
        self._tab_size = tab_size
        if datafile.source:
            self._language = lang if lang else language.check_file_language(datafile.source)
        else:
            self._language = lang if lang else None
        if self._language:
            store_language(self._language)
        # self._comment_table_names = language.get_headers_for(self._language, ('comment', 'comments'))

    @staticmethod
    def _get_curdir(path):
        return path.replace('\\', '\\\\') if path else None

    def add_preamble(self, row):
        self._datafile.add_preamble(row)

    def populate(self, path, resource=False):
        LOGGER.info("Parsing file '%s'." % path)
        source = self._open(path)
        try:
            # print(f"DEBUG: populators populate path={path} READER={self._get_reader(path, resource)}")
            self._get_reader(path, resource).read(source, self)
        except Exception:
            # print("DEBUG: populators populate CALLING DATAERROR")
            raise DataError(get_error_message())
        finally:
            source.close()

    @staticmethod
    def _open(path):
        if not os.path.isfile(path):
            raise DataError("File or directory to execute does not exist.")
        try:
            # IronPython handles BOM incorrectly if not using binary mode:
            # https://ironpython.codeplex.com/workitem/34655
            return open(path, 'rb')
        except Exception:
            raise DataError(get_error_message())

    def _get_reader(self, path, resource=False):
        file_format = os.path.splitext(path.lower())[-1][1:]
        if resource and file_format == 'resource':
            file_format = 'robot'
        try:
            return READERS[file_format](self._tab_size, self._language)
        except KeyError:
            raise DataError("Unsupported file format '%s'." % file_format)

    def start_table(self, header, lineno: int, llang: list = None):
        # DEBUG:
        # print(f"DEBUG: RFLib populators FromFilePopulator ENTER start_table header={header}")
        # if header[0].lower() in self._comment_table_names:  # don't create a Comments section
        #    print(f"DEBUG: RFLib populators FromFilePopulator comments section header={header}")
        #    # return False
        self._populator.populate()
        table = self._datafile.start_table(DataRow(header).all, lineno=lineno, llang=llang)
        # print(f"DEBUG: populators start_table header={header} got table={table} at lineno={lineno}"
        #       f" llang={llang}")
        if header[0] in language.get_headers_for(llang, ('Comment', 'Comments'), lowercase=False):
            self._populator = self._populators['comments'](table)
        else:
            self._populator = self._populators[table.type](table) if table is not None else NullPopulator()
        # print(f"DEBUG: populators start_table AFTER _populators table.type={table.type} table={table}\n"
        #      f"self._populators={self._populators}")
        return bool(self._populator)

    def eof(self):
        self._populator.populate()
        self._populator = NullPopulator()
        return bool(self._datafile)

    def add(self, row):
        # print(f"DEBUG: populators.py FromFilePopulator enter add row={row}")
        if PROCESS_CURDIR and self._curdir:
            row = self._replace_curdirs_in(row)
        data = DataRow(row, self._datafile.source)
        if data:
            # print(f"DEBUG: populators.py FromFilePopulator call _populator add data={data.cells} + {data.comments}\n"
            #       f"populator = {self._populator}")
            self._populator.add(data)

    def _replace_curdirs_in(self, row):
        old, new = '${CURDIR}', self._curdir
        return [cell if old not in cell else cell.replace(old, new)
                for cell in row]


class FromDirectoryPopulator(object):
    ignored_prefixes = ('_', '.')
    ignored_dirs = ('CVS',)

    def __init__(self, tab_size=2, lang=None):
        self.tab_size = tab_size
        self.language = lang

    def populate(self, path, datadir, include_suites=None,
                 include_extensions=None, recurse=True, tab_size=2):
        LOGGER.info("Parsing directory '%s'." % path)
        if not self.language:
            self.language = language.check_file_language(path)
        if self.language:
            store_language(self.language)
        include_suites = self._get_include_suites(path, include_suites)
        init_file, children = self._get_children(path, include_extensions, include_suites)
        if init_file:
            self._populate_init_file(datadir, init_file, tab_size)
        if recurse:
            self._populate_children(datadir, children, include_extensions, include_suites)

    def _populate_init_file(self, datadir, init_file, tab_size):
        datadir.initfile = init_file
        try:
            if not self.language:
                self.language = language.check_file_language(init_file)
            FromFilePopulator(datadir, tab_size, self.language).populate(init_file)
        except DataError as err:
            LOGGER.error(err.message)

    def _populate_children(self, datadir, children, include_extensions, include_suites):
        for child in children:
            try:
                datadir.add_child(child, include_suites, include_extensions, language=self.language)
            except NoTestsFound:
                LOGGER.info("Data source '%s' has no tests or tasks." % child)
            except DataError as err:
                LOGGER.error("Parsing '%s' failed: %s" % (child, err.message))

    def _get_include_suites(self, path, incl_suites):
        if not incl_suites:
            return None
        if not isinstance(incl_suites, SuiteNamePatterns):
            incl_suites = SuiteNamePatterns(self._create_included_suites(incl_suites))
        # If a directory is included, also all its children should be included.
        if self._is_in_included_suites(os.path.basename(path), incl_suites):
            return None
        return incl_suites

    @staticmethod
    def _create_included_suites(incl_suites):
        for suite in incl_suites:
            yield suite
            while '.' in suite:
                suite = suite.split('.', 1)[1]
                yield suite

    def _get_children(self, dirpath, incl_extensions, incl_suites):
        init_file = None
        children = []
        for path, is_init_file in self._list_dir(dirpath, incl_extensions,
                                                 incl_suites):
            if is_init_file:
                if not init_file:
                    init_file = path
                else:
                    LOGGER.error("Ignoring second test suite init file '%s'." % path)
            else:
                children.append(path)
        return init_file, children

    def _list_dir(self, dir_path, incl_extensions, incl_suites):
        # os.listdir returns Unicode entries when path is Unicode
        dir_path = unic(dir_path)
        names = os.listdir(dir_path)
        for name in sorted(names, key=lambda item: item.lower()):
            name = unic(name)  # needed to handle nfc/nfd normalization on OSX
            path = os.path.join(dir_path, name)
            base, ext = os.path.splitext(name)
            ext = ext[1:].lower()
            if self._is_init_file(path, base, ext, incl_extensions):
                yield path, True
            elif self._is_included(path, base, ext, incl_extensions, incl_suites):
                yield path, False
            else:
                LOGGER.info("Ignoring file or directory '%s'." % path)

    def _is_init_file(self, path, base, ext, incl_extensions):
        return (base.lower() == '__init__' and
                self._extension_is_accepted(ext, incl_extensions) and
                os.path.isfile(path))

    @staticmethod
    def _extension_is_accepted(ext, incl_extensions):
        if incl_extensions:
            return ext in incl_extensions
        return ext in READERS

    def _is_included(self, path, base, ext, incl_extensions, incl_suites):
        if base.startswith(self.ignored_prefixes):
            return False
        if os.path.isdir(path):
            return base not in self.ignored_dirs or ext
        if not self._extension_is_accepted(ext, incl_extensions):
            return False
        return self._is_in_included_suites(base, incl_suites)

    def _is_in_included_suites(self, name, incl_suites):
        if not incl_suites:
            return True
        return incl_suites.match(self._split_prefix(name))

    @staticmethod
    def _split_prefix(name):
        return name.split('__', 1)[-1]
