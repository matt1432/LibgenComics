from collections.abc import Callable
from inspect import isfunction
from typing import Any, TypeVar

import requests


def attempt_request(url: str) -> requests.Response:
    while True:
        try:
            return requests.get(url)
        except requests.exceptions.ConnectionError as e:
            print(e)
            return requests.get(url)


# attempts to chain attributes, indexes or functions of the root object
def opt_chain(root: Any, *keys: str | int | Callable[[Any], Any]) -> Any | None:
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


T = TypeVar("T")


def parse_value(
    obj: dict[str, str], key: str, parse_func: Callable[[str], T]
) -> T | None:
    try:
        return parse_func(obj[key])
    except Exception:
        return None
