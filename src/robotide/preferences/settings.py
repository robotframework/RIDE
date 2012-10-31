#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
from __future__ import with_statement
import os
import shutil

from robotide.context.platform import IS_WINDOWS
from robotide.preferences.configobj import ConfigObjError
from .configobj import ConfigObj, Section, UnreprError

if IS_WINDOWS:
    SETTINGS_DIRECTORY = os.path.join(os.environ['APPDATA'], 'RobotFramework', 'ride')
else:
    SETTINGS_DIRECTORY = os.path.join(os.path.expanduser('~/.robotframework'), 'ride')
if not os.path.exists(SETTINGS_DIRECTORY):
    os.mkdir(SETTINGS_DIRECTORY)

def initialize_settings(type, path, dest_file_name=None):
    if not os.path.exists(SETTINGS_DIRECTORY):
        os.makedirs(SETTINGS_DIRECTORY)
    if type == 'user settings':
        return _copy_or_migrate_user_settings(SETTINGS_DIRECTORY, path, dest_file_name)

def _copy_or_migrate_user_settings(settings_dir, source_path, dest_file_name):
    """ Creates settings directory and copies or merges the source to there.

    In case source already exists, merge is done.
    Destination file name is the source_path's file name unless dest_file_name
    is given.
    """
    if not dest_file_name:
        dest_file_name = os.path.basename(source_path)
    settings_path = os.path.join(settings_dir, dest_file_name)
    if not os.path.exists(settings_path):
        shutil.copy(source_path, settings_path)
    else:
        try:
            SettingsMigrator(source_path, settings_path).migrate()
        except ConfigObjError, parsing_error:
            print 'WARNING! corrupted configuration file replaced with defaults'
            print parsing_error
            shutil.copy(source_path, settings_path)
    return os.path.abspath(settings_path)

class SettingsMigrator(object):

    SETTINGS_VERSION = 'settings_version'
    CURRENT_SETTINGS_VERSION = 2 #used at least in tests

    def __init__(self, default_path, user_path):
        self._default_settings = ConfigObj(default_path, unrepr=True)
        self._user_path = user_path
        try:
            self._old_settings = ConfigObj(user_path, unrepr=True)
        except UnreprError, err:
            raise ConfigurationError("Invalid config file '%s': %s" %
                            (user_path, err))

    def migrate(self):
        # Add migrations here.
        # idea is that we are able to migrate from any of the previous settings
        # versions to the current one by applying as many migration scripts as
        # is needed --> so don't do migrate_from_0_to_3 or something other
        # that will leap over some versions to save space
        # NOTE!
        # Don't count on default settings when giving values in migration scripts
        # as default values could change in the future --> state after your
        # migration is something else then what you intended and this could
        # mess up the next migration script(s)
        if not self._old_settings.get(self.SETTINGS_VERSION):
            self.migrate_from_0_to_1(self._old_settings)
        if self._old_settings.get(self.SETTINGS_VERSION) == 1:
            self.migrate_from_1_to_2(self._old_settings)
        #so next would be something like:
        #if self._old_settings[self.SETTINGS_VERSION] == 2:
        #   self.migrate_from_2_to_3(self._old_settings)
        self.merge()

    def merge(self):
        self._default_settings.merge(self._old_settings)
        self._write_merged_settings(self._default_settings, self._user_path)

    def migrate_from_0_to_1(self, settings):
        if settings.get('Colors',{}).get('text library keyword') == 'blue':
            settings['Colors']['text library keyword'] = '#0080C0'
        settings[self.SETTINGS_VERSION] = 1

    def migrate_from_1_to_2(self, settings):
        # See issue http://code.google.com/p/robotframework-ride/issues/detail?id=925
        # And other reported issues about test run failure after pythonpath was added
        # to run
        pythonpath = settings.get('pythonpath', [])
        if pythonpath:
            settings['pythonpath'] = [p.strip() for p in pythonpath if p.strip()]
        settings[self.SETTINGS_VERSION] = 2

    def _write_merged_settings(self, settings, path):
        try:
            with open(path, 'wb') as outfile:
                settings.write(outfile)
        except IOError:
            raise RuntimeError('Could not open settings file "%s" for writing' %
                                   path)


class SectionError(Exception):
    """Used when section is tried to replace with normal value or vice versa."""


class ConfigurationError(Exception):
    """Used when settings file is invalid"""


class _Section:

    def __init__(self, section, parent):
        self._config_obj = section
        self._parent = parent

    def save(self):
        self._parent.save()

    def __setitem__(self, name, value):
        self.set(name, value)

    def __getitem__(self, name):
        value = self._config_obj[name]
        if isinstance(value, Section):
            return _Section(value, self)
        return value

    def __iter__(self):
        return iter(self._config_obj)

    def __len__(self):
        return len(self._config_obj)

    def iteritems(self):
        '''Returns an iterator over the (key,value) items of the section'''
        return self._config_obj.iteritems()

    def has_setting(self, name):
        return self._config_obj.has_key(name)

    def get(self, name, default):
        """Returns specified setting or (automatically set) default."""
        try:
            return self[name]
        except KeyError:
            self.set(name, default)
            return default

    def get_without_default(self, name):
        """Returns specified setting or None if setting is not defined."""
        try:
            return self[name]
        except KeyError:
            return None

    def set(self, name, value, autosave=True, override=True):
        """Sets setting 'name' value to 'value'.

        'autosave' can be used to define whether to save or not after values are
        changed. 'override' can be used to specify whether to override existing
        value or not. Setting which does not exist is anyway always created.
        """
        if self._is_section(name) and not isinstance(value, _Section):
            raise SectionError("Cannot override section with value.")
        if isinstance(value, _Section):
            if override:
                self._config_obj[name] = {}
            for key, _value in value._config_obj.items():
                self[name].set(key, _value, autosave, override)
        elif name not in self._config_obj or override:
            self._config_obj[name] = value
            if autosave:
                self.save()

    def set_values(self, settings, autosave=True, override=True):
        """Set values from settings. 'settings' needs to be a dictionary.

        See method set for more info about 'autosave' and 'override'.
        """
        if settings:
            for key, value in settings.items():
                self.set(key, value, autosave=False, override=override)
            if autosave:
                self.save()
        return self

    def set_defaults(self, settings_dict=None, **settings):
        """Sets defaults based on dict and kwargs, kwargs having precedence."""
        settings_dict = settings_dict or {}
        settings_dict.update(settings)
        return self.set_values(settings_dict, override=False)

    def add_section(self, name, **defaults):
        """Creates section or updates existing section with defaults."""
        if name in self._config_obj and not isinstance(self._config_obj[name], Section):
            raise SectionError('Cannot override value with section.')
        if name not in self._config_obj:
            self._config_obj[name] = {}
        return self[name].set_defaults(**defaults)

    def _is_section(self, name):
        return self._config_obj.has_key(name) and \
               isinstance(self._config_obj[name], Section)


class Settings(_Section):

    def __init__(self, user_path):
        try:
            self._config_obj = ConfigObj(user_path, unrepr=True)
        except UnreprError, error:
            raise ConfigurationError(error)
        self._listeners = []
        self.excludes = Excludes(self)

    def save(self):
        self._config_obj.write()

    def add_change_listener(self, l):
        self._listeners.append(l)

    def notify(self, name, old_value, new_value):
        for l in self._listeners:
            l.setting_changed(name, old_value, new_value)

class RideSettings(Settings):

    def __init__(self):
        default_path = os.path.join(os.path.dirname(__file__), 'settings.cfg')
        user_path = initialize_settings('user settings', default_path)
        Settings.__init__(self, user_path)
        self._settings_dir = os.path.dirname(user_path)
        self.set('install root', os.path.dirname(os.path.dirname(__file__)))

    def get_path(self, *parts):
        """Returns path which combines settings directory and given parts."""
        return os.path.join(self._settings_dir, *parts)


class Excludes():

    def __init__(self, settings):
        self._settings = settings if settings else RideSettings()
        self._dir_for_settings = os.path.join(SETTINGS_DIRECTORY, 'excludes')
        self._project_name = self._get_project_name(self._settings.get_without_default('default directory'))
        self._exclude_file_path = self._get_file_path()
        self._settings.add_change_listener(self)

    def _get_file_path(self):
        if not self._project_name:
            return None
        if not os.path.exists(self._dir_for_settings):
            os.makedirs(self._dir_for_settings)
        self._exclude_file_path = os.path.join(self._dir_for_settings, self._project_name)
        return self._exclude_file_path

    def setting_changed(self, name, old_value, new_value):
        if name == 'default directory':
            self._project_name = self._get_project_name(new_value)
            self._exclude_file_path = self._get_file_path()

    def _get_project_name(self, project_dir):
        if not project_dir: # might be None
            return None
        project_dir = project_dir.rstrip('/') # strip trailing slash for os.path.split
        project_name = os.path.split(project_dir)[-1]
        return project_name

    def get_excludes(self):
        with self._get_exclude_file('r') as exclude_file:
            if not exclude_file:
                return []
            return exclude_file.read().split()

    def remove_path(self, path):
        path = path.rstrip('/')
        excludes = self.get_excludes()
        self._write_excludes(filter(lambda item: item != path, excludes))

    def _write_excludes(self, excludes):
        with self._get_exclude_file(read_write='w') as exclude_file:
            for exclude in excludes:
                exclude_file.write("%s\n" % exclude)

    def update_excludes(self, new_excludes):
        excludes = self.get_excludes()
        new_excludes = [exclude.rstrip('/') for exclude in new_excludes]
        new_excludes = [exclude for exclude in new_excludes if exclude not in excludes]
        excludes.extend(new_excludes)
        self._write_excludes(excludes)
        
    def _get_exclude_file(self, read_write):
        if not self._exclude_file_path:
            raise NameError('No project name defined')
        if not os.path.exists(self._exclude_file_path) and read_write.startswith('r'):
            return open(self._exclude_file_path, 'w+')
        if os.path.isdir(self._exclude_file_path):
            raise NameError('"%s" is a directory, not file' % self._exclude_file_path)
        try:
            return open(self._exclude_file_path, read_write)
        except IOError as e:
            raise Exception(e) #TODO FIXME

    def contains(self, path, excludes=None):
        if not path:
            return False
        excludes = excludes or self.get_excludes()
        if len(excludes) < 1:
            return False
        if path in excludes:
            return True
        head, folder = os.path.split(path)
        if folder == self._project_name or head == '/':
            return False
        return self.contains(head, excludes)

