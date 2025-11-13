from simyan.comicvine import Comicvine
from simyan.schemas.volume import Volume

from libgencomics.libgen_objects import ResultFile

from .search_request import SearchRequest


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
    ) -> list[ResultFile]:
        session = Comicvine(api_key=api_key)

        cv_volume: Volume = session.get_volume(volume_id=id)

        series_request = SearchRequest(
            query=query or cv_volume.name,
            start_year=cv_volume.start_year,
            libgen_series_id=libgen_series_id,
            libgen_site_url=libgen_site_url,
            comicvine_url=str(cv_volume.site_url),
            issue_number=issue_number,
            search_unsorted=search_unsorted,
        )

        editions = await series_request.fetch_editions_data()

        filtered_editions = (
            editions
            if issue_number is None
            else [edition for edition in editions if edition.number == issue_number]
        )

        return await series_request.fetch_files_data(filtered_editions)
