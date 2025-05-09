import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from libgencomics.common import attempt_request, parse_value


@dataclass
class Series:
    id: int
    libgen_api_url: str
    json_obj: Any

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

    def __init__(self, id: str, comicvine_url: str | None = None):
        if comicvine_url is not None:
            self.comicvine_url = comicvine_url

        self.id = int(id)
        self.libgen_api_url = f"https://libgen.gs/json.php?object=s&ids={self.id}&fields=*&addkeys=309,101"

        self.json_obj = json.loads(attempt_request(self.libgen_api_url).text)

        series_results = {
            "add": {},
            **list(self.json_obj.values())[0],
        }

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

    def get(self, key: str) -> Any:
        return list(self.json_obj.values())[0][key]

    def __json__(self) -> dict[str, str | int]:
        return {
            "id": self.id,
            "title": self.title or "",
            "comicvine_url": self.comicvine_url or "",
            "publisher": self.publisher or "",
            "language": self.language or "",
            "year_start": self.year_start or "",
            "month_start": self.month_start or "",
            "day_start": self.day_start or "",
            "year_end": self.year_end or "",
            "month_end": self.month_end or "",
            "day_end": self.day_end or "",
            "time_added": str(self.time_added or ""),
            "time_last_modified": str(self.time_last_modified or ""),
        }

    def __str__(self) -> str:
        return json.dumps(
            self,
            sort_keys=True,
            indent=4,
            default=lambda o: o.__json__() if hasattr(o, "__json__") else None,
        )
