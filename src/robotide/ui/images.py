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
import wx
from robotide.controller.settingcontrollers import VariableController
from robotide.controller.macrocontrollers import TestCaseController, UserKeywordController
from robotide.controller.filecontrollers import TestDataDirectoryController, TestCaseFileController, ResourceFileController, ExcludedDirectoryController


_SIZE = (16, 16)
_BASE = os.path.join(os.path.dirname(__file__), '..', 'widgets')

ROBOT_IMAGE_INDEX = 3
RUNNING_IMAGE_INDEX = 7
PASSED_IMAGE_INDEX = 8
FAILED_IMAGE_INDEX = 9
PAUSED_IMAGE_INDEX = 10


class TreeImageList(wx.ImageList):

    def __init__(self):
        wx.ImageList.__init__(self, *_SIZE)
        self._execution_results = None
        self._images = {
            TestDataDirectoryController: _TreeImage(self, 'folder.png'),
            'resource directory': _TreeImage(self, 'folder_wrench.png'),
            TestCaseFileController: _TreeImage(self, 'page_white.png'),
            TestCaseController: _TreeImage(self, 'robot.png'),
            UserKeywordController: _TreeImage(self, 'cog.png'),
            ResourceFileController: _TreeImage(self, 'page_white_gear.png'),
            VariableController: _TreeImage(self, 'dollar.png'),
            'running': _TreeImage(self, 'robot-running.gif'),
            'passed': _TreeImage(self, 'robot_passed.png'),
            'failed': _TreeImage(self, 'robot_failed.png'),
            'paused': _TreeImage(self, 'robot-pause.gif'),
            ExcludedDirectoryController: _TreeImage(self, 'folder_excluded.png')
        }
# 'running': _TreeImage(self, 'robot_running.png'),
    @property
    def directory(self):
        return self._images['resource directory']

    def set_execution_results(self, results):
        self._execution_results = results

    def __getitem__(self, controller):
        if controller.__class__ == TestCaseController:
            if self._execution_results:
                if self._execution_results.is_paused(controller):
                    return self._images['paused']
                if self._execution_results.is_running(controller):
                    return self._images['running']
                if self._execution_results.has_passed(controller):
                    return self._images['passed']
                if self._execution_results.has_failed(controller):
                    return self._images['failed']
        elif controller.__class__ == TestDataDirectoryController:
            if not controller.contains_tests():
                return self._images['resource directory']
        return self._images[controller.__class__]


class _TreeImage(object):

    def __init__(self, image_list, normal, expanded=None):
        self.normal = self._get_image(image_list, normal)
        self.expanded = self._get_image(image_list, expanded) if expanded else self.normal

    def _get_image(self, image_list, source):
        if source.startswith('wx'):
            img = wx.ArtProvider_GetBitmap(source, wx.ART_OTHER, _SIZE)
        else:
            path = os.path.join(_BASE, source)
            if source.endswith('gif'):
                img = wx.Image(path, wx.BITMAP_TYPE_GIF).ConvertToBitmap()
            else:
                img = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        return image_list.Add(img)
