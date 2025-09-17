from collections.abc import Callable
from inspect import isfunction
from typing import Any

import grequests  # type: ignore # noqa: F401
import requests

__session = requests.Session()


class CONSTANTS:
    EDITION_REQUEST = "/json.php?object=e&ids="
    SERIES_REQUEST = "/json.php?object=s&fields=*&addkeys=309,101&ids="


def attempt_request(url: str) -> requests.Response:
    for _ in range(5):
        try:
            return __session.get(url)
        except requests.exceptions.ConnectionError:
            return __session.get(url)
    return __session.get(url)


# attempts to chain attributes, indexes or functions of the root object
def opt_chain(
    root: Any,
    *keys: str | int | Callable[[Any], Any],
) -> Any | None:
    result = root
    for k in keys:
        if isinstance(result, dict):
            result = result.get(k, None)
        elif isinstance(result, list) and isinstance(k, int):
            if k < len(result):
                result = result[k]
            else:
                result = None
        elif isfunction(k):
            result = k(result)
        else:
            result = getattr(result, str(k), None)
        if result is None:
            break
    return result


def parse_value[T](
    obj: dict[str, str], key: str, parse_func: Callable[[str], T]
) -> T | None:
    try:
        return parse_func(obj[key])
    except Exception:
        return None
