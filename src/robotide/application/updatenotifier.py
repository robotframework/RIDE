#  Copyright 2008-2015 Nokia Solutions and Networks
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


import wx, wx.html
from robotide.utils.versioncomparator import cmp_versions
from robotide.widgets.button import ButtonWithHandler

import time
import urllib2
import xmlrpclib
import robotide.version as version

_CHECK_FOR_UPDATES_SETTING = 'check for updates'
_LAST_UPDATE_CHECK_SETTING = 'last update check'

class UpdateNotifierController(object):

    VERSION = version.VERSION
    SECONDS_IN_WEEK = 60*60*24*7

    def __init__(self, settings):
        self._settings = settings

    def notify_update_if_needed(self, update_notification_callback):
        if self._should_check() and self._is_new_version_available():
            update_notification_callback(self._newest_version, self._download_url, self._settings)

    def _should_check(self):
        if self._settings.get(_CHECK_FOR_UPDATES_SETTING, None) is None:
            self._settings[_CHECK_FOR_UPDATES_SETTING] = True
            return True
        return self._settings[_CHECK_FOR_UPDATES_SETTING] and \
               time.time() - self._settings.get(_LAST_UPDATE_CHECK_SETTING, 0) > self.SECONDS_IN_WEEK

    def _is_new_version_available(self):
        self._settings[_LAST_UPDATE_CHECK_SETTING] = time.time()
        try:
            self._newest_version = self._get_newest_version()
            self._download_url = self._get_download_url(self._newest_version)
        except Exception, e:
            print e
            #There are many possible errors:
            # - Timeout
            # - Corrupted data
            # - Server fault message
            # - Unexpected change in dataformat
            return False
        return cmp_versions(self.VERSION, self._newest_version) == -1

    def _get_newest_version(self):
        return self._get_response(('robotframework-ride',), 'package_releases')[0]

    def _get_download_url(self, version):
        return self._get_response(('robotframework-ride', version), 'release_data')['download_url']

    def _get_response(self, params, method):
        req = urllib2.Request('http://pypi.python.org/pypi', xmlrpclib.dumps(params, method), {'Content-Type':'text/xml'})
        return xmlrpclib.loads(urllib2.urlopen(req, timeout=1).read())[0][0]


class HtmlWindow(wx.html.HtmlWindow):
    def __init__(self, parent, id, size=(600,400)):
        wx.html.HtmlWindow.__init__(self,parent, id, size=size)
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()

    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())


class UpdateDialog(wx.Dialog):

    def __init__(self, version, url, settings):
        self._settings = settings
        wx.Dialog.__init__(self, None, -1, "Update available")
        sizer = wx.BoxSizer(orient=wx.VERTICAL)
        hwin = HtmlWindow(self, -1, size=(400,200))
        hwin.SetPage('New version %s available from <a href="%s">%s</a>' % (version, url, url))
        irep = hwin.GetInternalRepresentation()
        hwin.SetSize((irep.GetWidth()+25, irep.GetHeight()+20))
        sizer.Add(hwin)
        checkbox = wx.CheckBox(self, -1, label='I\'m using another method for RIDE updates\n and do not need automatic update checks')
        checkbox.Bind(wx.EVT_CHECKBOX, handler=self.OnCheckboxChange)
        sizer.Add(checkbox)
        button = ButtonWithHandler(self, label='remind me later', handler=self.OnRemindMeLater)
        sizer.Add(button)
        self.SetSizer(sizer)
        self.CentreOnParent(wx.BOTH)
        self.Fit()
        self.SetFocus()
        self.ShowModal()
        self.Destroy()

    def OnRemindMeLater(self, event):
        self.Close(True)

    def OnCheckboxChange(self, event):
        self._settings[_CHECK_FOR_UPDATES_SETTING] = not event.IsChecked()
        event.Skip()
