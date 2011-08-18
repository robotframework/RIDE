#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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

class Runner(object):

    def __init__(self, model, random):
        self._model = model
        self._random = random
        self._actions = self._actions_from_model()
        self._count = 0

    def _actions_from_model(self):
        return [name for name,_ in inspect.getmembers(self._model, inspect.ismethod) if not name.startswith('_')]

    def step(self):
        self._count += 1
        self._model._do_not_skip()
        action = self._random.choice(self._actions)
        getattr(self._model, action)()

    def skip_step(self):
        self._count += 1
        self._model._skip_until_notified()
        action = self._random.choice(self._actions)
        getattr(self._model, action)()

    def skip_steps(self, count):
        for i in range(count):
            self.skip_step()

    @property
    def count(self):
        return self._count
