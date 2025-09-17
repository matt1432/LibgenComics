from simyan.comicvine import Comicvine
from simyan.schemas.volume import Volume

from libgencomics.libgen_objects import Edition, ResultFile

from .search_request import SearchRequest


class LibgenSearch:
    async def search_comicvine_id(
        self,
        *,
        api_key: str,
        id: int,
        libgen_site_url: str,
        libgen_series_id: int | None,
        issue_number: float | tuple[float, float] | None = None,
    ) -> list[ResultFile]:
        session = Comicvine(api_key=api_key)

        cv_volume: Volume = session.get_volume(volume_id=id)

        series_request = SearchRequest(
            query=cv_volume.name,
            libgen_series_id=libgen_series_id,
            libgen_site_url=libgen_site_url,
            comicvine_url=str(cv_volume.site_url),
        )

        editions = await series_request.fetch_editions_data()
        filtered_editions: list[Edition] = []

        for edition in editions:
            if issue_number is None or edition.number == issue_number:
                filtered_editions.append(edition)

        files: list[ResultFile] = []

        for filtered_ed in filtered_editions:
            for file in series_request.fetch_files_data(filtered_ed):
                files.append(file)

        return files
