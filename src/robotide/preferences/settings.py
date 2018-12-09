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
import sys

if sys.version_info[0] == 2:
    PYTHON2 = True
    PYTHON3 = False
elif sys.version_info[0] == 3:
    PYTHON2 = False
    PYTHON3 = True

from robotide.context import SETTINGS_DIRECTORY, LIBRARY_XML_DIRECTORY
from robotide.preferences.configobj import ConfigObj, ConfigObjError,\
    Section, UnreprError
from robotide.preferences import excludes
from robotide.publish import RideSettingsChanged


def initialize_settings(path, dest_file_name=None):
    if not os.path.exists(SETTINGS_DIRECTORY):
        os.makedirs(SETTINGS_DIRECTORY)
    (path, error) = _copy_or_migrate_user_settings(
        SETTINGS_DIRECTORY, path, dest_file_name)
    # if error: # DEBUG This does not work on unitests :(
    #    raise ConfigurationError(error)
    return path


def _copy_or_migrate_user_settings(settings_dir, source_path, dest_file_name):
    """ Creates settings directory and copies or merges the source to there.

    In case source already exists, merge is done.
    Destination file name is the source_path's file name unless dest_file_name
    is given.
    """
    m_error = None
    if not dest_file_name:
        dest_file_name = os.path.basename(source_path)
    settings_path = os.path.join(settings_dir, dest_file_name)
    if not os.path.exists(settings_path):
        shutil.copyfile(source_path, settings_path)
        # print("DEBUG: source %s new settings %s\n" %(source_path,settings_path))
    else:
        try:
            SettingsMigrator(source_path, settings_path).migrate()
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
        self._default_settings = ConfigObj(default_path, unrepr=True)
        self._user_path = user_path
        # print("DEBUG: Settings migrator 1: %s\ndefault_path %s" % (self._default_settings.__repr__(), default_path))
        try:
            self._old_settings = ConfigObj(user_path, unrepr=True)
        except UnreprError as err: # DEBUG errored file
            # print("DEBUG: Settings migrator ERROR -------- %s path %s" %
            #      (self._old_settings.__repr__(), user_path))
            raise ConfigurationError("Invalid config file '%s': %s" %
                                     (user_path, err))
        # print("DEBUG: Settings migrator old_settings: %s\nuser_path %s" %
        # (self._old_settings.__repr__(), self._user_path))
        # print("DEBUG: Settings migrator default_settings: %s\nsettings_path "
        # "%s" % (self._default_settings.__repr__(), default_path))

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
        # if self._old_settings.get(self.SETTINGS_VERSION) == 8:
        #     self.migrate_from_8_to_9(self._old_settings)
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
                if PYTHON2:
                    f.write(new)
                elif PYTHON3:
                    f.write(new.encode('UTF-8'))
        settings[self.SETTINGS_VERSION] = 3

    def migrate_from_3_to_4(self, settings):
        # See issue http://code.google.com/p/robotframework-ride/issues/detail?id=1124
        font_size = settings.get('font size', None)
        if font_size and font_size == 11:
            settings['font size'] = 8
        settings[self.SETTINGS_VERSION] = 4

    def migrate_from_4_to_5(self, settings):
        # Changed color section name
        # see http://code.google.com/p/robotframework-ride/issues/detail?id=1206
        colors = settings.get('Colors', None)
        if colors:
            settings['Grid Colors'] = colors
            del settings['Colors']
        settings[self.SETTINGS_VERSION] = 5

    def migrate_from_5_to_6(self, settings):
        # Made generic Text Edit and Grid sections.
        grid_colors = settings.get('Grid Colors', None)
        if grid_colors:
            settings['Grid'] = grid_colors
            del settings['Grid Colors']
        grid_font_size = settings.get('font size', None)
        if grid_font_size:
            settings['Grid']['font size'] = grid_font_size
            del settings['font size']
        text_edit_colors = settings.get('Text Edit Colors', None)
        if text_edit_colors:
            settings['Text Edit'] = text_edit_colors
            del settings['Text Edit Colors']
        text_font_size = settings.get('text edit font size', None)
        if text_font_size:
            settings['Text Edit']['font size'] = text_font_size
            del settings['text edit font size']
        settings[self.SETTINGS_VERSION] = 6

    def migrate_from_6_to_7(self, settings):
        settings['use installed robot libraries'] = True
        settings[self.SETTINGS_VERSION] = 7

    def migrate_from_7_to_8(self, settings):
        installed_rf_libs = settings.get('use installed robot libraries', None)
        if installed_rf_libs:
            del settings['use installed robot libraries']
            for name in [
                'BuiltIn', 'Collections', 'DateTime', 'Dialogs', 'Easter',
                'OperatingSystem', 'Process', 'Remote',
                'Screenshot', 'String', 'Telnet', 'XML']:
                lib_xml_path = os.path.join(LIBRARY_XML_DIRECTORY,
                                            '{}.xml'.format(name))
                if os.path.exists(lib_xml_path):
                    os.remove(lib_xml_path)
        settings[self.SETTINGS_VERSION] = 8

    """
    def migrate_from_8_to_9(self, settings):
        # mainframe_size = settings.get('mainframe size', (1100, 700))
        parameters = [
            'mainframe_size',
            'mainframe_position',
            'mainframe_maximized',
            'default_directory',
            'list_variable_columns',
            'list_col_min_width',
            'list_col_max_width',
            'auto_imports',
            'library_xml_directories',
            'txt_number_of_spaces',
            'txt_format_separator',
            'line_separator',
            'default_file_format',
            'check_for_updates',
            'last_update_check',
            'install_root'
        ]
        sec_text = ['font size']  # [Text Edit]
        sec_grid = [              # [Grid]
            'font_size',
            'fixed_font',
            'col_size',
            'max_col_size',
            'auto_size_cols',
            'text_user_keyword',
            'text_library_keyword',
            'text_variable',
            'text_unknown_variable',
            'text_commented',
            'text_string',
            'text_empty',
            'background_assign',
            'background_keyword',
            'background_mandatory',
            'background_optional',
            'background_must_be_empty',
            'background_unknown',
            'background_error',
            'background_highlight'
        ]
        try:
            for keyname in parameters:
                self._key_with_underscore(settings, keyname)
            for keyname in sec_text:
                self._key_with_underscore(settings, keyname, 'Text Edit')
            for keyname in sec_grid:
                self._key_with_underscore(settings, keyname, 'Grid')
        except AttributeError:  # DEBUG Ignore errors
            #  raise ConfigObjError
            pass
        settings[self.SETTINGS_VERSION] = 9
    """

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

    def _write_merged_settings(self, settings, path):
        try:
            with open(path, 'wb') as outfile: # DEBUG used to be 'wb'
                if PYTHON2:
                    settings.write(outfile)
                elif PYTHON3:  # DEBUG
                    settings.write(outfile) # DEBUG .encoding('UTF-8')
        except IOError:
            raise RuntimeError(
                'Could not open settings file "%s" for writing' % path)



class SectionError(Exception):
    """Used when section is tried to replace with normal value or vice versa."""


class ConfigurationError(Exception):
    """Used when settings file is invalid"""


class _Section(object):

    def __init__(self, section, parent=None, name=''):
        self._config_obj = section
        self._parent = parent
        self._name = name

    def save(self):
        self._parent.save()

    def __setitem__(self, name, value):
        self.set(name, value)

    def __getitem__(self, name):
        value = self._config_obj[name]
        if isinstance(value, Section):
            return _Section(value, self, name)
        return value

    def __iter__(self):
        return iter(self._config_obj)

    def __len__(self):
        return len(self._config_obj)

    def iteritems(self):
        """Returns an iterator over the (key,value) items of the section"""
        if PYTHON2:
            return self._config_obj.iteritems()
        elif PYTHON3:
            return self._config_obj.items()

    def has_setting(self, name):
        return name in self._config_obj

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
                self._config_obj[name] = {}
            for key, _value in value._config_obj.items():
                self[name].set(key, _value, autosave, override)
        elif name not in self._config_obj or override:
            old = self._config_obj[name] if name in self._config_obj else None
            self._config_obj[name] = value
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
        if name in self._config_obj and \
           not isinstance(self._config_obj[name], Section):
            raise SectionError('Cannot override value with section.')
        if name not in self._config_obj:
            self._config_obj[name] = {}
        return self[name].set_defaults(**defaults)

    def _is_section(self, name):
        return name in self._config_obj and \
            isinstance(self._config_obj[name], Section)


class Settings(_Section):

    def __init__(self, user_path):
        try:
            _Section.__init__(self, ConfigObj(user_path, unrepr=True))
        except UnreprError as error:
            raise ConfigurationError(error)
        self.excludes = excludes.Excludes(SETTINGS_DIRECTORY)

    def save(self):
        self._config_obj.write()


class RideSettings(Settings):

    def __init__(self):
        self._default_path = os.path.join(os.path.dirname(__file__), 'settings.cfg')
        # print("DEBUG: RideSettings, default_path %s\n" % self._default_path)
        user_path = initialize_settings(self._default_path)
        Settings.__init__(self, user_path)
        self._settings_dir = os.path.dirname(user_path)
        # print("DEBUG: RideSettings, self._settings_dir %s\n" % self._settings_dir)
        self.set('install root', os.path.dirname(os.path.dirname(__file__)))

    def get_path(self, *parts):
        """Returns path which combines settings directory and given parts."""
        return os.path.join(self._settings_dir, *parts)
