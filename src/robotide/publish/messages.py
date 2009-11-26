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

from robotide import utils


class messagetype(type):

    def __new__(cls, name, bases, dct):
        if not dct.get('topic'):
            dct['topic'] = cls._get_topic_from(name)
        dct['topic'] = dct['topic'].lower()
        return type.__new__(cls, name, bases, dct)

    @staticmethod
    def _get_topic_from(classname):
        if classname.endswith('Message'):
            classname = classname[:-len('Message')]
        return utils.printable_name(classname, code_style=True).replace(' ', '.')


class Message(object):
    __metaclass__ = messagetype
    topic = None
    data = []

    def __init__(self, **kwargs):
        if sorted(kwargs.keys()) != sorted(self.data):
            raise TypeError('Argument mismatch, expected: %s' % self.data)
        self.__dict__.update(kwargs)

    def publish(self):
        try:
            self._publish(self)
        except Exception, err:
            self._publish(RideLogMessage(message=str(err), level='ERROR'))

    def _publish(self, msg):
        WxPublisher().sendMessage(msg.topic, msg)


class RideMessage(Message):
    pass


class RideLogMessage(RideMessage):
    data = ['message', 'level', 'timestamp']

    def __init__(self, message, level='INFO'):
        RideMessage.__init__(self, message=message, level=level,
                             timestamp=utils.get_timestamp())


class RideTreeSelection(RideMessage):
    data = ['node', 'item', 'text']


class RideNotebookTabChanging(RideMessage):
    data = ['oldtab', 'newtab']


class RideNotebookTabChanged(RideMessage):
    pass


class RideSaving(RideMessage):
    data = ['path']


class RideSaved(RideMessage):
    data = ['path']


class RideSaveAll(RideMessage):
    pass


class RideOpenResource(RideMessage):
    data = ['path']


class RideOpenSuite(RideMessage):
    data = ['path']


class RideGridCellChanged(RideMessage):
    topic = 'Ride.Grid.Cell Changed'
    data = ['cell', 'value', 'previous', 'grid']


class RideClosing(RideMessage):
    pass
