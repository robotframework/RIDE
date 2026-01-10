
from typing import Callable, TypedDict, cast


class DetectResult(TypedDict):
    encoding: str
    confidence: float
    language: str


Detect = Callable[[bytes], DetectResult]


def _get_chardet_detect() -> Detect:
    try:
        detect = __import__("cchardet").detect
    except ImportError:
        detect = __import__("chardet").detect

    return cast(Detect, detect)


chardet_detect = _get_chardet_detect()


__all__ = ("DetectResult", "chardet_detect")
