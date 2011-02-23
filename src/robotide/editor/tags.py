from robotide.controller.tags import ForcedTag, DefaultTag, Tag
import wx
from robotide.editor.flowsizer import FlowSizer


class TagsDisplay(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self._sizer = FlowSizer()
        self.SetSizer(self._sizer)

    def add_tag(self, tag):
        tag_component = TagBox(self, tag)
        self._sizer.Add(tag_component)

    def build(self):
        self._sizer.SetSizeHints(self)

    def set_value(self, tags, plugin):
        print tags
        self.clear()
        for tag in tags:
            print tag
            self.add_tag(tag)
        self.build()

    def clear(self):
        self._sizer.Clear(True)

    def get_height(self):
        return self._sizer.height

class TagBox(wx.TextCtrl):

    def __init__(self, parent, tag):
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, tag.name)
        self._to_text_size(tag.name)
        self._colorize(tag)
        self.SetEditable(False)

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
