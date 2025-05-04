from pycomicvine import Volume

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

        filtered_editions = []

        for edition in editions:
            if edition["Number"] == str(issue_number):
                if edition["Pages"] == "" or int(edition["Pages"]) > 2:
                    filtered_editions.append(edition)

        files = []
        for filtered_ed in filtered_editions:
            for file in series_request.fetch_files_data(filtered_ed):
                files.append(file)

        return files

    def search_comicvine_id_filtered(
        self,
        id: int,
        issue_number: int,
        filters: dict[str, str],
        exact_match: bool = True,
    ) -> list[dict[str, str]]:
        return filter_results(
            results=self.search_comicvine_id(id, issue_number),
            filters=filters,
            exact_match=exact_match,
        )
