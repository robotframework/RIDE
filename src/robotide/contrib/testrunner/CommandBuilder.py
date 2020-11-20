import inspect
import os

from robotide.contrib.testrunner import TestRunnerAgent
from robotide.contrib.testrunner.FileWriter import FileWriter
try:
    from robotide.lib.robot.utils import encoding
except ImportError:
    from robotide.lib.robot.utils.encodingsniffer import get_system_encoding
    encoding.SYSTEM_ENCODING = get_system_encoding()


class CommandBuilder:

    def __init__(self):
        self._command_prefix = ''
        self._suite_source = ''
        self._listener = None
        self._arg_file = None

    def set_prefix(self, prefix):
        self._command_prefix = prefix

    def set_listener(self, port, pause_on_failure=False):
        if port:
            self._listener = (port, pause_on_failure)

    def set_suite_source(self, suite_source):
        self._suite_source = suite_source

    def add_arg_file(self, arg_file, args):
        if arg_file and args:
            self._arg_file = (arg_file, args)

    def build(self):
        command = []
        if self._command_prefix:
            command.append(self._command_prefix)

        if self._arg_file:
            FileWriter.write(self._arg_file[0], self._arg_file[1], "wb")
            command.extend(["-A", self._arg_file[0]])

        if self._listener:
            command.extend(["--listener", self._get_listener_to_cmd()])

        if self._suite_source:
            command.append(self._suite_source)

        return self._format_command(command)

    def _get_listener_to_cmd(self):
        path = os.path.abspath(inspect.getfile(TestRunnerAgent))
        if path[-1] in ['c', 'o']:
            path = path[:-1]
        return '%s:%s:%s' % (path, self._listener[0], self._listener[1])

    @staticmethod
    def _format_command(args):
        """Quote a list as if it were a command line command

        This isn't perfect but seems to work for the normal use
        cases. I'm not entirely sure what the perfect algorithm
        is since *nix and windows have different quoting
        behaviors.
        """
        result = []
        for arg in args:
            # arg = arg.encode(encoding.SYSTEM_ENCODING)
            if "'" in arg or " " in arg or "&" in arg:
                # for windows, if there are spaces we need to use
                # double quotes. Single quotes cause problems
                result.append('"%s"' % arg)
            elif '"' in arg:
                result.append("'%s'" % arg)
            else:
                result.append(arg)
        return " ".join(result)
