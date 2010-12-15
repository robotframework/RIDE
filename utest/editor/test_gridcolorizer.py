import unittest
import random

from robot.utils.asserts import assert_equals
from robot.libraries.String import String


from robotide.controller.cellinfo import CellInfo, ContentType, CellType
from robotide.editor.grid import GridEditor
from robotide.editor.gridcolorizer import Colorizer

from resources import PYAPP_REFERENCE as _ #Needed to be able to create wx components

# wx needs to imported last so that robotide can select correct wx version.
import wx


class MockGrid(object):
    SetCellTextColour = SetCellBackgroundColour = SetCellFont = lambda s, x, y, z: True

    def GetCellFont(self, x, y):
        return Font()


class Font(object):
    SetWeight = lambda s, x: True


class ControllerWithCellInfo(object):
    content_types = [getattr(ContentType, i) for i in dir(ContentType) if not i.startswith('__') ]
    cell_types = [getattr(CellType, i) for i in dir(CellType) if not i.startswith('__') ]

    def __init__(self):
        self._string = String()

    def get_cell_info(self, row, column):
        return CellInfo(self._get(self.content_types), self._get(self.cell_types), 
                        self._get_data())

    def _get(self, items):
        return items[random.randint(0, len(items)-1)]

    def _get_data(self):
        if random.randint(0, 5) == 0:
            return "data with some ${variable} in there"
        return self._string.generate_random_string(50)


class TestPerformance(unittest.TestCase):
    _data = ['Keyword', 'Some longer data in cell', '${variable}', 
             '#asdjaskdkjasdkjaskdjkasjd', 'asdasd,asdasd,as asd jasdj asjd asjdj asd']

    def test_colorizing_performance(self):
        
        editor = MockGrid()
        controller = ControllerWithCellInfo()
        colorizer = Colorizer(editor, controller)
        for i in range(0, 500):
            colorizer._colorize_cell(1,1, self._data[random.randint(0, 4)])


if __name__ == '__main__':
    unittest.main()
