import os
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

IS_WINDOWS = os.sep == '\\'


class VirtualList(wx.ListCtrl, ListCtrlAutoWidthMixin):
    _style = wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VIRTUAL

    def __init__(self, parent, headers, model):
        wx.ListCtrl.__init__(self, parent, style=self._style)
        ListCtrlAutoWidthMixin.__init__(self)
        self._model = model
        self._selection_listeners = []
        self._create_headers(headers)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListItemSelected)
        if IS_WINDOWS:
            self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.SetItemCount(model.count)
        self.SetImageList(model.images, wx.IMAGE_LIST_SMALL)

    def OnLeftDown(self, event):
        item, flags =  self.HitTest(event.Position)
        if flags | wx.LIST_HITTEST_ONITEM:
            wx.CallAfter(self._force_item_selection, item)
        event.Skip()

    def _force_item_selection(self, item):
        # On Windows, wx.EVT_LIST_ITEM_SELECTED is not generated when
        # already selected item is selected again.
        self.Select(item, False)
        self.Select(item, True)

    def _create_headers(self, headers):
        for idx, name in enumerate(headers):
            self.InsertColumn(idx, name)
        self.SetColumnWidth(0, 200)
        self.SetColumnWidth(1, 160)

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)

    def OnListItemSelected(self, event):
        for listener in self._selection_listeners:
            listener(event.Index)

    def OnGetItemText(self, row, col):
        return self._model.item_text(row, col)

    def OnGetItemImage(self, item):
        return self._model.image(item)
