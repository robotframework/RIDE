
from .check import (
    BinaryLikeliness,
    get_starting_chunk,
    has_null_bytes,
    is_binary_file,
    is_binary_string,
    is_decodable_as_unicode,
    is_likely_binary,
)


__version__ = "1.0.1"


__all__ = (
    "get_starting_chunk",
    "BinaryLikeliness",
    "is_likely_binary",
    "is_decodable_as_unicode",
    "has_null_bytes",
    "is_binary_string",
    "is_binary_file",
    "__version__",
)
