import resource
from asyncio import gather
from collections.abc import Callable
from inspect import isfunction
from typing import Any

import aiohttp
import requests

__session = requests.Session()


class CONSTANTS:
    EDITION_REQUEST = "/json.php?object=e&ids="
    RESULT_FILE_REQUEST = "/json.php?object=f&ids="
    SERIES_REQUEST = "/json.php?object=s&fields=*&addkeys=309,101&ids="


def attempt_request(url: str) -> requests.Response:
    for _ in range(5):
        try:
            return __session.get(url)
        except requests.exceptions.ConnectionError:
            return __session.get(url)
    return __session.get(url)


async def fetch_data(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        data = await response.text()
        response.close()
        return data


async def fetch_multiple_urls(urls: list[str]) -> list[str]:
    file_limit: int
    try:
        file_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
    except Exception:
        file_limit = 1024

    async with aiohttp.ClientSession() as session:
        chunks = [urls[x : x + file_limit] for x in range(0, len(urls), file_limit)]

        final_requests = []

        for chunk in chunks:
            current_requests = await gather(
                *[
                    fetch_data(
                        session,
                        url,
                    )
                    for url in chunk
                ]
            )
            final_requests += current_requests

        return final_requests


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
