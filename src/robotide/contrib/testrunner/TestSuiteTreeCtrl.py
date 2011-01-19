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


import wx

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
        style |= wx.TR_AUTO_CHECK_CHILD
        style |= wx.TR_HAS_VARIABLE_ROW_HEIGHT
        style |= wx.TR_FULL_ROW_HIGHLIGHT
    else:
        style = customtreectrl.TR_HIDE_ROOT
        style |= customtreectrl.TR_HAS_BUTTONS
        style |= customtreectrl.TR_AUTO_CHECK_CHILD
        style |= customtreectrl.TR_HAS_VARIABLE_ROW_HEIGHT
        style |= customtreectrl.TR_FULL_ROW_HIGHLIGHT

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
            "default": self._image_list.Add(getWhiteBulletBitmap()),
            "running": self._image_list.Add(getBlueBulletBitmap()),
            "pass":    self._image_list.Add(getGreenBulletBitmap()),
            "fail":    self._image_list.Add(getRedBulletBitmap()),
            }
        self.SetImageList(self._image_list)

        # nodes lets us get to the node of a specific test by its
        # ID without having to traverse the whole tree
        self._nodes = {}
        self._model = None
        self._suite = None

    def CollapseAll(self):
        '''Collapse all test suite files

        This collapses all test suite files, leaving test suite
        directories expanded. The net effect is you see a list
        of suites with no test cases. I *think* that makes more
        sense than collapsing everyting, leaving only the root 
        '''
        for item in self._nodes.values():
            tcuk = self.GetItemPyData(item).tcuk
            if isinstance(tcuk, TestCaseFile):
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
            if image == self._images["fail"]:
                result.append(item)
        return result

    def GetNode(self, longname):
        item = self._nodes[longname]
        node = self.GetItemPyData(item)
        return  node

    def GetUncheckedTests(self):
        result = []
        for (testId, item) in self._nodes.iteritems():
            pydata = self.GetItemPyData(item)
            if isinstance(pydata.tcuk, TestCase) and not self.IsItemChecked(item):
                result.append(pydata.name)
        return result

    def GetCheckedTests(self):
        result = []
        for (testId, item) in self._nodes.iteritems():
            if self.IsItemChecked(item):
                result.append(self.GetItemPyData(item).name)
        return result

    def GetCheckedTestsByName(self):
        '''Return a list of (suite name, test name) tuples for all checked tests'''
        result = []
        for (testId, item) in self._nodes.iteritems():
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
            self.CheckItem(item, image == self._images["fail"])

    def SelectChildren(self):
        item = self.GetSelection()
        self.AutoCheckChild(item, True)

    def SelectNodeByName(self, longname):
        '''Select an item in the tree, given the longname of a test'''
        if longname in self._nodes:
            item = self._nodes[longname]
            self.SelectItem(item, True)

    def Reset(self):
        '''Reset the running/pass/fail state of all nodes'''
        for node in self._nodes.values():
            self.SetItemImage(node, self._images["default"])

    def SetDataModel(self, model):
        '''Set the internal data model used by the tree control'''
        self._model = model
        self._suite = model.suite

    def Redraw(self):
        '''Redraw the whole tree'''
        # before doing this I need to save state (checked/unchecked, open/closed)
        saved_state = self.SaveState()
        self.DeleteAllItems()
        self._nodes = {}
        self._root = self.AddRoot("root")
        if self._suite is not None:
            try:
                self._addSuite(self._root, self._suite)
            except Exception, e:
                print "error adding a suite:", e
            self.RestoreState(saved_state)

    def RestoreState(self, state):
        '''Restore the checked and expanded state of all known nodes in the tree'''
        for node in self._nodes.values():
            pydata = self.GetItemPyData(node)
            tcuk = pydata.tcuk
            # if we find a node for which there is no state information,
            # default to unchecked, expanded
            (checked, expanded) = state.get(tcuk, (False, True))
            self.CheckItem(node, checked)
            if expanded:
                self.Expand(node)
            else:
                self.Collapse(node)

    def SaveState(self):
        '''Return a dictionary of checked/expanded states for each node in the tree

        This was primarily designed for saving and restoring the state of
        the tree immediately before and after a refresh
        '''
        state = {}
        for node in self._nodes.values():
            tcuk = self.GetItemPyData(node).tcuk
            checked = self.IsItemChecked(node)
            expanded = self.IsExpanded(node)
            state[tcuk] = (checked, expanded)
        return state

    def SetState(self, testId, state):
        '''Set the state and associated image for a test'''
        image = self._images[state]
        node = self._nodes[testId]
        self.SetItemImage(node, self._images[state])

    def _addSuite(self, parent_node, suite):
        '''Add a suite and all its children to the tree'''
        # Note to self; ct_type 1 == checkbox, ct_type 2 == radiobutton
        suite_node = self.AppendItem(parent_node, suite.name, image=self._images["default"])
        fullname = self._get_longname(suite)
        self._nodes[fullname] = suite_node
        self.SetItemPyData(suite_node, TreeNode(fullname, suite))
        for test in suite.testcase_table:
            self._addTest(suite_node, test)

        for child in suite.children:
            self._addSuite(suite_node, child)
        self.Expand(suite_node)

    def _get_longname(self, obj):
        longname = []
        while obj is not None:
            # The darn robot object model doesn't have a simple
            # parent/child relationship between suites and test cases.
            # The parent of a test case is a test case table rather
            # than a test suite. Go figure. So, only keep track of the
            # names of suites and test cases and not the intermediate
            # objects
            if (isinstance(obj, TestDataDirectory) or 
                isinstance(obj, TestCaseFile) or 
                isinstance(obj, TestCase)):
                longname.append(obj.name)
            obj = obj.parent
        name = ".".join(reversed(longname))
        return name

    def _addTest(self, parent_node, test):
        item = self.AppendItem(parent_node, test.name, ct_type=1, image=self._images["default"])
        fullname = self._get_longname(test)
        self.SetItemPyData(item, TreeNode(fullname, test))
        self._nodes[fullname] = item


class TreeNode:
    def __init__(self, longname, tcuk):
        self.longname= longname
        self.tcuk = tcuk

    @property
    def name(self):
        return self.tcuk.name

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

