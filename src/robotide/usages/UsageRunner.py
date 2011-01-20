from robotide.usages.commands import FindUsages
from robotide.usages.usagesdialog import UsagesDialogWithUserKwNavigation
from threading import Thread
import wx
import time

class Usages(object):

    def __init__(self, controller, highlight, name=None, kw_info=None):
        self._name = name or controller.name
        self._kw_info = kw_info
        self._controller = controller
        self._highlight = highlight
        self._dlg = UsagesDialogWithUserKwNavigation(self._name)
        self._worker = Thread(target=self._run)
        self._dialog_closed = False

    def show(self):
        self._dlg.add_selection_listener(self._highlight)
        self._dlg.Bind(wx.EVT_CLOSE, self._stop)
        self._dlg.Show()
        self._worker.start()

    def _run(self):
        wx.CallAfter(self._begin_search)
        for usage in self._controller.execute(FindUsages(self._name, self._kw_info)):
            time.sleep(0) # GIVE SPACE TO OTHER TRHEADS -- Thread.yield in Java
            if self._dialog_closed: return
            wx.CallAfter(self._add_usage, usage)
        wx.CallAfter(self._end_search)

    def _begin_search(self):
        if not self._dialog_closed:
            self._dlg.begin_searching()

    def _add_usage(self, usage):
        if not self._dialog_closed:
            self._dlg.add_usage(usage)

    def _end_search(self):
        if not self._dialog_closed:
            self._dlg.end_searching()

    def _stop(self, event):
        self._dialog_closed = True
        event.Skip()