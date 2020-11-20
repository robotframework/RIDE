class SettingsParser:

    @staticmethod
    def get_console_log_name(settings):
        return SettingsParser._get_settings_value('console_log_name', settings)

    @staticmethod
    def _get_settings_value(name, source, default=''):
        if name in source:
            switch = name
        else:
            return default
        i = source.index(switch)
        if len(source) == i:
            return default
        return source[i + 1]
