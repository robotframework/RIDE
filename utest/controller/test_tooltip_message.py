import unittest
from nose.tools import assert_false, assert_equals, assert_true

from robotide.utils import html_escape
from robotide.controller.cellinfo import CellInfo, CellContent, ContentType,\
    CellPosition, CellType, TipMessage, _TooltipMessage, _ForLoopTooltipMessage


class TestCellTooltip(unittest.TestCase):

    def test_empty_tooltip(self):
        cell = CellInfo(CellContent(ContentType.EMPTY, None),
                        CellPosition(CellType.UNKNOWN, None))
        assert_false(TipMessage(cell))

    def test_unknown_keyword(self):
        cell = CellInfo(CellContent(ContentType.STRING, 'What?'),
                        CellPosition(CellType.KEYWORD, None))
        msg = TipMessage(cell)
        assert_true(msg)
        assert_equals(str(msg), html_escape(_TooltipMessage.KEYWORD_NOT_FOUND))

    def test_known_keyword(self):
        cell = CellInfo(CellContent(ContentType.USER_KEYWORD, 'Known', 'my_source'),
                        CellPosition(CellType.KEYWORD, None))
        msg = TipMessage(cell)
        assert_true(msg)
        assert_equals(str(msg),
                      html_escape(_TooltipMessage.KEYWORD % 'my_source'))

    def test_for_loop_start(self):
        cell = CellInfo(CellContent(ContentType.STRING, ':FOR'),
                        CellPosition(CellType.MANDATORY, None), for_loop=True)
        assert_false(TipMessage(cell))

    def test_for_loop_var(self):
        cell = CellInfo(CellContent(ContentType.VARIABLE, '${i}'),
                        CellPosition(CellType.MANDATORY, None), for_loop=True)
        assert_false(TipMessage(cell))

    def test_unknown_variable(self):
        cell = CellInfo(CellContent(ContentType.UNKNOWN_VARIABLE, '${unknown}'),
                        CellPosition(CellType.UNKNOWN, None))
        assert_true(TipMessage(cell))

    def test_for_loop_too_many_args(self):
        cell = CellInfo(CellContent(ContentType.STRING, 'something'),
                        CellPosition(CellType.MUST_BE_EMPTY, None), for_loop=True)
        msg = TipMessage(cell)
        assert_true(msg)
        assert_equals(str(msg), _ForLoopTooltipMessage.TOO_MANY_ARGUMENTS)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
