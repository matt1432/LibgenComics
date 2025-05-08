import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .lib import attempt_request


@dataclass
class Edition:
    id: int
    libgen_api_url: str
    json_obj: Any
    comicvine_series_url: str

    number: str
    title: str
    author: str
    publisher: str
    year: int | None
    month: str | None
    day: int | None
    pages: int | None
    cover_url: str

    time_added: datetime
    time_last_modified: datetime

    def __init__(self, id: str, comicvine_url: str):
        self.comicvine_series_url = comicvine_url

        self.id = int(id)
        self.libgen_api_url = f"https://libgen.gs/json.php?object=e&ids={self.id}"

        self.json_obj = json.loads(attempt_request(self.libgen_api_url).text)

        edition_results = list(self.json_obj.values())[0]

        self.number = edition_results["issue_total_number"]
        self.title = edition_results["title"]
        self.author = edition_results["author"]
        self.publisher = edition_results["publisher"]
        self.cover_url = edition_results["cover_url"]

        self.year = (
            None
            if edition_results["year"] is None or edition_results["year"] == ""
            else int(edition_results["year"])
        )

        self.month = (
            None
            if edition_results["month"] is None or edition_results["month"] == ""
            else edition_results["month"]
        )

        self.day = (
            None
            if edition_results["day"] is None or edition_results["day"] == ""
            else int(edition_results["day"])
        )

        self.pages = (
            None
            if edition_results["pages"] is None or edition_results["pages"] == ""
            else int(edition_results["pages"])
        )

        self.time_added = datetime.fromisoformat(edition_results["time_added"])
        self.time_last_modified = datetime.fromisoformat(
            edition_results["time_last_modified"]
        )

    def get(self, key: str) -> Any:
        return list(self.json_obj.values())[0][key]

    def __str__(self) -> str:
        return f"""{{
    id: "{str(self.id)}",
    comicvine_series_url: "{self.comicvine_series_url}",

    number: "{self.number}",
    title: "{self.title}",
    author: "{self.author}",
    publisher: "{self.publisher}",
    year: "{str(self.year or "")}",
    month: "{str(self.month or "")}",
    day: "{str(self.day or "")}",
    pages: "{str(self.pages or "")}",
    cover_url: "{self.cover_url}",

    time_added: "{self.time_added}",
    time_last_modified: "{self.time_last_modified}",
}}"""
