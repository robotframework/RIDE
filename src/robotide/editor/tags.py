from robotide.controller.tags import ForcedTag, DefaultTag, Tag
import os
import wx
from robotide.editor.flowsizer import HorizontalFlowSizer
from robotide.controller.commands import ChangeTag


class TagsDisplay(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self._sizer = HorizontalFlowSizer()
        self.SetSizer(self._sizer)

    def add_tag(self, tag, editable):
        tag_component = TagBox(self, tag)
        tag_component.SetEditable(editable)
        self._sizer.Add(tag_component)

    def build(self):
        self._sizer.SetSizeHints(self)
        parent_sizer = self.GetParent().GetSizer()
        if parent_sizer is not None:
            parent_sizer.Layout()

    def set_value(self, tags, plugin):
        self.clear()
        for tag in tags:
            self.add_tag(tag, tag.controller == tags)
        self.build()

    def clear(self):
        self._sizer.Clear(True)

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
        self._tag = tag
        self._to_text_size(tag.name)
        self._colorize(tag)

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
        self.SetForegroundColour(tag.choose({Tag:'black', ForcedTag:'red', DefaultTag:'gray'}))

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
