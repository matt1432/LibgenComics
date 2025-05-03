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
        volume = pycomicvine.Volume(id, all=True)
        issue = volume.issues[issue_number - 1]

        series_request = SearchRequest(volume.name, volume.site_detail_url)
        issue_pages = series_request.aggregate_issues_data()

        filtered_issues = []

        for issue in issue_pages:
            if issue["Number"] == str(issue_number):
                if issue["Pages"] == "" or int(issue["Pages"]) > 2:
                    filtered_issues.append(issue)

        files = []
        for filtered_issue in filtered_issues:
            for file in series_request.aggregate_files_data(filtered_issue):
                files.append(file)

        return files

    def search_comicvine_id_filtered(self, id, issue_number, filters, exact_match=True):
        return filter_results(
            results=self.search_comicvine_id_filtered(id, issue_number),
            filters=filters,
            exact_match=exact_match,
        )
