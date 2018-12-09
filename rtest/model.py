#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License"self);
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
from robotide.controller.ctrlcommands import AddTestCaseFile, AddTestCase, AddKeyword, AddVariable, ChangeCellValue, AddRow, DeleteRow, InsertCell, DeleteCell, MoveRowsUp, MoveRowsDown, ExtractKeyword, RenameKeywordOccurrences, RenameTest, Undo, Redo, SaveFile, NullObserver, MoveUp, MoveDown, AddLibrary, AddResource, DeleteItem, InsertArea
from robotide.namespace import Namespace
from robotide.controller import Project
from robotide.preferences import RideSettings
from robotide.spec import librarydatabase


class RIDE(object):

    def __init__(self, random, path):
        print('librarydatabase.initialize_database()')
        print(librarydatabase.initialize_database())
        print('settings = RideSettings()')
        print('project = Project(Namespace(settings=settings),'
              ' settings=settings)')
        settings = RideSettings()
        self._project = Project(Namespace(settings=settings), settings=settings)
        self._path = path
        self._suite = None
        self._test = None
        self._keyword = None
        self._random = random
        self._skip = False

    def _skip_until_notified(self):
        self._skip = True

    def _do_not_skip(self):
        self._skip = False

    def open_test_dir(self):
        if self._skip:
            return
        self._open(os.path.join(self._path, 'testdir'))
        print('suite = project.data.children[0]')
        self._suite = self._project.data.children[0]
        print('test = list(t for t in suite.tests)[0]')
        self._test = list(t for t in self._suite.tests)[0]
        print('keyword = list(k for k in suite.keywords)[0]')
        self._keyword = list(k for k in self._suite.keywords)[0]

    def open_suite_file(self):
        if self._skip:
            return
        self._open(os.path.join(self._path, 'testdir', 'Suite.txt'))
        print('suite = project.data')
        self._suite = self._project.data
        print('test = list(t for t in suite.tests)[0]')
        self._test = list(t for t in self._suite.tests)[0]
        print('keyword = list(k for k in suite.keywords)[0]')
        self._keyword = list(k for k in self._suite.keywords)[0]

    def _open_resource_file(self):
        self._open(os.path.join(self._path, 'testdir', 'resources',
                                'resu.txt'))
        self._suite = None
        self._test = None
        self._keyword = None

    def _open(self, path):
        print('project.load_data("%s", NullObserver())' % path)
        self._project.load_data(path, NullObserver())

    def _create_suite(self):
        filename = os.path.join(self._path,'path_to_foo%s.txt' %
                                str(self._rand()))
        print('suite = project.data.execute(AddSuite(NewDatafile("%s")))' %
              filename)
        self._suite = self._project.data.execute(AddTestCaseFile(filename))

    def create_test(self):
        if self._skip:
            self._rand()
            return
        testname = 'foobar'+str(self._rand())
        print('test = suite.execute(AddTestCase("%s"))' % testname)
        self._test = self._suite.execute(AddTestCase(testname))

    def change_test_order(self):
        self._change_order([t.data for t in self._suite.tests], self._suite.tests)

    def _change_order(self, items, controller):
        command = MoveUp if self._rand() > 0.5 else MoveDown
        r = self._rand()
        if self._skip:
            return
        items = list(items)
        if items:
            i = int(r*(len(items)))
            print('%s.execute(%s(items[%d]))' %
                  (controller.__class__.__name__, command.__name__, i))
            controller.execute(command(items[i]))

    def _rand(self):
        return self._random.random()

    def _rand_row(self):
        return self._random.randint(0,100)

    def _rand_col(self):
        return self._random.randint(0, 30)

    def create_keyword(self):
        if self._skip:
            self._rand()
            return
        keyword_name = 'kwFoobar'+str(self._rand())
        print('keyword = suite.execute(AddKeyword("%s"))' % keyword_name)
        self._keyword = self._suite.execute(AddKeyword(keyword_name))

    def change_keyword_order(self):
        pass

    def add_variable(self):
        if self._skip:
            self._rand()
            self._rand()
            return
        command = AddVariable('${var%s}' % str(self._rand()),
                              str(self._rand()), 'comment')
        print('suite.execute(%s)' % str(command))
        self._suite.execute(command)

    def change_variable_order(self):
        pass

    def write_cell_data(self):
        value = self._random.choice(['# something', 'foobar', ': FOR',
                                     '${var}', 'No Operation', '\\',
                                      'zoo%d' % self._rand(), '${%d}' %
                                     self._rand()])
        self._macro_execute(ChangeCellValue(self._rand_row(), self._rand_col(),
                                            value))

    def write_for_loop(self):
        self._macro_execute(InsertArea((self._rand_row(), 0),
                            [[':FOR', '${i}', 'IN', '1', '2', 'foo'],
                             ['', 'No Operation']]))

    def _macro_execute(self, command):
        macro = self._random.choice([c for c in [self._test, self._keyword] if
                                     c])
        if not self._skip:
            print('%s.execute(%s)' % (self._name(macro), str(command)))
            macro.execute(command)

    def _name(self, macro):
        if macro == self._test:
            return 'test'
        return 'keyword'

    def add_row(self):
        self._macro_execute(AddRow(self._rand_row()))

    def remove_row(self):
        self._macro_execute(DeleteRow(self._rand_row()))

    def add_cell(self):
        self._macro_execute(InsertCell(self._rand_row(), self._rand_col()))

    def remove_cell(self):
        self._macro_execute(DeleteCell(self._rand_row(), self._rand_col()))

    def move_row_up(self):
        self._macro_execute(MoveRowsUp([self._rand_row()]))

    def move_row_down(self):
        self._macro_execute(MoveRowsDown([self._rand_row()]))

    def extract_keyword(self):
        first_row = self._rand_row()
        self._macro_execute(ExtractKeyword('foo', '',
                                           [first_row,
                                            first_row+
                                            self._random.randint(1,10)]))

    def add_library_import(self):
        if not self._skip:
            print('suite.imports.execute(AddLibrary('
                  '["OperatingSystem", "", ""], "#comment"))')
            self._suite.imports.execute(AddLibrary(['OperatingSystem', '', ''],
                                                   '#comment'))

    def remove_import(self):
        r = self._rand()
        if self._skip:
            return
        imps = list(self._suite.imports)
        if imps:
            i = int(r*len(imps))
            print('suite.imports.execute(DeleteItem(%d))' % i)
            self._suite.imports.execute(DeleteItem(i))

    def add_resource_import(self):
        if not self._skip:
            print('suite.imports.execute(AddResource(["SomeNonExisting.txt"],'
                  ' "#comment"))')
            self._suite.imports.execute(AddResource(['SomeNonExisting.txt'],
                                                    '#comment'))

    def change_import_order(self):
        self._change_order(range(sum(1 for _ in self._suite.imports)),
                           self._suite.imports)

    def rename_keyword(self):
        class Observer(object):
            def notify(self, *args):
                pass
            def finish(self, *args):
                pass
        self._macro_execute(RenameKeywordOccurrences('foo', 'bar', Observer()))

    def rename_test(self):
        if self._skip:
            self._rand()
            return
        self._test.execute(RenameTest('new_name%s' % str(self._rand())))

    def undo(self):
        self._macro_execute(Undo())

    def redo(self):
        self._macro_execute(Redo())

    def save(self):
        if self._skip:
            return
        command = SaveFile()
        print('suite.execute(%s)' % str(command))
        self._suite.execute(command)

    def get_cell_info(self):
        macro = self._random.choice([c for c in [self._test, self._keyword] if c])
        row = self._rand_row()
        col = self._rand_col()
        if self._skip:
            return
        print('%s.get_cell_info(%s, %s)' % (self._name(macro), row, col))
        macro.get_cell_info(row, col)
