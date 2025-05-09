from dataclasses import dataclass
from datetime import datetime

from libgencomics.common import parse_value

from .libgen_object import LibgenObject
from .series import Series


@dataclass
class Edition(LibgenObject):
    series: Series

    number: str | None
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

    def __init__(self, id: str, series: Series):
        super().__init__(id, "https://libgen.gs/json.php?object=e&ids=")
        edition_results = list(self.json_obj.values())[0]

        self.series = series

        self.number = parse_value(edition_results, "issue_total_number", str)
        self.title = parse_value(edition_results, "title", str)
        self.author = parse_value(edition_results, "author", str)
        self.publisher = parse_value(edition_results, "publisher", str)
        self.cover_url = parse_value(edition_results, "cover_url", str)

        self.year = parse_value(edition_results, "year", int)
        self.month = parse_value(edition_results, "month", str)
        self.day = parse_value(edition_results, "day", int)

        self.pages = parse_value(edition_results, "pages", int)

        self.time_added = parse_value(
            edition_results, "time_added", datetime.fromisoformat
        )
        self.time_last_modified = parse_value(
            edition_results, "time_last_modified", datetime.fromisoformat
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
