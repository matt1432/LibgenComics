import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .lib import attempt_request, parse_value


@dataclass
class Edition:
    id: int
    libgen_api_url: str
    json_obj: Any
    comicvine_series_url: str

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

    def __init__(self, id: str, comicvine_url: str):
        self.comicvine_series_url = comicvine_url

        self.id = int(id)
        self.libgen_api_url = f"https://libgen.gs/json.php?object=e&ids={self.id}"

        self.json_obj = json.loads(attempt_request(self.libgen_api_url).text)

        edition_results = list(self.json_obj.values())[0]

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

    def get(self, key: str) -> Any:
        return list(self.json_obj.values())[0][key]

    def __json__(self) -> dict[str, str | int]:
        return {
            "id": self.id,
            "comicvine_series_url": self.comicvine_series_url,
            "number": self.number or "",
            "title": self.title or "",
            "author": self.author or "",
            "publisher": self.publisher or "",
            "year": self.year or "",
            "month": self.month or "",
            "day": self.day or "",
            "pages": self.pages or "",
            "cover_url": self.cover_url or "",
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
