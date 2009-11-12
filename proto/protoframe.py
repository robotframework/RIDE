import wx
from wx.lib import flatnotebook as fnb

from menu import *


class ProtoFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title='ProtoFrame')
        self.mb = MenuBar(self)
        self.mb.register_menu_entry(MenuEntry('File', 'Event', self.OnEvent,
                                              shortcut='Alt-e'))
        self.SetMenuBar(self.mb)
        self.CreateStatusBar()
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(200)
        tree = Tree(splitter)
        self.nb = fnb.FlatNotebook(splitter)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
        self.nb.AddPage(ProtoPanel(self, self.nb, 1), 'P1')
        self.nb.AddPage(ProtoPanel(self, self.nb, 2), 'P2')
        self.nb.AddPage(ProtoPanel(self, self.nb, 3, scut='Del'), 'P3')
        splitter.SplitVertically(tree, self.nb, 100)

    def OnPageChanging(self, event):
        newindex = event.GetSelection()
        if newindex <= self.nb.GetPageCount() - 1:
            self.nb.GetPage(newindex).SetFocus()

    def register_menu_entry(self, menu, name, action, container=None,
                            shortcut=None, doc=''):
        self.mb.register_menu_entry(MenuEntry(menu, name, action, container,
                                              shortcut, doc))

    def OnEvent(self):
        wx.MessageBox('Main frame')


class Tree(wx.TreeCtrl):

    def __init__(self, parent):
        wx.TreeCtrl.__init__(self, parent)
        root = self.AddRoot('root')
        self.AppendItem(root, 'Foo')


class ProtoPanel(wx.Panel):

    def __init__(self, frame, parent, id, name='Foo', scut='Ctrl-F'):
        wx.Panel.__init__(self, parent)
        handler = lambda: wx.MessageBox('panel %s' % id)
        frame.register_menu_entry('Edit', name, handler, self, scut,
                                  'Documentation')
        wx.TextCtrl(self, value='I AM PANEL %s' % id)


if __name__ == '__main__':
    app = wx.PySimpleApp()
    ProtoFrame().Show()
    app.MainLoop()
