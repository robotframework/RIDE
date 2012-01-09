#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
from threading import Thread

from robot.parsing.model import TestData, TestDataDirectory
from robot.parsing.populators import FromFilePopulator


class DataLoader(object):

    def __init__(self, namespace):
        self._namespace = namespace
        self._namespace.reset_resource_and_library_cache()

    def load_datafile(self, path, load_observer):
        return self._load(_DataLoader(path), load_observer)

    def load_initfile(self, path, load_observer):
        res = self._load(_InitFileLoader(path), load_observer)
        return res

    def resources_for(self, datafile, load_observer):
        return self._load(_ResourceLoader(datafile, self._namespace.get_resources),
                          load_observer)

    def _load(self, loader, load_observer):
        self._wait_until_loaded(loader, load_observer)
        return loader.result

    def _wait_until_loaded(self, loader, load_observer):
        loader.start()
        load_observer.notify()
        while loader.isAlive():
            loader.join(0.1)
            load_observer.notify()


class _DataLoaderThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.result = None
        self._sanitizer = DataSanitizer()

    def run(self):
        try:
            self.result = self._sanitize(self._run())
        except Exception:
            pass # TODO: Log this error somehow

    def _sanitize(self, result):
        return self._sanitizer.sanitize(result)


class _DataLoader(_DataLoaderThread):

    def __init__(self, path):
        _DataLoaderThread.__init__(self)
        self._path = path

    def _run(self):
        return TestData(source=self._path)


class _InitFileLoader(_DataLoaderThread):

    def __init__(self, path):
        _DataLoaderThread.__init__(self)
        self._path = path

    def _run(self):
        result = TestDataDirectory(source=os.path.dirname(self._path))
        result.initfile = self._path
        FromFilePopulator(result).populate(self._path)
        return result


class _ResourceLoader(_DataLoaderThread):

    def __init__(self, datafile, resource_loader):
        _DataLoaderThread.__init__(self)
        self._datafile = datafile
        self._loader = resource_loader

    def _run(self):
        return self._loader(self._datafile)

    def _sanitize(self, results):
        return [self._sanitizer.sanitize(r) for r in results]


class DataSanitizer(object):

    def sanitize(self, datafile):
        self._sanitize_headers(datafile)
        return datafile

    def _sanitize_headers(self, datafile):
        # Black magic warning:
        # Older RIDE versions wrote headers like
        #   ['Test Cases', 'Action', 'Argument, 'Argument', 'Argument']
        # Since currently column aligning works based on custom headers,
        # the old default headers need be removed.
        for table in datafile.setting_table, datafile.variable_table:
            if self._is_old_style_setting_or_variable_header(table.header):
                self._reset_header(table)
        for table in datafile.testcase_table, datafile.keyword_table:
            if self._is_old_style_test_or_keyword_header(table.header):
                self._reset_header(table)

    def _is_old_style_test_or_keyword_header(self, header):
        if len(header) < 3:
            return False
        if header[1].lower() != 'action':
            return False
        for h in header[2:]:
            if not h.lower().startswith('arg'):
                return False
        return True

    def _is_old_style_setting_or_variable_header(self, header):
        if len(header) < 3:
            return False
        return all((True if e.lower() == 'value' else False) for e in header[1:])

    def _reset_header(self, table):
        table.set_header([table.header[0]])
