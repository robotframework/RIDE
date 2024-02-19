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
from threading import Thread

from robotide.lib.compat.parsing import language as lang
from robotide.lib.robot.errors import DataError
from .. import robotapi


class DataLoader(object):

    def __init__(self, namespace, settings, language=None):
        self.namespace = namespace
        self.namespace.reset_resource_and_library_cache()
        self._settings = settings
        self.language = language

    def load_datafile(self, path, load_observer, language=None):
        if not language:
            self.language = lang.check_file_language(path)
        else:
            self.language = language
        return self._load(_DataLoader(path, self._settings, language=self.language), load_observer)

    def load_initfile(self, path, load_observer, language=None):
        if not language:
            self.language = lang.check_file_language(path)
        else:
            self.language = language
        # print(f"DEBUG: datloder.py DataLoader.load_initfile ENTER self.language={self.language} language={language}")
        return self._load(_InitFileLoader(path, language=self.language), load_observer)

    def load_resource_file(self, datafile, load_observer, language=None):
        if not language:
            self.language = lang.check_file_language(datafile)
        else:
            self.language = language
        return self._load(_ResourceLoader(datafile, self.namespace.get_resource, language=self.language), load_observer)

    def resources_for(self, datafile, load_observer, language=None):
        if not language:
            self.language = lang.check_file_language(datafile.source)
        else:
            self.language = language
        return self._load(_ResourceLoader(datafile, self.namespace.get_resources, language=self.language),
                          load_observer)

    def _load(self, loader, load_observer):
        self._wait_until_loaded(loader, load_observer)
        return loader.result

    @staticmethod
    def _wait_until_loaded(loader, load_observer):
        loader.start()
        load_observer.notify()
        while loader.is_alive():
            loader.join(0.1)
            load_observer.notify()


class _DataLoaderThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.result = None

    def run(self):
        try:
            self.result = self._run()
        except Exception as e:
            print("DEBUG: exception at DataLoader %s\n" % str(e))

    def _run(self):
        return NotImplemented


class _DataLoader(_DataLoaderThread):

    def __init__(self, path, settings, language=None):
        _DataLoaderThread.__init__(self)
        self._path = path
        self._settings = settings
        self.language = language

    def _run(self):
        if not self.language:
            self.language = lang.check_file_language(self._path)
        return test_data(source=self._path, settings=self._settings, language=self.language)


class _InitFileLoader(_DataLoaderThread):

    def __init__(self, path, settings=None, language=None):
        _DataLoaderThread.__init__(self)
        self._path = path
        self._settings = settings
        self.language = language

    def _run(self):
        result = robotapi.TestDataDirectory(source=os.path.dirname(self._path), settings=self._settings,
                                            language=self.language)
        result.initfile = self._path
        if not self.language:
            self.language = lang.check_file_language(self._path)
        robotapi.FromFilePopulator(result, lang=self.language).populate(self._path)
        return result


class _ResourceLoader(_DataLoaderThread):

    def __init__(self, datafile, resource_loader, language=None):
        _DataLoaderThread.__init__(self)
        self._datafile = datafile
        self.language = language
        self._loader = resource_loader

    def _run(self):
        return self._loader(self._datafile, self.language)


class TestDataDirectoryWithExcludes(robotapi.TestDataDirectory):

    def __init__(self, parent, source, settings, language=None):
        self._settings = settings
        self.language = language
        robotapi.TestDataDirectory.__init__(self, parent, source, settings=self._settings, language=self.language)

    def add_child(self, path, include_suites, extensions=None,
                  warn_on_skipped=False, language=None):
        if not self._settings.excludes.contains(path):
            self.children.append(test_data(parent=self, source=path, settings=self._settings, language=self.language))
        else:
            self.children.append(ExcludedDirectory(self, path, language=self.language))


def test_data(source, parent=None, settings=None, language=None):
    """Parses a file or directory to a corresponding model object.

    :param source: path where test data is read from.
    :returns: :class:`~.model.TestDataDirectory`  if `source` is a directory,
        :class:`~.model.TestCaseFile` otherwise.
    """
    # Check if opening an __init__.robot
    if os.path.basename(source) == '__init__.robot':
        source = os.path.dirname(source)
    if os.path.isdir(source):
        if not language:
            init_file = os.path.join(source, '__init__.robot')
            if os.path.isfile(init_file):
                language = lang.check_file_language(init_file)
                # print(f"DEBUG: Dataloader TestCaseFile init file {init_file=}\n"
                #       f" language={language} {source=}")
        data = TestDataDirectoryWithExcludes(parent, source, settings, language)
        # print("DEBUG: Dataloader testdata %s\n" % data.name)
        data.populate()
        # print("DEBUG: Dataloader after populate %s  %s\n" % (data._tables, data.name))
        return data
    language = language if language else lang.check_file_language(source)
    # print(f"DEBUG: Dataloader TestCaseFile getting datafile language={language}")
    datafile = None
    try:
        datafile = robotapi.TestCaseFile(parent, source, settings, language).populate()
    except DataError:
        # print(f"DEBUG: Dataloader TestCaseFile testdata DataError source={source}")
        pass  # We try once more in case is a Resource
    if datafile:
        # print(f"DEBUG: Dataloader TestCaseFile return datafile={datafile}")
        return datafile
    if source.endswith(("resource", "robot")):
        datafile = robotapi.ResourceFile(source, settings, language).populate()
    # print(f"DEBUG: Dataloader returning TestCaseFile datafile={datafile}, type={type(datafile)}")
    return datafile


class ExcludedDirectory(robotapi.TestDataDirectory):
    def __init__(self, parent, path, language=None):
        self._parent = parent
        self._path = path
        self.language = language
        robotapi.TestDataDirectory.__init__(self, parent, path, language=self.language)

    def has_tests(self):
        return True
