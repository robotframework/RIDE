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


class RideEvent(object):
    _attrs = []

    def __init__(self, **kwargs):
        self.topic = self._get_topic()
        self._check_mandatory_attrs_given(kwargs)
        self._set_attrs(kwargs)

    def _check_mandatory_attrs_given(self, kwargs):
        missing = [ name for name in self._attrs if not name in kwargs ]
        if missing:
            raise AttributeError('Missing mandatory attributes: %s' 
                                 % ', '.join(missing))

    def _set_attrs(self, kwargs):
        for name, value in kwargs.items():
            if name not in self._attrs:
                raise AttributeError('%s has no attribute %s' 
                                     % (self.__class__.__name__, name))
            setattr(self, name, value)

    def _get_topic(self):
        return utils.name_from_class(self, 'Event').replace(' ', '.')
