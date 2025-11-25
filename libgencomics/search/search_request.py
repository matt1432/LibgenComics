from enum import StrEnum

from bs4 import BeautifulSoup

from libgencomics.common import (
    CONSTANTS,
    attempt_request,
    fetch_multiple_urls,
    opt_chain,
)
from libgencomics.errors import LibgenNginxException
from libgencomics.libgen_objects import Edition, ResultFile, Series


class Category(StrEnum):
    FILES = "f"
    EDITIONS = "e"
    SERIES = "s"
    AUTHORS = "a"
    PUBLISHERS = "p"
    WORKS = "w"


class SearchSorted(StrEnum):
    ALL = "all"
    SORTED = "sort"
    UNSORTED = "unsort"


def build_search_url(
    *,
    base: str,
    query: str,
    category: Category,
    paging: int = 25,
    page: int | None = None,
    sort: SearchSorted = SearchSorted.ALL,
    show_chapters=False,
    google_mode=False,
) -> str:
    query_parsed = "%20".join(query.split(" "))

    search_url = (
        f"{base}/index.php?req={query_parsed}"
        "&topics[]=c"  # Only search in Comics
        f"&curtab={category}&objects[]={category}"  # Only search in category wanted
        f"&res={paging}"
        f"&filesuns={sort}"
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
        start_year: int | None,
        comicvine_url: str,
        libgen_site_url: str,
        libgen_series_id: int | list[int] | None = None,
        issue_number: float | tuple[float, float] | None = None,
        search_unsorted: bool = True,
        flaresolverr_url: str | None = None,
    ) -> None:
        self.query = query
        self.start_year = start_year
        self.comicvine_url = comicvine_url
        self.libgen_site_url = libgen_site_url
        self.libgen_series_id = libgen_series_id
        self.issue_number = issue_number
        self.search_unsorted = search_unsorted
        self.flaresolverr_url = flaresolverr_url

    def get_search_page(self, unsorted=False) -> str:
        if unsorted:
            final_query = (
                f"{self.query} {self.issue_number}"
                if self.issue_number is not None
                else self.query
            )

            search_url = build_search_url(
                base=self.libgen_site_url,
                query=final_query,
                category=Category.FILES,
                sort=SearchSorted.UNSORTED,
            )
        else:
            search_url = build_search_url(
                base=self.libgen_site_url,
                query=self.query,
                category=Category.SERIES,
            )

        return attempt_request(search_url)

    def get_search_soup(self, unsorted=False) -> BeautifulSoup:
        return BeautifulSoup(self.get_search_page(unsorted), "html.parser")

    async def aggregate_series_data(self, soup: BeautifulSoup) -> list[Series]:
        if opt_chain(soup.find_all("center"), 1, "string") == "nginx":
            raise LibgenNginxException(opt_chain(soup.find_all("center"), 0, "string"))

        json_link = soup.select_one("li.navbar-right a.nav-link")

        if json_link is None:
            return []

        raw_series_ids = json_link.attrs["href"]

        if not raw_series_ids:
            return []

        raw_series_ids = str(raw_series_ids)
        if raw_series_ids.count("/json.php?object=s&ids=") == 0:
            return []
        raw_series_ids = raw_series_ids.replace("/json.php?object=s&ids=", "")

        series_ids = raw_series_ids.split(",")

        series_requests = await fetch_multiple_urls(
            [
                self.libgen_site_url + CONSTANTS.SERIES_REQUEST + str(series_id)
                for series_id in series_ids
            ],
            self.flaresolverr_url,
        )

        matched_series: list[Series] = []

        for index, response in enumerate(series_requests):
            series = Series(
                id=int(series_ids[index]),
                libgen_site_url=self.libgen_site_url,
                comicvine_url=None,
                response=response,
            )

            if series.comicvine_url is not None:
                if series.comicvine_url == self.comicvine_url:
                    matched_series.append(series)

            elif series.year_start == self.start_year:
                matched_series.append(series)

        return matched_series

    async def get_series(self) -> list[Series]:
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

        soup = self.get_search_soup()
        return await self.aggregate_series_data(soup)

    async def get_unsorted_files_ids(self) -> list[str]:
        soup = self.get_search_soup(unsorted=True)

        if opt_chain(soup.find_all("center"), 1, "string") == "nginx":
            raise LibgenNginxException(opt_chain(soup.find_all("center"), 0, "string"))

        json_link = soup.select_one("li.navbar-right a.nav-link")

        if json_link is None:
            return []

        raw_files_ids = json_link.attrs["href"]

        if not raw_files_ids:
            return []

        raw_files_ids = str(raw_files_ids)
        if raw_files_ids.count("/json.php?object=f&ids=") == 0:
            return []
        raw_files_ids = raw_files_ids.replace("/json.php?object=f&ids=", "")

        return raw_files_ids.split(",")

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
            ],
            self.flaresolverr_url,
        )

        for index, response in enumerate(edition_requests):
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
        result_files_ids: list[tuple[str, Edition | None]] = []

        for issue in issues:
            try:
                files = list(issue.get("files").values())
            except KeyError:
                files = []

            for result_file in files:
                result_files_ids.append((result_file["f_id"], issue))

        if self.search_unsorted:
            result_files_ids += [
                (id, None) for id in (await self.get_unsorted_files_ids())
            ]

        output_data: list[ResultFile] = []

        file_requests = await fetch_multiple_urls(
            [
                self.libgen_site_url + CONSTANTS.RESULT_FILE_REQUEST + file_id
                for file_id, _ in result_files_ids
            ],
            self.flaresolverr_url,
        )

        for index, response in enumerate(file_requests):
            file = ResultFile(
                id=int(result_files_ids[index][0]),
                issue=result_files_ids[index][1],
                libgen_site_url=self.libgen_site_url,
                response=response,
            )

            if not file.broken:
                output_data.append(file)

        return output_data
