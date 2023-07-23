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

import sys
import threading
import traceback


def _print_stacks():
    id2name = dict((th.ident, th.name) for th in threading.enumerate())
    for thread_id, stack in sys._current_frames().items():
        print(id2name[thread_id])
        traceback.print_stack(f=stack)


def start(ride):
    import code
    help_string = """\
RIDE - access to the running application
print_stacks() - print current stack traces
"""
    console = code.InteractiveConsole(
        locals={'RIDE': ride, 'print_stacks': _print_stacks})
    thread = threading.Thread(target=lambda: console.interact(help_string))
    thread.start()
