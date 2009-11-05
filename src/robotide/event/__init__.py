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

from robotide import utils
from robotide.context import PUBLISHER


class eventtype(type):

    def __new__(cls, name, bases, dct):
        if 'topic' not in dct or dct['topic'] is None:
            dct['topic'] = eventtype.get_topic(name)
        return type.__new__(cls, name, bases, dct)

    @staticmethod
    def get_topic(classname):
        if classname.endswith('Event'):
            classname = classname[:-len('Event')]
        return utils.printable_name(classname, code_style=True).replace(' ', '.')


class RideEvent(object):
    __metaclass__ = eventtype
    topic = None
    attr_names = []

    def __init__(self, **kwargs):
        if not sorted(kwargs.keys()) == sorted(self.attr_names):
            raise TypeError('Argument mismatch, expected: %s' % self.attr_names)
        self.__dict__.update(kwargs)

    def publish(self):
        PUBLISHER.publish(self)
