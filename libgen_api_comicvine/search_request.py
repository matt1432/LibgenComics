import json
import re
import urllib.parse
from inspect import isfunction

import requests
from bs4 import BeautifulSoup

# WHY
# The SearchRequest module contains all the internal logic for the library.
#
# This encapsulates the logic,
# ensuring users can work at a higher level of abstraction.

# USAGE
# req = search_request.SearchRequest("[QUERY]", search_type="[title]")


# attempts to chain attributes, indexes or functions of the root object
def opt_chain(root, *keys):
    result = root
    for k in keys:
        if isinstance(result, dict):
            result = result.get(k, None)
        elif isinstance(result, list):
            if k < len(result):
                result = result[k]
            else:
                result = None
        elif isfunction(k):
            result = k(result)
        else:
            result = getattr(result, k, None)
        if result is None:
            break
    return result


def opt_chain_str(root, *keys):
    return opt_chain(root, *keys) or ""


class SearchRequest:
    def __init__(self, query, search_type="title"):
        self.query = query
        self.search_type = search_type

        if len(self.query) < 3:
            raise Exception("Query is too short")

    def get_search_page(self):
        query_parsed = "%20".join(self.query.split(" "))
        if self.search_type.lower() == "title":
            search_url = f"https://libgen.gs/index.php?req={query_parsed}&column=title&res=100&filesuns=sort"
        elif self.search_type.lower() == "author":
            search_url = f"https://libgen.gs/index.php?req={query_parsed}&column=author&res=100&filesuns=sort"
        elif self.search_type.lower() == "default":
            search_url = f"https://libgen.gs/index.php?req={query_parsed}&column=default&res=100&filesuns=sort"
        return requests.get(search_url)

    def add_direct_download_links(self, output_data):
        # Add a direct download link to each result
        for book in output_data:
            id = book["ID"]
            download_id = str(id)[:-3] + "000"
            md5 = book["Mirrors"]["libgen"].split("/")[-1].lower()
            title = urllib.parse.quote(book["Title"])
            extension = book["Extension"]
            book["Direct_Download_Link"] = (
                f"https://download.books.ms/main/{download_id}/{md5}/{title}.{extension}"
            )
        return output_data

    def add_book_cover_links(self, output_data):
        ids = ",".join([book["ID"] for book in output_data])

        url = f"https://libgen.is/json.php?ids={ids}&fields=id,md5,openlibraryid"

        response = json.loads(requests.get(url).text)

        # match openlibraryid to id
        for book in output_data:
            for book_json in response:
                if book["ID"] == book_json["id"]:
                    book["Cover"] = (
                        f"https://covers.openlibrary.org/b/olid/{book_json['openlibraryid']}-M.jpg"
                    )
        return output_data

    def add_comicvine_url(self, output_data):
        for book in output_data:
            if book["Series"]["ID"] != "":
                series_url = f"https://libgen.gs/json.php?object=s&ids={book['Series']['ID']}&fields=*&addkeys=309"
                series = list(json.loads(requests.get(series_url).text).values())[0]

                if "add" in series:
                    for added_key in series["add"].values():
                        if added_key["value"].startswith(
                            "https://comicvine.gamespot.com"
                        ):
                            book["Comicvine"] = added_key["value"]
        return output_data

    def aggregate_request_data(self):
        soup = BeautifulSoup(self.get_search_page().text, "html.parser")

        if opt_chain_str(soup.find_all("center"), 1, "string") == "nginx":
            raise Exception(opt_chain_str(soup.find_all("center"), 0, "string"))

        # Table of data to scrape.
        information_table = soup.find(id="tablelibgen").tbody

        output_data = []

        for row in information_table.find_all("tr"):
            unsorted = False

            _first_cell_data = opt_chain(
                row, "td", "b", lambda x: x.find_all("a"), 1, "attrs", "title"
            )

            if _first_cell_data is None:
                unsorted = True

            first_cell_data = (
                _first_cell_data
                or opt_chain_str(
                    row, "td", "b", lambda x: x.find_all("a"), 0, "attrs", "title"
                )
            ).split("; ")

            add_edit = (
                opt_chain_str(first_cell_data, 0).replace("Add/Edit : ", "").split("/")
            )

            extension = opt_chain_str(
                row, lambda x: x.find_all("td"), 7, "string"
            ).strip()

            mirrors = {}
            mirror_elements = (
                opt_chain(row, lambda x: x.find_all("td"), 8, lambda x: x.find_all("a"))
                or []
            )

            for mirror in mirror_elements:
                mirrors[mirror.attrs["title"]] = mirror.attrs["href"]

            output_data.append(
                {
                    "ID": opt_chain_str(
                        first_cell_data, 1, lambda x: x.split("<br>"), 0
                    )
                    .replace("ID: ", "")
                    .strip(),
                    "Filename": str(
                        f"{
                            opt_chain_str(
                                first_cell_data, 1, lambda x: x.split('<br>'), 1
                            )
                        }.{extension}"
                    ).strip(),
                    "Add": opt_chain_str(add_edit, 0).strip(),
                    "Edit": opt_chain_str(add_edit, 1).strip(),
                    "Title": opt_chain_str(
                        row, "td", lambda x: x.find_all("a"), 1, "i", "string"
                    ).strip()
                    if not unsorted
                    else opt_chain_str(
                        row,
                        "td",
                        lambda x: x.find_all("a"),
                        1,
                        lambda x: x.get_text(strip=True),
                    ),
                    "Resolution": opt_chain_str(
                        row, "td", "font", "b", "string", lambda x: x.split(" "), 0
                    ).strip(),
                    "DPI": opt_chain_str(
                        row, "td", "font", "b", "string", lambda x: x.split(" "), 1
                    ).strip(),
                    "Series": {
                        "ID": opt_chain_str(row, "td", "a", "attrs", "href")
                        .replace("series.php?id=", "")
                        .strip()
                        if not unsorted
                        else "",
                        "Name": opt_chain(row, "td", "a", "string").strip()
                        if not unsorted
                        else opt_chain_str(
                            row,
                            "td",
                            "b",
                            lambda x: x.get_text(strip=True),
                        ),
                    },
                    "Author(s)": opt_chain_str(
                        row, lambda x: x.find_all("td"), 1, "string"
                    ).strip(),
                    "Publisher": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        2,
                        lambda x: ";".join(
                            map(lambda x: opt_chain_str(x, "string"), x.find_all("a"))
                        ),
                        "string",
                    ).strip(),
                    "Year": opt_chain_str(
                        row, lambda x: x.find_all("td"), 3, "nobr", "string"
                    ).strip(),
                    "Language": opt_chain_str(
                        row, lambda x: x.find_all("td"), 4, "string"
                    ).strip(),
                    "Pages": opt_chain_str(
                        row, lambda x: x.find_all("td"), 5, "string"
                    ).strip(),
                    "Size": opt_chain_str(
                        row, lambda x: x.find_all("td"), 6, "nobr", "a", "string"
                    ).strip(),
                    "Extension": extension,
                    "Mirrors": mirrors,
                    "Comicvine": "",
                }
            )
        output_data = self.add_direct_download_links(output_data)
        output_data = self.add_book_cover_links(output_data)
        output_data = self.add_comicvine_url(output_data)
        return output_data


class SearchSeriesRequest:
    def __init__(self, query, comicvine_url):
        self.query = query
        self.comicvine_url = comicvine_url

        if len(self.query) < 3:
            raise Exception("Query is too short")

    def get_search_page(self, page=None):
        query_parsed = "%20".join(self.query.split(" "))
        if page is None:
            search_url = (
                f"https://libgen.gs/index.php?req={query_parsed}&curtab=s&res=100"
            )
        else:
            search_url = f"https://libgen.gs/index.php?req={query_parsed}&curtab=s&res=100&page={page}"
        print(search_url)
        return requests.get(search_url)

    def add_comicvine_url(self, output_data):
        for series in output_data:
            if series["ID"] != "":
                series_url = f"https://libgen.gs/json.php?object=s&ids={series['ID']}&fields=*&addkeys=309"
                series_results = list(
                    json.loads(requests.get(series_url).text).values()
                )[0]

                if "add" in series_results:
                    for added_key in series_results["add"].values():
                        if added_key["value"].startswith(
                            "https://comicvine.gamespot.com"
                        ):
                            series["Comicvine"] = added_key["value"]
        return output_data

    def aggregate_series_data(self, soup):
        if opt_chain_str(soup.find_all("center"), 1, "string") == "nginx":
            raise Exception(opt_chain_str(soup.find_all("center"), 0, "string"))

        # Table of data to scrape.
        information_table = soup.find(id="tablelibgen").tbody

        output_data = []

        for row in information_table.find_all("tr"):
            first_cell_data = opt_chain(
                row, lambda x: x.find_all("td"), 0, lambda x: x.find_all("a"), 0
            )

            add_edit = (
                opt_chain_str(
                    first_cell_data, "attrs", "title", lambda x: x.split("<br>"), 0
                )
                .replace("Time added/Time modified : ", "")
                .split("/")
            )

            published_period = (
                opt_chain_str(row, lambda x: x.find_all("td"), 1, "nobr", "string")
                .strip()
                .split("―")
            )

            output_data.append(
                {
                    "Title": opt_chain_str(first_cell_data, "string").strip(),
                    "ID": opt_chain_str(first_cell_data, "attrs", "href")
                    .replace("series.php?id=", "")
                    .strip(),
                    "Add": opt_chain_str(add_edit, 0).strip(),
                    "Edit": opt_chain_str(add_edit, 1).strip(),
                    "Started": opt_chain_str(published_period, 0),
                    "Ended": opt_chain_str(published_period, 1),
                    "Publisher": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        2,
                        lambda x: ";".join(
                            map(lambda x: opt_chain_str(x, "string"), x.find_all("a"))
                        ),
                        "string",
                    ).strip(),
                    "Language": opt_chain_str(
                        row, lambda x: x.find_all("td"), 3, "string"
                    ).strip(),
                    "Comicvine": "",
                }
            )
        output_data = self.add_comicvine_url(output_data)
        return output_data

    def get_series(self):
        soup = BeautifulSoup(self.get_search_page().text, "html.parser")

        if opt_chain_str(soup.find_all("center"), 1, "string") == "nginx":
            raise Exception(opt_chain_str(soup.find_all("center"), 0, "string"))

        if soup.find(id="paginator_example_top") is not None:
            page = 1

            while soup.tbody is not None:
                for series in self.aggregate_series_data(soup):
                    if series["Comicvine"] == self.comicvine_url:
                        return series

                page += 1
                soup = BeautifulSoup(self.get_search_page(page).text, "html.parser")
        else:
            for series in self.aggregate_series_data(soup):
                if series["Comicvine"] == self.comicvine_url:
                    return series

        return None

    def get_issues_page(self, id):
        search_url = f"https://libgen.gs/series.php?id={id}&covers=0&sort=date&sortmode=asc&viewmode=list"
        print(search_url)
        return requests.get(search_url)

    def aggregate_issues_data(self):
        series = self.get_series()

        if series is None:
            return []

        soup = BeautifulSoup(self.get_issues_page(series["ID"]).text, "html.parser")

        if opt_chain_str(soup.find_all("center"), 1, "string") == "nginx":
            raise Exception(opt_chain_str(soup.find_all("center"), 0, "string"))

        # Table of data to scrape.
        information_table = soup.find(id="tablelibgen").tbody

        output_data = []

        for row in information_table.find_all("tr"):
            output_data.append(
                {
                    "ID": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        1,
                        "a",
                        "attrs",
                        "href",
                    )
                    .replace("edition.php?id=", "")
                    .strip(),
                    "Year": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        1,
                        "a",
                        "string",
                    ).strip(),
                    "YearNumber": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        2,
                        "a",
                        "string",
                    ).strip(),
                    "Number": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        3,
                        "a",
                        "string",
                    ).strip(),
                    "Volume": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        4,
                        "a",
                        "string",
                    ).strip(),
                    "Issue": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        5,
                        "a",
                        "string",
                    ).strip(),
                    "Title": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        6,
                        "a",
                        "string",
                    ).strip(),
                    "Author(s)": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        7,
                        lambda x: x.get_text(),
                    )
                    .replace("[...]", "")
                    .strip(),
                    "Publisher": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        8,
                        lambda x: ";".join(
                            map(lambda x: opt_chain_str(x, "string"), x.find_all("a"))
                        ),
                        "string",
                    ).strip(),
                    "Pages": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        9,
                        "string",
                    ).strip(),
                    "ISBN": opt_chain_str(
                        row,
                        lambda x: x.find_all("td"),
                        10,
                        "string",
                    ).strip(),
                    "Comicvine": series["Comicvine"],
                }
            )
        return output_data

    def get_files_page(self, id):
        search_url = f"https://libgen.gs/edition.php?id={id}"
        return requests.get(search_url)

    def aggregate_files_data(self, issue):
        soup = BeautifulSoup(self.get_files_page(issue["ID"]).text, "html.parser")

        if opt_chain_str(soup.find_all("center"), 1, "string") == "nginx":
            raise Exception(opt_chain_str(soup.find_all("center"), 0, "string"))

        # Table of data to scrape.
        information_table = soup.find(id="tablelibgen")

        output_data = []

        for row in information_table.find_all("tr"):
            cell_data = opt_chain_str(row, lambda x: x.find_all("td"), 1)

            filename = opt_chain_str(cell_data, "font", "string")

            links = {}
            to_filter = []
            for a_elem in opt_chain(cell_data, lambda x: x.find_all("a")) or []:
                to_filter.append(opt_chain_str(a_elem.get_text()))

                source = opt_chain(a_elem, "attrs", "title")

                if source is not None:
                    links[source] = (
                        opt_chain_str(a_elem, "attrs", "href")
                        if source != "torrent"
                        else "https://libgen.gs"
                        + opt_chain_str(a_elem, "attrs", "href")
                    )

            text_data = opt_chain_str(cell_data, lambda x: x.get_text()).replace(
                "".join([" ".join(to_filter), "\n", filename]), ""
            )

            regex = r"([A-Za-z ]+?): ([^:]+?)(?=\s[A-Za-z ]+?:|$)"

            output_data.append(
                {
                    "Filename": filename,
                    "Pages": "",
                    **{
                        match[0].strip(): match[1].strip()
                        for match in re.findall(regex, text_data)
                    },
                    "Links": links,
                    "Comicvine": issue["Comicvine"],
                }
            )
        return output_data
