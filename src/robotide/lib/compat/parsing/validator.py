from robot.api.parsing import ModelVisitor
from robotide.lib.robot.errors import DataError


class ErrorReporter(ModelVisitor):

    def generic_visit(self, node):
        if node.errors:
            print(f"DEBUG: validator.py ErrorReporter: Error on line {node.lineno}:")
            for error in node.errors:
                print(f"- {error}")
                raise DataError(message=error,details=node.lineno)
        ModelVisitor.generic_visit(self, node)
