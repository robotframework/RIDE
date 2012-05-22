# Copyright 2010 Orbitz WorldWide
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import wx
import os

'''TestSuiteTreeCtrl

This is a tree control specifically for working with Robot test
suites.

Each test in the tree will have a checkbox next to it, as well as
an icon. The icon can be changed to different colors depending on
state ("default", "run", "pass", "fail").

'''

from wx.lib.embeddedimage import PyEmbeddedImage
from robot.parsing.model import TestCaseFile, TestCase, TestDataDirectory
try:
    import wx.lib.agw.customtreectrl as customtreectrl
except ImportError:
    import wx.lib.customtreectrl as customtreectrl

class TestSuiteTreeCtrl(customtreectrl.CustomTreeCtrl):
    '''A tree control designed to manage a Robot test suite'''

    if wx.VERSION <= (2,8,9):
        style=wx.SIMPLE_BORDER
        style |= wx.TR_HIDE_ROOT
        style |= wx.TR_HAS_BUTTONS
        style |= wx.TR_HAS_VARIABLE_ROW_HEIGHT
        style |= wx.TR_FULL_ROW_HIGHLIGHT
    else:
        style = customtreectrl.TR_HIDE_ROOT
        style |= customtreectrl.TR_HAS_BUTTONS
        style |= customtreectrl.TR_HAS_VARIABLE_ROW_HEIGHT
        style |= customtreectrl.TR_FULL_ROW_HIGHLIGHT

    DEFAULT_IMAGE_KEY = 'default'
    RUNNING_IMAGE_KEY = 'running'
    PASSED_IMAGE_KEY = 'pass'
    FAILED_IMAGE_KEY = 'failed'

    def __init__(self, parent, id=wx.ID_ANY, size=(-1,-1)):
        try:
            # older versions of customtreectrl don't support agwStyle
            customtreectrl.CustomTreeCtrl.__init__(self, parent, id=id,
                                                   size=size,
                                                   style=wx.SIMPLE_BORDER,
                                                   agwStyle=self.style)
        except TypeError:
            customtreectrl.CustomTreeCtrl.__init__(self, parent, id=wx.ID_ANY,
                                                   size=size,
                                                   style=self.style)

        self._image_list = wx.ImageList(16,16)
        self._images = {
            self.DEFAULT_IMAGE_KEY: self._image_list.Add(getWhiteBulletBitmap()),
            self.RUNNING_IMAGE_KEY: self._image_list.Add(getBlueBulletBitmap()),
            self.PASSED_IMAGE_KEY:  self._image_list.Add(getGreenBulletBitmap()),
            self.FAILED_IMAGE_KEY:  self._image_list.Add(getRedBulletBitmap()),
            }
        self.SetImageList(self._image_list)

        # nodes lets us get to the node of a specific test by its
        # ID without having to traverse the whole tree
        self._nodes = {}
        self._model = None
        self._suite = None
        self._is_redrawing = False

    def CollapseAll(self):
        '''Collapse all test suite files

        This collapses all test suite files, leaving test suite
        directories expanded. The net effect is you see a list
        of suites with no test cases. I *think* that makes more
        sense than collapsing everything, leaving only the root
        '''
        for item in self._nodes.values():
            data = self.GetItemPyData(item).data
            if isinstance(data, TestCaseFile):
                self.Collapse(item)

    def DeselectAll(self):
        '''De-select all items with checkboxes'''
        for item in self._nodes.values():
            self.CheckItem(item, False)

    def DeselectChildren(self):
        '''De-select all child items with checkboxes'''
        item = self.GetSelection()
        self.AutoCheckChild(item, False)

    def GetFailedTests(self):
        '''Return a list of all tree nodes of failed tests'''
        result = []
        for item in self._nodes.values():
            image = self.GetItemImage(item)
            if image == self._images[self.FAILED_IMAGE_KEY]:
                result.append(item)
        return result

    def _convert_test_longname_key(self, longname):
        if os.name == 'nt':
            parts = longname.split('.')
            return '.'.join([parent.lower() for parent in parts[:-1]]+[parts[-1]])
        return longname

    def _convert_suite_longname_key(self, longname):
        if os.name == 'nt':
            return longname.lower()
        return longname

    def GetUncheckedTests(self):
        result = []
        for item in self._nodes.values():
            pydata = self.GetItemPyData(item)
            if isinstance(pydata.data, TestCase) and not self.IsItemChecked(item):
                result.append(pydata.name)
        return result

    def GetCheckedTests(self):
        return [self.GetItemPyData(item).name for item in self._nodes.values() if self.IsItemChecked(item)]

    def GetCheckedTestsByName(self):
        '''Return a list of (suite name, test name) tuples for all checked tests'''
        result = []
        for item in self._nodes.values():
            if self.IsItemChecked(item):
                item_name = self.GetItemPyData(item).name
                parent_item = self.GetItemParent(item)
                parent_name = self.GetItemPyData(parent_item).longname
                result.append((parent_name, item_name))
        return result

    def SelectAll(self):
        '''Select all items with checkboxes'''
        for item in self._nodes.values():
            self.CheckItem(item, True)

    def SelectAllFailed(self):
        '''Select all tests that have a "fail" icon'''
        for item in self._nodes.values():
            image = self.GetItemImage(item)
            self.CheckItem(item, image == self._images[self.FAILED_IMAGE_KEY])

    def SelectChildren(self):
        item = self.GetSelection()
        self.AutoCheckChild(item, True)

    def Reset(self):
        '''Reset the running/pass/fail state of all nodes'''
        for node in self._nodes.values():
            self.SetItemImage(node, self._images[self.DEFAULT_IMAGE_KEY])

    def SetDataModel(self, model):
        '''Set the internal data model used by the tree control'''
        self._model = model
        self._suite = model.data

    def Redraw(self):
        '''Redraw the whole tree'''
        # before doing this I need to save state (checked/unchecked, open/closed)
        if self._is_redrawing:
            return
        self._is_redrawing = True
        saved_state = self.SaveState()
        self._reset_tree_state()
        def redraw_ready():
            self._is_redrawing = False
        self._draw_current_suite(saved_state, redraw_ready)

    def _draw_current_suite(self, saved_state, call_when_ready):
        if self._suite is not None:
            def call_after():
                self.RestoreState(saved_state, call_when_ready)
            self._addSuite(self._root, self._suite, call_after)
        else:
            call_when_ready()

    def _reset_tree_state(self):
        self.DeleteAllItems()
        self._nodes = {}
        self._root = self.AddRoot("root")

    def RestoreState(self, state, call_after):
        '''Restore the checked and expanded state of all known nodes in the tree'''
        def create_func(node):
            def func():
                pydata = self.GetItemPyData(node)
                data = pydata.data
                # if we find a node for which there is no state information,
                # default to unchecked, collapsed for test case files and expanded for others
                (checked, expanded) = state.get(data, (False, not isinstance(data, TestCaseFile)))
                self.CheckItem(node, checked)
                if expanded:
                    self.Expand(node)
                else:
                    self.Collapse(node)
            return func
        self._call_in_sequence([create_func(node) for node in self._nodes.values()]+[call_after])

    def _call_in_sequence(self, funcs):
        if funcs == []:
            return
        funcs[0]()
        time.sleep(0)
        wx.CallAfter(self._call_in_sequence, funcs[1:])

    def SaveState(self):
        '''Return a dictionary of checked/expanded states for each node in the tree

        This was primarily designed for saving and restoring the state of
        the tree immediately before and after a refresh
        '''
        state = {}
        for node in self._nodes.values():
            data = self.GetItemPyData(node).data
            checked = self.IsItemChecked(node)
            expanded = self.IsExpanded(node)
            state[data] = (checked, expanded)
        return state

    def SetState(self, testId, state):
        '''Set the state and associated image for a test'''
        image = self._images[state]
        node = self._nodes[self._convert_test_longname_key(testId)]
        self.SetItemImage(node, image)

    def running_test(self, testId):
        self.SetState(testId, self.RUNNING_IMAGE_KEY)

    def running_suite(self, suiteId):
        suiteId = suiteId.lower() if os.name == 'nt' else suiteId
        self.SetState(suiteId, self.RUNNING_IMAGE_KEY)

    def suite_passed(self, suiteId):
        suiteId = suiteId.lower() if os.name == 'nt' else suiteId
        self.SetState(suiteId, self.PASSED_IMAGE_KEY)

    def test_passed(self, testId):
        self.SetState(testId, self.PASSED_IMAGE_KEY)

    def suite_failed(self, suiteId):
        suiteId = suiteId.lower() if os.name == 'nt' else suiteId
        self.SetState(suiteId, self.FAILED_IMAGE_KEY)

    def test_failed(self, testId):
        self.SetState(testId, self.FAILED_IMAGE_KEY)

    def _addSuite(self, parent_node, suite, call_after):
        suite_node = self._add_suite_node(parent_node, suite)
        def expand_and_call_after():
            self.Expand(suite_node)
            call_after()
        def create_add_test(test):
            def add_test():
                self._addTest(suite_node, test)
            return add_test
        def create_add_subsuites(children):
            def add_suites():
                self._add_subsuites(suite_node, children, expand_and_call_after)
            return add_suites if len(children) > 0 else call_after
        self._call_in_sequence([create_add_test(test) for test in suite.tests]+
                               [create_add_subsuites(suite.suites)])

    def _add_suite_node(self, parent_node, suite):
        suite_node = self._suite_node(parent_node, suite.name)
        fullname = suite.longname
        self._nodes[self._convert_suite_longname_key(fullname)] = suite_node
        self.SetItemPyData(suite_node, TreeNode(fullname, suite))
        return suite_node

    def _suite_node(self, parent_node, suite_name):
        return self.AppendItem(parent_node, suite_name, image=self._images["default"])

    def _add_tests(self, suite_node, testcases):
        for test in testcases:
            wx.CallAfter(self._addTest, suite_node, test)

    def _add_subsuites(self, suite_node, children, call_after):
        number_of_children = len(children)
        if number_of_children > 0:
            delayed_call_after = self._call_when_called(number_of_children, call_after)
            for child in children:
                self._addSuite(suite_node, child, delayed_call_after)
        else:
            call_after()

    def _call_when_called(self, times, call_after):
        counter = range(times-1)
        def callable():
            if counter == []:
                call_after()
            else:
                counter.pop()
        return callable

    def _addTest(self, parent_node, test):
        item = self.AppendItem(parent_node, test.name, ct_type=1, image=self._images["default"])
        fullname = test.longname
        self.SetItemPyData(item, TreeNode(fullname, test))
        self._nodes[self._convert_test_longname_key(fullname)] = item


class TreeNode:
    def __init__(self, longname, data):
        self.longname= longname
        self.data = data.data
        self.controller = data

    @property
    def name(self):
        return self.data.name

GreenBullet = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAM1J"
    "REFUOI3tkr0OAVEQRr8VEQkJ1RLRivAKKg+xhYjWa/AcW1Ao9xGUSiIRCpFIVCob4u/ae3fu"
    "6GUKyXZiysn5TmYm4zAzklQqUfo3BGmp2Z62KgD6TOwhZlhtA46sP+vMj18JAPS71d6gnm8i"
    "ogi7cDuYrMYAMPwExRU4Zq+Wa2B92WAZLlHIFsGKPImVBdriYe546gdiaxDFL9CTxFFFASkK"
    "Duc9ytkS3IyL2/UKc9KBxIo3sIr8yWIEUuSRIphQB3Q2vsQ6/1dOLngDxfpfkNVlZ28AAAAA"
    "SUVORK5CYII=")
getGreenBulletBitmap = GreenBullet.GetBitmap

RedBullet = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAMdJ"
    "REFUOI3dkj0KwlAQhGeTPE8gCCGIxxA8R67gIYTA8xpeIZWFhaBY2VgJEgRrDdhIfkzUxJf1"
    "AL4iEhBxYLvZj91hiJnRREaj7X8GtMhGi+RTUJBbFFxMkkciW+tl5vcRkGosuVzMuZhNOfI8"
    "3oOkzqu9oGC41aAPtVmjXC0hOm2kMNzaL9wqQEUxVJyA7w9U1wwJzPoZZICfb3eA0wM7XcRR"
    "ihOEr/OSrokHMu0MGGYw3RSEEMI/w5qMOAprAT7Rrxbpm4AXDVdrGGTBi2sAAAAASUVORK5C"
    "YII=")
getRedBulletBitmap = RedBullet.GetBitmap

BlueBullet = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAL5J"
    "REFUOI3tkjsKwlAQRU9EQRDUwkpE3IC9LiRbEHcRQVeRBdhkDXaKjZ1bUEHEIj81eT97mUJI"
    "J045nDlwL+M556gytUrXvyGoS0tvTR+YYbWPKUG/ItQjdPPB5SsBMFuMbTDtwks3ONxUsNxn"
    "AItPUI5gSn/SsezOhs1J0Ws2oEx9CZUF+klcGhJlKKwj1xaKRERlQZFHx/uDURuGLUeSxZCe"
    "IwmVO1BZuNpeQeU+RQrpJSK/hhLq/V+5uuANlCtSkjpF1zcAAAAASUVORK5CYII=")
getBlueBulletBitmap = BlueBullet.GetBitmap

WhiteBullet = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAJpJ"
    "REFUOI3tkrEJw0AMRZ9DdJ0XCHisW8FrJHN4hdvL9bWyOf1USRHOEHAXokqIpwcSf5DEmbqc"
    "2v4NwbU3XNf1BsxAloSkImmZpmn9SgDM4zjezQyAbdvutVaAxyd4dEI2M/Z9x90xMyTlHtgV"
    "vLIREe/+KC9HguLupJRIKeHutNZKj+3+ICKWWiuSsiRaayUilh47/KN8XvAE8EhTts2QCn0A"
    "AAAASUVORK5CYII=")
getWhiteBulletBitmap = WhiteBullet.GetBitmap

