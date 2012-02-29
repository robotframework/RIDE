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
if __name__ == '__main__':
    import robotide as _

import urllib2
import wx
import xmlrpclib
from robotide.version import VERSION

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
        if VERSION >= version:
            return False
        url = get_download_url(version)
        wx.MessageBox(version + ' ' + url)
        print version, url
    except urllib2.URLError:
        print 'timeout'

if __name__ == '__main__':
    class MyMenuApp( wx.App):
        def OnInit(self):
            wx.Frame(None, -1, 'frame')
            should_update()
            return True
    # Run program
    app=MyMenuApp(0)
    app.MainLoop()
