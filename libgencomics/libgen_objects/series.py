from dataclasses import dataclass
from datetime import datetime

from libgencomics.common import CONSTANTS, parse_value

from .libgen_object import LibgenObject


@dataclass
class Series(LibgenObject):
    title: str | None = None
    publisher: str | None = None
    time_added: datetime | None = None
    time_last_modified: datetime | None = None

    year_start: int | None = None
    month_start: int | None = None
    day_start: int | None = None

    year_end: int | None = None
    month_end: int | None = None
    day_end: int | None = None

    comicvine_url: str | None = None
    language: str | None = None

    def __init__(
        self,
        *,
        id: int,
        libgen_site_url: str,
        comicvine_url: str | None,
        response: str | None = None,
    ):
        super().__init__(
            id=id,
            url=libgen_site_url + CONSTANTS.SERIES_REQUEST,
            response=response,
        )

        series_results = {
            "add": {},
            **list(self.json_obj.values())[0],
        }

        if comicvine_url is not None:
            self.comicvine_url = comicvine_url

        for added_key in series_results["add"].values():
            if added_key["key"] == "101":
                self.language = added_key["value"]

            elif added_key["value"].startswith("https://comicvine.gamespot.com"):
                self.comicvine_url = added_key["value"]

        if "date_start" in series_results and series_results["date_start"] is not None:
            date_start = series_results["date_start"].split("-")

            self.year_start = int(date_start[0])
            self.month_start = int(date_start[1])
            self.day_start = int(date_start[2])

        if "date_end" in series_results and series_results["date_end"] is not None:
            date_end = series_results["date_end"].split("-")

            self.year_end = int(date_end[0])
            self.month_end = int(date_end[1])
            self.day_end = int(date_end[2])

        self.title = parse_value(series_results, "title", str)
        self.publisher = parse_value(series_results, "publisher", str)

        self.time_added = parse_value(
            series_results, "time_added", datetime.fromisoformat
        )

        self.time_last_modified = parse_value(
            series_results, "time_last_modified", datetime.fromisoformat
        )

    def __json__(self) -> dict[str, str | int | None]:
        return super().__to_json__(
            [
                "comicvine_url",
                "day_end",
                "day_start",
                "id",
                "language",
                "month_end",
                "month_start",
                "publisher",
                "time_added",
                "time_last_modified",
                "title",
                "year_start",
                "year_end",
            ]
        )
