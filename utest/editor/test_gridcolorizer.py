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

import unittest
import random

import pytest

from robotide.lib.robot.libraries.String import String

from robotide.controller.cellinfo import CellInfo, ContentType, CellType, CellContent, CellPosition, UPPERCASE_KWS
from robotide.editor.gridcolorizer import Colorizer


class MockGrid(object):
    noop = lambda *args: None
    SetCellTextColour = SetCellBackgroundColour = SetCellFont = noop
    settings = None

    def GetCellFont(self, x, y):
        return Font()


class Font(object):
    SetWeight = lambda s, x: True


class ControllerWithCellInfo(object):
    content_types = [getattr(ContentType, i) for i in
                     dir(ContentType) if not i.startswith('__') ]
    cell_types = [getattr(CellType, i) for i in
                  dir(CellType) if not i.startswith('__') ]

    def __init__(self):
        self._string = String()

    def get_cell_info(self, row, column):
        return CellInfo(CellContent(self._get(self.content_types), self._get_data(), None),
                        CellPosition(self._get(self.cell_types), None))

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
        colorizer = Colorizer(MockGrid(), ControllerWithCellInfo())
        for _ in range(0, 500):
            colorizer._colorize_cell(1,1, self._data[random.randint(0, 4)])


@pytest.mark.skip('Needs to be fixed')
class TestColorIdentification(unittest.TestCase):
    _type = CellInfo(CellContent(CellType.UNKNOWN, ''), CellPosition(CellType.UNKNOWN, ''))
    _data = ['Log', 'FOR', 'try', 'for']
    colorizer = None

    def setup(self):
        self.colorizer = Colorizer(MockGrid(), ControllerWithCellInfo())
        for x in range(0, 5):
            self.colorizer._colorize_cell(x, 1, self._data[random.randint(0, 4)])

    def test_unknown(self):
        color = self.colorizer._get_text_color(self._data)
        print(f"DEBUG: color={color.title()}")


if __name__ == '__main__':
    unittest.main()
