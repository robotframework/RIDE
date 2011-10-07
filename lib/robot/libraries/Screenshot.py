#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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

import sys
import os
if sys.platform.startswith('java'):
    from java.awt import Toolkit, Robot, Rectangle
    from javax.imageio import ImageIO
    from java.io import File
else:
    try:
        import wx
        _wx_app_reference = wx.PySimpleApp()
    except ImportError:
        wx = None
    try:
        from gtk import gdk
    except ImportError:
        gdk = None
    try:
        from PIL import ImageGrab  # apparently available only on Windows
    except ImportError:
        ImageGrab = None

from robot.version import get_version
from robot import utils
from robot.libraries.BuiltIn import BuiltIn


class Screenshot(object):

    """A test library for taking screenshots and embedding them into log files.

    *Using with Jython*

    On Jython this library uses Java AWT APIs. They are always available
    and thus no external modules are needed.

    *Using with Python*

    On Python you need to have one of the following modules installed to be
    able to use this library. The first module that is found will be used.

    - wxPython :: http://wxpython.org :: Required also by RIDE so many Robot
      Framework users already have this module installed.
    - PyGTK :: http://pygtk.org :: This module is available by default on most
      Linux distributions.
    - Python Imaging Library (PIL) :: http://www.pythonware.com/products/pil ::
      This module can take screenshots only on Windows.

    Python support was added in Robot Framework 2.5.5.

    *Where screenshots are saved*

    By default screenshots are saved into the same directory where the Robot
    Framework log file is written. If no log is created, screenshots are saved
    into the directory where the XML output file is written.

    It is possible to specify a custom location for screenshots using
   `screenshot_directory` argument in `importing` and `Set Screenshot Directory`
    keyword during execution. It is also possible to save screenshots using
    an absolute path.

    Note that prior to Robot Framework 2.5.5 the default screenshot location
    was system's temporary directory.

    *Changes in Robot Framework 2.5.5 and Robot Framework 2.6*

    This library was heavily enhanced in Robot Framework 2.5.5 release. The
    changes are listed below and explained more thoroughly in affected places.

    - The support for using this library on Python (see above) was added.
    - The default location where screenshots are saved was changed (see above).
    - New `Take Screenshot` and `Take Screenshot Without Embedding` keywords
      were added. These keywords should be used for taking screenshots in
      the future. Other screenshot taking keywords will be deprecated and
      removed later.
    - `log_file_directory` argument was deprecated everywhere it was used.

    In Robot Framework 2.6, following additional changes were made:

    - `log_file_directory` argument was removed altogether.
    - `Set Screenshot Directories` keyword was removed.
    - `Save Screenshot`, `Save Screenshot To` and `Log Screenshot`
      keywords were deprecated. They will be removed in 2.7 version.
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    ROBOT_LIBRARY_VERSION = get_version()

    def __init__(self, screenshot_directory=None):
        """Configure where screenshots are saved.

        If `screenshot_directory` is not given, screenshots are saved into
        same directory as the log file. The directory can also be set using
        `Set Screenshot Directory` keyword.

        Examples (use only one of these):

        | *Setting* | *Value*  | *Value*    | *Value* |
        | Library | Screenshot |            | # Default location |
        | Library | Screenshot | ${TEMPDIR} | # System temp (this was default prior to 2.5.5) |
        """
        self._given_screenshot_dir = self._norm_path(screenshot_directory)
        self._screenshot_taker = ScreenshotTaker()

    def _norm_path(self, path):
        if not path:
            return path
        return os.path.normpath(path.replace('/', os.sep))

    @property
    def _screenshot_dir(self):
        return self._given_screenshot_dir or self._log_dir

    @property
    def _log_dir(self):
        variables = BuiltIn().get_variables()
        outdir = variables['${OUTPUTDIR}']
        log = variables['${LOGFILE}']
        log = os.path.dirname(log) if log != 'NONE' else '.'
        return self._norm_path(os.path.join(outdir, log))

    def set_screenshot_directory(self, path):
        """Sets the directory where screenshots are saved.

        It is possible to use `/` as a path separator in all operating systems.
        Path to the old directory is returned.

        The directory can also be set in `importing`.
        """
        path = self._norm_path(path)
        if not os.path.isdir(path):
            raise RuntimeError("Directory '%s' does not exist." % path)
        old = self._screenshot_dir
        self._given_screenshot_dir = path
        return old

    def save_screenshot_to(self, path):
        """*DEPRECATED* Use `Take Screenshot` or `Take Screenshot Without Embedding` instead."""
        path = self._screenshot_to_file(path)
        self._link_screenshot(path)
        return path

    def save_screenshot(self, basename="screenshot", directory=None):
        """*DEPRECATED* Use `Take Screenshot` or `Take Screenshot Without Embedding` instead."""
        path = self._save_screenshot(basename, directory)
        self._link_screenshot(path)
        return path

    def log_screenshot(self, basename='screenshot', directory=None,
                       width='100%'):
        """*DEPRECATED* Use `Take Screenshot` or `Take Screenshot Without Embedding` instead."""
        path = self._save_screenshot(basename, directory)
        self._embed_screenshot(path, width)
        return path

    def take_screenshot(self, name="screenshot", width="800px"):
        """Takes a screenshot and embeds it into the log file.

        Name of the file where the screenshot is stored is derived from `name`.
        If `name` ends with extension `.jpg` or `.jpeg`, the screenshot will be
        stored with that name. Otherwise a unique name is created by adding
        underscore, a running index and extension to the `name`.

        The name will be interpreted to be relative to the directory where
        the log file is written. It is also possible to use absolute paths.

        `width` specifies the size of the screenshot in the log file.

        The path where the screenshot is saved is returned.

        Examples: (LOGDIR is determined automatically by the library)
        | Take Screenshot |                  |     | # LOGDIR/screenshot_1.jpg (index automatically incremented) |
        | Take Screenshot | mypic            |     | # LOGDIR/mypic_1.jpg (index automatically incremented) |
        | Take Screenshot | ${TEMPDIR}/mypic |     | # /tmp/mypic_1.jpg (index automatically incremented) |
        | Take Screenshot | pic.jpg          |     | # LOGDIR/pic.jpg (always uses this file) |
        | Take Screenshot | images/login.jpg | 80% | # Specify both name and width. |
        | Take Screenshot | width=550px      |     | # Specify only width. |

        Screenshots can be only taken in JPEG format. It is possible to use `/`
        as a path separator in all operating systems.
        """
        path = self._save_screenshot(name)
        self._embed_screenshot(path, width)
        return path

    def take_screenshot_without_embedding(self, name="screenshot"):
        """Takes a screenshot and links it from the log file.

        This keyword is otherwise identical to `Take Screenshot` but the saved
        screenshot is not embedded into the log file. The screenshot is linked
        so it is nevertheless easily available.
        """
        path = self._save_screenshot(name)
        self._link_screenshot(path)
        return path

    def _save_screenshot(self, basename, directory=None):
        path = self._get_screenshot_path(basename, directory)
        return self._screenshot_to_file(path)

    def _screenshot_to_file(self, path):
        path = utils.abspath(self._norm_path(path))
        self._validate_screenshot_path(path)
        print '*DEBUG* Using %s modules for taking screenshot.' \
            % self._screenshot_taker.module
        self._screenshot_taker(path)
        return path

    def _validate_screenshot_path(self, path):
        if not os.path.exists(os.path.dirname(path)):
            raise RuntimeError("Directory '%s' where to save the screenshot does "
                               "not exist" % os.path.dirname(path))

    def _get_screenshot_path(self, basename, directory):
        directory = self._norm_path(directory) if directory else self._screenshot_dir
        if basename.lower().endswith(('.jpg', '.jpeg')):
            return os.path.join(directory, basename)
        index = 0
        while True:
            index += 1
            path = os.path.join(directory, "%s_%d.jpg" % (basename, index))
            if not os.path.exists(path):
                return path

    def _embed_screenshot(self, path, width):
        link = utils.get_link_path(path, self._log_dir)
        print '*HTML* <a href="%s"><img src="%s" width="%s"></a>' \
              % (link, link, width)

    def _link_screenshot(self, path):
        link = utils.get_link_path(path, self._log_dir)
        print "*HTML* Screenshot saved to '<a href=\"%s\">%s</a>'." % (link, path)


class ScreenshotTaker(object):

    def __init__(self, module_name=None):
        self._screenshot = self._get_screenshot_taker(module_name)
        self.module = self._screenshot.__name__.split('_')[1]

    def __call__(self, path):
        self._screenshot(path)

    def _get_screenshot_taker(self, module_name):
        if sys.platform.startswith('java'):
            return self._java_screenshot
        if module_name:
            method_name = '_%s_screenshot' % module_name.lower()
            if hasattr(self, method_name):
                return getattr(self, method_name)
        return self._get_default_screenshot_taker()

    def _get_default_screenshot_taker(self):
        for module, screenshot_taker in [(wx, self._wx_screenshot),
                                         (gdk, self._gtk_screenshot),
                                         (ImageGrab, self._pil_screenshot),
                                         (True, self._no_screenshot)]:
            if module:
                return screenshot_taker

    def _java_screenshot(self, path):
        size = Toolkit.getDefaultToolkit().getScreenSize()
        rectangle = Rectangle(0, 0, size.width, size.height)
        image = Robot().createScreenCapture(rectangle)
        ImageIO.write(image, 'jpg', File(path))

    def _wx_screenshot(self, path):
        context = wx.ScreenDC()
        width, height = context.GetSize()
        bitmap = wx.EmptyBitmap(width, height, -1)
        memory = wx.MemoryDC()
        memory.SelectObject(bitmap)
        memory.Blit(0, 0, width, height, context, -1, -1)
        memory.SelectObject(wx.NullBitmap)
        bitmap.SaveFile(path, wx.BITMAP_TYPE_JPEG)

    def _gtk_screenshot(self, path):
        window = gdk.get_default_root_window()
        if not window:
            raise RuntimeError('Taking screenshot failed')
        width, height = window.get_size()
        pb = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8, width, height)
        pb = pb.get_from_drawable(window, window.get_colormap(),
                                  0, 0, 0, 0, width, height)
        if not pb:
            raise RuntimeError('Taking screenshot failed')
        pb.save(path, 'jpeg')

    def _pil_screenshot(self, path):
        ImageGrab.grab().save(path, 'JPEG')

    def _no_screenshot(self, path):
        raise RuntimeError('Taking screenshots is not supported on this platform '
                           'by default. See library documentation for details.')


if __name__ == "__main__":
    if len(sys.argv) not in [2, 3]:
        print "Usage: %s path [wx|gtk|pil]" % os.path.basename(sys.argv[0])
        sys.exit(1)
    path = utils.abspath(sys.argv[1])
    module = sys.argv[2] if len(sys.argv) == 3 else None
    shooter = ScreenshotTaker(module)
    print 'Using %s modules' % shooter.module
    shooter(path)
    print path
