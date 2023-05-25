.. container:: document

   `RIDE (Robot Framework
   IDE) <https://github.com/robotframework/RIDE/>`__ v2.0.6 is a new
   release with minor enhancements and bug fixes. The reference for
   valid arguments is `Robot Framework <http://robotframework.org>`__
   installed version, which is at this moment 6.0.2. However, internal
   library is based on version 3.1.2, to keep compatibility with old
   formats.

   -  This version supports Python 3.6 up to 3.10.
   -  There are some changes, or known issues:

      -  Newlines in Grid Editor can be made visible with the `filter newlines` set to False.
      -  On Text Editor when Saving the selection of tests in Test
         Suites (Tree) is cleared.
      -  Test Suite with *\**\* Comments \**\** can be edited but
         newlines are introduced.
      -  Some argument types detection (and colorization) is not correct
         in Grid Editor.
      -  RIDE **DOES NOT KEEP** Test Suites formatting or structure,
         causing differences in files when used on other IDE or Editors.

   **New Features and Fixes Highlights**

   -  Newlines in Grid Editor can be made visible with the `filter newlines` set to False, by editing `settings.cfg`
   -  Improve auto-suggestions of keywords in Grid Editor by allowing to close suggestions list with keys ARROW_LEFT or ARROW_RIGHT
   -  Improve Text Editor auto-suggestions by using: selected text, text at left or at right of cursor


   We hope to implement or complete features and make fixes on next
   major version 2.1 (in the end of 2023).

   **The minimal wxPython version is, 4.0.7, and RIDE supports the
   current version, 4.2.0.**

   *Linux users are advised to install first wxPython from .whl package
   at*
   `wxPython.org <https://extras.wxpython.org/wxPython4/extras/linux/gtk3/>`__,
   or by using the system package manager.

   The
   `CHANGELOG.adoc <https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc>`__
   lists the changes done on the different versions.

   All issues targeted for RIDE v2.1 can be found from the `issue
   tracker
   milestone <https://github.com/robotframework/RIDE/issues?q=milestone%3Av2.1>`__.

   Questions and comments related to the release can be sent to the
   `robotframework-users <http://groups.google.com/group/robotframework-users>`__
   mailing list or to the channel #ride on `Robot Framework
   Slack <https://robotframework-slack-invite.herokuapp.com>`__, and
   possible bugs submitted to the `issue
   tracker <https://github.com/robotframework/RIDE/issues>`__. You
   should see `Robot Framework
   Forum <https://forum.robotframework.org/c/tools/ride/>`__ if your
   problem is already known.

   To install with `pip <http://pip-installer.org>`__ installed, just
   run

   .. code:: literal-block

      pip install --upgrade robotframework-ride==v2.0.6

   to install exactly this release, which is the same as using

   .. code:: literal-block

      pip install --upgrade robotframework-ride

   Alternatively you can download the source distribution from
   `PyPI <https://pypi.python.org/pypi/robotframework-ride>`__ and
   install it manually. For more details and other installation
   approaches, see the `installation
   instructions <https://github.com/robotframework/RIDE/wiki/Installation-Instructions>`__.
   If you want to help in the development of RIDE, by reporting issues
   in current development version, you can install with:

   .. code:: literal-block

      pip install -U https://github.com/robotframework/RIDE/archive/master.zip

   Important document for helping with development is the
   `CONTRIBUTING.adoc <https://github.com/robotframework/RIDE/blob/master/CONTRIBUTING.adoc>`__.

   See the `FAQ <https://github.com/robotframework/RIDE/wiki/F.A.Q.>`__
   for important info about : FOR changes and other known issues and
   workarounds.

   A possible way to start RIDE is:

   .. code:: literal-block

      python -m robotide.__init__

   You can then go to Tools>Create RIDE Desktop Shortcut, or run the
   shortcut creation script with:

   .. code:: literal-block

      python -m robotide.postinstall -install

   RIDE v2.0.6dev2 was released on 25/May/2023.
