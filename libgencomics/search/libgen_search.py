from aiohttp import ClientSession
from bs4 import BeautifulSoup
from simyan.comicvine import Comicvine, SQLiteCache
from simyan.schemas.volume import Volume

from libgencomics.common import flaresolverr_get
from libgencomics.libgen_objects import ResultFile

from .search_request import SearchRequest


async def get_annas_archive_download(
    rf: ResultFile,
    flaresolverr_url: str,
    annas_archive_site_url: str,
    n_dl_partner: int = 4,
) -> str | None:
    if rf.md5 is None:
        return None

    async with ClientSession() as session:
        url = f"{annas_archive_site_url}/slow_download/{rf.md5}/0/{n_dl_partner}"
        anna_response = await flaresolverr_get(session, url, flaresolverr_url)

    anna_soup = BeautifulSoup(anna_response, "html.parser")
    for a_elem in anna_soup.select("p.mb-4 > a"):
        if a_elem.text.count("Download with short filename") != 0:
            return str(a_elem.attrs["href"])

    return None


class LibgenSearch:
    async def search_comicvine_id(
        self,
        *,
        api_key: str,
        id: int,
        libgen_site_url: str,
        libgen_series_id: int | list[int] | None,
        issue_number: float | tuple[float, float] | None = None,
        search_unsorted: bool = True,
        query: str | None = None,
        cv_cache: SQLiteCache | None = None,
        flaresolverr_url: str | None = None,
    ) -> list[ResultFile]:
        session = Comicvine(api_key=api_key, cache=cv_cache)

        cv_volume: Volume = session.get_volume(volume_id=id)

        series_request = SearchRequest(
            query=query or cv_volume.name,
            start_year=cv_volume.start_year,
            libgen_series_id=libgen_series_id,
            libgen_site_url=libgen_site_url,
            comicvine_url=str(cv_volume.site_url),
            issue_number=issue_number,
            search_unsorted=search_unsorted,
            flaresolverr_url=flaresolverr_url,
        )

        editions = await series_request.fetch_editions_data()

        filtered_editions = (
            editions
            if issue_number is None
            else [edition for edition in editions if edition.number == issue_number]
        )

        return await series_request.fetch_files_data(filtered_editions)
