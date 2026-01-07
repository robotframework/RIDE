#  Copyright 2025-     Robot Framework Foundation
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
#
# Note: These tests were initially created with GitHub CoPilot

import robotide.application.restartutil as restartutil
import types
import unittest
from multiprocessing import shared_memory
from pytest import MonkeyPatch
from robotide.application import RIDE


class ManageSharedLangTestCase(unittest.TestCase):

    def test_no_restart_uses_initial_constructor(self):
        """
        Case: ShareableList called with (['en'], name='language') and do_restart() returns False.
        Expectation: No cleanup attempted.
        """
        created = []

        class FakeShm:
            def __init__(self):
                self.close_called = False
                self.unlink_called = False

            def close(self):
                self.close_called = True

            def unlink(self):
                self.unlink_called = True

        class FakeShareable:
            def __init__(self, *args, **kwargs):
                # record how it was called
                created.append({"args": args, "kwargs": kwargs})
                self.shm = FakeShm()

        with MonkeyPatch().context() as m:
            # Patch ShareableList
            m.setattr(shared_memory, "ShareableList", FakeShareable)
            # Ensure do_restart returns False
            m.setattr(restartutil, "do_restart", lambda: False)

            # Run function (should not raise)
            RIDE._manage_shared_lang()

            # Assertions
            assert len(created) == 1
            assert created[0]["args"] == (['en'],)
            assert created[0]["kwargs"] == {"name": "language"}
            # cleanup should not have been called
            assert created[0]["kwargs"]["name"] == "language"
            assert created[0]["args"][0] == ['en']

    def test_fileexists_fallback_and_cleanup_success(self):
        """
        Case: First ShareableList call raises FileExistsError -> second call used.
        do_restart() returns True -> close() and unlink() should be called.
        """
        calls = []

        class FakeShm:
            def __init__(self):
                self.close_called = False
                self.unlink_called = False

            def close(self):
                self.close_called = True
                calls.append("close")

            def unlink(self):
                self.unlink_called = True
                calls.append("unlink")

        class FakeFactory:
            def __init__(self):
                self.call_count = 0
                self.instances = []

            def __call__(self, *args, **kwargs):
                self.call_count += 1
                # First call simulates FileExistsError
                if self.call_count == 1:
                    raise FileExistsError("simulated existing shared memory")
                inst = types.SimpleNamespace(shm=FakeShm())
                self.instances.append({"args": args, "kwargs": kwargs, "obj": inst})
                return inst

        fake_factory = FakeFactory()
        with MonkeyPatch().context() as m:
            m.setattr(shared_memory, "ShareableList", fake_factory)
            m.setattr(restartutil, "do_restart", lambda: True)

            # Run function (should not raise)
            RIDE._manage_shared_lang()

            # Two calls: first raised, second created instance
            assert fake_factory.call_count == 2
            # Ensure the second call received only name kwarg (fallback path)
            assert fake_factory.instances, "expected at least one successful instance creation"
            inst_info = fake_factory.instances[0]
            assert inst_info["args"] == ()
            assert inst_info["kwargs"] == {"name": "language"}
            # Ensure cleanup methods were called
            assert calls == ["close", "unlink"]

    def test_cleanup_file_not_found_is_handled(self):
        """
        Case: do_restart() returns True but shm.close() raises FileNotFoundError.
        Expectation: the FileNotFoundError is caught and function does not raise.
        """
        recorded = []

        class FakeShm:
            def __init__(self):
                self.attempted_close = False
                self.attempted_unlink = False

            def close(self):
                # record that we attempted to close, then raise FileNotFoundError
                self.attempted_close = True
                recorded.append("close_attempt")
                raise FileNotFoundError("simulated missing file on close")

            def unlink(self):
                # If close raises, unlink may not be called, but implement for completeness
                self.attempted_unlink = True
                recorded.append("unlink_attempt")

        def fake_shareable(*args, **kwargs):
            _ = args
            _ = kwargs
            # always succeed constructing the ShareableList
            return types.SimpleNamespace(shm=FakeShm())

        with MonkeyPatch().context() as m:
            m.setattr(shared_memory, "ShareableList", fake_shareable)
            m.setattr(restartutil, "do_restart", lambda: True)

            # This should not raise despite FileNotFoundError in close()
            RIDE._manage_shared_lang()

            # Ensure the close attempt was recorded and FileNotFoundError was swallowed
            assert recorded == ["close_attempt"]
