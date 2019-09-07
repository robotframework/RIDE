===========================
Robot Framework IDE 1.7.4b2
===========================


.. default-role:: code


`RIDE (Robot Framework IDE)`_ 1.7.4b2 is a new release with major enhancements
and bug fixes. This version 1.7.4b2 includes fixes for installer, Font Type selection, Text Editor improvements and new File explorer.
The reference for valid arguments is `Robot Framework`_ version 3.1.2.
**MORE intro stuff...**

* This is the **last version supporting Python 2.7**.
* A new File Explorer allows to open supported file types in RIDE, or other types in a basic code editor. To open a file you must double-click on it (project folders open with right-click). If it is a supported file format but not with the correct structure (for example a resource file), an error message is shown, and then opens in code editor.
* On Grid Editor, the cells can be autoajusting with wordwrap. There is a new checkbox in `Tools>Preferences>Grid Editor`.
* Font Type selection is available for Text Editor and Run panels.
* Pressing the Ctrl on the Grid Editor, when over a keyword it will show its documentation (that can be detached with mouse click).
* There are some important changes, or known issues:

  - On Windows to call autocomplete in Grid Editor, you have to use Ctrl-Alt-Space, (or keep using Ctrl-Space after disabling Text Editor)

  - On MacOS to call autocomplete in Grid Editor, you have to use Alt-Space

  - On Linux to call autocomplete in Grid Editor, you have to use Ctrl-Space

  - On Text Editor the TAB key adds the defined number of spaces. With Shift moves to the left, and together with Control selects text.

  - On some Linuxes (Fedora, for example), when you click No in some Dialog boxes, there is the repetition of those Dialogs

(and more for you to find out ;) )
**THIS IS THE LAST RELEASE SUPPORTING PYTHON 2.7**

**wxPython will be updated to current version 4.0.6**

*Linux users are advised to install first wxPython from .whl package at* `wxPython.org`_.


**REMOVE reference to tracker if release notes contain all issues.**
All issues targeted for RIDE v1.7.4 can be found
from the `issue tracker milestone`_.

Questions and comments related to the release can be sent to the
`robotframework-users`_ mailing list or to the channel #ride on 
`Robot Framework Slack`_, and possible bugs submitted to the `issue tracker`_.

**REMOVE ``--pre`` from the next command with final releases.**
If you have pip_ installed, just run

::

   pip install --upgrade robotframework-ride==1.7.4b2

to install this **BETA** release, and for the **final** release use

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

RIDE 1.7.4b2 was released on Saturday September 7, 2019.

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

Full list of fixes and enhancements
===================================

.. list-table::
    :header-rows: 1

    * - ID
      - Type
      - Priority
      - Summary
    * - `#1064`_
      - bug
      - ---
      - It shows wrong Character for non-ascii characters when running
    * - `#1367`_
      - bug
      - ---
      - Pressing delete in the search box on the text edit tab, deletes from the test text.
    * - `#1601`_
      - bug
      - ---
      -  User keyword remains on tree view after deleted from a suite
    * - `#1614`_
      - bug
      - ---
      - Deleting a tag from View All Tags dialog or by deleting tag text does not remove the [Tags] section
    * - `#1739`_
      - bug
      - ---
      - I'm unable to select text in cell 
    * - `#1741`_
      - bug
      - ---
      - Rename Test Suite always give Validation Error: Filename contains illegal characters
    * - `#1747`_
      - bug
      - ---
      - RIDE-1.7.2 the Simplified-Chinese displayed problem 
    * - `#1793`_
      - bug
      - ---
      - Dependencies are not installed along with RIDE
    * - `#1803`_
      - bug
      - ---
      - the new ride v1.7.3.1 can not support the project that chinese in path
    * - `#1804`_
      - bug
      - ---
      - The new ride v1.7.3.1 can not execute by pythonw.exe
    * - `#1806`_
      - bug
      - ---
      - Can't install RIDE 1.7.3.1 when using buildout
    * - `#1809`_
      - bug
      - ---
      - Korean with Comment keyword makes UnicodeEncodeError .
    * - `#1812`_
      - bug
      - ---
      - Unable to run test cases if # comment is commented
    * - `#1818`_
      - bug
      - ---
      - I can't delete new file
    * - `#1821`_
      - bug
      - ---
      - Not allowing to add or edit name of scalar variable 
    * - `#1824`_
      - bug
      - ---
      - Move/delete keywords doesn't show up in RIDE GUI.
    * - `#1825`_
      - bug
      - ---
      - Cannot able to delete the keywords in RIDE GUI
    * - `#1826`_
      - bug
      - ---
      - RIDE doesnt support new FOR loop syntax
    * - `#1845`_
      - bug
      - ---
      - Grid editor issues on new RIDE
    * - `#1853`_
      - bug
      - ---
      - Chinese character random code
    * - `#1857`_
      - bug
      - ---
      - Duplicate save button
    * - `#1869`_
      - bug
      - ---
      - Permission Issue after creating new test suite
    * - `#1870`_
      - bug
      - ---
      - 1.7.3.1 editor "Cut" is not working, the grid content is still here
    * - `#1873`_
      - bug
      - ---
      - Please bring back tag wrapping
    * - `#1886`_
      - bug
      - ---
      - Disabled RIDE Log plugin because of error when opened a folder
    * - `#1888`_
      - bug
      - ---
      - Tags events aren't working properly
    * - `#1891`_
      - bug
      - ---
      - Outdir issue with custom date
    * - `#1892`_
      - bug
      - ---
      - Chinese character random code
    * - `#1895`_
      - bug
      - ---
      - The keyword in Resource can't  be Rename，if you modified and saved, the system will be broken!
    * - `#1900`_
      - bug
      - ---
      - Deleting a tag causes RIDE to crash
    * - `#1906`_
      - bug
      - ---
      - Issues reported in google group
    * - `#1912`_
      - bug
      - ---
      - On python3 there is no detection of file changes outside RIDE
    * - `#1919`_
      - bug
      - ---
      - Text Editor does not update color and font size when preferences are changed
    * - `#1958`_
      - bug
      - ---
      - Freeze/loading when collapsing tree
    * - `#1960`_
      - bug
      - ---
      - robotframework-ride-1.7.3.1.zip lacks requirements.txt
    * - `#1967`_
      - bug
      - ---
      - Ride crash when suggestion popup is shown
    * - `#1996`_
      - bug
      - ---
      - Reset changes after validation
    * - `#1590`_
      - enhancement
      - ---
      - Unknown variables color not documented
    * - `#1798`_
      - enhancement
      - ---
      - RIDE:set default column size seems doesn't work
    * - `#1832`_
      - enhancement
      - ---
      - Reopen ride，the Suite turns into Resource
    * - `#1836`_
      - enhancement
      - ---
      - RIDE doesn't scroll to searched text in Text Edit view
    * - `#1837`_
      - enhancement
      - ---
      - Yaml support
    * - `#1850`_
      - enhancement
      - ---
      - Robot IDE - Import Errors on Startup
    * - `#1861`_
      - enhancement
      - ---
      - Add a file explorer
    * - `#1904`_
      - enhancement
      - ---
      - Add Reset colors button for Grid Editor preferences
    * - `#1905`_
      - enhancement
      - ---
      - Add customizable colors for both Run and Text Edit in preferences
    * - `#1909`_
      - enhancement
      - ---
      - RIDE does not allow to create .resource resource files extension
    * - `#1920`_
      - enhancement
      - ---
      - Fixes issue `#1919`_: Text editor update
    * - `#1921`_
      - enhancement
      - ---
      - Fixes issue `#1909`_: Added support for Resource filetype
    * - `#1926`_
      - enhancement
      - ---
      - Fixes issue `#1905`_: Added colors and font face options
    * - `#1929`_
      - enhancement
      - ---
      - Alternative fix for issue `#1873`_: No wrapping, just show a scrollbar instead
    * - `#1933`_
      - enhancement
      - ---
      - No tests selected message
    * - `#1936`_
      - enhancement
      - ---
      - Adds a switch to Preferences->Test Runner
    * - `#1941`_
      - enhancement
      - ---
      - Made some improvements to fix from issue `#1905`_
    * - `#1943`_
      - enhancement
      - ---
      - Validation error fix
    * - `#1948`_
      - enhancement
      - ---
      - Conditioned sizes of Tagboxes and ComboBoxes to be platform specific
    * - `#1966`_
      - enhancement
      - ---
      - How to close text editor's auto wrap
    * - `#1969`_
      - enhancement
      - ---
      - Attempt to fix app icon on Wayland. Changed robot.ico to have all sizes.
    * - `#1971`_
      - enhancement
      - ---
      - [FR] Option to disable code reformatting when saving file
    * - `#1977`_
      - enhancement
      - ---
      - New Parser Log tab to avoid dialog when loading Test Suite
    * - `#1980`_
      - enhancement
      - ---
      - Open Files or Directories in RIDE with right-click from Files panel
    * - `#1981`_
      - enhancement
      - ---
      - Update robot 3.1.2
    * - `#1994`_
      - enhancement
      - ---
      - Change TAB to add spaces in Text Editor
    * - `#1805`_
      - ---
      - ---
      - The new ride v1.7.3.1 shortcut is not working on Windows 7
    * - `#1807`_
      - ---
      - ---
      - Fix `#1804`_
    * - `#1808`_
      - ---
      - ---
      - Adds more files to MANIFEST, specially requirements.txt. Fixes `#1806`_
    * - `#1819`_
      - ---
      - ---
      - Column sizing on Mac doesn't work.
    * - `#1838`_
      - ---
      - ---
      - Wip fix win encoding
    * - `#1846`_
      - ---
      - ---
      - Grid editor fixes
    * - `#1848`_
      - ---
      - ---
      - fix cells size in Grid editor
    * - `#1862`_
      - ---
      - ---
      - Installer - Fixes installation to all OS
    * - `#1863`_
      - ---
      - ---
      - Cell Sizes fixes
    * - `#1864`_
      - ---
      - ---
      - Installer
    * - `#1865`_
      - ---
      - ---
      - Desktopshortcut removal of GUI
    * - `#1866`_
      - ---
      - ---
      - Fixes Commented cells with # on Pause parsing
    * - `#1880`_
      - ---
      - ---
      - Changes encoding. Fixes running chinese path in python2.7 under Windows
    * - `#1882`_
      - ---
      - ---
      - Error when install v1.7.3.1 on mac
    * - `#1883`_
      - ---
      - ---
      - Installer
    * - `#1884`_
      - ---
      - ---
      - Fixes utf-8 arguments and include/exclude options in Python2.
    * - `#1889`_
      - ---
      - ---
      - Fix for ticket `#1888`_
    * - `#1890`_
      - ---
      - ---
      - Fixes `#1824`_. Deleted Keywords are now removed from the tree.
    * - `#1893`_
      - ---
      - ---
      - Fix `#1836`_
    * - `#1897`_
      - ---
      - ---
      -  Fix for ticket `#1739`_
    * - `#1898`_
      - ---
      - ---
      - Fixes not possible to delete with Ctrl-Shift-D a commented cell
    * - `#1899`_
      - ---
      - ---
      - Fix for ticket `#1614`_
    * - `#1901`_
      - ---
      - ---
      - Fix for ticket `#1739`_ - Fix cell select
    * - `#1902`_
      - ---
      - ---
      - Fix issue  `#1857`_: Duplicate save button
    * - `#1903`_
      - ---
      - ---
      - Fixes issue `#1821`_: Add or edit name
    * - `#1907`_
      - ---
      - ---
      -  Fixes issue `#1904`_: Reset colors button
    * - `#1908`_
      - ---
      - ---
      - Alternate fix for issue `#1888`_
    * - `#1918`_
      - ---
      - ---
      - Fix colors
    * - `#1922`_
      - ---
      - ---
      - Support new "For In" loop syntax 
    * - `#1928`_
      - ---
      - ---
      - Fixes issue `#1912`_: Metaclass compatibility
    * - `#1935`_
      - ---
      - ---
      - Examples of Custom Scripts to use `maven` and `pabot`
    * - `#1939`_
      - ---
      - ---
      - Update example pom.xml
    * - `#1942`_
      - ---
      - ---
      -  Recovers missing commit, from `#1908`_.
    * - `#1950`_
      - ---
      - ---
      - Fixes permission issue
    * - `#1951`_
      - ---
      - ---
      - Fixes `#1832`_:  Added default template for when new suite is created
    * - `#1954`_
      - ---
      - ---
      - When I delete or move use cases and keywords, ride must be restarted to display correctly.
    * - `#1959`_
      - ---
      - ---
      - Fixes `#1958`_: Modified OnTreeItemCollapsing to be less recursive
    * - `#1962`_
      - ---
      - ---
      - Fixes some Grid resize issues
    * - `#1974`_
      - ---
      - ---
      - Modified OnTreeItemCollapsing to be more recursive
    * - `#1982`_
      - ---
      - ---
      - Change to setFocus on Windows 10
    * - `#1991`_
      - ---
      - ---
      - Fix `#1891`_
    * - `#1998`_
      - ---
      - ---
      - Correctly keep changes if validation failed and user did not reset th…

Altogether 105 issues. View on the `issue tracker <https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.4>`__.

.. _#1064: https://github.com/robotframework/RIDE/issues/1064
.. _#1367: https://github.com/robotframework/RIDE/issues/1367
.. _#1601: https://github.com/robotframework/RIDE/issues/1601
.. _#1614: https://github.com/robotframework/RIDE/issues/1614
.. _#1739: https://github.com/robotframework/RIDE/issues/1739
.. _#1741: https://github.com/robotframework/RIDE/issues/1741
.. _#1747: https://github.com/robotframework/RIDE/issues/1747
.. _#1793: https://github.com/robotframework/RIDE/issues/1793
.. _#1803: https://github.com/robotframework/RIDE/issues/1803
.. _#1804: https://github.com/robotframework/RIDE/issues/1804
.. _#1806: https://github.com/robotframework/RIDE/issues/1806
.. _#1809: https://github.com/robotframework/RIDE/issues/1809
.. _#1812: https://github.com/robotframework/RIDE/issues/1812
.. _#1818: https://github.com/robotframework/RIDE/issues/1818
.. _#1821: https://github.com/robotframework/RIDE/issues/1821
.. _#1824: https://github.com/robotframework/RIDE/issues/1824
.. _#1825: https://github.com/robotframework/RIDE/issues/1825
.. _#1826: https://github.com/robotframework/RIDE/issues/1826
.. _#1845: https://github.com/robotframework/RIDE/issues/1845
.. _#1853: https://github.com/robotframework/RIDE/issues/1853
.. _#1857: https://github.com/robotframework/RIDE/issues/1857
.. _#1869: https://github.com/robotframework/RIDE/issues/1869
.. _#1870: https://github.com/robotframework/RIDE/issues/1870
.. _#1873: https://github.com/robotframework/RIDE/issues/1873
.. _#1886: https://github.com/robotframework/RIDE/issues/1886
.. _#1888: https://github.com/robotframework/RIDE/issues/1888
.. _#1891: https://github.com/robotframework/RIDE/issues/1891
.. _#1892: https://github.com/robotframework/RIDE/issues/1892
.. _#1895: https://github.com/robotframework/RIDE/issues/1895
.. _#1900: https://github.com/robotframework/RIDE/issues/1900
.. _#1906: https://github.com/robotframework/RIDE/issues/1906
.. _#1912: https://github.com/robotframework/RIDE/issues/1912
.. _#1919: https://github.com/robotframework/RIDE/issues/1919
.. _#1958: https://github.com/robotframework/RIDE/issues/1958
.. _#1960: https://github.com/robotframework/RIDE/issues/1960
.. _#1967: https://github.com/robotframework/RIDE/issues/1967
.. _#1996: https://github.com/robotframework/RIDE/issues/1996
.. _#1590: https://github.com/robotframework/RIDE/issues/1590
.. _#1798: https://github.com/robotframework/RIDE/issues/1798
.. _#1832: https://github.com/robotframework/RIDE/issues/1832
.. _#1836: https://github.com/robotframework/RIDE/issues/1836
.. _#1837: https://github.com/robotframework/RIDE/issues/1837
.. _#1850: https://github.com/robotframework/RIDE/issues/1850
.. _#1861: https://github.com/robotframework/RIDE/issues/1861
.. _#1904: https://github.com/robotframework/RIDE/issues/1904
.. _#1905: https://github.com/robotframework/RIDE/issues/1905
.. _#1909: https://github.com/robotframework/RIDE/issues/1909
.. _#1920: https://github.com/robotframework/RIDE/issues/1920
.. _#1921: https://github.com/robotframework/RIDE/issues/1921
.. _#1926: https://github.com/robotframework/RIDE/issues/1926
.. _#1929: https://github.com/robotframework/RIDE/issues/1929
.. _#1933: https://github.com/robotframework/RIDE/issues/1933
.. _#1936: https://github.com/robotframework/RIDE/issues/1936
.. _#1941: https://github.com/robotframework/RIDE/issues/1941
.. _#1943: https://github.com/robotframework/RIDE/issues/1943
.. _#1948: https://github.com/robotframework/RIDE/issues/1948
.. _#1966: https://github.com/robotframework/RIDE/issues/1966
.. _#1969: https://github.com/robotframework/RIDE/issues/1969
.. _#1971: https://github.com/robotframework/RIDE/issues/1971
.. _#1977: https://github.com/robotframework/RIDE/issues/1977
.. _#1980: https://github.com/robotframework/RIDE/issues/1980
.. _#1981: https://github.com/robotframework/RIDE/issues/1981
.. _#1994: https://github.com/robotframework/RIDE/issues/1994
.. _#1805: https://github.com/robotframework/RIDE/issues/1805
.. _#1807: https://github.com/robotframework/RIDE/issues/1807
.. _#1808: https://github.com/robotframework/RIDE/issues/1808
.. _#1819: https://github.com/robotframework/RIDE/issues/1819
.. _#1838: https://github.com/robotframework/RIDE/issues/1838
.. _#1846: https://github.com/robotframework/RIDE/issues/1846
.. _#1848: https://github.com/robotframework/RIDE/issues/1848
.. _#1862: https://github.com/robotframework/RIDE/issues/1862
.. _#1863: https://github.com/robotframework/RIDE/issues/1863
.. _#1864: https://github.com/robotframework/RIDE/issues/1864
.. _#1865: https://github.com/robotframework/RIDE/issues/1865
.. _#1866: https://github.com/robotframework/RIDE/issues/1866
.. _#1880: https://github.com/robotframework/RIDE/issues/1880
.. _#1882: https://github.com/robotframework/RIDE/issues/1882
.. _#1883: https://github.com/robotframework/RIDE/issues/1883
.. _#1884: https://github.com/robotframework/RIDE/issues/1884
.. _#1889: https://github.com/robotframework/RIDE/issues/1889
.. _#1890: https://github.com/robotframework/RIDE/issues/1890
.. _#1893: https://github.com/robotframework/RIDE/issues/1893
.. _#1897: https://github.com/robotframework/RIDE/issues/1897
.. _#1898: https://github.com/robotframework/RIDE/issues/1898
.. _#1899: https://github.com/robotframework/RIDE/issues/1899
.. _#1901: https://github.com/robotframework/RIDE/issues/1901
.. _#1902: https://github.com/robotframework/RIDE/issues/1902
.. _#1903: https://github.com/robotframework/RIDE/issues/1903
.. _#1907: https://github.com/robotframework/RIDE/issues/1907
.. _#1908: https://github.com/robotframework/RIDE/issues/1908
.. _#1918: https://github.com/robotframework/RIDE/issues/1918
.. _#1922: https://github.com/robotframework/RIDE/issues/1922
.. _#1928: https://github.com/robotframework/RIDE/issues/1928
.. _#1935: https://github.com/robotframework/RIDE/issues/1935
.. _#1939: https://github.com/robotframework/RIDE/issues/1939
.. _#1942: https://github.com/robotframework/RIDE/issues/1942
.. _#1950: https://github.com/robotframework/RIDE/issues/1950
.. _#1951: https://github.com/robotframework/RIDE/issues/1951
.. _#1954: https://github.com/robotframework/RIDE/issues/1954
.. _#1959: https://github.com/robotframework/RIDE/issues/1959
.. _#1962: https://github.com/robotframework/RIDE/issues/1962
.. _#1974: https://github.com/robotframework/RIDE/issues/1974
.. _#1982: https://github.com/robotframework/RIDE/issues/1982
.. _#1991: https://github.com/robotframework/RIDE/issues/1991
.. _#1998: https://github.com/robotframework/RIDE/issues/1998
