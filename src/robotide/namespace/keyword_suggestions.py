
from robot.parsing.model import ResourceFile
from robot.parsing.settings import Library, Resource
from robotide.namespace.cache import LibraryCache
import os


class KeywordSuggestions(object):

    def __init__(self, namespace):
        self.namespace = namespace

    def get_suggestions_for(self, start):
        start_lower = start.lower()
        suggestions = self.namespace.get_keywords()
        return sorted([sug for sug in suggestions 
                       if sug.name.lower().startswith(start_lower)])


class KeywordInfo(object):

    def __init__(self, name, source=None, doc=None):
        self.name = name
        self.source = source
        self.doc = doc

    def __str__(self):
        return 'KeywordInfo[name: %s, source: %s, doc: %s]' %(self.name,
                                                              self.source,
                                                              self.doc)

    def __cmp__(self, other):
        return cmp(self.name, other.name)


class Namespace(object):

    def __init__(self, datafile):
        self.datafile = datafile
        self.lib_cache = LibraryCache()
        self.res_cache = ResourceCache()

    def _get_default_keywords(self):
        kws = []
        for kw in self.lib_cache.get_default_keywords():
            kws.append(KeywordInfo(kw.name, kw.source, kw.doc))
        return kws

    def _get_datafile_keywords(self, datafile):
        return [KeywordInfo(kw.name, datafile.source, kw.doc) 
                for kw in datafile.keywords]

    def _get_imported_keywords(self, datafile):
        return self.__collect_kws_from_imports(datafile, Library, self.__lib_kw_getter)

    def __lib_kw_getter(self, imp):
        return self.lib_cache.get_library_keywords(imp.name, imp.args)

    def _get_import_resource_keywords(self, datafile):
        kws = self.__collect_kws_from_imports(datafile, Resource, self.__res_kw_recursive_getter)
        return kws

    def __res_kw_recursive_getter(self, imp):
        res = self.res_cache.get_resource(imp)
        kws = []
        for child in self.__collect_import_of_type(res, Resource):
            kws.extend(self.__res_kw_recursive_getter(child))
        kws.extend(self._get_imported_keywords(res))
        return res.keywords + kws

    def __collect_kws_from_imports(self, datafile, instance_type, getter):
        kws = []
        for imp in self.__collect_import_of_type(datafile, instance_type):
            kws.extend([KeywordInfo(kw.name, kw.source, kw.doc) 
                        for kw in getter(imp)])
        return kws

    def __collect_import_of_type(self, datafile, instance_type):
        return [imp for imp in datafile.imports
                if isinstance(imp, instance_type)]

    def get_keywords(self):
        return self._get_default_keywords() + self._get_datafile_keywords(self.datafile) +\
               self._get_imported_keywords(self.datafile) + self._get_import_resource_keywords(self.datafile)

    def _get_name_and_args(self, libsetting):
        parts = libsetting.split('|')
        if len(parts) == 1:
            return parts[0], None
        return parts[0], parts[1:]


class ResourceCache(object):

    def __init__(self):
        self.cache = {}

    def get_resource(self, resource_import):
        path = os.path.join(resource_import.directory, resource_import.name) 
        normalized = os.path.normpath(path)
        if normalized not in self.cache:
            self.cache[normalized] = ResourceFile(normalized)
        return self.cache[normalized]
