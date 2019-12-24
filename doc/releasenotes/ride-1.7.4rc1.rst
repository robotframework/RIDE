============================
Robot Framework IDE 1.7.4rc1
============================


.. default-role:: code


`RIDE (Robot Framework IDE)`_ 1.7.4rc1 is a new release with major enhancements
and bug fixes. This version 1.7.4rc1 includes fixes for installer, Font Type selection, Text Editor improvements and new File explorer.
The reference for valid arguments is `Robot Framework`_ version 3.1.2.

* This is the **last version supporting Python 2.7**.
* A new File Explorer allows to open supported file types in RIDE, or other types in a basic code editor. To open a file you must double-click on it (project folders open with right-click after being highlighted with left-click). If it is a supported file format but not with the correct structure (for example a resource file), an error message is shown, and then opens in code editor.
* On Grid Editor, the cells can be autoajusting with wordwrap. There is a new checkbox in `Tools>Preferences>Grid Editor`.
* Font Type selection is available for all Editors and Run panels.
* Zoom in and zoom out is possible on Text Editor and Run panels.
* Pressing the Ctrl on the Grid Editor, when over a keyword it will show its documentation (that can be detached with mouse click).
* There are some important changes, or known issues:

  - On MacOS to call autocomplete in Grid and Text Editors, you have to use Alt-Space (not Command-Space)

  - On Linux and Windows to call autocomplete in Grid and Text Editors, you have to use Ctrl-Space

  - On Text Editor the TAB key adds the defined number of spaces. With Shift moves to the left, and together with Control selects text.

  - On Text Editor the **: FOR** loop structure must use Robot Framework 3.1.2 syntax, i.e. **FOR** and **END**. The only solution to disable this, is to disable Text Editor Plugin.

**THIS IS THE LAST RELEASE SUPPORTING PYTHON 2.7**

**wxPython will be updated to current version 4.0.7post2**

*Linux users are advised to install first wxPython from .whl package at* `wxPython.org`_.


All issues targeted for RIDE v1.7.4rc1 can be found
from the `issue tracker milestone`_.

Questions and comments related to the release can be sent to the
`robotframework-users`_ mailing list or to the channel #ride on 
`Robot Framework Slack`_, and possible bugs submitted to the `issue tracker`_.

If you have pip_ installed, just run

::

   pip install --upgrade robotframework-ride==1.7.4rc1

to install this **RELEASE CANDIDATE** release, and for the **final** release use

::

   pip install --upgrade robotframework-ride

::

   pip install robotframework-ride==1.7.4

to install exactly the **final** version. Alternatively you can download the source
distribution from PyPI_ and install it manually. For more details and other
installation approaches, see the `installation instructions`_.
See the `FAQ`_ for important info about `: FOR` changes.

A possible way to start RIDE is:

::

    python -m robotide.__init__

You can then go to `Tools>Create RIDE Desktop Shortcut`, or run the shortcut creation script with:

::

    python -m robotide.postinstall -install

RIDE 1.7.4rc1 was released on Tuesday December 24, 2019.

.. _RIDE (Robot Framework IDE): https://github.com/robotframework/RIDE/
.. _Robot Framework: http://robotframework.org
.. _pip: http://pip-installer.org
.. _PyPI: https://pypi.python.org/pypi/robotframework-ride
.. _issue tracker milestone: https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.4
.. _issue tracker: https://github.com/robotframework/RIDE/issues
.. _robotframework-users: http://groups.google.com/group/robotframework-users
.. _Robot Framework Slack: https://robotframework-slack-invite.herokuapp.com
.. _installation instructions: ../../INSTALL.rst
.. _wxPython.org: https://extras.wxpython.org/wxPython4/extras/linux/gtk3/
.. _FAQ: https://github.com/robotframework/RIDE/wiki/F.A.Q.


.. contents::
   :depth: 2
   :local:
