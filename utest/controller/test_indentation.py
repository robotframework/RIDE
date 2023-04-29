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

import os
import pathlib
import sys
from robotide.controller.ctrlcommands import MoveRowsDown, MoveRowsUp

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

FOURSPC = '    '
NOOPERATION = 'No Operation'
FNOOPERATION = FOURSPC + NOOPERATION
NOMATTER = 'No matter the result, this is always shown'
LOOPNOTFINISH = 'The loop did not finish within the limit.'
VARTEST = '"${test}" == "test"'
STEST1 = '${test + 1}'
NOTEST = 'Not test'
SECONDBRANCH = 'second branch'
TESTAS = '${test}='
SETVAR = 'Set Variable'
LIMIT = 'limit=10'
TESTTRUE = '"${test}" == "true"'
FIRSTMVDN = 'First line to move down'
FIRSTWHILE = 'First while'
TESTL3 = '${test} < ${3}'
TESTNOT = '"${test}" != "test"'
SECONDWHILE = 'Second while'
FINALSTEP = 'Final step'
EXECUTED = 'Executed until the given loop limit (10) is hit.'
WHILEABRT = 'WHILE loop was aborted'
TSTART = 'type=start'


_TEST_WITH_TWO_IF_BLOCKS = ['If blocks',
                            '  Log  First line to move down',
                            '  ${test}=  Set Variable  test',
                            '  IF  "${test}" == "true"',
                            '    Log  True',
                            FNOOPERATION,
                            '  ELSE IF  "${test}" == "test"',
                            '    Log  second branch',
                            FNOOPERATION,
                            '  ELSE',
                            '    Log  False',
                            FNOOPERATION,
                            '  END',
                            '  IF  "${test}" != "test"',
                            '    Log  Not test',
                            FNOOPERATION,
                            '  ELSE',
                            '    Log  last branch',
                            FNOOPERATION,
                            '  END',
                            '  Log  Last line to move up']

_TEST_WITH_TRY_BLOCK = ['Try block',
                        '  TRY',
                        '    WHILE  True'+'  '+LIMIT,
                        '      Log'+'  '+EXECUTED,
                        '    END',
                        '  EXCEPT  WHILE loop was aborted  type=start',
                        '    Log  The loop did not finish within the limit.',
                        '  FINALLY',
                        '    Log  No matter the result, this is always shown',
                        '  END']

_TEST_WITH_WHILE_BLOCKS = ['While blocks',
                           '  WHILE  True'+'  '+LIMIT,
                           '    Log  First while',
                           FNOOPERATION,
                           '    ${test}=  Set Variable  ${1}',
                           '    WHILE  ${test} < ${3}'+'  '+LIMIT,
                           '      Log  Second while',
                           '      ${test}=  Set Variable  ${test + 1}',
                           '    END',
                           '    Log  Final step',
                           '  END']


class IfBlocksMoveDown(TestCaseCommandTest):

    def _create_data(self):
        return _TEST_WITH_TWO_IF_BLOCKS[:]

    def test_move_down_first_line_into_block(self):
        self._exec(MoveRowsDown((0,)))
        self._verify_step(1, '', ['Log', FIRSTMVDN])
        self._exec(MoveRowsDown((1,)))
        self._verify_step(1, '', ['IF', TESTTRUE])
        self._verify_step(2, '', ['', 'Log', FIRSTMVDN])

    def test_move_down_if_line_into_block(self):
        self._exec(MoveRowsDown((2,)))
        self._verify_step(2, '', ['Log', 'True'])  # decreased indent
        self._verify_step(3, '', ['IF', TESTTRUE])  # kept no indent

    def test_move_down_line_inside_block(self):
        self._exec(MoveRowsDown((3,)))
        self._verify_step(3, '', ['', NOOPERATION])  # kept indent
        self._verify_step(4, '', ['', 'Log', 'True'])  # kept indent

    def test_move_down_line_inside_block_after_elseif(self):
        self._exec(MoveRowsDown((4,)))
        self._verify_step(3, '', ['', 'Log', 'True'])  # kept indent
        self._verify_step(4, '', ['ELSE IF', VARTEST])  # kept no indent
        self._verify_step(5, '', ['', NOOPERATION])  # kept indent

    def test_move_down_line_inside_block_after_else(self):
        self._exec(MoveRowsDown((7,)))
        self._verify_step(7, '', ['ELSE'])  # kept no indent
        self._verify_step(8, '', ['', NOOPERATION])  # kept indent
        self._verify_step(9, '', ['', 'Log', 'False'])  # kept indent

    def test_move_down_line_out_of_block(self):
        self._exec(MoveRowsDown((10,)))
        self._verify_step(10, '', ['END'])  # kept no indent
        self._verify_step(11, '', [NOOPERATION])  # decrease indent
        self._verify_step(12, '', ['IF', TESTNOT])  # kept indent

    def test_move_down_end_inside_if_block(self):
        self._exec(MoveRowsDown((11,)))
        self._verify_step(10, '', ['', NOOPERATION])  # kept indent
        self._verify_step(11, '', ['IF', TESTNOT])  # kept no indent
        self._verify_step(12, '', ['END'])   # kept no indent
        self._exec(MoveRowsDown((12,)))
        self._verify_step(11, '', ['IF', TESTNOT])  # kept no indent
        self._verify_step(12, '', ['', 'Log', NOTEST])  # kept indent
        self._verify_step(13, '', ['END'])  # kept no indent

    def test_move_down_end_to_last_line(self):
        self._exec(MoveRowsDown((18,)))
        self._verify_step(17, '', ['', NOOPERATION])  # kept indent
        self._verify_step(18, '', ['', 'Log', 'Last line to move up'])  # increase indent
        self._verify_step(19, '', ['END'])   # kept no indent

    def test_move_down_elseif_inside_block(self):
        self._exec(MoveRowsDown((5,)))
        self._verify_step(4, '', ['', NOOPERATION])  # kept indent
        self._verify_step(5, '', ['', 'Log', SECONDBRANCH])  # kept indent
        self._verify_step(6, '', ['ELSE IF', VARTEST])  # kept no indent
        # Move ELSE IF after ELSE
        self._exec(MoveRowsDown((6,)))
        self._exec(MoveRowsDown((7,)))
        self._exec(MoveRowsDown((8,)))
        self._verify_step(5, '', ['', 'Log', SECONDBRANCH])  # kept indent
        self._verify_step(6, '', ['', NOOPERATION])  # kept indent
        self._verify_step(7, '', ['ELSE'])  # kept no indent
        self._verify_step(8, '', ['', 'Log', 'False'])  # kept indent
        self._verify_step(9, '', ['ELSE IF', VARTEST])  # kept no indent
        """ print("Test After MoveRowsDown:")
            for el in self._ctrl.steps:
                print(f"{el.as_list()}")
        """

    def test_move_down_else_inside_block(self):
        self._exec(MoveRowsDown((8,)))
        self._verify_step(7, '', ['', NOOPERATION])  # kept indent
        self._verify_step(8, '', ['', 'Log', 'False'])  # kept indent
        self._verify_step(9, '', ['ELSE'])  # kept no indent

    def test_move_down_else_after_end(self):
        self._exec(MoveRowsDown((15,)))
        self._exec(MoveRowsDown((16,)))
        self._exec(MoveRowsDown((17,)))
        self._verify_step(15, '', ['', 'Log', 'last branch'])  # kept indent
        self._verify_step(16, '', ['', NOOPERATION])  # kept indent
        self._verify_step(17, '', ['END'])  # kept no indent
        self._verify_step(18, '', ['ELSE'])  # kept no indent


class IfBlocksMoveUp(TestCaseCommandTest):

    def _create_data(self):
        return _TEST_WITH_TWO_IF_BLOCKS[:]

    def test_move_up_last_line_into_block(self):
        self._exec(MoveRowsUp((19,)))
        self._verify_step(18, '', ['', 'Log', 'Last line to move up'])
        self._verify_step(19, '', ['END'])

    def test_move_up_if_line_into_block(self):
        self._exec(MoveRowsUp((12,)))
        self._verify_step(11, '', ['IF', TESTNOT])  # keep no indent
        self._verify_step(12, '', ['END'])  # kept no indent

    def test_move_up_line_inside_block(self):
        self._exec(MoveRowsUp((17,)))
        self._verify_step(16, '', ['', NOOPERATION])  # kept indent
        self._verify_step(17, '', ['', 'Log', 'last branch'])  # kept indent

    def test_move_up_line_inside_block_after_elseif(self):
        self._exec(MoveRowsUp((6,)))
        self._verify_step(5, '', ['', 'Log', SECONDBRANCH])  # kept indent
        self._verify_step(6, '', ['ELSE IF', VARTEST])  # kept no indent
        self._verify_step(7, '', ['', NOOPERATION])  # kept indent

    def test_move_up_line_inside_block_after_else(self):
        self._exec(MoveRowsUp((9,)))
        self._verify_step(8, '', ['', 'Log', 'False'])  # kept indent
        self._verify_step(9, '', ['ELSE'])  # kept no indent
        self._verify_step(10, '', ['', NOOPERATION])  # kept indent

    def test_move_up_line_out_of_block(self):
        self._exec(MoveRowsUp((13,)))
        self._verify_step(12, '', ['Log', NOTEST])  # decrease indent
        self._verify_step(13, '', ['IF', TESTNOT])  # kept no indent
        self._verify_step(14, '', ['', NOOPERATION])  # kept indent

    def test_move_up_end_inside_if_block(self):
        self._exec(MoveRowsUp((11,)))
        self._verify_step(10, '', ['END'])   # kept no indent
        self._verify_step(11, '', [NOOPERATION])  # decrease indent
        self._verify_step(12, '', ['IF', TESTNOT])  # kept no indent

    def test_move_up_end_to_first_line(self):
        self._exec(MoveRowsUp((11,)))
        self._exec(MoveRowsUp((10,)))
        self._exec(MoveRowsUp((9,)))
        self._exec(MoveRowsUp((8,)))
        self._exec(MoveRowsUp((7,)))
        self._exec(MoveRowsUp((6,)))
        self._exec(MoveRowsUp((5,)))
        self._verify_step(6, '', ['ELSE IF', VARTEST])  # kept indent
        self._exec(MoveRowsUp((4,)))
        self._exec(MoveRowsUp((3,)))
        self._exec(MoveRowsUp((2,)))
        self._exec(MoveRowsUp((1,)))
        self._verify_step(0, '', ['END'])   # kept no indent
        self._verify_step(1, '', ['Log', FIRSTMVDN])  # kept indent
        self._verify_step(2, '', [TESTAS, SETVAR, 'test'])  # kept indent
        self._verify_step(3, '', ['IF', TESTTRUE])  # kept no indent
        self._verify_step(4, '', ['Log', 'True'])  # decrased indent, because was outside END
        self._verify_step(5, '', [NOOPERATION])  # decrased indent, because was outside END

    def test_move_up_elseif_inside_block(self):
        self._exec(MoveRowsUp((5,)))
        self._verify_step(3, '', ['', 'Log', 'True'])  # kept indent
        self._verify_step(4, '', ['ELSE IF', VARTEST])  # kept no indent
        self._verify_step(5, '', ['', NOOPERATION])  # kept indent

    def test_move_up_else_inside_block(self):
        self._exec(MoveRowsUp((8,)))
        self._verify_step(6, '', ['', 'Log', SECONDBRANCH])  # kept indent
        self._verify_step(7, '', ['ELSE'])  # kept no indent
        self._verify_step(8, '', ['', NOOPERATION])  # kept indent

    def test_move_up_else_out_of_if(self):
        self._exec(MoveRowsUp((15,)))
        self._exec(MoveRowsUp((14,)))
        self._exec(MoveRowsUp((13,)))
        self._verify_step(11, '', ['END'])  # kept no indent
        self._verify_step(12, '', ['ELSE'])  # kept no indent
        self._verify_step(13, '', ['IF', TESTNOT])  # kept no indent
        self._verify_step(14, '', ['', 'Log', NOTEST])  # kept indent
        self._verify_step(15, '', ['', NOOPERATION])  # kept indent


class WhileBlocksMoveDown(TestCaseCommandTest):

    def _create_data(self):
        return _TEST_WITH_WHILE_BLOCKS[:]

    def test_move_down_first_while(self):
        self._exec(MoveRowsDown((0,)))
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', ['WHILE', 'True', LIMIT])
        self._exec(MoveRowsDown((1,)))
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', ['WHILE', 'True', LIMIT])
        self._exec(MoveRowsDown((2,)))
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', 'True', LIMIT])
        self._exec(MoveRowsDown((3,)))
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', 'WHILE', 'True', LIMIT])
        self._verify_step(5, '', ['', '', 'Log', SECONDWHILE])
        self._exec(MoveRowsDown((4,)))
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', 'WHILE', 'True', LIMIT])
        self._verify_step(6, '', ['', '', TESTAS, SETVAR, STEST1])
        self._exec(MoveRowsDown((5,)))
        self._verify_step(4, '', ['', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'WHILE', 'True', LIMIT])
        self._verify_step(7, '', ['', 'END'])
        self._exec(MoveRowsDown((6,)))
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'WHILE', 'True', LIMIT])
        self._verify_step(8, '', ['', 'Log', FINALSTEP])
        self._exec(MoveRowsDown((7,)))
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', FINALSTEP])
        self._verify_step(8, '', ['', 'WHILE', 'True', LIMIT])
        self._verify_step(9, '', ['END'])
        self._exec(MoveRowsDown((8,)))
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', FINALSTEP])
        self._verify_step(8, '', ['END'])
        self._verify_step(9, '', ['WHILE', 'True', LIMIT])
        # Extra test, move after last test line
        self._exec(MoveRowsDown((9,)))
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', FINALSTEP])
        self._verify_step(8, '', ['END'])
        self._verify_step(9, '', ['WHILE', 'True', LIMIT])

    def test_move_down_inner_while_block(self):
        self._exec(MoveRowsDown([4, 7]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', FIRSTWHILE])
        self._verify_step(2, '', ['', NOOPERATION])
        self._verify_step(3, '', ['', TESTAS, SETVAR, '${1}'])
        self._verify_step(4, '', ['', 'Log', FINALSTEP])
        self._verify_step(5, '', ['', 'WHILE', TESTL3, LIMIT])
        self._verify_step(6, '', ['', '', 'Log', SECONDWHILE])
        self._verify_step(7, '', ['', '', TESTAS, SETVAR, STEST1])
        self._verify_step(8, '', ['', 'END'])
        self._verify_step(9, '', ['END'])

    def test_move_down_while_range_reverted(self):
        self._exec(MoveRowsDown([7, 4]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', FIRSTWHILE])
        self._verify_step(2, '', ['', NOOPERATION])
        self._verify_step(3, '', ['', TESTAS, SETVAR, '${1}'])
        self._verify_step(4, '', ['', 'Log', FINALSTEP])
        self._verify_step(5, '', ['', 'WHILE', TESTL3, LIMIT])
        self._verify_step(6, '', ['', '', 'Log', SECONDWHILE])
        self._verify_step(7, '', ['', '', TESTAS, SETVAR, STEST1])
        self._verify_step(8, '', ['', 'END'])
        self._verify_step(9, '', ['END'])

    def test_move_down_while_range_equal(self):
        self._exec(MoveRowsDown([4, 4]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', FIRSTWHILE])
        self._verify_step(2, '', ['', NOOPERATION])
        self._verify_step(3, '', ['', TESTAS, SETVAR, '${1}'])
        self._verify_step(4, '', ['', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', 'WHILE', TESTL3, LIMIT])
        self._verify_step(6, '', ['', '', TESTAS, SETVAR, STEST1])
        self._verify_step(7, '', ['', 'END'])
        self._verify_step(8, '', ['', 'Log', FINALSTEP])
        self._verify_step(9, '', ['END'])

    def test_move_down_while_range_invalid_start(self):
        self._exec(MoveRowsDown([-1, 0]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])

    def test_move_down_while_range_invalid_end(self):
        self._exec(MoveRowsDown([1, -1]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])

    def test_move_down_while_range_out(self):
        self._exec(MoveRowsDown([11, 0]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])

    def test_move_down_while_range_full(self):
        self._exec(MoveRowsDown([0, 9]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])

    def test_move_down_while_range_all_but_last(self):
        self._exec(MoveRowsDown([0, 8]))
        # print("Test After MoveRowsDown:")
        # for el in self._ctrl.steps:
        #    print(f"{el.as_list()}")
        self._verify_step(0, '', ['END'])
        self._verify_step(1, '', ['WHILE', 'True', LIMIT])
        self._verify_step(2, '', ['', 'Log', FIRSTWHILE])
        self._verify_step(3, '', ['', NOOPERATION])
        self._verify_step(4, '', ['', TESTAS, SETVAR, '${1}'])
        self._verify_step(5, '', ['', 'WHILE', TESTL3, LIMIT])
        self._verify_step(6, '', ['', 'Log', SECONDWHILE])  # decreased indent because of moving up END
        self._verify_step(7, '', ['', TESTAS, SETVAR, STEST1])  # decreased indent
        self._verify_step(8, '', ['END'])  # decreased indent because of moving up END
        self._verify_step(9, '', ['Log', FINALSTEP])  # decreased indent because of moving up END


class WhileBlocksMoveUp(TestCaseCommandTest):

    def _create_data(self):
        return _TEST_WITH_WHILE_BLOCKS[:] + ['  Log  Last line to move up']

    def test_move_up_last_line(self):
        self._exec(MoveRowsUp((10,)))
        self._verify_step(8, '', ['', 'Log', FINALSTEP])
        self._verify_step(9, '', ['', 'Log', 'Last line to move up'])
        self._verify_step(10, '', ['END'])

    def test_move_up_two_while_lines(self):
        self._exec(MoveRowsUp([1, 2]))
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', ['WHILE', 'True', LIMIT])
        self._verify_step(3, '', ['', TESTAS, SETVAR, '${1}'])
        self._verify_step(4, '', ['', 'WHILE', TESTL3, LIMIT])

    def test_move_up_inner_while_block(self):
        self._exec(MoveRowsUp([4, 8]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', FIRSTWHILE])
        self._verify_step(2, '', ['', NOOPERATION])
        self._verify_step(3, '', ['', 'WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', '', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', '', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', FINALSTEP])
        self._verify_step(8, '', ['', TESTAS, SETVAR, '${1}'])
        self._verify_step(9, '', ['END'])
        self._verify_step(10, '', ['Log', 'Last line to move up'])

    def test_move_up_while_range_reverted(self):
        self._exec(MoveRowsUp([8, 4]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', FIRSTWHILE])
        self._verify_step(2, '', ['', NOOPERATION])
        self._verify_step(3, '', ['', 'WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', '', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', '', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', FINALSTEP])
        self._verify_step(8, '', ['', TESTAS, SETVAR, '${1}'])
        self._verify_step(9, '', ['END'])
        self._verify_step(10, '', ['Log', 'Last line to move up'])

    def test_move_up_while_range_equal(self):
        self._exec(MoveRowsUp([8, 8]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', FIRSTWHILE])
        self._verify_step(2, '', ['', NOOPERATION])
        self._verify_step(3, '', ['', TESTAS, SETVAR, '${1}'])
        self._verify_step(4, '', ['', 'WHILE', TESTL3, LIMIT])
        self._verify_step(5, '', ['', '', 'Log', SECONDWHILE])
        self._verify_step(6, '', ['', '', TESTAS, SETVAR, STEST1])
        self._verify_step(7, '', ['', '', 'Log', FINALSTEP])
        self._verify_step(8, '', ['', 'END'])
        self._verify_step(9, '', ['END'])
        self._verify_step(10, '', ['Log', 'Last line to move up'])

    def test_move_up_while_range_invalid_start(self):
        self._exec(MoveRowsUp([-1, 10]))
        self._verify_step(9, '', ['END'])
        self._verify_step(10, '', ['Log', 'Last line to move up'])

    def test_move_up_while_range_invalid_end(self):
        self._exec(MoveRowsUp([10, -1]))
        self._verify_step(9, '', ['END'])
        self._verify_step(10, '', ['Log', 'Last line to move up'])

    def test_move_up_while_range_out(self):
        self._exec(MoveRowsUp([11, 0]))
        self._verify_step(9, '', ['END'])
        self._verify_step(10, '', ['Log', 'Last line to move up'])

    def test_move_up_while_range_full(self):
        self._exec(MoveRowsUp([0, 10]))
        self._verify_step(9, '', ['END'])
        self._verify_step(10, '', ['Log', 'Last line to move up'])

    def test_move_up_while_range_all_but_first(self):
        self._exec(MoveRowsUp([1, 10]))
        print("Test After MoveRowsUp:")
        for el in self._ctrl.steps:
            print(f"{el.as_list()}")
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', FINALSTEP])
        self._verify_step(8, '', ['END'])
        self._verify_step(9, '', ['Log', 'Last line to move up'])
        self._verify_step(10, '', ['WHILE', 'True', LIMIT])

    def test_move_up_while_full_sequence(self):
        self._exec(MoveRowsUp([1]))
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', ['WHILE', 'True', LIMIT])
        self._verify_step(2, '', ['', NOOPERATION])
        self._verify_step(3, '', ['', TESTAS, SETVAR, '${1}'])
        self._exec(MoveRowsUp([2]))
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', ['WHILE', 'True', LIMIT])
        self._verify_step(3, '', ['', TESTAS, SETVAR, '${1}'])
        self._verify_step(4, '', ['', 'WHILE', TESTL3, LIMIT])
        self._exec(MoveRowsUp([3]))
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', 'True', LIMIT])
        self._verify_step(4, '', ['', 'WHILE', TESTL3, LIMIT])
        self._exec(MoveRowsUp([4]))
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', 'WHILE', 'True', LIMIT])
        self._verify_step(5, '', ['', '', 'Log', SECONDWHILE])
        self._verify_step(6, '', ['', '', TESTAS, SETVAR, STEST1])
        self._exec(MoveRowsUp([5]))
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', 'WHILE', 'True', LIMIT])
        self._verify_step(6, '', ['', '', TESTAS, SETVAR, STEST1])
        self._exec(MoveRowsUp([6]))
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'WHILE', 'True', LIMIT])
        self._verify_step(7, '', ['', 'END'])
        self._exec(MoveRowsUp([7]))
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'WHILE', 'True', LIMIT])
        self._verify_step(8, '', ['', 'Log', FINALSTEP])
        self._exec(MoveRowsUp([8]))
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', FINALSTEP])
        self._verify_step(8, '', ['', 'WHILE', 'True', LIMIT])
        self._verify_step(9, '', ['END'])
        self._exec(MoveRowsUp([9]))
        # print("Test After MoveRowsUp:")
        # for el in self._ctrl.steps:
        #     print(f"{el.as_list()}")
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', FINALSTEP])
        self._verify_step(8, '', ['END'])
        self._verify_step(9, '', ['WHILE', 'True', LIMIT])
        self._verify_step(10, '', ['Log', 'Last line to move up'])
        self._exec(MoveRowsUp([10]))
        # print("Test After MoveRowsUp:")
        # for el in self._ctrl.steps:
        #     print(f"{el.as_list()}")
        self._verify_step(0, '', ['Log', FIRSTWHILE])
        self._verify_step(1, '', [NOOPERATION])
        self._verify_step(2, '', [TESTAS, SETVAR, '${1}'])
        self._verify_step(3, '', ['WHILE', TESTL3, LIMIT])
        self._verify_step(4, '', ['', 'Log', SECONDWHILE])
        self._verify_step(5, '', ['', TESTAS, SETVAR, STEST1])
        self._verify_step(6, '', ['', 'END'])
        self._verify_step(7, '', ['', 'Log', FINALSTEP])
        self._verify_step(8, '', ['END'])
        self._verify_step(9, '', ['Log', 'Last line to move up'])
        self._verify_step(10, '', ['WHILE', 'True', LIMIT])


class TryBlockMoveDown(TestCaseCommandTest):

    def _create_data(self):
        return _TEST_WITH_TRY_BLOCK[:]

    def test_move_down_try(self):
        self._exec(MoveRowsDown([0]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'TRY'])
        self._verify_step(2, '', ['', '', 'Log', EXECUTED])
        self._exec(MoveRowsDown([1]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', EXECUTED])
        self._verify_step(2, '', ['', 'TRY'])
        self._verify_step(3, '', ['', 'END'])
        self._exec(MoveRowsDown([2]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', EXECUTED])
        self._verify_step(2, '', ['', 'END'])
        self._verify_step(3, '', ['', 'TRY'])
        self._verify_step(4, '', ['EXCEPT', WHILEABRT, TSTART])
        self._exec(MoveRowsDown([3]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', EXECUTED])
        self._verify_step(2, '', ['', 'END'])
        self._verify_step(3, '', ['EXCEPT', WHILEABRT, TSTART])
        self._verify_step(4, '', ['TRY'])
        self._verify_step(5, '', ['', 'Log', LOOPNOTFINISH])
        self._exec(MoveRowsDown([4]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', EXECUTED])
        self._verify_step(2, '', ['', 'END'])
        self._verify_step(3, '', ['EXCEPT', WHILEABRT, TSTART])
        self._verify_step(4, '', ['Log', LOOPNOTFINISH])  # decreased indent
        self._verify_step(5, '', ['TRY'])
        self._verify_step(6, '', ['FINALLY'])
        self._exec(MoveRowsDown([5]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', EXECUTED])
        self._verify_step(2, '', ['', 'END'])
        self._verify_step(3, '', ['EXCEPT', WHILEABRT, TSTART])
        self._verify_step(4, '', ['Log', LOOPNOTFINISH])
        self._verify_step(5, '', ['FINALLY'])
        self._verify_step(6, '', ['TRY'])
        self._verify_step(7, '', ['', 'Log', NOMATTER])
        self._exec(MoveRowsDown([6]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', EXECUTED])
        self._verify_step(2, '', ['', 'END'])
        self._verify_step(3, '', ['EXCEPT', WHILEABRT, TSTART])
        self._verify_step(4, '', ['Log', LOOPNOTFINISH])
        self._verify_step(5, '', ['FINALLY'])
        self._verify_step(6, '', ['Log', NOMATTER])  # decreased indent
        self._verify_step(7, '', ['TRY'])
        self._verify_step(8, '', ['END'])
        self._exec(MoveRowsDown([7]))
        self._verify_step(0, '', ['WHILE', 'True', LIMIT])
        self._verify_step(1, '', ['', 'Log', EXECUTED])
        self._verify_step(2, '', ['', 'END'])
        self._verify_step(3, '', ['EXCEPT', WHILEABRT, TSTART])
        self._verify_step(4, '', ['Log', LOOPNOTFINISH])
        self._verify_step(5, '', ['FINALLY'])
        self._verify_step(6, '', ['Log', NOMATTER])  # decreased indent
        self._verify_step(7, '', ['END'])
        self._verify_step(8, '', ['TRY'])
