#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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
from robotide.controller import NewDatafile
from robotide.controller.commands import AddSuite, AddTestCase, AddKeyword, AddVariable, ChangeCellValue, AddRow, DeleteRow, InsertCell, DeleteCell, MoveRowsUp, MoveRowsDown, ExtractKeyword, RenameKeywordOccurrences, RenameTest, Undo, Redo, SaveFile
from robotide.namespace import Namespace
from robotide.controller.chiefcontroller import ChiefController


class RIDE(object):

    def __init__(self, random, path):
        self._chief = ChiefController(Namespace())
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

    def _open_test_dir(self):
        class NullObserver(object):
            def notify(self, *args):
                pass

            def finish(self, *args):
                pass

            def error(self, *args):
                print args

        self._chief.load_data(self._path, NullObserver())

    def _create_suite(self):
        self._suite = self._chief.data.execute(AddSuite(NewDatafile(os.path.join(self._path,'path_to_foo%s.txt' % str(self._rand())), False)))

    def create_test(self):
        if self._skip:
            self._rand()
            return
        self._test = self._suite.execute(AddTestCase('foobar'+str(self._rand())))

    def _rand(self):
        return self._random.random()

    def _rand_row(self):
        return self._random.randint(0,100)

    def _rand_col(self):
        return self._random.randint(0, 30)

    def create_keyword(self):
        if self._skip:
            self._rand()
        self._keyword = self._suite.execute(AddKeyword('kwFoobar'+str(self._rand())))

    def add_variable(self):
        if self._skip:
            self._rand()
            self._rand()
            return
        self._suite.execute(AddVariable('${var%s}' % str(self._rand()), str(self._rand()), 'comment'))

    def write_cell_data(self):
        self._macro_execute(ChangeCellValue(self._rand_row(), self._rand_col(), 'foobar%s' % str(self._rand())))

    def _macro_execute(self, command):
        macro = self._random.choice([c for c in [self._test, self._keyword] if c])
        if not self._skip:
            print macro
            macro.execute(command)

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
        self._macro_execute(ExtractKeyword('foo', '', [first_row, first_row+self._random.randint(1,10)]))

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
        self._suite.execute(SaveFile())
