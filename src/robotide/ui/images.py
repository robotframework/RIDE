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

from ..controller import filecontrollers
from ..controller import macrocontrollers
from ..controller import settingcontrollers

_SIZE = (16, 16)
_BASE = os.path.join(os.path.dirname(__file__), '..', 'widgets')

ROBOT_IMAGE_INDEX = 3
RUNNING_IMAGE_INDEX = 7
PASSED_IMAGE_INDEX = 8
FAILED_IMAGE_INDEX = 9
PAUSED_IMAGE_INDEX = 10
SKIPPED_IMAGE_INDEX = 11

RESOURCE_DIR = 'resource directory'


class TreeImageList(wx.ImageList):

    def __init__(self):
        wx.ImageList.__init__(self, *_SIZE)
        self._execution_results = None
        self._images = {
            filecontrollers.TestDataDirectoryController: _TreeImage(self, 'folder.png'),
            RESOURCE_DIR: _TreeImage(self, 'folder_wrench.png'),
            filecontrollers.TestCaseFileController: _TreeImage(self, 'page_white.png'),
            macrocontrollers.TestCaseController: _TreeImage(self, 'robot.png'),
            macrocontrollers.UserKeywordController: _TreeImage(self, 'cog.png'),
            filecontrollers.ResourceFileController: _TreeImage(self, 'page_white_gear.png'),
            settingcontrollers.VariableController: _TreeImage(self, 'dollar.png'),
            'running': _TreeImage(self, 'robot-running.gif'),
            'passed': _TreeImage(self, 'robot_passed.png'),
            'failed': _TreeImage(self, 'robot_failed.png'),
            'paused': _TreeImage(self, 'robot-pause.gif'),
            'skipped': _TreeImage(self, 'robot_skipped.png'),
            filecontrollers.ExcludedDirectoryController: _TreeImage(self, 'folder_excluded.png'),
            filecontrollers.ExcludedFileController: _TreeImage(self, 'folder_excluded.png')
        }

    @property
    def directory(self):
        return self._images[RESOURCE_DIR]

    def set_execution_results(self, results):
        self._execution_results = results

    def _get_image(self, controller):
        if self._execution_results.is_paused(controller):
            return self._images['paused']
        if self._execution_results.is_running(controller):
            return self._images['running']
        if self._execution_results.has_passed(controller):
            return self._images['passed']
        if self._execution_results.has_failed(controller):
            return self._images['failed']
        if self._execution_results.has_skipped(controller):
            return self._images['skipped']
        return None

    def __getitem__(self, controller):
        if controller.__class__ == macrocontrollers.TestCaseController:
            if self._execution_results:
                image = self._get_image(controller)
                if image is not None:
                    return image
        elif controller.__class__ == filecontrollers.TestDataDirectoryController:
            if not controller.contains_tests():
                return self._images[RESOURCE_DIR]
        return self._images[controller.__class__]


class _TreeImage(object):

    def __init__(self, image_list, normal, expanded=None):
        self.normal = self._get_image(image_list, normal)
        self.expanded = self._get_image(image_list, expanded) if expanded else self.normal

    @staticmethod
    def _get_image(image_list, source):
        if source.startswith('wx'):
            img = wx.ArtProvider_GetBitmap(source, wx.ART_OTHER, _SIZE)
        else:
            path = os.path.join(_BASE, source)
            if source.endswith('gif'):
                img = wx.Image(path, wx.BITMAP_TYPE_GIF).ConvertToBitmap()
            else:
                img = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        return image_list.Add(img)
