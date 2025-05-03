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


def opt_chain_str(root: Any, *keys: str | int | Callable[[Any], Any]) -> Any | str:
    return opt_chain(root, *keys) or ""


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
                f"https://libgen.gs/index.php?req={query_parsed}&curtab=s&res=100"
            )
        else:
            search_url = f"https://libgen.gs/index.php?req={query_parsed}&curtab=s&res=100&page={page}"
        return requests.get(search_url)

    def add_comicvine_url(
        self, output_data: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        for series in output_data:
            if series["ID"] != "":
                series_url = f"https://libgen.gs/json.php?object=s&ids={series['ID']}&fields=*&addkeys=309"
                series_results = list(
                    json.loads(requests.get(series_url).text).values()
                )[0]

                if "add" in series_results:
                    for added_key in series_results["add"].values():
                        if added_key["value"].startswith(
                            "https://comicvine.gamespot.com"
                        ):
                            series["Comicvine"] = added_key["value"]
        return output_data

    def aggregate_series_data(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        if opt_chain_str(soup.find_all("center"), 1, "string") == "nginx":
            raise Exception(opt_chain_str(soup.find_all("center"), 0, "string"))

        # Table of data to scrape.
        information_table = opt_chain(soup.find(id="tablelibgen"), "tbody")

        if information_table is None:
            return []

        output_data = []

        for row in information_table.find_all("tr"):
            first_cell_data = opt_chain(
                row, lambda x: x.find_all("td"), 0, lambda x: x.find_all("a"), 0
            )

            add_edit = (
                opt_chain_str(
                    first_cell_data, "attrs", "title", lambda x: x.split("<br>"), 0
                )
                .replace("Time added/Time modified : ", "")
                .split("/")
            )

            published_period = (
                opt_chain_str(row, lambda x: x.find_all("td"), 1, "nobr", "string")
                .strip()
                .split("―")
            )

            output_data.append(
                {
                    "Title": opt_chain_str(first_cell_data, "string").strip(),
                    "ID": opt_chain_str(first_cell_data, "attrs", "href")
                    .replace("series.php?id=", "")
                    .strip(),
                    "Add": opt_chain_str(add_edit, 0).strip(),
                    "Edit": opt_chain_str(add_edit, 1).strip(),
                    "Started": opt_chain_str(published_period, 0),
                    "Ended": opt_chain_str(published_period, 1),
                    "Publisher": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        2,
                        lambda x: ";".join(
                            map(lambda x: opt_chain_str(x, "string"), x.find_all("a"))
                        ),
                        "string",
                    ).strip(),
                    "Language": opt_chain_str(
                        row, lambda x: x.find_all("td"), 3, "string"
                    ).strip(),
                    "Comicvine": "",
                }
            )
        output_data = self.add_comicvine_url(output_data)
        return output_data

    def get_series(self) -> dict[str, str] | None:
        soup = BeautifulSoup(self.get_search_page().text, "html.parser")

        if opt_chain_str(soup.find_all("center"), 1, "string") == "nginx":
            raise Exception(opt_chain_str(soup.find_all("center"), 0, "string"))

        if soup.find(id="paginator_example_top") is not None:
            page = 1

            while soup.find("tbody") is not None:
                for series in self.aggregate_series_data(soup):
                    if series["Comicvine"] == self.comicvine_url:
                        return series

                page += 1
                soup = BeautifulSoup(self.get_search_page(page).text, "html.parser")
        else:
            for series in self.aggregate_series_data(soup):
                if series["Comicvine"] == self.comicvine_url:
                    return series

        return None

    def fetch_editions_data(self) -> list[dict[str, str]]:
        series = self.get_series()

        if series is None:
            return []

        series_url = (
            f"https://libgen.gs/json.php?object=s&fields=editions&ids={series['ID']}"
        )
        edition_ids = list(
            list(json.loads(requests.get(series_url).text).values())[0][
                "editions"
            ].keys()
        )

        output_data = []

        for ed_id in edition_ids:
            ed_url = f"https://libgen.gs/json.php?object=e&ids={ed_id}"
            edition = list(json.loads(requests.get(ed_url).text).values())[0]

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
            list(json.loads(requests.get(files_url).text).values())[0]["files"].values()
        )

        output_data = []

        for file_result in files_results:
            file_url = f"https://libgen.gs/json.php?object=f&ids={file_result['f_id']}"
            file = list(json.loads(requests.get(file_url).text).values())[0]

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
