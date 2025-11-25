import json
import resource
from asyncio import gather
from collections.abc import Callable
from inspect import isfunction
from typing import Any

import aiohttp
import requests
from bs4 import BeautifulSoup

from libgencomics.errors import (
    LibgenMaxUserConnectionsException,
    LibgenRateLimitedException,
    LibgenRequestURITooLargeException,
    LibgenTimeoutException,
)

__session = requests.Session()


class CONSTANTS:
    EDITION_REQUEST = "/json.php?object=e&ids="
    RESULT_FILE_REQUEST = "/json.php?object=f&ids="
    SERIES_REQUEST = "/json.php?object=s&fields=*&addkeys=309,101&ids="


async def flaresolverr_get(
    session: aiohttp.ClientSession, url: str, flaresolverr_url: str
) -> str:
    data = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,  # 60 seconds
    }
    response = await session.post(
        flaresolverr_url,
        data=json.dumps(data),
        headers={"Content-Type": "application/json"},
    )
    result = await response.json()
    return (
        BeautifulSoup(result["solution"]["response"], "html.parser")
        .select_one("pre")
        .get_text()  # type: ignore
    )


def attempt_request(url: str) -> str:
    for _ in range(5):
        try:
            return __session.get(url).text
        except requests.exceptions.ConnectionError:
            return __session.get(url).text
    return __session.get(url).text


async def fetch_data(
    session: aiohttp.ClientSession, url: str, flaresolverr_url: str | None
) -> str:
    if flaresolverr_url is not None:
        return await flaresolverr_get(session, url, flaresolverr_url)
    async with session.get(url) as response:
        data = await response.text()
        response.close()
        return data


def check_response_error(response: str) -> str:
    if (
        opt_chain(
            BeautifulSoup(response, "html.parser"),
            "title",
            lambda x: x.get_text(),
        )
        or ""
    ).count("Request-URI Too Large") != 0:
        raise LibgenRequestURITooLargeException()
    elif (
        opt_chain(
            BeautifulSoup(response, "html.parser"),
            "div",
            lambda x: x.get_text(),
        )
        or ""
    ).count("max_user_connections") != 0:
        raise LibgenMaxUserConnectionsException()
    elif (
        opt_chain(
            BeautifulSoup(response, "html.parser"),
            "title",
            lambda x: x.get_text(),
        )
        or ""
    ).count("524: A timeout occurred") != 0:
        raise LibgenTimeoutException()
    elif (
        opt_chain(
            BeautifulSoup(response, "html.parser"),
            lambda x: x.select_one("div#what-happened-section p"),
            lambda x: x.get_text(),
        )
        or ""
    ).count("Too many requests for") != 0:
        raise LibgenRateLimitedException

    return response


def is_valid_response(response: str) -> bool:
    try:
        check_response_error(response)
        return True
    except (
        LibgenMaxUserConnectionsException,
        LibgenRequestURITooLargeException,
        LibgenTimeoutException,
    ):
        return False


async def fetch_multiple_urls(
    urls: list[str], flaresolverr_url: str | None
) -> list[str]:
    file_limit: int
    try:
        file_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
    except Exception:
        file_limit = 1024

    async with aiohttp.ClientSession() as session:
        chunks = [urls[x : x + file_limit] for x in range(0, len(urls), file_limit)]

        to_retry: list[str] = []
        final_requests: list[str] = []

        for chunk in chunks:
            current_requests = await gather(
                *[
                    fetch_data(
                        session,
                        url,
                        None,
                    )
                    for url in chunk
                ]
            )
            for index, req in enumerate(current_requests):
                try:
                    if is_valid_response(req):
                        final_requests.append(req)
                    else:
                        to_retry.append(chunk[index])
                except LibgenRateLimitedException:
                    if flaresolverr_url:
                        freq = await fetch_data(session, chunk[index], flaresolverr_url)
                        if is_valid_response(freq):
                            final_requests.append(freq)
                        else:
                            to_retry.append(chunk[index])
                    else:
                        to_retry.append(chunk[index])

    if len(to_retry) != 0:
        final_requests += await fetch_multiple_urls(to_retry, flaresolverr_url)

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
    obj: dict[str, str],
    key: str,
    parse_func: Callable[[str], T],
) -> T | None:
    try:
        return parse_func(obj[key])
    except Exception:
        return None
