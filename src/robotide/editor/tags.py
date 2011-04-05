#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

# Configure wx version to allow running test app in __main__
if __name__ == '__main__':
    import robotide as _

import os
import wx

from robotide.editor.flowsizer import HorizontalFlowSizer
from robotide.controller.commands import ChangeTag
from robotide.controller.tags import ForcedTag, DefaultTag, Tag


class TagsDisplay(wx.Panel):

    def __init__(self, parent, controller):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self._controller = controller
        self._sizer = HorizontalFlowSizer()
        self._tag_boxes = []
        self.SetSizer(self._sizer)

    def add_tag(self, tag):
        tag_component = TagBox(self, tag, self._controller)
        self._sizer.Add(tag_component)
        self._tag_boxes.append(tag_component)

    def build(self):
        self._sizer.SetSizeHints(self)
        parent_sizer = self.GetParent().GetSizer()
        if parent_sizer is not None:
            parent_sizer.Layout()

    def clear(self):
        self.set_value(self._controller)

    def close(self):
        for tag_box in self._tag_boxes:
            tag_box.close()

    def set_value(self, tags, plugin=None):
        if self._tag_boxes == []:
            self._create_values(tags)
        else:
            #in GNOME you can have focus in a dead object
            #  .. this causes Segmentation Faults
            # Thus instead of clearing old values and adding new ones
            # modify the ones that exist
            self._modify_values(tags)
        self.build()

    def _create_values(self, tags):
        self._add_tags(list(tags) + [tags.empty_tag()], tags)

    def _modify_values(self, tags):
        self._recursive_tag_set(list(tags)+[tags.empty_tag()], self._tag_boxes[:], tags)

    def _recursive_tag_set(self, tags, tbs, controller):
        if tags == []:
            self._destroy_tagboxes(tbs)
            return
        if tbs == []:
            self._add_tags(tags, controller)
            return
        tagbox = tbs[0]
        if tagbox.GetValue().strip() and len(tbs) > 1:
            self._destroy_tagbox(tagbox)
            self._recursive_tag_set(tags, tbs[1:], controller)
            return
        t = tags[0]
        tagbox.set_tag(t)
        self._recursive_tag_set(tags[1:], tbs[1:], controller)

    def _destroy_tagboxes(self, tbs):
        for tagbox in tbs:
            self._destroy_tagbox(tagbox)

    def _destroy_tagbox(self, tagbox):
        tagbox.Destroy()
        self._tag_boxes.remove(tagbox)

    def _add_tags(self, tags, controller):
        for tag in tags:
            self.add_tag(tag)

    def GetSelection(self):
        return None

    def get_height(self):
        if os.name == 'nt':
            return 50
        return self._sizer.height


class TagBox(wx.TextCtrl):

    def __init__(self, parent, tag, controller):
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, '', style=wx.TE_CENTER)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self._controller = controller
        self.set_tag(tag)

    def set_tag(self, tag):
        self._tag = tag
        self._set_properties()

    def _set_properties(self, properties=None):
        self._properties = properties or self._create_properties()
        self.SetValue(self._properties.text)
        self.SetToolTipString(self._properties.tooltip)
        self.SetEditable(self._properties.enabled)
        size = self._get_size()
        self.SetMaxSize(size)
        self.SetMinSize(size)
        self._colorize()

    def _create_properties(self):
        return self._get_property_class()(self._tag)

    def _get_property_class(self):
        if self._tag.is_empty():
            return AddTagBoxProperties
        if self._tag.controller == self._controller:
            return TagBoxProperties
        return self._tag.choose({ForcedTag: ForcedTagBoxProperties,
                                 DefaultTag: DefaultTagBoxProperties})

    def _get_size(self):
        size = self.GetTextExtent(self.GetValue())
        return wx.Size(max(size[0]+10, 70), max(size[1]+3, 25))

    def _colorize(self):
        self.SetForegroundColour(self._properties.foreground_color)
        self.SetBackgroundColour(self._properties.background_color)

    def close(self):
        self._update_value()

    def OnKeyUp(self, event):
        if self._properties.modifiable:
            if event.GetKeyCode() == wx.WXK_ESCAPE:
                self._cancel_editing()
            elif event.GetKeyCode() == wx.WXK_RETURN:
                self._update_value()
                return #Crashes RIDE on Linux if event.Skip is called
        event.Skip()

    def _cancel_editing(self):
        self.SetValue(self._properties.text)
        self._colorize()

    def OnKeyDown(self, event):
        if not self._properties.modifiable:
            self.OnSetFocus(event)
        event.Skip()

    def OnKillFocus(self, event):
        self._update_value()
        # event.Skip() Can't skip on Linux as this causes crash

    def _update_value(self):
        value = self.GetValue()
        if self._properties.modifiable and value != self._tag.name:
            self._tag.controller.execute(ChangeTag(self._tag, value))

    def OnSetFocus(self, event):
        if isinstance(self._properties, AddTagBoxProperties):
            self._set_properties(TagBoxProperties(self._tag))
        event.Skip()


class _TagBoxProperties(object):
    foreground_color = 'black'
    background_color = 'white'
    enabled = True

    def __init__(self, tag=None):
        self._tag = tag

    @property
    def text(self):
        return self._tag.name or ''

    @property
    def tooltip(self):
        #TODO: Move to GUI layer and show were tag came from if possible
        return self._tag.tooltip

    @property
    def modifiable(self):
        return self.enabled



class TagBoxProperties(_TagBoxProperties):
    pass

class AddTagBoxProperties(_TagBoxProperties):
    foreground_color = 'gray'
    text = '<Add New>'
    tooltip = 'Click to add new tag'
    modifiable = False

class ForcedTagBoxProperties(_TagBoxProperties):
    foreground_color = 'red'
    background_color = '#D3D3D3'
    enabled = False

class DefaultTagBoxProperties(_TagBoxProperties):
    foreground_color = '#666666'
    background_color = '#D3D3D3'
    enabled = False


if __name__ == '__main__':
    class MyFrame(wx.Frame):
        def __init__(self, parent, id, title):
            wx.Frame.__init__(self, parent, id, title)
    class MyMenuApp( wx.App):
        def OnInit(self):
            frame = MyFrame(None , -1, 'Frame Window Demo')
            sz = wx.BoxSizer()
            display = TagsDisplay(frame, None)
            display.add_tag(ForcedTag('forced'), False)
            display.add_tag(DefaultTag('default'), False)
            for name in ['foo', 'bar', 'foobo', 'jee', 'huu', 'asb', 'sdfajkd', 'Sprint-1']:
                display.add_tag(Tag(name), True)
            display.add_tag(Tag(''), False)
            display.build()
            sz.Add(display, 0, wx.GROW|wx.ALL, 5)
            frame.Show(True)
            self.SetTopWindow(frame)
            return True
    # Run program
    app=MyMenuApp(0)
    app.MainLoop()
