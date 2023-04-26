#  Copyright 2023-     Robot Framework Foundation
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

import sys
import pathlib
import unittest
from robotide.controller.tags import DefaultTag
from robotide.controller.ctrlcommands import *

# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.insert(0, os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
SCRIPT_DIR = os.path.dirname(pathlib.Path(__file__).parent)
sys.path.insert(0, SCRIPT_DIR)

try:
    from base_command_test import TestCaseCommandTest
except ModuleNotFoundError:
    from .base_command_test import TestCaseCommandTest

try:
    from controller_creator import *
except ModuleNotFoundError:
    from .controller_creator import *


_TEST_WITH_TWO_IF_BLOCKS = ['If blocks',
                            '  Log  First line to move down',
                            '  ${test}=  Set Variable  test',
                            '  IF  "${test}" == "true"',
                            '    Log  True',
                            '    No Operation',
                            '  ELSE IF  "${test}" == "test"',
                            '    Log  second branch',
                            '    No Operation',
                            '  ELSE',
                            '    Log  False',
                            '    No Operation',
                            '  END',
                            '  IF  "${test}" != "test"',
                            '    Log  Not test',
                            '    No Operation',
                            '  ELSE',
                            '    Log  last branch',
                            '    No Operation',
                            '  END',
                            '  Log  Last line to move up']


class IfBlocksMoveDown(TestCaseCommandTest):

    def _create_data(self):
        return _TEST_WITH_TWO_IF_BLOCKS[:]

    def test_move_down_first_line_into_block(self):
        self._exec(MoveRowsDown((0,)))
        self._verify_step(1, '', ['Log', 'First line to move down'])
        self._exec(MoveRowsDown((1,)))
        self._verify_step(1, '', ['IF', '"${test}" == "true"'])
        self._verify_step(2, '', ['', 'Log', 'First line to move down'])
        # print("Test After MoveRowsDown:")
        # for el in self._ctrl.steps:
        #    print(f"{el.as_list()}")

    def test_move_down_if_line_into_block(self):
        self._exec(MoveRowsDown((2,)))
        self._verify_step(2, '', ['Log', 'True'])  # decreased indent
        self._verify_step(3, '', ['IF', '"${test}" == "true"'])  # kept no indent

    def test_move_down_line_inside_block(self):
        self._exec(MoveRowsDown((3,)))
        self._verify_step(3, '', ['', 'No Operation'])  # kept indent
        self._verify_step(4, '', ['', 'Log', 'True'])  # kept indent

    def test_move_down_line_inside_block_after_elseif(self):
        self._exec(MoveRowsDown((4,)))
        self._verify_step(3, '', ['', 'Log', 'True'])  # kept indent
        self._verify_step(4, '', ['ELSE IF', '"${test}" == "test"'])  # kept no indent
        self._verify_step(5, '', ['', 'No Operation'])  # kept indent

    def test_move_down_line_inside_block_after_else(self):
        self._exec(MoveRowsDown((7,)))
        self._verify_step(7, '', ['ELSE'])  # kept no indent
        self._verify_step(8, '', ['', 'No Operation'])  # kept indent
        self._verify_step(9, '', ['', 'Log', 'False'])  # kept indent

    def test_move_down_line_out_of_block(self):
        self._exec(MoveRowsDown((10,)))
        self._verify_step(10, '', ['END'])  # kept no indent
        self._verify_step(11, '', ['No Operation'])  # decrease indent
        self._verify_step(12, '', ['IF', '"${test}" != "test"'])  # kept indent

    def test_move_down_end_inside_if_block(self):
        self._exec(MoveRowsDown((11,)))
        self._verify_step(10, '', ['', 'No Operation'])  # kept indent
        self._verify_step(11, '', ['IF', '"${test}" != "test"'])  # kept no indent
        self._verify_step(12, '', ['END'])   # kept no indent
        self._exec(MoveRowsDown((12,)))
        self._verify_step(11, '', ['IF', '"${test}" != "test"'])  # kept no indent
        self._verify_step(12, '', ['', 'Log', 'Not test'])  # kept indent
        self._verify_step(13, '', ['END'])  # kept no indent

    def test_move_down_end_to_last_line(self):
        self._exec(MoveRowsDown((18,)))
        self._verify_step(17, '', ['', 'No Operation'])  # kept indent
        self._verify_step(18, '', ['', 'Log', 'Last line to move up'])  # increase indent
        self._verify_step(19, '', ['END'])   # kept no indent

    def test_move_down_elseif_inside_block(self):
        self._exec(MoveRowsDown((5,)))
        self._verify_step(4, '', ['', 'No Operation'])  # kept indent
        self._verify_step(5, '', ['', 'Log', 'second branch'])  # kept indent
        self._verify_step(6, '', ['ELSE IF', '"${test}" == "test"'])  # kept no indent
        # Move ELSE IF after ELSE
        self._exec(MoveRowsDown((6,)))
        self._exec(MoveRowsDown((7,)))
        self._exec(MoveRowsDown((8,)))
        self._verify_step(5, '', ['', 'Log', 'second branch'])  # kept indent
        self._verify_step(6, '', ['', 'No Operation'])  # kept indent
        self._verify_step(7, '', ['ELSE'])  # kept no indent
        self._verify_step(8, '', ['', 'Log', 'False'])  # kept indent
        self._verify_step(9, '', ['ELSE IF', '"${test}" == "test"'])  # kept no indent
        # print("Test After MoveRowsDown:")
        # for el in self._ctrl.steps:
        #     print(f"{el.as_list()}")

    def test_move_down_else_inside_block(self):
        self._exec(MoveRowsDown((8,)))
        self._verify_step(7, '', ['', 'No Operation'])  # kept indent
        self._verify_step(8, '', ['', 'Log', 'False'])  # kept indent
        self._verify_step(9, '', ['ELSE'])  # kept no indent

    def test_move_down_else_after_end(self):
        self._exec(MoveRowsDown((15,)))
        self._exec(MoveRowsDown((16,)))
        self._exec(MoveRowsDown((17,)))
        self._verify_step(15, '', ['', 'Log', 'last branch'])  # kept indent
        self._verify_step(16, '', ['', 'No Operation'])  # kept indent
        self._verify_step(17, '', ['END'])  # kept no indent
        self._verify_step(18, '', ['ELSE'])  # kept no indent


class IfBlocksMoveUp(TestCaseCommandTest):

    def _create_data(self):
        return _TEST_WITH_TWO_IF_BLOCKS[:]

    def test_move_up_last_line_into_block(self):
        self._exec(MoveRowsUp((19,)))
        self._verify_step(18, '', ['', 'Log', 'Last line to move up'])
        self._verify_step(19, '', ['END'])
        # print("Test After MoveRowsUp:")
        # for el in self._ctrl.steps:
        #     print(f"{el.as_list()}")

    def test_move_up_if_line_into_block(self):
        self._exec(MoveRowsUp((12,)))
        self._verify_step(11, '', ['IF', '"${test}" != "test"'])  # keep no indent
        self._verify_step(12, '', ['END'])  # kept no indent

    def test_move_up_line_inside_block(self):
        self._exec(MoveRowsUp((17,)))
        self._verify_step(16, '', ['', 'No Operation'])  # kept indent
        self._verify_step(17, '', ['', 'Log', 'last branch'])  # kept indent

    def test_move_up_line_inside_block_after_elseif(self):
        self._exec(MoveRowsUp((6,)))
        self._verify_step(5, '', ['', 'Log', 'second branch'])  # kept indent
        self._verify_step(6, '', ['ELSE IF', '"${test}" == "test"'])  # kept no indent
        self._verify_step(7, '', ['', 'No Operation'])  # kept indent

    def test_move_up_line_inside_block_after_else(self):
        self._exec(MoveRowsUp((9,)))
        self._verify_step(8, '', ['', 'Log', 'False'])  # kept indent
        self._verify_step(9, '', ['ELSE'])  # kept no indent
        self._verify_step(10, '', ['', 'No Operation'])  # kept indent

    def test_move_up_line_out_of_block(self):
        self._exec(MoveRowsUp((13,)))
        self._verify_step(12, '', ['Log', 'Not test'])  # decrease indent
        self._verify_step(13, '', ['IF', '"${test}" != "test"'])  # kept no indent
        self._verify_step(14, '', ['', 'No Operation'])  # kept indent

    def test_move_up_end_inside_if_block(self):
        self._exec(MoveRowsUp((11,)))
        self._verify_step(10, '', ['END'])   # kept no indent
        self._verify_step(11, '', ['No Operation'])  # decrease indent
        self._verify_step(12, '', ['IF', '"${test}" != "test"'])  # kept no indent

    def test_move_up_end_to_first_line(self):
        self._exec(MoveRowsUp((11,)))
        self._exec(MoveRowsUp((10,)))
        self._exec(MoveRowsUp((9,)))
        self._exec(MoveRowsUp((8,)))
        self._exec(MoveRowsUp((7,)))
        self._exec(MoveRowsUp((6,)))
        self._exec(MoveRowsUp((5,)))
        self._verify_step(6, '', ['ELSE IF', '"${test}" == "test"'])  # kept indent
        self._exec(MoveRowsUp((4,)))
        self._exec(MoveRowsUp((3,)))
        self._exec(MoveRowsUp((2,)))
        self._exec(MoveRowsUp((1,)))
        self._verify_step(0, '', ['END'])   # kept no indent
        self._verify_step(1, '', ['Log', 'First line to move down'])  # kept indent
        self._verify_step(2, '', ['${test}=', 'Set Variable', 'test'])  # kept indent
        self._verify_step(3, '', ['IF', '"${test}" == "true"'])  # kept no indent
        self._verify_step(4, '', ['Log', 'True'])  # decrased indent, because was outside END
        self._verify_step(5, '', ['No Operation'])  # decrased indent, because was outside END
        print("Test After MoveRowsUp:")
        for el in self._ctrl.steps:
            print(f"{el.as_list()}")

    def test_move_up_elseif_inside_block(self):
        self._exec(MoveRowsUp((5,)))
        self._verify_step(3, '', ['', 'Log', 'True'])  # kept indent
        self._verify_step(4, '', ['ELSE IF', '"${test}" == "test"'])  # kept no indent
        self._verify_step(5, '', ['', 'No Operation'])  # kept indent

    def test_move_up_else_inside_block(self):
        self._exec(MoveRowsUp((8,)))
        self._verify_step(6, '', ['', 'Log', 'second branch'])  # kept indent
        self._verify_step(7, '', ['ELSE'])  # kept no indent
        self._verify_step(8, '', ['', 'No Operation'])  # kept indent

    def test_move_up_else_out_of_if(self):
        self._exec(MoveRowsUp((15,)))
        self._exec(MoveRowsUp((14,)))
        self._exec(MoveRowsUp((13,)))
        self._verify_step(11, '', ['END'])  # kept no indent
        self._verify_step(12, '', ['ELSE'])  # kept no indent
        self._verify_step(13, '', ['IF', '"${test}" != "test"'])  # kept no indent
        self._verify_step(14, '', ['', 'Log', 'Not test'])  # kept indent
        self._verify_step(15, '', ['', 'No Operation'])  # kept indent


_TEST_WITH_WHILE_BLOCKS = ['While blocks',
                           '  WHILE  True  limit=4',
                           '    Log  First while',
                           '    No Operation',
                           '    ${test}=  Set Variable  ${1}',
                           '    WHILE  ${test} < ${3}  limit=4',
                           '      Log  Second while',
                           '      ${test}=  Set Variable  ${test + 1}',
                           '    END',
                           '    Log  Final step',
                           '  END']


class WhileBlocksMoveDown(TestCaseCommandTest):

    def _create_data(self):
        return _TEST_WITH_WHILE_BLOCKS[:]

    def test_move_down_first_while(self):
        self._exec(MoveRowsDown((0,)))
        self._verify_step(0, '', ['Log', 'First while'])
        self._verify_step(1, '', ['WHILE', 'True', 'limit=4'])
        self._exec(MoveRowsDown((1,)))
        self._verify_step(1, '', ['No Operation'])
        self._verify_step(2, '', ['WHILE', 'True', 'limit=4'])
        self._exec(MoveRowsDown((2,)))
        self._verify_step(1, '', ['No Operation'])
        self._verify_step(2, '', ['${test}=', 'Set Variable', '${1}'])
        self._verify_step(3, '', ['WHILE', 'True', 'limit=4'])
        self._exec(MoveRowsDown((3,)))
        self._verify_step(1, '', ['No Operation'])
        self._verify_step(2, '', ['${test}=', 'Set Variable', '${1}'])
        self._verify_step(3, '', ['WHILE', '${test} < ${3}', 'limit=4'])
        self._verify_step(4, '', ['', 'WHILE', 'True', 'limit=4'])
        self._verify_step(5, '', ['', '', 'Log', 'Second while'])
        self._exec(MoveRowsDown((4,)))
        self._verify_step(1, '', ['No Operation'])
        self._verify_step(2, '', ['${test}=', 'Set Variable', '${1}'])
        self._verify_step(3, '', ['WHILE', '${test} < ${3}', 'limit=4'])
        self._verify_step(4, '', ['', 'Log', 'Second while'])
        self._verify_step(5, '', ['', 'WHILE', 'True', 'limit=4'])
        self._verify_step(6, '', ['', '', '${test}=', 'Set Variable', '${test + 1}'])
        self._exec(MoveRowsDown((5,)))
        self._verify_step(4, '', ['', 'Log', 'Second while'])
        self._verify_step(5, '', ['', '${test}=', 'Set Variable', '${test + 1}'])
        self._verify_step(6, '', ['', 'WHILE', 'True', 'limit=4'])
        self._verify_step(7, '', ['', 'END'])
        self._exec(MoveRowsDown((6,)))
        self._verify_step(5, '', ['', '${test}=', 'Set Variable', '${test + 1}'])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'WHILE', 'True', 'limit=4'])
        self._verify_step(8, '', ['', 'Log', 'Final step'])
        self._exec(MoveRowsDown((7,)))
        self._verify_step(5, '', ['', '${test}=', 'Set Variable', '${test + 1}'])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', 'Final step'])
        self._verify_step(8, '', ['', 'WHILE', 'True', 'limit=4'])
        self._verify_step(9, '', ['END'])
        self._exec(MoveRowsDown((8,)))
        self._verify_step(5, '', ['', '${test}=', 'Set Variable', '${test + 1}'])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', 'Final step'])
        self._verify_step(8, '', ['END'])
        self._verify_step(9, '', ['WHILE', 'True', 'limit=4'])
        # Extra test, move after last test line
        self._exec(MoveRowsDown((9,)))
        # print("Test After MoveRowsDown:")
        # for el in self._ctrl.steps:
        #     print(f"{el.as_list()}")
        self._verify_step(5, '', ['', '${test}=', 'Set Variable', '${test + 1}'])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', 'Final step'])
        self._verify_step(8, '', ['END'])
        self._verify_step(9, '', ['WHILE', 'True', 'limit=4'])

    def test_move_down_inner_while_block(self):
        self._exec(MoveRowsDown([4,7]))
        # print("Test After MoveRowsDown:")
        # for el in self._ctrl.steps:
        #     print(f"{el.as_list()}")
        self._verify_step(0, '', ['WHILE', 'True', 'limit=4'])
        self._verify_step(1, '', ['', 'Log', 'First while'])
        self._verify_step(2, '', ['', 'No Operation'])
        self._verify_step(3, '', ['', '${test}=', 'Set Variable', '${1}'])
        self._verify_step(4, '', ['', 'Log', 'Final step'])
        self._verify_step(5, '', ['', 'WHILE', '${test} < ${3}', 'limit=4'])
        self._verify_step(6, '', ['', '', 'Log', 'Second while'])
        self._verify_step(7, '', ['', '', '${test}=', 'Set Variable', '${test + 1}'])
        self._verify_step(8, '', ['', 'END'])
        self._verify_step(9, '', ['END'])
