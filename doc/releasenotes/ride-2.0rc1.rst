.. container:: document

   `RIDE (Robot Framework
   IDE) <https://github.com/robotframework/RIDE/>`__ v2.0rc1 is a new
   release with major enhancements and bug fixes. This version v2.0rc1
   includes removal of Python 2.7 support. The reference for valid
   arguments is `Robot Framework <http://robotframework.org>`__
   installed version, which is at this moment 6.0.2. However, internal
   library is based on version 3.1.2, to keep compatibility with old
   formats.

   -  This is the **first version without support for Python 2.7**.
   -  The last version with support for Python 2.7 was **1.7.4.2**.
   -  Support for Python 3.6 up to 3.10 (current version on this date).
   -  There are some important changes, or known issues:

      -  On MacOS to call autocomplete in Grid and Text Editors, you
         have to use Alt-Space (not Command-Space).
      -  On Linux and Windows to call autocomplete in Grid and Text
         Editors, you have to use Ctrl-Space.
      -  On Text Editor the TAB key adds the defined number of spaces.
         With Shift moves to the left, and together with Control selects
         text.
      -  Text Editor also accepts the old **: FOR** loop structure, but
         recommended is **FOR** and **END**.
      -  On Grid Editor and Linux the auto enclose is only working on
         cell selection, but not on cell content edit.
      -  On Text Editor when Saving the selection of tests in Test
         Suites (Tree) is cleared.
      -  Test Suite with *\**\* Comments \**\** can be edited but
         newlines are introduced.
      -  Some argument types detection (and colorization) is not correct
         in Grid Editor.
      -  RIDE **DOES NOT KEEP** Test Suites formatting or structure,
         causing differences in files when used on other IDE or Editors.

   **New Features and Fixes Highlights**

   -  Auto enclose text in {}, [], "", ''
   -  Auto indent in Text Editor on new lines
   -  Block indent in Text Editor (TAB on block of selected text)
   -  Ctrl-number with number, 1-5 also working on Text Editor:

      #. create scalar variable
      #. create list variable
      #. Comment line (with Shift comment content with #)
      #. Uncomment line (with Shift uncomment content with #)
      #. create dictionary variable

   -  Persistence of the position and state of detached panels, File
      Explorer and Test Suites
   -  File Explorer and Test Suites panels are now Plugins and can be
      disabled or enabled and made Visible with F11 ( Test Suites with
      F12, but disabled for now)
   -  File Explorer now shows selected file when RIDE starts
   -  Block comment and uncomment on both Grid and Text editors
   -  Extensive color customization of panel elements via
      Tools>Preferences
   -  Color use on Console and Messages Log panels on Test Run tab
   -  In Text Editor the same commands as in Grid Editor are now
      supported: Move Up/Down Rows, Insert or Delete Rows and Insert or
      Delete 'Cells'

   We hope to implement or complete features and make fixes on next
   version 2.1 (in the end of 2023).

   **The minimal wxPython version is, 4.0.7, and RIDE supports the
   current version, 4.2.0.**

   *Linux users are advised to install first wxPython from .whl package
   at*
   `wxPython.org <https://extras.wxpython.org/wxPython4/extras/linux/gtk3/>`__.

   The
   `CHANGELOG.adoc <https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc>`__
   lists the changes done on the different versions.

   All issues targeted for RIDE v2.0 can be found from the `issue
   tracker
   milestone <https://github.com/robotframework/RIDE/issues?q=milestone%3Av2.0>`__.

   Questions and comments related to the release can be sent to the
   `robotframework-users <http://groups.google.com/group/robotframework-users>`__
   mailing list or to the channel #ride on `Robot Framework
   Slack <https://robotframework-slack-invite.herokuapp.com>`__, and
   possible bugs submitted to the `issue
   tracker <https://github.com/robotframework/RIDE/issues>`__. You
   should see `Robot Framework
   Forum <https://forum.robotframework.org/c/tools/ride/>`__ if your
   problem is already known.

   If you have `pip <http://pip-installer.org>`__ installed, just run

   .. code:: literal-block

      pip install --pre --upgrade robotframework-ride==2.0rc1

   to install this **RELEASE CANDIDATE** release, and for the **final**
   release use

   .. code:: literal-block

      pip install --upgrade robotframework-ride

   .. code:: literal-block

      pip install robotframework-ride==2.0

   to install exactly the **final** version. Alternatively you can
   download the source distribution from
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

   RIDE v2.0rc1 was released on 26/Feb/2023.
