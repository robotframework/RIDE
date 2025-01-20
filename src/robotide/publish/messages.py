#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

import inspect
import sys
import traceback
from .. import utils


class RideMessage:
    """Base class for all messages sent by RIDE.

    :CVariables:
      topic
        Topic of this message. If not overridden, value is got from the class
        name by lowercasing it, separating words with a dot and dropping possible
        ``Message`` from the end. For example classes ``MyExample`` and
        ``AnotherExampleMessage`` get titles ``my.example`` and
        ``another.example``, respectively.
      data
        Names of attributes this message provides. These must be given as
        keyword arguments to `__init__` when an instance is created.
    """

    _topic = None
    data = []

    def __init__(self, **kwargs):
        """Initializes message based on given keyword arguments.

        Names of the given keyword arguments must match to names in `data`
        class attribute, otherwise the initialization fails.

        Must be called explicitly by subclass if overridden.
        """
        if sorted(kwargs.keys()) != sorted(self.data):
            raise TypeError('Argument mismatch, expected: %s' % self.data)
        self.__dict__.update(kwargs)

    @classmethod
    def topic(cls):
        if not cls._topic:
            cls_name = cls.__name__
            if cls_name.endswith('Message'):
                cls_name = cls_name[:-len('Message')]
            topic_name = utils.printable_name(cls_name, code_style=True).replace(' ', '.')
        else:
            topic_name = cls._topic
        return topic_name.lower()

    def publish(self):
        """Publishes the message.

        All listeners that have subscribed to the topic of this message will be
        called with this instance as an argument.

        Notifications are sent sequentially. Due to the limitations of current
        implementation, if any of the listeners raises an exception, subsequent
        listeners will not get the notification.
        """
        from robotide.publish.publisher import PUBLISHER
        PUBLISHER.publish(self.__class__, self)


class RideLog(RideMessage):
    """This class represents a general purpose log message.

    Subclasses of this be may be used to inform error conditions or to provide
    some kind of debugging information.
    """
    data = ['message', 'level', 'timestamp', 'notify_user']


class RideLogMessage(RideLog):
    """This class represents a general purpose log message.

    This message may be used to inform error conditions or to provide
    some kind of debugging information.
    """
    data = ['message', 'level', 'timestamp', 'notify_user']

    def __init__(self, message, level='INFO', notify_user=False):
        """Initializes a RIDE log message.

        The log ``level`` has default value ``INFO`` and the ``timestamp``
        is generated automatically.
        """
        RideMessage.__init__(
            self, message=message, level=level,
            timestamp=utils.get_timestamp(), notify_user=notify_user)


class RideLogException(RideLog):
    """This class represents a general purpose log message with a traceback
    appended to message text. Also, the original exception is included with
    the message.

    This message may be used to inform error conditions or to provide
    some kind of debugging information.
    """
    data = ['message', 'level', 'timestamp', 'exception', 'notify_user']

    def __init__(self, message, exception, level='INFO', notify_user=False):
        """Initializes a RIDE log exception.

        The log ``level`` has default value ``INFO`` and the ``timestamp``
        is generated automatically. Message is automatically appended with
        a traceback.
        """
        _, _, exc_traceback = sys.exc_info()
        if exc_traceback:
            tb = traceback.extract_tb(exc_traceback)
            message += '\n\nTraceback (most recent call last):\n%s\n%s' % \
                (str(exception), ''.join(traceback.format_list(tb)))
        RideMessage.__init__(
            self, message=message, level=level, notify_user=notify_user,
            timestamp=utils.get_timestamp(), exception=exception)


class RideParserLogMessage(RideMessage):
    """This class represents a general purpose log message.

    This message may be used to inform parser errors and to provide
    some kind of debugging information.
    """
    data = ['message', 'level', 'timestamp', 'notify_user']

    def __init__(self, message, level='', notify_user=False):
        """Initializes a RIDE log message.

        The log ``level`` has default value ``WARN`` and the ``timestamp``
        is generated automatically.
        """
        RideMessage.__init__(
            self, message=message, level=level,
            timestamp=utils.get_timestamp(), notify_user=notify_user)


class RideInputValidationError(RideMessage):
    """Sent whenever user input is invalid."""
    data = ['message']


class RideModificationPrevented(RideMessage):
    """Sent whenever modifying command is prevented for some reason"""
    data = ['controller']


class RideSettingsChanged(RideMessage):
    """Sent when settings are changed

    keys is a tuple of key names. For example, if the "Grid Colors" section
    was modified the keys would be ("Grid Colors"), or a specific plugin
    setting might be ("Plugin", "Preview", "format").
    `old` and `new` contain the old and the new value of the setting.
    """
    data = ['keys', 'old', 'new']


class RideExecuteSpecXmlImport(RideMessage):
    """Sent whenever spec xml import is requested"""


class RideTreeSelection(RideMessage):
    """Sent whenever user selects a node from the tree."""
    data = ['node', 'item', 'silent']


class RideOpenVariableDialog(RideMessage):
    """Sent when variable dialog is requested to be open"""
    data = ['controller']


class RideTestExecutionStarted(RideMessage):
    """Sent whenever new test execution is started."""
    data = ['results']


class RideTestSelectedForRunningChanged(RideMessage):
    """Sent whenever a test is selected or unselected from the tree."""
    data = ['tests']


class RideTestRunning(RideMessage):
    """Sent whenever RIDE is starting to run a test case."""
    data = ['item']


class RideTestPaused(RideMessage):
    """Sent whenever RIDE is running a test case and paused."""
    data = ['item']


class RideTestPassed(RideMessage):
    """Sent whenever RIDE has executed a test case, and it passed."""
    data = ['item']


class RideTestFailed(RideMessage):
    """Sent whenever RIDE has executed a test case, and it failed."""
    data = ['item']


class RideTestSkipped(RideMessage):
    """Sent whenever RIDE has executed a test case, and it was skipped."""
    data = ['item']


class RideTestStopped(RideMessage):
    """Sent whenever RIDE was executing a test case, and it was stopped or aborted."""
    data = ['item']


class RideNotebookTabChanging(RideMessage):
    """Sent when the notebook tab change has started.

    Subscribing to this event allows the listener to do something before the
    tab has actually changed in the UI.
    """
    data = ['oldtab', 'newtab']


class RideNotebookTabChanged(RideMessage):
    """Sent after the notebook tab change has completed."""
    pass


class RideSaving(RideMessage):
    """Sent when user selects Save from File menu or via shortcut.

    This is used for example to store current changes from editor to data
    model, to guarantee that all changes are really saved."""
    data = ['path', 'datafile']


class RideBeforeSaving(RideMessage):
    """Sent before files are going to be saved."""
    pass


class RideSaved(RideMessage):
    """Sent after the file has been actually saved to disk."""
    data = ['path']


class RideSaveAll(RideMessage):
    """Sent when user selects ``Save All`` from ``File`` menu or via shortcut."""
    pass


class RideDataDirtyCleared(RideMessage):
    """Sent when datafiles dirty marking is cleared

    datafile has been saved and datafile in memory equals the serialized one.
    """
    data = ['datafile']


class RideNewProject(RideMessage):
    """Sent when a new project has been created."""
    data = ['path', 'datafile']


class RideClosing(RideMessage):
    """Sent when user selects ``Quit`` from ``File`` menu or via shortcut."""
    pass


class RideOpenSuite(RideMessage):
    """Sent when a new suite has finished loading."""
    data = ['path', 'datafile']


class RideOpenResource(RideMessage):
    """Sent when a new resource has finished loading."""
    data = ['path', 'datafile']


class RideSelectResource(RideMessage):
    """Sent when a resource should be selected."""
    data = ['item']


class RideDataChanged(RideMessage):
    """Base class for all messages notifying that data in model has changed."""
    pass


class RideFileNameChanged(RideDataChanged):
    """Sent after test suite or resource file is renamed"""
    data = ['datafile', 'old_filename']


class RideDataFileRemoved(RideDataChanged):
    data = ['path', 'datafile']


class RideSuiteAdded(RideDataChanged):
    data = ['parent', 'suite']


class RideInitFileRemoved(RideDataChanged):
    data = ['path', 'datafile']


class RideImportSetting(RideDataChanged):
    """Base class for all messages about changes to import settings."""
    data = ['datafile', 'type', 'import_controller']

    def is_resource(self):
        return self.type == 'resource'

    @property
    def name(self):
        return self.import_controller.name


class _RideExcludes(RideMessage):
    data = ['old_controller', 'new_controller']


class RideIncludesChanged(_RideExcludes):
    pass


class RideExcludesChanged(_RideExcludes):
    pass


class RideImportSettingAdded(RideImportSetting):
    """Sent whenever an import setting is added.

    ``datafile`` is the suite or resource file whose imports have changed,
    ``type`` is either ``resource``, ``library``, or ``variables``.
    """
    pass


class RideImportSettingChanged(RideImportSetting):
    """Sent whenever a value of import setting is changed.

    ``datafile`` is the suite or resource file whose imports have changed,
    ``type`` is either ``resource``, ``library``, or ``variables``.
    """
    pass


class RideImportSettingRemoved(RideImportSetting):
    """Sent whenever a value of import setting is removed.

    ``datafile`` is the suite or resource file whose imports have removed,
    ``type`` is either ``resource``, ``library``, or ``variables``.
    """
    pass


class RideDataChangedToDirty(RideDataChanged):
    """Sent when datafile changes from serialized version"""
    data = ['datafile']


class RideDataFileSet(RideDataChanged):
    """Set when a whole datafile is replaced with new one in a controller
    """
    data = ['item']


class RideUserKeyword(RideDataChanged):
    """Base class for all messages about changes to any user keyword."""
    pass


class RideUserKeywordAdded(RideUserKeyword):
    """Sent when a new user keyword is added to a suite or resource."""
    data = ['datafile', 'name', 'item']


class RideUserKeywordRemoved(RideUserKeyword):
    """Sent when a user keyword is removed from a suite or resource."""
    data = ['datafile', 'name', 'item']


class RideUserKeywordRenamed(RideUserKeyword):
    """Sent after a user keyword is renamed"""
    data = ['datafile', 'item', 'old_name']


class RideItem(RideDataChanged):
    """Base class for all messages about changes to any data item."""
    data = ['item']


class RideItemStepsChanged(RideItem):
    """"""
    pass


class RideItemNameChanged(RideItem):
    """"""
    data = ['item', 'old_name', 'new_name']


class RideItemSettingsChanged(RideItem):
    """"""
    pass


class RideTestCaseAdded(RideDataChanged):
    """Sent when a new test case is added to a suite."""
    data = ['datafile', 'name', 'item']


class RideTestCaseRemoved(RideDataChanged):
    """Sent when a test case is removed from a suite."""
    data = ['datafile', 'name', 'item']


class RideItemMovedUp(RideDataChanged):
    """Sent when an item (test, keyword, variable) is moved up."""
    data = ['item']


class RideItemMovedDown(RideDataChanged):
    """Sent when an item (test, keyword, variable) is moved down."""
    data = ['item']


class RideVariableAdded(RideDataChanged):
    """Sent when a new variable is added to a suite."""
    data = ['datafile', 'name', 'item', 'index']


class RideVariableRemoved(RideDataChanged):
    """Sent when a variable is removed from a suite."""
    data = ['datafile', 'name', 'item']


class RideVariableMovedUp(RideItemMovedUp):
    """Sent when a variable is moved up
    item   is the item that has been moved up
    other  is the item that was swapped down
    """
    data = ['item', 'other']


class RideVariableMovedDown(RideItemMovedDown):
    """Sent when a variable is moved down
    item   is the item that has been moved down
    other  is the item that was swapped up
    """
    data = ['item', 'other']


class RideVariableUpdated(RideDataChanged):
    """Sent when the state of a variable is changed"""
    data = ['item']


class RideOpenTagSearch(RideMessage):
    """ Sent we when want to open Search Tags """
    data = ['includes', 'excludes']


class RideTreeAwarePluginAdded(RideMessage):
    data = ['plugin']


class RideRunnerStarted(RideMessage):
    """ Sent when a process is started at Runner/RunAnything """
    data = ['process']

class RideRunnerStopped(RideMessage):
    """ Sent when a process is stopped at Runner/RunAnything """
    data = ['process']


__all__ = [name for name, cls in globals().items()
           if inspect.isclass(cls) and issubclass(cls, RideMessage)]
