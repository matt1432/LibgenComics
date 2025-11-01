from dataclasses import dataclass
from datetime import datetime
from typing import Any

from libgencomics.common import CONSTANTS, parse_value

from .libgen_object import LibgenObject
from .series import Series


@dataclass
class Edition(LibgenObject):
    series: Series

    number: float | tuple[float, float] | None
    title: str | None
    author: str | None
    publisher: str | None
    year: int | None
    month: str | None
    day: int | None
    pages: int | None
    cover_url: str | None

    time_added: datetime | None
    time_last_modified: datetime | None

    def __parse_number(
        self, edition_results: Any
    ) -> float | tuple[float, float] | None:
        issue_str = parse_value(edition_results, "issue_total_number", str)

        if issue_str is not None:
            try:
                issue_str = issue_str.replace(",", ".")

                if issue_str.count("-") != 0:
                    covered_issues = issue_str.split("-")

                    if len(covered_issues) == 2:
                        return (
                            float(covered_issues[0]),
                            float(covered_issues[1]),
                        )
                else:
                    return float(issue_str)

            except Exception:
                return None

        return None

    def __init__(
        self,
        *,
        id: int,
        libgen_site_url: str,
        series: Series,
        response: str | None = None,
    ):
        super().__init__(
            id=id, url=libgen_site_url + CONSTANTS.EDITION_REQUEST, response=response
        )

        edition_results = list(self.json_obj.values())[0]

        self.series = series

        self.number = self.__parse_number(edition_results)

        self.title = parse_value(edition_results, "title", str)
        self.author = parse_value(edition_results, "author", str)
        self.publisher = parse_value(edition_results, "publisher", str)
        self.cover_url = parse_value(edition_results, "cover_url", str)

        self.year = parse_value(edition_results, "year", int)
        self.month = parse_value(edition_results, "month", str)
        self.day = parse_value(edition_results, "day", int)

        self.pages = parse_value(edition_results, "pages", int)

        self.time_added = parse_value(
            edition_results,
            "time_added",
            datetime.fromisoformat,
        )

        self.time_last_modified = parse_value(
            edition_results,
            "time_last_modified",
            datetime.fromisoformat,
        )

    def __json__(self) -> dict[str, str | int | None]:
        return super().__to_json__(
            [
                "author",
                "cover_url",
                "day",
                "id",
                "month",
                "number",
                "pages",
                "publisher",
                "time_added",
                "time_last_modified",
                "title",
                "year",
            ]
        )
