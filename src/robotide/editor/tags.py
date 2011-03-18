from robotide.controller.tags import ForcedTag, DefaultTag, Tag
import os
import wx
from itertools import chain
from robotide.editor.flowsizer import HorizontalFlowSizer
from robotide.controller.commands import ChangeTag


class TagsDisplay(wx.Panel):

    def __init__(self, parent, controller):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self._controller = controller
        self._sizer = HorizontalFlowSizer()
        self._tag_boxes = []
        self.SetSizer(self._sizer)

    def add_tag(self, tag, editable):
        tag_component = TagBox(self, tag)
        tag_component.SetEditable(editable)
        self._sizer.Add(tag_component)
        self._tag_boxes.append(tag_component)

    def build(self):
        self._sizer.SetSizeHints(self)
        parent_sizer = self.GetParent().GetSizer()
        if parent_sizer is not None:
            parent_sizer.Layout()

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

    def _add_new_tag(self, tags):
        self.add_tag(tags.empty_tag(), True)

    def clear(self):
        self.set_value(self._controller)

    def _create_values(self, tags):
        self._add_tags(chain(tags, [tags.empty_tag()]), tags)

    def _modify_values(self, tags):
        self._recursive_tag_set([t for t in tags]+[tags.empty_tag()], self._tag_boxes, tags)

    def _recursive_tag_set(self, tags, tbs, controller):
        if tags == []:
            return self._destroy_tagboxes(tbs)
        if tbs == []:
            return self._add_tags(tags, controller)
        tagbox = tbs[0]
        if tagbox.GetValue().strip() == '' and len(tbs) > 1:
            self._destroy_tagbox(tagbox)
            return self._recursive_tag_set(tags, tbs[1:], controller)
        t = tags[0]
        tagbox.set_tag(t)
        tagbox.SetEditable(t.controller == controller)
        return self._recursive_tag_set(tags[1:], tbs[1:], controller)

    def _destroy_tagboxes(self, tbs):
        for tagbox in tbs:
            self._destroy_tagbox(tagbox)

    def _destroy_tagbox(self, tagbox):
        tagbox.Destroy()
        self._tag_boxes.remove(tagbox)

    def _add_tags(self, tags, controller):
        for tag in tags:
            self.add_tag(tag, tag.controller == controller)

    def GetSelection(self):
        return None

    def get_height(self):
        if os.name == 'nt':
            return 80
        return self._sizer.height

class TagBox(wx.TextCtrl):

    def __init__(self, parent, tag):
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, tag.name)
        self.Bind(wx.EVT_KILL_FOCUS, self._focus_lost)
        self.Bind(wx.EVT_KEY_UP, self._key_up)
        self.set_tag(tag)

    def set_tag(self, tag):
        self._tag = tag
        if self.GetValue() != tag.name:
            self.SetValue(tag.name)
        self._to_text_size(tag.name)
        self._colorize(tag)

    def SetEditable(self, editable):
        wx.TextCtrl.SetEditable(self, editable)
        self._colorize(self._tag)

    def _key_up(self, event):
        if not self.IsEditable():
            return
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.SetValue(self._tag.name)

    def _focus_lost(self, event):
        if not self.IsEditable():
            return
        value = self.GetValue()
        if value == self._tag.name:
            return
        self._tag.controller.execute(ChangeTag(self._tag, value))

    def _to_text_size(self, text):
        size = self.GetTextExtent(text)
        new_size = wx.Size(size[0]+10, size[1]+3)
        self.SetMaxSize(new_size)
        self.SetMinSize(new_size)

    def _colorize(self, tag):
        if not self.IsEditable():
            self.SetForegroundColour(tag.choose({Tag:'black', ForcedTag:'red', DefaultTag:'gray'}))
        else:
            self.SetForegroundColour('black')

if __name__ == '__main__':
    class MyFrame(wx.Frame):
        def __init__(self, parent, id, title):
            wx.Frame.__init__(self, parent, id, title)
    class MyMenuApp( wx.App):
        def OnInit(self):
            frame = MyFrame(None , -1, 'Frame Window Demo')
            sz = wx.BoxSizer()
            display = TagsDisplay(frame)
            display.add_tag(ForcedTag('forced'))
            display.add_tag(DefaultTag('default'))
            for name in ['foo', 'bar', 'foobo', 'jee', 'huu', 'asb', 'sdfajkd', 'Sprint-1']:
                display.add_tag(Tag(name))
            display.add_tag_componen_adder()
            display.build()
            sz.Add(display, 0, wx.GROW|wx.ALL, 5)
            frame.Show(True)
            self.SetTopWindow(frame)
            return True
    # Run program
    app=MyMenuApp(0)
    app.MainLoop()
