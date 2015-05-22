import inspect
from model import RIDE
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
