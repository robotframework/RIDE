
import enum
import os
from typing import Final, Union

from ._chardet import chardet_detect


_default_starting_chunk_len: Final = 2028

_control_chars: Final = b"\n\r\t\f\b"
_printable_ascii: Final = _control_chars + bytes(range(32, 127))
_printable_high_ascii: Final = bytes(range(127, 256))


def get_starting_chunk(
    filename: Union[str, os.PathLike], /, *, chunk_len: int = _default_starting_chunk_len
) -> bytes:
    """
    :param filename: File to open and get the first little chunk of.
    :param chunk_len: Number of bytes to read, default 2048.
    :return: Starting chunk of bytes.
    """
    with open(filename, "rb") as f:
        return f.read(chunk_len)


class BinaryLikeliness(enum.Enum):
    HIGH = enum.auto()
    MID = enum.auto()
    LOW = enum.auto()

    @property
    def likely(self) -> bool:
        return self == BinaryLikeliness.MID or self == BinaryLikeliness.HIGH


def is_likely_binary(bytes_to_check: bytes, /) -> BinaryLikeliness:
    """
    :param bytes_to_check: A chunk of bytes to check.
    :return: True if is likely binary, False otherwise.
    """
    # Check for a high percentage of ASCII control characters
    # Binary if control chars are > 30% of the string
    low_chars = bytes_to_check.translate(None, _printable_ascii)
    nontext_ratio1 = float(len(low_chars)) / float(len(bytes_to_check))

    # and check for a low percentage of high ASCII characters:
    # Binary if high ASCII chars are < 5% of the string
    # From: https://en.wikipedia.org/wiki/UTF-8
    # If the bytes are random, the chances of a byte with the high bit set
    # starting a valid UTF-8 character is only 6.64%. The chances of finding 7
    # of these without finding an invalid sequence is actually lower than the
    # chance of the first three bytes randomly being the UTF-8 BOM.

    high_chars = bytes_to_check.translate(None, _printable_high_ascii)
    nontext_ratio2 = float(len(high_chars)) / float(len(bytes_to_check))

    if nontext_ratio1 > 0.9 and nontext_ratio2 > 0.9:
        return BinaryLikeliness.HIGH

    if nontext_ratio1 > 0.3 and nontext_ratio2 < 0.05:
        return BinaryLikeliness.MID
    elif nontext_ratio1 > 0.8 and nontext_ratio2 > 0.8:
        return BinaryLikeliness.MID
    else:
        return BinaryLikeliness.LOW


def is_decodable_as_unicode(bytes_to_check: bytes, /) -> bool:
    """
    :param bytes_to_check: A chunk of bytes to check.
    :return: True if is unicode-decodable, False otherwise.
    """

    # Check for binary for possible encoding detection with chardet
    detected_encoding = chardet_detect(bytes_to_check)

    # Decide if binary or text
    decodable_as_unicode = False
    if detected_encoding["confidence"] > 0.9 and detected_encoding["encoding"] != "ascii":
        try:
            bytes_to_check.decode(encoding=detected_encoding["encoding"])
            decodable_as_unicode = True
        except (LookupError, UnicodeDecodeError):
            pass

    return decodable_as_unicode


def has_null_bytes(bytes_to_check: bytes, /) -> bool:
    """
    :param bytes_to_check: A chunk of bytes to check.
    :return: True if the chunk contains null bytes, False otherwise.
    """
    return b"\x00" in bytes_to_check or b"\xff" in bytes_to_check


def is_binary_string(bytes_to_check: bytes, /) -> bool:
    """
    Uses a simplified version of the Perl detection algorithm,
    based roughly on Eli Bendersky's translation to Python:
    https://eli.thegreenplace.net/2011/10/19/perls-guess-if-file-is-text-or-binary-implemented-in-python/

    This is biased slightly more in favour of deeming files as text
    files than the Perl algorithm, since all ASCII compatible character
    sets are accepted as text, not just utf-8.

    :param bytes_to_check: A chunk of bytes to check.
    :return: True if the chunk appears to be binary (not text), False otherwise.
    """

    # Empty files are considered text files.
    if not bytes_to_check:
        return False

    likely_binary = is_likely_binary(bytes_to_check)
    if likely_binary == BinaryLikeliness.HIGH:
        return True

    decodable_as_unicode = is_decodable_as_unicode(bytes_to_check)

    if likely_binary.likely:
        return not decodable_as_unicode

    if decodable_as_unicode:
        return False

    return has_null_bytes(bytes_to_check)


def is_binary_file(
    filename: Union[str, os.PathLike], /, *, starting_chunk_len: int = _default_starting_chunk_len
) -> bool:
    """
    :param filename: File to check.
    :param starting_chunk_len: Number of bytes to read, default 2048.
    :return: True if it's a binary file, otherwise False.
    """
    # Check if the starting chunk is a binary string
    try:
        chunk = get_starting_chunk(filename, chunk_len=starting_chunk_len)
    except FileNotFoundError:
        if os.path.islink(filename) and not os.path.exists(filename):
            return True
        raise

    return is_binary_string(chunk)


__all__ = (
    "get_starting_chunk",
    "BinaryLikeliness",
    "is_likely_binary",
    "is_decodable_as_unicode",
    "has_null_bytes",
    "is_binary_string",
    "is_binary_file",
)
