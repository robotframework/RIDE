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
import sys

from robotide.run.process import Process
from robotide.widgets import Label, Font


class Runner(wx.EvtHandler):

    def __init__(self, config, notebook):
        wx.EvtHandler.__init__(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.name = config.name
        self._timer = wx.Timer(self)
        self._config = config
        self._window = self._get_output_window(notebook)

    def _get_output_window(self, notebook):
        return _OutputWindow(notebook, self)

    def run(self):
        self._process = Process(self._config.command)
        self._process.start()
        self._timer.Start(500)

    def OnTimer(self, event=None):
        finished = self._process.is_finished()
        self._window.update_output(self._process.get_output(), finished)
        if finished:
            self._timer.Stop()

    def stop(self):
        try:
            self._process.stop()
        except Exception as err:
            wx.MessageBox(str(err), style=wx.ICON_ERROR)


class _OutputWindow(wx.ScrolledWindow):

    def __init__(self, notebook, runner):
        wx.ScrolledWindow.__init__(self, notebook)
        self._create_ui()
        self._add_to_notebook(notebook, runner.name)
        self._runner = runner

    def _create_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._create_state_button())
        sizer.Add(self._create_output())
        self.SetSizer(sizer)
        self.SetScrollRate(20, 20)

    def _create_state_button(self):
        if sys.version_info[:2] >= (2,6):
            self._state_button = _StopAndRunAgainButton(self)
        else:
            self._state_button = _RunAgainButton(self)
        return self._state_button

    def _create_output(self):
        self._output = _OutputDisplay(self)
        return self._output

    def _add_to_notebook(self, notebook, name):
        notebook.add_tab(self, '%s (running)' % name, allow_closing=False)
        notebook.show_tab(self)

    def update_output(self, output, finished=False):
        if output:
            self._output.update(output)
            self.SetVirtualSize(self._output.Size)
        if finished:
            self._rename_tab('%s (finished)' % self._runner.name)
            self.Parent.allow_closing(self)
            self._state_button.enable_run_again()

    def OnStop(self):
        self._runner.stop()

    def OnRunAgain(self):
        self._output.clear()
        self._rename_tab('%s (running)' % self._runner.name)
        self.Parent.disallow_closing(self)
        self._state_button.reset()
        self._runner.run()

    def _rename_tab(self, name):
        self.Parent.rename_tab(self, name)


class _OutputDisplay(Label):

    def __init__(self, parent):
        Label.__init__(self, parent)
        self.SetFont(Font().fixed)

    def update(self, addition):
        self.SetLabel(self.LabelText + addition.decode('UTF-8', 'ignore'))

    def clear(self):
        self.SetLabel('')


class _StopAndRunAgainButton(wx.Button):

    def __init__(self, parent):
        wx.Button.__init__(self, parent, label='Stop')
        self.Bind(wx.EVT_BUTTON, self.OnClick, self)

    def OnClick(self, event):
        self.Enable(False)
        getattr(self.Parent, 'On' + self.LabelText.replace(' ', ''))()

    def enable_run_again(self):
        self.Enable()
        self.SetLabel('Run Again')

    def reset(self):
        self.Enable()
        self.SetLabel('Stop')


class _RunAgainButton(wx.Button):

    def __init__(self, parent):
        wx.Button.__init__(self, parent, label='Run Again')
        self.Bind(wx.EVT_BUTTON, self.OnClick, self)
        self.Enable(False)

    def OnClick(self, event):
        self.Parent.OnRunAgain()

    def enable_run_again(self):
        self.Enable()

    def reset(self):
        self.Enable(False)

