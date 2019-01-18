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
import random
import shutil
import os


class Runner(object):

    def __init__(self, seed, path, root):
        self._path = path
        self._root = root
        self._seed = seed
        self._model = None
        self._random = random

    def initialize(self):
        shutil.rmtree(self._path, ignore_errors=True)
        shutil.copytree(
            os.path.join(self._root, 'testdir'),
            os.path.join(self._path, 'testdir'))
        self._random.seed(self._seed)
        self._model = RIDE(self._random, self._path)
        self._actions = self._actions_from_model()
        self._count = 0
        if self._random.random() > 0.5:
            self._model.open_test_dir()
        else:
            self._model.open_suite_file()
        return self

    def _actions_from_model(self):
        return [name for name, _
                in inspect.getmembers(self._model, inspect.ismethod)
                if not name.startswith('_')]

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
