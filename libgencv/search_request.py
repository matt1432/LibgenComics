import json

import requests
from bs4 import BeautifulSoup

from .lib import attempt_request, opt_chain
from .series import Series


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

    def aggregate_series_data(self, soup: BeautifulSoup) -> Series | None:
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
                series_id = series_temp_url.replace("series.php?id=", "").strip()
                series = Series(series_id)

                if series.comicvine_url == self.comicvine_url:
                    return series
        return None

    def get_series(self) -> Series | None:
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

        edition_ids = list(series.get("editions").keys())

        output_data = []

        for ed_id in edition_ids:
            ed_url = f"https://libgen.gs/json.php?object=e&ids={ed_id}"
            edition = list(json.loads(attempt_request(ed_url).text).values())[0]

            output_data.append(
                {
                    "Number": edition["issue_total_number"],
                    "ID": ed_id,
                    "Comicvine": series.comicvine_url,
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
