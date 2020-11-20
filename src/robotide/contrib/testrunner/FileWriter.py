import codecs

from robotide.context import IS_WINDOWS
from sys import getfilesystemencoding

OUTPUT_ENCODING = getfilesystemencoding()


class FileWriter:

    @staticmethod
    def write(file_path, lines, windows_mode, mode='w'):
        if IS_WINDOWS:
            f = codecs.open(file_path, mode=windows_mode)
            for item in lines:
                if isinstance(item, str):
                    enc_arg = item.encode('UTF-8')  # OUTPUT_ENCODING
                else:
                    enc_arg = item
                try:
                    f.write(enc_arg)
                    f.write("\n".encode(OUTPUT_ENCODING))
                except UnicodeError:
                    f.write(bytes(item, 'UTF-8'))
                    f.write(b"\n")
        else:
            f = codecs.open(file_path, mode, "UTF-8")
            f.write("\n".join(lines))
        f.close()
