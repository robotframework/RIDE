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

    def clear(self):
        self.set_value(self._controller)

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
        self._add_tags(chain(tags, [tags.empty_tag()]), tags)

    def _modify_values(self, tags):
        self._recursive_tag_set([t for t in tags]+[tags.empty_tag()], self._tag_boxes[:], tags)

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
        tagbox.SetEditable(t.controller == controller and not t.is_empty())
        return self._recursive_tag_set(tags[1:], tbs[1:], controller)

    def _destroy_tagboxes(self, tbs):
        for tagbox in tbs:
            self._destroy_tagbox(tagbox)

    def _destroy_tagbox(self, tagbox):
        tagbox.Destroy()
        self._tag_boxes.remove(tagbox)

    def _add_tags(self, tags, controller):
        for tag in tags:
            self.add_tag(tag, tag.controller == controller and not tag.is_empty())

    def GetSelection(self):
        return None

    def get_height(self):
        if os.name == 'nt':
            return 50
        return self._sizer.height


class TagBox(wx.TextCtrl):

    ADD_TEXT = ' Add '
    ADD_BACKGROUND = '#C2DFFF'
    NOT_EDITABLE_BACKGROUND = '#D3D3D3'

    def __init__(self, parent, tag):
        wx.TextCtrl.__init__(self, parent, wx.ID_ANY, self._get_text_value(tag),
                             style=wx.TE_CENTER)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.set_tag(tag)

    def set_tag(self, tag):
        self._tag = tag
        if tag.is_empty() or self.GetValue() != tag.name:
            self.SetValue(self._get_text_value())
        self._to_text_size(self._get_text_value())
        self._colorize(tag)

    def SetEditable(self, editable):
        wx.TextCtrl.SetEditable(self, editable)
        self._colorize(self._tag)

    def OnKeyUp(self, event):
        if self.IsEditable():
            if event.GetKeyCode() == wx.WXK_ESCAPE:
                self._cancel_editing()
            elif event.GetKeyCode() == wx.WXK_RETURN:
                self._update_value()
                return #Crashes RIDE on Linux if event.Skip is called
        event.Skip()

    def _cancel_editing(self):
        self.SetValue(self._get_text_value())
        if self._tag.is_empty():
            self.SetEditable(False)
            self._colorize(self._tag)

    def OnKeyDown(self, event):
        if not self.IsEditable():
            self.OnSetFocus(event)
        event.Skip()

    def _get_text_value(self, tag=None):
        if tag is None:
            tag = self._tag
        if tag.is_empty():
            return TagBox.ADD_TEXT
        return tag.name

    def OnKillFocus(self, event):
        if self.IsEditable():
            self._update_value()
        # event.Skip() Can't skip on Linux as this causes crash

    def _update_value(self):
        value = self.GetValue()
        if value != self._tag.name:
            self._tag.controller.execute(ChangeTag(self._tag, value))

    def OnSetFocus(self, event):
        if self._tag.is_empty():
            self.SetEditable(True)
            self.SetValue('')
            self._colorize(self._tag)
        event.Skip()

    def _to_text_size(self, text):
        if text == '':
            new_size = wx.Size(75, 25)
        else:
            size = self.GetTextExtent(text)
            new_size = wx.Size(size[0]+10, max(size[1]+3, 25))
        self.SetMaxSize(new_size)
        self.SetMinSize(new_size)

    def _colorize(self, tag):
        if not self.IsEditable():
            if tag.is_empty():
                self.SetForegroundColour('black')
                self.SetBackgroundColour(TagBox.ADD_BACKGROUND)
            else:
                self.SetForegroundColour(tag.choose({Tag:'black', ForcedTag:'red', DefaultTag:'#666666'}))
                self.SetBackgroundColour(TagBox.NOT_EDITABLE_BACKGROUND)
        else:
            self.SetForegroundColour('black')
            self.SetBackgroundColour('white')


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
