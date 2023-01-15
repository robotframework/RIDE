`RIDE (Robot Framework IDE)`_ v2.0b3 is a new release with major enhancements and bug fixes.
This version v2.0b3 includes removal of Python 2.7 support. The reference for valid arguments is `Robot Framework`_ installed version, which is at this moment 6.0.2. However, internal library is based on version 3.1.2, to keep compatibility with old formats.

* This is the **first version without support for Python 2.7**.
* The last version with support for Python 2.7 was **1.7.4.2**.
* Support for Python 3.6 up to 3.10 (current version on this date).
* There are some important changes, or known issues:

  - On MacOS to call autocomplete in Grid and Text Editors, you have to use Alt-Space (not Command-Space).
  - On Linux and Windows to call autocomplete in Grid and Text Editors, you have to use Ctrl-Space.
  - On Text Editor the TAB key adds the defined number of spaces. With Shift moves to the left, and together with Control selects text.
  - On Text Editor the **: FOR** loop structure must use Robot Framework 3.1.2 syntax, i.e. **FOR** and **END**.
  - On Grid Editor and Linux the auto enclose is only working on cell selection, but not on cell content edit.
  - On Text Editor when Saving the selection os tests in Test Suites (Tree) is cleared.

**New Features and Fixes Highlights**

* Auto enclose text in {}, [], "", ''
* Auto indent in Text Editor on new lines
* Block indent in Text Editor (TAB on block of selected text)
* Ctrl-number with number, 1-5 also working on Text Editor:

  1. create scalar variable
  2. create list variable
  3. Comment line (with Shift comment content with #)
  4. Uncomment line (with Shift uncomment content with #)
  5. create dictionary variable

* Persistence of the position and state of detached panels, File Explorer and Test Suites
* File Explorer and Test Suites panels are now Plugins and can be disabled or enabled and made Visible with F11 ( Test Suites with F12, but disabled for now)
* File Explorer now shows selected file when RIDE starts
* Block comment and uncomment on both Grid and Text editors
* Extensive color customization of panel elements via `Tools>Preferences`
* Color use on Console and Messages Log panels on Test Run tab

Please note, that the features and fixes are not yet closed. This pre-release is being done because it has important fixes.

**The minimal wxPython version is, 4.0.7, and RIDE supports the current version, 4.2.0.**

*Linux users are advised to install first wxPython from .whl package at* `wxPython.org`_.

The `CHANGELOG.adoc`_ lists the changes done on the different versions.

All issues targeted for RIDE v2.0 can be found
from the `issue tracker milestone`_.

Questions and comments related to the release can be sent to the
`robotframework-users`_ mailing list or to the channel #ride on 
`Robot Framework Slack`_, and possible bugs submitted to the `issue tracker`_.
You should see `Robot Framework Forum`_ if your problem is already known.

If you have pip_ installed, just run

::

   pip install --pre --upgrade robotframework-ride==2.0b3

to install this **BETA** release, and for the **final** release use

::

   pip install --upgrade robotframework-ride

::

   pip install robotframework-ride==2.0

to install exactly the **final** version. Alternatively you can download the source
distribution from PyPI_ and install it manually. For more details and other
installation approaches, see the `installation instructions`_.
If you want to help in the development of RIDE, by reporting issues in current development version, you can install with:

::

  pip install -U https://github.com/robotframework/RIDE/archive/master.zip

Important document for helping with development is the `CONTRIBUTING.adoc_`.

See the `FAQ`_ for important info about `: FOR` changes and other known issues and workarounds.

A possible way to start RIDE is:

::

    python -m robotide.__init__

You can then go to `Tools>Create RIDE Desktop Shortcut`, or run the shortcut creation script with:

::

    python -m robotide.postinstall -install

RIDE v2.0b3 was released on 15/Jan/2023.

.. _RIDE (Robot Framework IDE): https://github.com/robotframework/RIDE/
.. _Robot Framework: http://robotframework.org
.. _pip: http://pip-installer.org
.. _PyPI: https://pypi.python.org/pypi/robotframework-ride
.. _issue tracker milestone: https://github.com/robotframework/RIDE/issues?q=milestone%3Av2.0
.. _issue tracker: https://github.com/robotframework/RIDE/issues
.. _robotframework-users: http://groups.google.com/group/robotframework-users
.. _Robot Framework Forum: https://forum.robotframework.org/c/tools/ride/
.. _Robot Framework Slack: https://robotframework-slack-invite.herokuapp.com
.. _installation instructions: https://github.com/robotframework/RIDE/wiki/Installation-Instructions
.. _wxPython.org: https://extras.wxpython.org/wxPython4/extras/linux/gtk3/
.. _FAQ: https://github.com/robotframework/RIDE/wiki/F.A.Q.
.. _CHANGELOG.adoc: https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc
.. _CONTRIBUTING.adoc: https://github.com/robotframework/RIDE/blob/master/CONTRIBUTING.adoc
