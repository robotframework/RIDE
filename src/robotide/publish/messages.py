#  Copyright 2008-2009 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org:licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from wx.lib.pubsub import Publisher as WxPublisher
import inspect
import messagetype
import sys
import traceback

from robotide import utils


class RideMessage(object):
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
    __metaclass__ = messagetype.messagetype
    topic = None
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

    def publish(self):
        """Publishes the message.

        All listeners that have subscribed to the topic of this message will be
        called with the this instance as an argument.

        Notifications are sent sequentially. Due to the limitations of current
        implementation, if any of the listeners raises an exception, subsequent
        listeners will not get the notification.
        """
        try:
            self._publish(self)
        except Exception, err:
            self._publish(RideLogException(message='Error in publishing message: ' + str(err),
                                           exception=err, level='ERROR'))

    def _publish(self, msg):
        WxPublisher().sendMessage(msg.topic, msg)

class RideLog(RideMessage):
    """This class represents a general purpose log message.

    Subclasses of this be may used to inform error conditions or to provide
    some kind of debugging information.
    """
    data = ['message', 'level', 'timestamp']


class RideLogMessage(RideLog):
    """This class represents a general purpose log message.

    This message may used to inform error conditions or to provide
    some kind of debugging information.
    """
    data = ['message', 'level', 'timestamp']

    def __init__(self, message, level='INFO'):
        """Initializes a RIDE log message.

        The log ``level`` has default value ``INFO`` and the ``timestamp``
        is generated automatically.
        """
        RideMessage.__init__(self, message=message, level=level,
                             timestamp=utils.get_timestamp())


class RideLogException(RideLog):
    """This class represents a general purpose log message with a traceback
    appended to message text. Also the original exception is included with
    the message.

    This message may used to inform error conditions or to provide
    some kind of debugging information.
    """
    data = ['message', 'level', 'timestamp', 'exception']

    def __init__(self, message, exception, level='INFO'):
        """Initializes a RIDE log exception.

        The log ``level`` has default value ``INFO`` and the ``timestamp``
        is generated automatically. Message is automatically appended with
        a traceback.
        """
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_traceback:
            tb = traceback.extract_tb(exc_traceback)
            message += '\n\nTraceback (most recent call last):\n%s\n%s' % (str(exception) ,''.join(traceback.format_list(tb)))
        RideMessage.__init__(self, message=message, level=level,
                             timestamp=utils.get_timestamp(),
                             exception=exception)


class RideTreeSelection(RideMessage):
    """Sent whenever user selects a node from the tree."""
    data = ['node', 'item', 'text']


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


class RideSaved(RideMessage):
    """Sent after the file has been actually saved to disk."""
    data = ['path']


class RideSaveAll(RideMessage):
    """Sent when user selects ``Save All`` from ``File`` menu or via shortcut."""
    pass


class RideChangeFormat(RideMessage):
    """Sent when user has changed the format of a file."""
    data = ['oldpath', 'newpath']


class RideNewProject(RideMessage):
    """Sent when a new project has been created."""
    data = ['path', 'datafile']


class RideOpenSuite(RideMessage):
    """Sent when a new suite has finished loading."""
    data = ['path', 'datafile']


class RideOpenResource(RideMessage):
    """Sent when a new resource has finished loading."""
    data = ['path', 'datafile']


class RideDataFileRemoved(RideMessage):
    data = ['path', 'datafile']


class RideInitFileRemoved(RideMessage):
    data = ['path', 'datafile']


class RideGridCellChanged(RideMessage):
    """Sent when a value in grid cell has changed.

    This message is sent both with regular edits and with cut, paste or delete
    operations.  If a single cut, paste or delete operation affects multiple
    cells, this message is sent individually for each cell.
    """
    topic = 'ride.grid.cell changed'
    data = ['cell', 'value', 'previous', 'grid']


class RideImportSetting(RideMessage):
    """Base class for all messages about changes to import settings."""


class RideImportSettingAdded(RideImportSetting):
    """Sent whenever an import setting is added.

    ``datafile`` is the suite or resource file whose imports have changed,
    ``type`` is either ``resource``, ``library``, or ``variables``.
    """
    data = ['datafile', 'type', 'name']


class RideImportSettingChanged(RideImportSetting):
    """Sent whenever a value of import setting is changed.

    ``datafile`` is the suite or resource file whose imports have changed,
    ``type`` is either ``resource``, ``library``, or ``variables``.
    """
    data = ['datafile', 'type', 'name']


class RideImportSettingRemoved(RideImportSetting):
    """Sent whenever a value of import setting is removed.

    ``datafile`` is the suite or resource file whose imports have removed,
    ``type`` is either ``resource``, ``library``, or ``variables``.
    """
    data = ['datafile', 'type', 'name']


class RideDataChangedToDirty(RideMessage):
    """Sent when datafile changes from serialized version"""
    data = ['datafile']


class RideDataDirtyCleared(RideMessage):
    """Sent when datafiles dirty marking is cleared

    datafile has been saved and datafile in memory equals the serialized one.
    """
    data = ['datafile']


class RideUserKeyword(RideMessage):
    """Base class for all messages about changes to any user keyword."""


class RideUserKeywordAdded(RideMessage):
    """Sent when a new user keyword is added to a suite or resource."""
    data = ['datafile', 'name', 'item']


class RideUserKeywordRemoved(RideMessage):
    """Sent when a user keyword is removed from a suite or resource."""
    data = ['datafile', 'name', 'item']


class RideItem(RideMessage):
    """Base class for all messages about changes to any data item."""
    data = ['item']


class RideItemStepsChanged(RideItem):
    """"""


class RideItemNameChanged(RideItem):
    """"""


class RideItemSettingsChanged(RideItem):
    """"""


class RideTestCaseAdded(RideMessage):
    """Sent when a new test case is added to a suite."""
    data = ['datafile', 'name', 'item']


class RideTestCaseRemoved(RideMessage):
    """Sent when a test case is removed from a suite."""
    data = ['datafile', 'name', 'item']


class RideVariableAdded(RideMessage):
    """Sent when a new variable is added to a suite."""
    data = ['datafile', 'name', 'item']


class RideVariableRemoved(RideMessage):
    """Sent when a variable is removed from a suite."""
    data = ['datafile', 'name', 'item']


class RideVariableMovedUp(RideMessage):
    """Sent when a variable is moved up"""
    data = ['item']


class RideVariableMovedDown(RideMessage):
    """Sent when a variable is moved down"""
    data = ['item']


class RideVariableUpdated(RideMessage):
    """Sent when the state of a variable is changed"""
    data = ['item']


class RideClosing(RideMessage):
    """Sent when user selects ``Quit`` from ``File`` menu or via shortcut."""
    pass


__all__ = [ name for name, cls in globals().items()
            if inspect.isclass(cls) and issubclass(cls, RideMessage) ]
