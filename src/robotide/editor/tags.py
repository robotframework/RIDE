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

import wx

from robotide.controller.ctrlcommands import ChangeTag, ClearSetting
from robotide.controller.tags import ForcedTag, DefaultTag
from robotide.context import IS_WINDOWS


class TagsDisplay(wx.lib.scrolledpanel.ScrolledPanel):

    def __init__(self, parent, controller):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, style=wx.HSCROLL)
        self._controller = controller
        self._sizer = wx.BoxSizer()
        self._tag_boxes = []
        self.SetAutoLayout(1)
        self.SetupScrolling(scroll_y=False, scrollIntoView=False)
        self.SetSizer(self._sizer)

    def add_tag(self, tag):
        self._add_tagbox(Properties(tag, self._controller))

    def _add_tagbox(self, properties):
        tagbox = TagBox(self, properties)
        self._sizer.Add(tagbox)
        self._tag_boxes.append(tagbox)

    def build(self):
        if not (self._tag_boxes and self._tag_boxes[-1].add_new):
            self.add_new_tag_tagbox(rebuild=False)
            self._remove_empty_tagboxes()
        parent_sizer = self.GetParent().GetSizer()
        if parent_sizer:
            parent_sizer.Layout()

    def clear(self):
        self.set_value(self._controller)

    def close(self):
        for tag_box in self._tag_boxes:
            tag_box.close()

    def saving(self):
        for tag_box in self._tag_boxes:
            tag_box.saving()

    def set_value(self, controller, plugin=None):
        if not self._tag_boxes:
            self._add_tags(list(controller))
        else:
            # in GTK you can have focus in a dead object
            #  .. this causes Segmentation Faults
            # Thus instead of clearing old values and adding new ones
            # modify the ones that exist
            self._modify_values(controller)
        self.build()

    def add_new_tag_tagbox(self, rebuild=True):
        self._add_tagbox(AddTagBoxProperties(self._controller.empty_tag(), self))
        if rebuild:
            self.build()

    def _add_tags(self, tags):
        for tag in tags:
            self.add_tag(tag)

    def _modify_values(self, controller):
        self._remove_empty_tagboxes()
        self._set_tags(list(controller), self._tag_boxes[:], controller)

    def _remove_empty_tagboxes(self):
        for tb in self._tag_boxes[:]:
            if tb.value == '':
                self._destroy_tagbox(tb)
                if self._modifiable_tags_count() == 0:
                    self._controller.execute(ClearSetting())

    def _modifiable_tags_count(self):
        return sum(1 for tb in self._tag_boxes[:] if tb._properties.modifiable)

    def _set_tags(self, tags, tagboxes, controller):
        if not tags:
            self._destroy_tagboxes(tagboxes)
        elif not tagboxes:
            self._add_tags(tags)
        else:
            tagboxes[0].set_properties(Properties(tags[0], controller))
            self._set_tags(tags[1:], tagboxes[1:], controller)

    def _destroy_tagboxes(self, tagboxes):
        for tb in tagboxes:
            if not tb.add_new:
                self._destroy_tagbox(tb)

    def _destroy_tagbox(self, tagbox):
        tagbox.Destroy()
        self._tag_boxes.remove(tagbox)

    def GetSelection(self):
        return None

    def get_height(self):
        return self._sizer.height


class TagBox(wx.TextCtrl):

    def __init__(self, parent, properties):
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, '', style=wx.TE_CENTER)
        self._bind()
        self.set_properties(properties)

    def _bind(self):
        for event, handler in [(wx.EVT_SET_FOCUS, self.OnSetFocus),
                               (wx.EVT_KILL_FOCUS, self.OnKillFocus),
                               (wx.EVT_LEFT_UP, self.OnSetFocus),
                               (wx.EVT_KEY_UP, self.OnKeyUp),
                               (wx.EVT_CHAR, self.OnChar)]:
            self.Bind(event, handler)

    def set_properties(self, properties):
        self._properties = properties
        self._apply_properties()

    def _apply_properties(self):
        self.SetValue(self._properties.text)
        # DEBUG wxPhoenix  self.SetToolTipString(self._properties.tooltip)
        self.MySetToolTip(self, self._properties.tooltip)
        self.SetEditable(self._properties.enabled)
        size = self._get_size()
        self.SetMaxSize(size)
        self.SetMinSize(size)
        self._colorize()

    def MySetToolTip(self, obj, tip):
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            obj.SetToolTip(tip)
        else:
            obj.SetToolTipString(tip)

    def _get_size(self):
        size = self.GetTextExtent(self.value)
        offset = 13 if IS_WINDOWS else 26  # On GTK3 labels are bigger
        return wx.Size(max(size[0]+offset, 75), max(size[1]+3, 25))

    def _colorize(self):
        self.SetForegroundColour(self._properties.foreground_color)
        self.SetBackgroundColour(self._properties.background_color)

    def close(self):
        self._update_value()

    def saving(self):
        self._update_value()

    def OnKeyUp(self, event):
        if self._properties.modifiable:
            if event.GetKeyCode() == wx.WXK_ESCAPE:
                self._cancel_editing()
            elif event.GetKeyCode() == wx.WXK_RETURN:
                self._update_value()
            elif event.GetKeyCode() == wx.WXK_DELETE:
                self.SetValue('')
        event.Skip()

    def _cancel_editing(self):
        self.SetValue(self._properties.text)
        self._colorize()

    def OnChar(self, event):
        # For some reason at least ESC and F<num> keys are considered chars.
        # We only special case ESC, though.
        if event.GetKeyCode() != wx.WXK_ESCAPE:
            self._properties.activate(self)
        event.Skip()

    def OnKillFocus(self, event):
        self._update_value()
        # Send skip event only if tagbox is empty and about to be destroyed
        # On some platforms this event is sent too late and causes crash
        if self.value != '':
            event.Skip()

    def _update_value(self):
        self._properties.change_value(self.value)

    def OnSetFocus(self, event):
        if self._properties.add_new:
            wx.CallAfter(self.SelectAll)
        event.Skip()

    @property
    def value(self):
        return self.GetValue().strip()

    @property
    def add_new(self):
        return self._properties.add_new


def Properties(tag, controller):
    if tag.controller == controller:
        return TagBoxProperties(tag)
    return tag.choose({ForcedTag: ForcedTagBoxProperties,
                       DefaultTag: DefaultTagBoxProperties})(tag)


class _TagBoxProperties(object):
    foreground_color = 'black'
    background_color = 'white'
    enabled = True
    add_new = False

    def __init__(self, tag):
        self._tag = tag

    @property
    def text(self):
        return self._tag.name or ''

    @property
    def tooltip(self):
        return self._tag.tooltip

    @property
    def modifiable(self):
        return self.enabled

    def change_value(self, value):
        if self.modifiable and value != self.text:
            self._tag.controller.execute(ChangeTag(self._tag, value))

    def activate(self, tagbox):
        pass


class TagBoxProperties(_TagBoxProperties):
    pass


class AddTagBoxProperties(_TagBoxProperties):
    foreground_color = 'gray'
    text = '<Add New>'
    tooltip = 'Click to add new tag'
    modifiable = False
    add_new = True

    def __init__(self, tag, display):
        _TagBoxProperties.__init__(self, tag)
        self._display = display

    def activate(self, tagbox):
        tagbox.set_properties(TagBoxProperties(self._tag))
        self._display.add_new_tag_tagbox()


class ForcedTagBoxProperties(_TagBoxProperties):
    foreground_color = 'red'
    background_color = '#D3D3D3'
    enabled = False


class DefaultTagBoxProperties(_TagBoxProperties):
    foreground_color = '#666666'
    background_color = '#D3D3D3'
    enabled = False
