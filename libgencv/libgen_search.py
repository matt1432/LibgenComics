from pycomicvine import Volume

from .edition import Edition
from .lib import filter_results
from .search_request import SearchRequest


# TODO: add search from comicvine ID and supplied libgen.gs series url
class LibgenSearch:
    def search_comicvine_id(self, id: int, issue_number: int) -> list[dict[str, str]]:
        cv_volume: Volume = Volume(id, all=True)  # type: ignore

        series_request = SearchRequest(
            str(cv_volume.name), str(cv_volume.site_detail_url)
        )
        editions = series_request.fetch_editions_data()

        filtered_editions: list[Edition] = []

        for edition in editions:
            if edition.number == issue_number:
                filtered_editions.append(edition)

        files = []
        for filtered_ed in filtered_editions:
            for file in series_request.fetch_files_data(filtered_ed):
                files.append(file)

        return files
