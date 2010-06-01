
from robotide.robotapi import TestDataDirectory, TestCaseFile, ResourceFile

class DataController(object):

    def __init__(self, data):
        self.file = data

    def has_been_modified_on_disk(self):
        return False

    @property
    def dirty(self):
        return False

