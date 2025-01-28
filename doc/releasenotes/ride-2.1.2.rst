.. container:: document

   `RIDE (Robot Framework
   IDE) <https://github.com/robotframework/RIDE/>`__ v2.1.2 is a new
   release with some enhancements and bug fixes. The reference for valid
   arguments is `Robot Framework <https://robotframework.org/>`__
   previous version, which was 7.1.1 (currently is 7.2). However,
   internal library code is originally based on version 3.1.2, but
   adapted for new versions.

   -  This version supports Python 3.8 up to 3.13.
   -  There are some changes, or known issues:

      -  🐞 - When upgrading RIDE and activate Restart, some errors are
         visible about missing /language file, and behaviour is not
         normal. Better to close RIDE and start a new instance.
      -  🐞 - Problems with COPY/PASTE in Text Editor have been reported
         when using wxPython 4.2.0, but not with version 4.2.1 and
         4.2.2, which we now *recommend*.
      -  🐞 - Rename Keywords, Find Usages/Find where used are not
         finding all occurrences. Please, double-check findings and
         changes.
      -  🐞 - Some argument types detection (and colorization) is not
         correct in Grid Editor.
      -  🐞 - RIDE **DOES NOT KEEP** Test Suites formatting or
         structure, causing differences in files when used on other IDE
         or Editors. The option to not reformat the file is not working.

   **New Features and Fixes Highlights**

   -  *Partial fix* of no update of renaming resource prefixed keywords.
      Issue #1230 from 29 Jan 2013.
   -  Fixed no recognition of keywords with embedded arguments and full
      name. Issue #1106 from 12 Sep 2012.

   **The minimal wxPython version is, 4.0.7, and RIDE supports the
   current version, 4.2.2, which we recommend.**

   *Linux users are advised to install first wxPython from .whl package
   at*
   `wxPython.org <https://extras.wxpython.org/wxPython4/extras/linux/gtk3/>`__,
   or by using the system package manager.

   The
   `CHANGELOG.adoc <https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc>`__
   lists the changes done on the different versions.

   All issues targeted for RIDE v2.2 can be found from the `issue
   tracker
   milestone <https://github.com/robotframework/RIDE/issues?q=milestone%3Av2.2>`__.

   Questions and comments related to the release can be sent to the
   `robotframework-users <https://groups.google.com/group/robotframework-users>`__
   mailing list or to the channel #ride on `Robot Framework
   Slack <https://robotframework-slack-invite.herokuapp.com>`__, and
   possible bugs submitted to the `issue
   tracker <https://github.com/robotframework/RIDE/issues>`__. You
   should see `Robot Framework
   Forum <https://forum.robotframework.org/c/tools/ride/>`__ if your
   problem is already known.

   To install the latest release with
   `pip <https://pypi.org/project/pip/>`__ installed, just run

   .. code:: literal-block

      pip install --upgrade robotframework-ride==2.1.2

   to install exactly the specified release, which is the same as using

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

      pip install -U https://github.com/robotframework/RIDE/archive/develop.zip

   Important document for helping with development is the
   `CONTRIBUTING.adoc <https://github.com/robotframework/RIDE/blob/develop/CONTRIBUTING.adoc>`__.

   To start RIDE from a command window, shell or terminal, just enter:

   ::

      ride

   You can also pass some arguments, like a path for a test suite file
   or directory.

   ::

      ride example.robot

   Another possible way to start RIDE is:

   .. code:: literal-block

      python -m robotide

   You can then go to Tools>Create RIDE Desktop Shortcut, or run the
   shortcut creation script with:

   .. code:: literal-block

      python -m robotide.postinstall -install

   or

   .. code:: literal-block

      ride_postinstall.py -install

   RIDE v2.1.2 was released on 28/January/2025.
