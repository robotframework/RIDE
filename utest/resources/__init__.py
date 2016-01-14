# The following import is needed for wx.select() to work properly
import robotide as _
import os
import sys
import wx

from mocks import FakeSettings, FakeApplication, MessageRecordingLoadObserver
from setting_utils import TestSettingsHelper

if os.sep == '\\':
    CIF = True
else:
    try:
        CIF = os.listdir('/tmp') == os.listdir('/TMP')
    except OSError:
        CIF = False

DATAPATH = os.path.join(
    os.path.abspath(os.path.split(__file__)[0]), 'robotdata')
sys.path.append(os.path.join(DATAPATH, 'put_into_python_path'))
SUITEPATH = os.path.join(DATAPATH, 'testsuite')
COMPLEX_SUITE_PATH = os.path.join(SUITEPATH, 'everything.html')
MINIMAL_SUITE_PATH = os.path.join(SUITEPATH, 'minimal.html')
NO_RIDE_PATH = os.path.join(DATAPATH, 'no_ride', 'no_ride.html')
NO_RIDE_RESOURCE_PATH = os.path.join(
    DATAPATH, 'no_ride', 'no_ride_resource.html')
_RESOURCE_DIR = os.path.join(DATAPATH, 'resources')
RELATIVE_PATH_TO_RESOURCE_FILE = os.path.join('resources', 'resource.html')
RESOURCE_PATH = os.path.normpath(
    os.path.join(DATAPATH, RELATIVE_PATH_TO_RESOURCE_FILE))
RESOURCE_PATH2 = os.path.normpath(
    os.path.join(_RESOURCE_DIR, 'resource2.html'))
RESOURCE_PATH3 = os.path.normpath(
    os.path.join(_RESOURCE_DIR, 'resource3.html'))
RESOURCE_PATH_TXT = os.path.normpath(
    os.path.join(_RESOURCE_DIR, 'resource.txt'))
INVALID_PATH = os.path.join(SUITEPATH, 'invalid.html')
EXTERNAL_RES_UNSORTED_PATH = os.path.join(
    DATAPATH, 'external_resources_unsorted', 'suite')

PATH_RESOURCE_NAME = 'pathresource.html' if CIF else 'PathResource.html'

PYAPP_REFERENCE = wx.App()
