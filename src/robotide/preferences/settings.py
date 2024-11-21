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

import os
import shutil

from ..context import SETTINGS_DIRECTORY, LIBRARY_XML_DIRECTORY, EXECUTABLE
# from .configobj import ConfigObj, ConfigObjError, Section, UnreprError
from . import ConfigObj, ConfigObjError, Section, UnreprError
from .excludes_class import Excludes
from ..publish import RideSettingsChanged

FONT_SIZE = 'font size'
GRID_COLORS = 'Grid Colors'
USE_INSTALLED = 'use installed robot libraries'


def initialize_settings(path, dest_file_name=None):
    if not os.path.exists(SETTINGS_DIRECTORY):
        os.makedirs(SETTINGS_DIRECTORY)
    if not os.path.exists(path):
        path = os.path.join(SETTINGS_DIRECTORY, path)
    (path, error) = _copy_or_migrate_user_settings(
        SETTINGS_DIRECTORY, path, dest_file_name)
    if error:
        raise ConfigurationError(error)
    return path


def _copy_or_migrate_user_settings(settings_dir, source_path, dest_file_name):
    """ Creates settings directory and copies or merges the source to there.

    In case source already exists, merge is done.
    Destination file name is the source_path's file name unless dest_file_name
    is given.
    """
    m_error = None
    if not os.path.exists(source_path):
        raise(FileNotFoundError(source_path))
    if not dest_file_name:
        dest_file_name = os.path.basename(source_path)
    settings_path = os.path.join(settings_dir, dest_file_name)
    if not os.path.exists(settings_path):
        shutil.copyfile(source_path, settings_path)
        # print("DEBUG: source %s new settings %s\n" %(source_path,settings_path))
    else:
        try:
            SettingsMigrator(source_path, settings_path).migrate()
            # print(f"DEBUG: settings After migration {source_path} with {settings_path}")
        except ConfigObjError as parsing_error:
            print("WARNING! corrupted configuration file replaced with defaults")
            print(parsing_error)
            m_error = parsing_error
            shutil.copyfile(settings_path, settings_path + '_old_broken')
            print("(backed up corrupted configuration file at: %s)" %
                  (settings_path + '_old_broken'))
            shutil.copyfile(source_path, settings_path)
            # print("DEBUG: source %s corrupted settings %s\n" % (source_path, settings_path))
        finally:  # DEBUG Try to merge some settings
            # print("DEBUG: Finally merge() %s\n" % settings_path)
            SettingsMigrator(source_path, settings_path).merge()
    return os.path.abspath(settings_path), m_error


class SettingsMigrator(object):

    SETTINGS_VERSION = 'settings_version'

    def __init__(self, default_path, user_path):
        self._default_settings = ConfigObj(default_path, encoding='UTF-8', unrepr=True)
        self._user_path = user_path
        # print("DEBUG: Settings migrator 1: %s\ndefault_path %s" % (self._default_settings.__repr__(), default_path))
        try:
            self._old_settings = ConfigObj(user_path, encoding='UTF-8', unrepr=True)
        except UnreprError as err:  # DEBUG errored file
            # print("DEBUG: Settings migrator ERROR -------- %s path %s" %
            #      (self._old_settings.__repr__(), user_path))
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
        if self._old_settings.get(self.SETTINGS_VERSION) == 2:
            self.migrate_from_2_to_3(self._old_settings)
        if self._old_settings.get(self.SETTINGS_VERSION) == 3:
            self.migrate_from_3_to_4(self._old_settings)
        if self._old_settings.get(self.SETTINGS_VERSION) == 4:
            self.migrate_from_4_to_5(self._old_settings)
        if self._old_settings.get(self.SETTINGS_VERSION) == 5:
            self.migrate_from_5_to_6(self._old_settings)
        if self._old_settings.get(self.SETTINGS_VERSION) == 6:
            self.migrate_from_6_to_7(self._old_settings)
        if self._old_settings.get(self.SETTINGS_VERSION) == 7:
            self.migrate_from_7_to_8(self._old_settings)
        self.merge()

    def merge(self):
        # print("DEBUG: Merge before: %s\n", self._default_settings.__repr__())
        self._default_settings.merge(self._old_settings)
        # print("DEBUG: Merge after: %s, old%s\n" % (self._default_settings.__repr__(), self._old_settings.__repr__()))
        self._write_merged_settings(self._default_settings, self._user_path)

    def migrate_from_0_to_1(self, settings):
        if settings.get('Colors', {}).get('text library keyword') == 'blue':
            settings['Colors']['text library keyword'] = '#0080C0'
        settings[self.SETTINGS_VERSION] = 1

    def migrate_from_1_to_2(self, settings):
        # See issue http://code.google.com/p/robotframework-ride/issues/detail?id=925
        # And other reported issues about test run failure after pythonpath was added
        # to run
        pythonpath = settings.get('pythonpath', [])
        if pythonpath:
            settings['pythonpath'] = [p.strip() for p
                                      in pythonpath if p.strip()]
        settings[self.SETTINGS_VERSION] = 2

    def migrate_from_2_to_3(self, settings):
        # See issue http://code.google.com/p/robotframework-ride/issues/detail?id=1107
        old_excludes = os.path.join(SETTINGS_DIRECTORY, 'excludes')
        if os.path.isfile(old_excludes):
            with open(old_excludes) as f:
                old = f.read()
            new = '\n'.join(d for d in old.split('\n') if os.path.isdir(d))+'\n'
            with open(old_excludes, 'wb') as f:
                f.write(new.encode('UTF-8'))
        settings[self.SETTINGS_VERSION] = 3

    def migrate_from_3_to_4(self, settings):
        # See issue http://code.google.com/p/robotframework-ride/issues/detail?id=1124
        font_size = settings.get(FONT_SIZE, None)
        if font_size and font_size == 11:
            settings[FONT_SIZE] = 8
        settings[self.SETTINGS_VERSION] = 4

    def migrate_from_4_to_5(self, settings):
        # Changed color section name
        # see http://code.google.com/p/robotframework-ride/issues/detail?id=1206
        colors = settings.get('Colors', None)
        if colors:
            settings[GRID_COLORS] = colors
            del settings['Colors']
        settings[self.SETTINGS_VERSION] = 5

    def migrate_from_5_to_6(self, settings):
        # Made generic Text Edit and Grid sections.
        grid_colors = settings.get(GRID_COLORS, None)
        if grid_colors:
            settings['Grid'] = grid_colors
            del settings[GRID_COLORS]
        grid_font_size = settings.get(FONT_SIZE, None)
        if grid_font_size:
            settings['Grid'][FONT_SIZE] = grid_font_size
            del settings[FONT_SIZE]
        text_edit_colors = settings.get('Text Edit Colors', None)
        if text_edit_colors:
            settings['Text Edit'] = text_edit_colors
            del settings['Text Edit Colors']
        text_font_size = settings.get('text edit font size', None)
        if text_font_size:
            settings['Text Edit'][FONT_SIZE] = text_font_size
            del settings['text edit font size']
        settings[self.SETTINGS_VERSION] = 6

    def migrate_from_6_to_7(self, settings):
        settings[USE_INSTALLED] = True
        settings[self.SETTINGS_VERSION] = 7

    def migrate_from_7_to_8(self, settings):
        installed_rf_libs = settings.get(USE_INSTALLED, None)
        if installed_rf_libs:
            del settings[USE_INSTALLED]
            for name in [
                         'BuiltIn', 'Collections', 'DateTime', 'Dialogs', 'Easter', 'OperatingSystem', 'Process',
                         'Remote', 'Screenshot', 'String', 'Telnet', 'XML']:
                lib_xml_path = os.path.join(LIBRARY_XML_DIRECTORY, '{}.xml'.format(name))
                if os.path.exists(lib_xml_path):
                    os.remove(lib_xml_path)
        settings[self.SETTINGS_VERSION] = 8

    @staticmethod
    def _key_with_underscore(settings, keyname, section=None):
        keyname_old = keyname.replace('_', ' ')
        if not section:
            value = settings.get(keyname_old, None)
            if value:
                settings[keyname] = value
                del settings[keyname_old]
        else:
            value = settings.get(section, {}).get(keyname_old, None)
            if value:
                settings[section][keyname] = value
                del settings[section][keyname_old]

    @staticmethod
    def _write_merged_settings(settings, path):
        try:
            with open(path, 'wb') as outfile:  # DEBUG used to be 'wb'
                settings.write(outfile)  # DEBUG .encoding('UTF-8')
        except IOError:
            raise RuntimeError(
                'Could not open settings file "%s" for writing' % path)


class SectionError(Exception):
    """Used when section is tried to replace with normal value or vice versa."""


class ConfigurationError(Exception):
    """Used when settings file is invalid"""


class _Section(object):

    def __init__(self, section, parent=None, name=''):
        self.config_obj = section
        self._parent = parent
        self._name = name

    def save(self):
        self._parent.save()

    def __setitem__(self, name, value):
        self.set(name, value)

    def __getitem__(self, name):
        value = self.config_obj[name]
        if isinstance(value, Section):
            return _Section(value, self, name)
        return value

    def __iter__(self):
        return iter(self.config_obj)

    def __len__(self):
        return len(self.config_obj)

    def iteritems(self):
        """Returns an iterator over the (key,value) items of the section"""
        return self.config_obj.items()

    def has_setting(self, name):
        return name in self.config_obj

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

        'autosave' can be used to define whether to save automatically
        after values are changed. 'override' can be used to specify
        whether to override existing value or not. Setting which does
        not exist is anyway always created.
        """
        if self._is_section(name) and not isinstance(value, _Section):
            raise SectionError("Cannot override section with value.")
        if isinstance(value, _Section):
            if override:
                self.config_obj[name] = {}
            for key, _value in value.config_obj.items():
                self[name].set(key, _value, autosave, override)
        elif name not in self.config_obj or override:
            old = self.config_obj[name] if name in self.config_obj else None
            self.config_obj[name] = value
            if autosave:
                self.save()
            RideSettingsChanged(
                keys=[self._name, name], old=old, new=value).publish()

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
        if name in self.config_obj and \
           not isinstance(self.config_obj[name], Section):
            raise SectionError('Cannot override value with section.')
        if name not in self.config_obj:
            self.config_obj[name] = {}
        return self[name].set_defaults(**defaults)

    def _is_section(self, name):
        return name in self.config_obj and \
            isinstance(self.config_obj[name], Section)


class Settings(_Section):

    def __init__(self, user_path):
        try:
            _Section.__init__(self, ConfigObj(user_path, encoding='UTF-8', unrepr=True))
        except UnreprError as error:
            raise ConfigurationError(error)
        self.excludes = Excludes(SETTINGS_DIRECTORY)

    def save(self):
        self.config_obj.write()


class RideSettings(Settings):

    def __init__(self, path=None):
        if path:
            self._default_path = path
        else:
            path = os.getenv('RIDESETTINGS', 'user')
            if path == 'user':
                self._default_path = os.path.join(os.path.dirname(__file__), 'settings.cfg')
            elif path.endswith('.cfg') and os.path.exists(path):
                self._default_path = path
        # print(f"DEBUG: settings.py RideSettings SETTINGS {self._default_path=}")
        user_path = initialize_settings(self._default_path)
        Settings.__init__(self, user_path)
        self._settings_dir = os.path.dirname(user_path)
        # print(f"DEBUG: RideSettings, self._settings_dir={self._settings_dir}")
        self.get('install root', os.path.dirname(os.path.dirname(__file__)))
        self.executable = self.get('executable', EXECUTABLE)
        if self.executable != EXECUTABLE:
            digest = 0
            for c in EXECUTABLE:
                digest += ord(c)
            new_user_path = user_path.replace("settings.cfg", f"settings_{digest}.cfg")
            new_user_path = initialize_settings(user_path, new_user_path)
            Settings.__init__(self, new_user_path)
            self._settings_dir = os.path.dirname(new_user_path)
            self.set('install root', os.path.dirname(os.path.dirname(__file__)))
            self.executable = self.set('executable', EXECUTABLE)

    def get_path(self, *parts):
        """Returns path which combines settings directory and given parts."""
        return os.path.join(self._settings_dir, *parts)
