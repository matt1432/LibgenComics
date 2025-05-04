from collections.abc import Callable
from inspect import isfunction
from typing import Any

import requests


def attempt_request(url: str) -> requests.Response:
    while True:
        try:
            return requests.get(url)
        except ConnectionError as e:
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


def filter_results(
    results: list[dict[str, str]], filters: dict[str, str], exact_match: bool = True
) -> list[dict[str, str]]:
    """
    Returns a list of results that match the given filter criteria.
    When exact_match = true, we only include results that exactly match
    the filters (ie. the filters are an exact subset of the result).

    When exact-match = false,
    we run a case-insensitive check between each filter field and each result.

    exact_match defaults to TRUE -
    this is to maintain consistency with older versions of this library.
    """

    filtered_list = []
    if exact_match:
        for result in results:
            # check whether a candidate result matches the given filters
            if filters.items() <= result.items():
                filtered_list.append(result)

    else:
        filter_matches_result = False
        for result in results:
            for field, query in filters.items():
                if query.casefold() in result[field].casefold():
                    filter_matches_result = True
                else:
                    filter_matches_result = False
                    break
            if filter_matches_result:
                filtered_list.append(result)
    return filtered_list
