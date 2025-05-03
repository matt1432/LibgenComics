import pycomicvine

from .search_request import SearchRequest


def filter_results(results, filters, exact_match):
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
    def search_comicvine_id(self, id, issue_number):
        cv_volume = pycomicvine.Volume(id, all=True)

        series_request = SearchRequest(cv_volume.name, cv_volume.site_detail_url)
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

    def search_comicvine_id_filtered(self, id, issue_number, filters, exact_match=True):
        return filter_results(
            results=self.search_comicvine_id_filtered(id, issue_number),
            filters=filters,
            exact_match=exact_match,
        )
