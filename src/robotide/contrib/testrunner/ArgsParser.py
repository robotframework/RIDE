from robotide.robotapi import LOG_LEVELS


class ArgsParser:

    @staticmethod
    def get_message_log_level(args, default='INFO'):
        level = ArgsParser._get_arg_value('-L', '--loglevel',
                                          args, default)
        return LOG_LEVELS.get(level.upper(), default)

    @staticmethod
    def get_output_directory(args, default):
        return ArgsParser._get_arg_value('-d', '--outputdir',
                                         args, default)

    @staticmethod
    def _get_arg_value(short_name, full_name, source, default):
        if short_name in source:
            switch = short_name
        elif full_name in source:
            switch = full_name
        else:
            return default
        i = source.index(switch)
        if len(source) == i:
            return default
        return source[i + 1]
