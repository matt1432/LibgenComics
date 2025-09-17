import requests
from bs4 import BeautifulSoup

from libgencomics.common import attempt_request, opt_chain
from libgencomics.errors import LibgenSeriesNotFoundException
from libgencomics.libgen_objects import Edition, ResultFile, Series


class SearchRequest:
    def __init__(
        self,
        *,
        query: str,
        comicvine_url: str,
        libgen_site_url: str,
        libgen_series_id: int | None = None,
    ) -> None:
        self.query = query
        self.comicvine_url = comicvine_url
        self.libgen_site_url = libgen_site_url
        self.libgen_series_id = libgen_series_id

    def get_search_page(self, page: int | None = None) -> requests.Response:
        query_parsed = "%20".join(self.query.split(" "))
        if page is None:
            search_url = (
                f"{self.libgen_site_url}/index.php?req={query_parsed}&curtab=s&res=25"
            )
        else:
            search_url = f"{self.libgen_site_url}/index.php?req={query_parsed}&curtab=s&res=25&page={page}"
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
                series_id = int(series_temp_url.replace("series.php?id=", "").strip())
                series = Series(
                    id=series_id,
                    libgen_site_url=self.libgen_site_url,
                    comicvine_url=None,
                )

                if series.comicvine_url == self.comicvine_url:
                    return series
        return None

    def get_series(self) -> Series | None:
        if self.libgen_series_id is not None:
            return Series(
                id=self.libgen_series_id,
                comicvine_url=self.comicvine_url,
                libgen_site_url=self.libgen_site_url,
            )

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
        raise LibgenSeriesNotFoundException(
            f"No matching series were found for {self.query}."
        )

    def fetch_editions_data(self) -> list[Edition]:
        series = self.get_series()

        if series is None or series.comicvine_url is None:
            return []

        output_data: list[Edition] = []
        edition_ids = list(series.get("editions").keys())

        for ed_id in edition_ids:
            output_data.append(
                Edition(id=ed_id, series=series, libgen_site_url=self.libgen_site_url)
            )

        return output_data

    def fetch_files_data(self, issue: Edition) -> list[ResultFile]:
        try:
            result_files = list(issue.get("files").values())
        except KeyError:
            return []

        output_data = []

        for result_file in result_files:
            file = ResultFile(
                id=result_file["f_id"],
                issue=issue,
                libgen_site_url=self.libgen_site_url,
            )

            if not file.broken:
                output_data.append(file)

        return output_data
