import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .lib import attempt_request


@dataclass
class Series:
    id: int
    libgen_api_url: str
    json_obj: Any

    title: str
    publisher: str
    time_added: datetime
    time_last_modified: datetime

    year_start: int | None = None
    month_start: int | None = None
    day_start: int | None = None

    year_end: int | None = None
    month_end: int | None = None
    day_end: int | None = None

    comicvine_url: str = ""
    language: str = ""

    def __init__(self, id: str, comicvine_url: str | None = None):
        self.comicvine_url = "" if comicvine_url is None else comicvine_url

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

        self.title = series_results["title"]
        self.publisher = series_results["publisher"]
        self.time_added = datetime.fromisoformat(series_results["time_added"])
        self.time_last_modified = datetime.fromisoformat(
            series_results["time_last_modified"]
        )

    def get(self, key: str) -> Any:
        return list(self.json_obj.values())[0][key]

    def __str__(self) -> str:
        return f"""{{
    id: "{str(self.id)}",
    title: "{self.title}",
    language: "{self.language}",
    comicvine_url: "{self.comicvine_url}",
    publisher: "{self.publisher}",

    year_start: "{str(self.year_start or "")}",
    month_start: "{str(self.month_start or "")}",
    day_start: "{str(self.day_start or "")}",

    year_end: "{str(self.year_end or "")}",
    month_end: "{str(self.month_end or "")}",
    day_end: "{str(self.day_end or "")}",

    time_added: "{self.time_added}",
    time_last_modified: "{self.time_last_modified}",
}}"""
