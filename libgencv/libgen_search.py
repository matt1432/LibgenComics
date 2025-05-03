from pycomicvine import Volume

from .search_request import SearchRequest


def filter_results(
    results: list[dict[str, str]], filters: dict[str, str], exact_match: bool = True
) -> list[dict[str, str]]:
    """
    Returns a list of results that match the given filter criteria.
    When exact_match = true, we only include results that exactly match
    the filters (ie. the filters are an exact subset of the result).

    When exact-match = false,
    we run a case-insensitive check between each filter field and each result.

    exact_match defaults to TRUE -
    this is to maintain consistency with older versions of this library.
    """

    filtered_list = []
    if exact_match:
        for result in results:
            # check whether a candidate result matches the given filters
            if filters.items() <= result.items():
                filtered_list.append(result)

    else:
        filter_matches_result = False
        for result in results:
            for field, query in filters.items():
                if query.casefold() in result[field].casefold():
                    filter_matches_result = True
                else:
                    filter_matches_result = False
                    break
            if filter_matches_result:
                filtered_list.append(result)
    return filtered_list


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
