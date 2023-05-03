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

from .. import robotapi


class DataLoader(object):

    def __init__(self, namespace, settings):
        self.namespace = namespace
        self.namespace.reset_resource_and_library_cache()
        self._settings = settings

    def load_datafile(self, path, load_observer):
        return self._load(_DataLoader(path, self._settings), load_observer)

    def load_initfile(self, path, load_observer):
        return self._load(_InitFileLoader(path), load_observer)

    def load_resource_file(self, datafile, load_observer):
        return self._load(_ResourceLoader(
            datafile, self.namespace.get_resource), load_observer)

    def resources_for(self, datafile, load_observer):
        return self._load(_ResourceLoader(
            datafile, self.namespace.get_resources), load_observer)

    def _load(self, loader, load_observer):
        self._wait_until_loaded(loader, load_observer)
        return loader.result

    def _wait_until_loaded(self, loader, load_observer):
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
            # print("DEBUG: exception at DataLoader %s\n" % str(e))
            pass  # TODO: Log this error somehow


class _DataLoader(_DataLoaderThread):

    def __init__(self, path, settings):
        _DataLoaderThread.__init__(self)
        self._path = path
        self._settings = settings

    def _run(self):
        # print(f"DEBUG: Dataloader returning TestData source={self._path}")
        return TestData(source=self._path, settings=self._settings)


class _InitFileLoader(_DataLoaderThread):

    def __init__(self, path, settings=None):
        _DataLoaderThread.__init__(self)
        self._path = path
        self._settings = settings

    def _run(self):
        result = robotapi.TestDataDirectory(source=os.path.dirname(self._path), settings=self._settings)
        result.initfile = self._path
        robotapi.FromFilePopulator(result).populate(self._path)
        return result


class _ResourceLoader(_DataLoaderThread):

    def __init__(self, datafile, resource_loader):
        _DataLoaderThread.__init__(self)
        self._datafile = datafile
        self._loader = resource_loader

    def _run(self):
        return self._loader(self._datafile)


class TestDataDirectoryWithExcludes(robotapi.TestDataDirectory):

    def __init__(self, parent, source, settings):
        self._settings = settings
        robotapi.TestDataDirectory.__init__(self, parent, source, settings=self._settings)

    def add_child(self, path, include_suites, extensions=None,
                  warn_on_skipped=False):
        if not self._settings.excludes.contains(path):
            self.children.append(TestData(
                parent=self, source=path, settings=self._settings))
        else:
            self.children.append(ExcludedDirectory(self, path))


def TestData(source, parent=None, settings=None):
    """Parses a file or directory to a corresponding model object.

    :param source: path where test data is read from.
    :returns: :class:`~.model.TestDataDirectory`  if `source` is a directory,
        :class:`~.model.TestCaseFile` otherwise.
    """
    if os.path.isdir(source):
        # print("DEBUG: Dataloader Is dir getting testdada %s\n" % source)
        data = TestDataDirectoryWithExcludes(parent, source, settings)
        # print("DEBUG: Dataloader testdata %s\n" % data.name)
        data.populate()
        # print("DEBUG: Dataloader after populate %s  %s\n" % (data._tables, data.name))
        return data
    #print("DEBUG: Dataloader returning TestCaseFile")
    datafile = robotapi.TestCaseFile(parent, source, settings).populate()
    if datafile:
        return datafile
    if source.endswith(("resource", "robot")):
        datafile = robotapi.ResourceFile(source, settings).populate()
    # print(f"DEBUG: Dataloader returning TestCaseFile datafile={datafile}, type={type(datafile)}")
    return datafile


class ExcludedDirectory(robotapi.TestDataDirectory):
    def __init__(self, parent, path):
        self._parent = parent
        self._path = path
        robotapi.TestDataDirectory.__init__(self, parent, path)

    def has_tests(self):
        return True
