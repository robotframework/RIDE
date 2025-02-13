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
import builtins
import os
import re
import subprocess
import sys
import tempfile
# Configure wx uversion to allow running test app in __main__


import time
import urllib.request as urllib2
from dataclasses import dataclass

import psutil
import requests
import wx
from wx import Colour
from os import path

from .. import version
from ..utils.versioncomparator import cmp_versions, parse_version
from ..widgets import ButtonWithHandler, HtmlWindow, RIDEDialog
from ..postinstall import MessageDialog
from ..publish import PUBLISHER, RideRunnerStopped

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

_CHECK_FOR_UPDATES_SETTING = "check for updates"
_LAST_UPDATE_CHECK_SETTING = "last update check"
SPC = "  "


class UpdateNotifierController(object):

    VERSION = version.VERSION
    SECONDS_IN_WEEK = 60*60*24*7

    def __init__(self, settings, notebook):
        self._settings = settings
        self._notebook = notebook

    def notify_update_if_needed(self, update_notification_callback, ignore_check_condition=False, show_no_update=False):
        if ignore_check_condition:
            dev_version = checking_version = True
        else:
            checking_version = self._should_check()
            dev_version = parse_version(self.VERSION).is_devrelease
        if checking_version and self._is_new_version_available():
            update_notification_callback(self._newest_version, self._download_url, self._settings, self._notebook)
        if checking_version and dev_version:
            upgrade_from_dev_dialog(version_installed=self.VERSION, notebook=self._notebook,
                                    show_no_update=show_no_update)

    def _should_check(self):
        if self._settings.get(_CHECK_FOR_UPDATES_SETTING, None) is None:
            self._settings[_CHECK_FOR_UPDATES_SETTING] = True
            return True
        return (self._settings[_CHECK_FOR_UPDATES_SETTING] and
                time.time() - self._settings.get(_LAST_UPDATE_CHECK_SETTING, 0) > self.SECONDS_IN_WEEK)

    def _is_new_version_available(self):
        self._settings[_LAST_UPDATE_CHECK_SETTING] = time.time()
        try:
            self._get_rf_pypi_data()
            self._newest_version = self._get_newest_version()
            self._download_url = self._get_download_url()
        except Exception as e:
            print(e)
            # There are many possible errors:
            #  - Timeout
            #  - Corrupted data
            #  - Server fault message
            #  - Unexpected change in dataformat
            return False
        return cmp_versions(self.VERSION, self._newest_version) == -1

    def _get_newest_version(self):
        return self.pyver

    def _get_download_url(self):
        return self.pyurl

    def _get_rf_pypi_data(self):
        resp = requests.get("https://pypi.org/simple/robotframework-ride/",
                            headers={"Accept": "application/vnd.pypi.simple.v1+json"})
        pydata = resp.json()
        self.pyver = pydata['versions'][-1]
        self.pyurl = pydata['files'][-1]['url']


def upgrade_from_dev_dialog(version_installed, notebook, show_no_update=False):
    dev_version = urllib2.urlopen('https://raw.githubusercontent.com/robotframework/'
                                  'RIDE/develop/src/robotide/version.py', timeout=1).read().decode('utf-8')
    matches = re.findall(r"VERSION\s*=\s*'([\w.]*)'", dev_version)
    version_latest = matches[0] if matches else None
    if cmp_versions(version_installed, version_latest) == -1:
        # Here is the Menu Help->Upgrade insertion part, try to highlight menu # wx.CANCEL_DEFAULT
        command = sys.executable + " -m pip install -U https://github.com/robotframework/RIDE/archive/develop.zip"
        _add_content_to_clipboard(command)
        if not _askyesno(_("Upgrade?"), f"{SPC}{_('New development version is available.')}{SPC}\n{SPC}"
                                        f"{_('You may install version %s with:') % version_latest}\n"
                                        f"{SPC}{command}{SPC}\n\n{SPC}{_('Click OK to Upgrade now!')}\n{SPC}"
                                        f"{_('After upgrade you will see another dialog informing to close this RIDE instance.')}"
                                        f"{SPC}\n", wx.GetActiveWindow(),  no_default=True):
            return False
        else:
            do_upgrade(command, notebook)
            return True
    else:
        if show_no_update:
            _askyesno(_("No Upgrade Available"), f"{SPC}{_('You have the latest version of RIDE.')}{SPC}"
                                                 f"\n\n{SPC}{_('              Have a nice day :)')}\n",
                      wx.GetActiveWindow())
        return False


def _askyesno(title, message, frame=None,  no_default=False):
    if frame is None:
        _ = wx.GetApp() or wx.App()
        parent = wx.Frame(None, size=(0, 0))
    else:
        parent = wx.Frame(frame, size=(0, 0))
    parent.CenterOnScreen()
    dlg = MessageDialog(parent, message, title, ttl=8, no_default=no_default)
    dlg.Fit()
    result = dlg.ShowModal() in [wx.ID_YES, wx.ID_OK]
    # print("DEBUG: updatenotifier _askyesno Result %s" % result)
    if dlg:
        dlg.Destroy()
    # parent.Destroy()
    return result


def _add_content_to_clipboard(content):
    wx.TheClipboard.Open()
    wx.TheClipboard.SetData(wx.TextDataObject(content))
    wx.TheClipboard.Close()


@dataclass
class RunnerCommand:
    def __init__(self, name, command, documentation):
        self.name = name
        self.command = command
        self.documentation = documentation


def do_upgrade(command, notebook):
    _add_content_to_clipboard(command)
    # print("DEBUG: Here will be the installation step.") # DEBUG 'pip list'
    from ..run import ui
    config = RunnerCommand('Upgrade RIDE', command, 'Uses pip to upgrade RIDE.')
    PUBLISHER.subscribe(start_upgraded, RideRunnerStopped)
    result = ui.Runner(config, notebook).run()
    time.sleep(10)
    if result == -1:
        _askyesno(_("Failed to Upgrade"), f"{SPC}{_('An error occurred when installing new version')}",
                  wx.GetActiveWindow())
        return False


def start_upgraded(message):
    __ = message
    import zipfile
    import requests

    def download_url(url, save_path, chunk_size=128):
        r = requests.get(url, stream=True)
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)

    backup_configobj = tempfile.NamedTemporaryFile(delete=False)
    config_obj_dir = path.join(path.dirname(__file__), '../preferences')
    # print(f"DEBUG: updatenotifier, Starting do_upgrade {config_obj_dir=} zip is {backup_configobj.name=}")
    download_url('https://robotframework.transformidea.com/RIDE/packages/configobj.zip', backup_configobj.name)
    with zipfile.ZipFile(backup_configobj, 'r') as zzip:
        zzip.extractall(config_obj_dir)
    # print(f"DEBUG: updatenotifier, {config_obj_dir=} extracted {backup_configobj.name}")
    try:
        os.remove(backup_configobj.name)
    except  PermissionError:
        pass
    command = sys.executable + " -m robotide.__init__ --noupdatecheck"
    wx.CallLater(1000, subprocess.Popen, command.split(' '), start_new_session=True)
    p = psutil.Process()
    result = _askyesno(_("Completed Upgrade"), f"\n{SPC}{_('You should close this RIDE (Process ID = ')}{p.pid}){SPC}"
                                               f"\n{SPC}{_('Do you want to CLOSE RIDE now?')}\n{SPC}",
                       wx.GetActiveWindow())
    PUBLISHER.unsubscribe(start_upgraded, RideRunnerStopped)
    if result:
        wx.CallAfter(wx.App.Get().GetTopWindow().Close)
        # wx.CallAfter(p.terminate)


class LocalHtmlWindow(HtmlWindow):
    def __init__(self, parent, size=(600, 400)):
        HtmlWindow.__init__(self, parent, size)
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            self.SetStandardFonts()

    def OnLinkClicked(self, link):  # Overrides wx method
        wx.LaunchDefaultBrowser(link.GetHref())


class UpdateDialog(RIDEDialog):

    def __init__(self, uversion, url, settings, notebook, modal=True):
        self._settings = settings
        self._notebook = notebook
        self._command = sys.executable + f" -m pip install -U robotframework-ride=={uversion}"
        _add_content_to_clipboard(self._command)
        RIDEDialog.__init__(self, title=_("Update available"), size=(600, 400),
                            style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        sizer = wx.BoxSizer(orient=wx.VERTICAL)
        hwin = LocalHtmlWindow(self, size=(600, 200))
        hwin.set_content(f"{SPC}{_('New version ')}{uversion}{_(' available from ')}<a href=\"{url}\">{url}</a><br/>"
                         f"{SPC}{_('See this version ')}<a href=\"https://github.com/robotframework/RIDE/blob/master/doc"
                         f"/releasenotes/ride-{uversion}.rst\">Release Notes</a><br/><br/>"
                         f"{SPC}{_('You can update with the command:')}<br/><b>{self._command}</b>"
                         f"<br/><br/>{SPC}{_('Or, click <b>Upgrade Now</b>')}.<br/>"
                         f"{SPC}{_('After upgrade you will see another dialog informing to close this RIDE instance.')}</b>"
                         f"<br/><br/>{SPC}{_('See the latest development ')}<a href=\"https://github.com/robotframework/RIDE"
                         f"/blob/master/CHANGELOG.adoc\">CHANGELOG</a>")
        irep = hwin.GetInternalRepresentation()
        hwin.SetSize((irep.GetWidth()+25, irep.GetHeight()+20))
        sizer.Add(hwin)
        checkbox = wx.CheckBox(self, -1, label=_("I\'m using another method for RIDE updates\n and "
                                                 "do not need automatic update checks"))
        checkbox.Bind(wx.EVT_CHECKBOX, handler=self.on_checkbox_change)
        sizer.Add(checkbox)
        hsizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        button = ButtonWithHandler(self, label=_("remind me later"), mk_handler="remind me later",
                                   handler=self.on_remind_me_later)
        button.SetBackgroundColour(Colour(self.color_secondary_background))
        button.SetForegroundColour(Colour(self.color_secondary_foreground))
        hsizer.Add(button)
        hsizer.AddSpacer(50)
        up_button = ButtonWithHandler(self, label=_("Upgrade Now"), mk_handler="Upgrade Now",
                                      handler=self.on_upgrade_now)
        up_button.SetBackgroundColour(Colour(self.color_secondary_background))
        up_button.SetForegroundColour(Colour(self.color_secondary_foreground))
        hsizer.Add(up_button)
        sizer.Add(hsizer)
        self.SetSizer(sizer)
        self.CentreOnParent(wx.BOTH)
        self.Fit()
        self.SetFocus()
        if modal:
            self.ShowModal()
            self.Destroy()
        else:
            self.Show()

    def on_remind_me_later(self, event):
        __ = event
        self.Close(True)

    def on_checkbox_change(self, event):
        self._settings[_CHECK_FOR_UPDATES_SETTING] = not event.IsChecked()
        event.Skip()

    def on_upgrade_now(self, event):
        __ = event
        _add_content_to_clipboard(self._command)
        self.Close()
        do_upgrade(self._command, self._notebook)
