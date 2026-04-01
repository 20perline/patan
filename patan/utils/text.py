import re
from typing import TypeVar, overload

T = TypeVar("T")

@overload
def sanitize_filename_text(obj: str) -> str: ...
@overload
def sanitize_filename_text(obj: list[str]) -> list[str]: ...
@overload
def sanitize_filename_text(obj: T) -> T: ...

def sanitize_filename_text(obj: str | list[str] | T) -> str | list[str] | T:
    pattern = r"[^\u4e00-\u9fa5a-zA-Z0-9#]"
    if isinstance(obj, list):
        return [re.sub(pattern, "_", item) for item in obj]
    if isinstance(obj, str):
        return re.sub(pattern, "_", obj)
    return obj
