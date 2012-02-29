#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
import time


if __name__ == '__main__':
    import robotide as _

import urllib2
import wx, wx.html
import xmlrpclib
from robotide.version import VERSION
from robotide.widgets.button import ButtonWithHandler

class UpdateNotifierController(object):

    def __init__(self, settings):
        self._settings = settings

    def should_check(self):
        return self._settings['check for updates'] and time.time() - self._settings['last update check'] > 60*60*24*7

    def is_new_version_available(self):
        self._settings['last update check'] = time.time()
        return True

    def get_new_version_information(self):
        return 'new version', 'download url'

def _get_response(params, method):
    req = urllib2.Request('http://pypi.python.org/pypi', xmlrpclib.dumps(params, method), {'Content-Type':'text/xml'})
    return xmlrpclib.loads(urllib2.urlopen(req, timeout=1).read())[0][0]

def get_newest_version():
    return _get_response(('robotframework-ride',), 'package_releases')[0]

def get_download_url(version):
    return _get_response(('robotframework-ride', version), 'release_data')['download_url']

def should_update():
    try:
        version = get_newest_version()
        #if VERSION >= version:
        #    return False
        url = get_download_url(version)
        return version, url
    except urllib2.URLError:
        print 'timeout'

if __name__ == '__main__':

    class MyMenuApp( wx.App):

        def OnInit(self):
            wx.Frame(None, -1, 'frame')
            u = UpdateDialog(*should_update())
            u.ShowModal()
            u.Destroy()
            return True

    class HtmlWindow(wx.html.HtmlWindow):
        def __init__(self, parent, id, size=(600,400)):
            wx.html.HtmlWindow.__init__(self,parent, id, size=size)
            if "gtk2" in wx.PlatformInfo:
                self.SetStandardFonts()

        def OnLinkClicked(self, link):
            wx.LaunchDefaultBrowser(link.GetHref())

    class UpdateDialog(wx.Dialog):

        def __init__(self, version, url):
            wx.Dialog.__init__(self, None, -1, "Update available")
            sizer = wx.BoxSizer(orient=wx.VERTICAL)
            hwin = HtmlWindow(self, -1, size=(400,200))
            hwin.SetPage('New version %s available from <a href="%s">%s</a>' % (version, url, url))
            irep = hwin.GetInternalRepresentation()
            hwin.SetSize((irep.GetWidth()+25, irep.GetHeight()+10))
            sizer.Add(hwin)
            checkbox = wx.CheckBox(self, -1, label='do not check for updates')
            sizer.Add(checkbox)
            button = ButtonWithHandler(self, label='remind me later', handler=self.OnRemindMeLater)
            sizer.Add(button)
            self.SetSizer(sizer)
            self.CentreOnParent(wx.BOTH)
            self.Fit()
            self.SetFocus()

        def OnRemindMeLater(self, event):
            self.Close(True)

    # Run program
    app=MyMenuApp(0)
    app.MainLoop()
