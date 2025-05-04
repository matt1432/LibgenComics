import json
from collections.abc import Callable
from inspect import isfunction
from typing import Any

import requests
from bs4 import BeautifulSoup

# WHY
# The SearchRequest module contains all the internal logic for the library.
#
# This encapsulates the logic,
# ensuring users can work at a higher level of abstraction.

# USAGE
# req = search_request.SearchRequest("[QUERY]", search_type="[title]")


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


class SearchRequest:
    def __init__(self, query: str, comicvine_url: str) -> None:
        self.query = query
        self.comicvine_url = comicvine_url

        if len(self.query) < 3:
            raise Exception("Query is too short")

    def get_search_page(self, page: int | None = None) -> requests.Response:
        query_parsed = "%20".join(self.query.split(" "))
        if page is None:
            search_url = (
                f"https://libgen.gs/index.php?req={query_parsed}&curtab=s&res=25"
            )
        else:
            search_url = f"https://libgen.gs/index.php?req={query_parsed}&curtab=s&res=25&page={page}"
        return attempt_request(search_url)

    def aggregate_series_data(self, soup: BeautifulSoup) -> dict[str, str] | None:
        if opt_chain(soup.find_all("center"), 1, "string") == "nginx":
            raise Exception(opt_chain(soup.find_all("center"), 0, "string"))

        # Table of data to scrape.
        information_table = opt_chain(soup.find(id="tablelibgen"), "tbody")

        if information_table is None:
            return None

        for row in information_table.find_all("tr"):
            series_temp_url = opt_chain(
                row,
                "td",
                "a",
                "attrs",
                "href",
            )

            if series_temp_url is not None:
                series = {
                    "Comicvine": "",
                    "ID": series_temp_url.replace("series.php?id=", "").strip(),
                    "Language": "",
                }

                series_url = f"https://libgen.gs/json.php?object=s&ids={series['ID']}&fields=*&addkeys=309,101"
                series_results = {
                    "add": {},
                    **list(json.loads(attempt_request(series_url).text).values())[0],
                }

                for added_key in series_results["add"].values():
                    if added_key["key"] == "101":
                        series["Language"] = added_key["value"]

                    elif added_key["value"].startswith(
                        "https://comicvine.gamespot.com"
                    ):
                        series["Comicvine"] = added_key["value"]

                if series["Comicvine"] == self.comicvine_url:
                    return {
                        "Title": series_results["title"],
                        "Publisher": series_results["publisher"],
                        "Started": series_results["date_start"],
                        "Ended": series_results["date_end"],
                        "Added": series_results["time_added"],
                        "Edited": series_results["time_last_modified"],
                        **series,
                    }
        return None

    def get_series(self) -> dict[str, str] | None:
        soup = BeautifulSoup(self.get_search_page().text, "html.parser")

        series = self.aggregate_series_data(soup)

        if series is not None:
            return series

        if soup.find(id="paginator_example_top") is not None:
            page = 2
            soup = BeautifulSoup(self.get_search_page(page).text, "html.parser")

            while soup.find("tbody") is not None:
                series = self.aggregate_series_data(soup)

                if series is not None:
                    return series

                page += 1
                soup = BeautifulSoup(self.get_search_page(page).text, "html.parser")
        return None

    def fetch_editions_data(self) -> list[dict[str, str]]:
        series = self.get_series()

        if series is None:
            return []

        series_url = (
            f"https://libgen.gs/json.php?object=s&fields=editions&ids={series['ID']}"
        )
        edition_ids = list(
            list(json.loads(attempt_request(series_url).text).values())[0][
                "editions"
            ].keys()
        )

        output_data = []

        for ed_id in edition_ids:
            ed_url = f"https://libgen.gs/json.php?object=e&ids={ed_id}"
            edition = list(json.loads(attempt_request(ed_url).text).values())[0]

            output_data.append(
                {
                    "Number": edition["issue_total_number"],
                    "ID": ed_id,
                    "Comicvine": series["Comicvine"],
                    "Title": edition["title"],
                    "Author": edition["author"],
                    "Publisher": edition["publisher"],
                    "Year": edition["year"],
                    "Month": edition["month"],
                    "Day": edition["day"],
                    "Pages": edition["pages"],
                    "Cover": edition["cover_url"],
                    "Added": edition["time_added"],
                    "Edited": edition["time_last_modified"],
                }
            )
        return output_data

    def fetch_files_data(self, issue: dict[str, str]) -> list[dict[str, str]]:
        files_url = (
            f"https://libgen.gs/json.php?object=e&fields=files&ids={issue['ID']}"
        )
        files_results = list(
            list(json.loads(attempt_request(files_url).text).values())[0][
                "files"
            ].values()
        )

        output_data = []

        for file_result in files_results:
            file_url = f"https://libgen.gs/json.php?object=f&ids={file_result['f_id']}"
            file = list(json.loads(attempt_request(file_url).text).values())[0]

            if file["broken"] == "N":
                output_data.append(
                    {
                        "Download": f"https://libgen.gl/get.php?md5={file['md5']}",
                        "Filename": file["locator"].split("\\")[-1],
                        "Pages": file["archive_files_pic_count"],
                        "Comicvine": issue["Comicvine"],
                        "DPI": file["dpi"],
                        "Added": file["time_added"],
                        "Edited": file["time_last_modified"],
                        "Size": file["filesize"],
                        "Extension": file["extension"],
                        "Created": file["file_create_date"],
                        "Type": file["scan_type"],
                        "Releaser": file["releaser"],
                        "Resolution": file["scan_size"],
                    }
                )
        return output_data
