from robotide.controller.commands import FindOccurrences
from robotide.controller.macrocontrollers import KeywordNameController


class FindUsages(FindOccurrences):

    def execute(self, context):
        prev = None
        for occ in FindOccurrences.execute(self, context):
            if isinstance(occ.item, KeywordNameController):
                continue
            if prev == occ:
                prev.count += 1
            else:
                if prev:
                    yield prev
                prev = occ
        if prev:
            yield prev