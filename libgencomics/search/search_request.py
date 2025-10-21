from enum import StrEnum

from bs4 import BeautifulSoup
from requests import Response

from libgencomics.common import (
    CONSTANTS,
    attempt_request,
    fetch_multiple_urls,
    opt_chain,
)
from libgencomics.errors import LibgenSeriesNotFoundException
from libgencomics.libgen_objects import Edition, ResultFile, Series


class Category(StrEnum):
    FILES = "f"
    EDITIONS = "e"
    SERIES = "s"
    AUTHORS = "a"
    PUBLISHERS = "p"
    WORKS = "w"


def build_search_url(
    *,
    base: str,
    query: str,
    category: Category,
    paging: int = 25,
    page: int | None = None,
    show_chapters=False,
    google_mode=False,
) -> str:
    query_parsed = "%20".join(query.split(" "))

    search_url = (
        f"{base}/index.php?req={query_parsed}"
        "&topics[]=c"  # Only search in Comics
        f"&curtab={category}&objects[]={category}"  # Only search in category wanted
        f"&res={paging}"
        "&filesuns=all"  # search in both sorted and unsorted files
        "&columns[]=t"  # Search in Title field
        "&columns[]=a"  # Search in Author field
        "&columns[]=s"  # Search in Series field
        "&columns[]=y"  # Search in Year field
        "&columns[]=p"  # Search in Publisher field
        "&columns[]=i"  # Search in ISBN field
    )

    if page is not None:
        search_url = search_url + f"&page={page}"

    if show_chapters:
        search_url = search_url + "&showch=on"

    if google_mode:
        search_url = search_url + "&gmode=on"

    return search_url


class SearchRequest:
    def __init__(
        self,
        *,
        query: str,
        comicvine_url: str,
        libgen_site_url: str,
        libgen_series_id: int | list[int] | None = None,
    ) -> None:
        self.query = query
        self.comicvine_url = comicvine_url
        self.libgen_site_url = libgen_site_url
        self.libgen_series_id = libgen_series_id

    def get_search_page(self, page: int | None = None) -> Response:
        search_url = build_search_url(
            base=self.libgen_site_url,
            query=self.query,
            category=Category.SERIES,
            page=page,
        )

        return attempt_request(search_url)

    def get_search_soup(self, page: int | None = None) -> BeautifulSoup:
        return BeautifulSoup(self.get_search_page(page).text, "html.parser")

    async def aggregate_series_data(self, soup: BeautifulSoup) -> Series | None:
        if opt_chain(soup.find_all("center"), 1, "string") == "nginx":
            raise Exception(opt_chain(soup.find_all("center"), 0, "string"))

        # Table of data to scrape.
        information_table = opt_chain(soup.find(id="tablelibgen"), "tbody")

        if information_table is None:
            return None

        series_ids: list[int] = []

        for row in information_table.find_all("tr"):
            series_temp_url = opt_chain(
                row,
                "td",
                "a",
                "attrs",
                "href",
            )

            if series_temp_url is not None:
                series_ids.append(
                    int(series_temp_url.replace("series.php?id=", "").strip())
                )

        series_requests = await fetch_multiple_urls(
            [
                self.libgen_site_url + CONSTANTS.SERIES_REQUEST + str(series_id)
                for series_id in series_ids
            ]
        )

        for index, response in enumerate(series_requests):
            # print(f"Series: #{index} {series_ids[index]}")
            series = Series(
                id=series_ids[index],
                libgen_site_url=self.libgen_site_url,
                comicvine_url=None,
                response=response,
            )

            if series.comicvine_url == self.comicvine_url:
                return series

        return None

    async def get_series(self) -> list[Series] | None:
        if self.libgen_series_id is not None:
            if isinstance(self.libgen_series_id, int):
                return [
                    Series(
                        id=self.libgen_series_id,
                        comicvine_url=self.comicvine_url,
                        libgen_site_url=self.libgen_site_url,
                    )
                ]
            else:
                return [
                    Series(
                        id=id,
                        comicvine_url=self.comicvine_url,
                        libgen_site_url=self.libgen_site_url,
                    )
                    for id in self.libgen_series_id
                ]

        # Search first page before checking following ones
        soup = self.get_search_soup()
        series = await self.aggregate_series_data(soup)

        # Don't have to check following pages if we found a match
        if series is not None:
            return [series]

        if soup.find(id="paginator_example_top") is not None:
            page = 2
            soup = self.get_search_soup(page)

            while soup.find("tbody") is not None:
                series = await self.aggregate_series_data(soup)

                if series is not None:
                    return [series]

                page += 1
                soup = self.get_search_soup(page)

        raise LibgenSeriesNotFoundException(
            f"No matching series were found for {self.query}."
        )

    async def fetch_editions_data(self) -> list[Edition]:
        series = await self.get_series()

        if series is None:
            return []

        output_data: list[Edition] = []
        edition_ids: list[tuple[int, Series]] = []

        for s in series:
            for key in list(s.get("editions").keys()):
                edition_ids.append((int(key), s))

        edition_requests = await fetch_multiple_urls(
            [
                self.libgen_site_url + CONSTANTS.EDITION_REQUEST + str(ed_id)
                for ed_id, _ in edition_ids
            ]
        )

        for index, response in enumerate(edition_requests):
            # print(f"Edition: #{index} {edition_ids[index]}")
            output_data.append(
                Edition(
                    id=edition_ids[index][0],
                    series=edition_ids[index][1],
                    libgen_site_url=self.libgen_site_url,
                    response=response,
                )
            )

        return output_data

    async def fetch_files_data(self, issues: list[Edition]) -> list[ResultFile]:
        result_files_ids: list[tuple[int, Edition]] = []

        for issue in issues:
            try:
                files = list(issue.get("files").values())
            except KeyError:
                files = []

            for result_file in files:
                result_files_ids.append((int(result_file["f_id"]), issue))

        output_data: list[ResultFile] = []

        file_requests = await fetch_multiple_urls(
            [
                self.libgen_site_url + CONSTANTS.RESULT_FILE_REQUEST + str(file_id)
                for file_id, _ in result_files_ids
            ]
        )

        for index, response in enumerate(file_requests):
            # print(f"ResultFile: #{index} {result_files_ids[index][0]}")
            file = ResultFile(
                id=result_files_ids[index][0],
                issue=result_files_ids[index][1],
                libgen_site_url=self.libgen_site_url,
                response=response,
            )

            if not file.broken:
                output_data.append(file)

        return output_data
