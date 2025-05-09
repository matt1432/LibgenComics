import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .lib import attempt_request, parse_value


@dataclass
class ResultFile:
    id: int
    libgen_api_url: str
    json_obj: Any
    comicvine_series_url: str

    broken: bool = False

    download_link: str | None = None
    filename: str | None = None
    filesize: int | None = None
    pages: int | None = None
    extension: str | None = None
    releaser: str | None = None
    scan_type: str | None = None
    resolution: str | None = None
    dpi: str | None = None

    time_created: datetime | None = None
    time_added: datetime | None = None
    time_last_modified: datetime | None = None

    def __init__(self, id: str, comicvine_url: str):
        self.comicvine_series_url = comicvine_url

        self.id = int(id)
        self.libgen_api_url = f"https://libgen.gs/json.php?object=f&ids={self.id}"
        self.json_obj = json.loads(attempt_request(self.libgen_api_url).text)

        file_results = list(self.json_obj.values())[0]

        if "broken" not in file_results or file_results["broken"] != "N":
            self.broken = True
        else:
            md5 = parse_value(file_results, "md5", str)

            if md5 is not None:
                self.download_link = f"https://libgen.gl/get.php?md5={md5}"

                locator = parse_value(file_results, "locator", str)

                self.filename = None if locator is None else locator.split("\\")[-1]

                self.extension = parse_value(file_results, "extension", str)
                self.releaser = parse_value(file_results, "releaser", str)
                self.scan_type = parse_value(file_results, "scan_type", str)
                self.resolution = parse_value(file_results, "scan_size", str)
                self.dpi = parse_value(file_results, "dpi", str)

                self.filesize = parse_value(file_results, "filesize", int)
                self.pages = parse_value(file_results, "archive_files_pic_count", int)

                self.time_created = parse_value(
                    file_results, "file_create_date", datetime.fromisoformat
                )
                self.time_added = parse_value(
                    file_results, "time_added", datetime.fromisoformat
                )
                self.time_last_modified = parse_value(
                    file_results, "time_last_modified", datetime.fromisoformat
                )

    def get(self, key: str) -> Any:
        return list(self.json_obj.values())[0][key]

    def __str__(self) -> str:
        if self.broken:
            return "{ broken: true }"
        else:
            return f"""{{
    id: "{self.id}",
    comicvine_series_url: "{self.comicvine_series_url}",

    download_link: "{self.download_link or ""}",
    filename: "{self.filename or ""}",
    filesize: "{self.filesize or ""}",
    pages: "{self.pages or ""}",
    extension: "{self.extension or ""}",
    releaser: "{self.releaser or ""}",
    scan_type: "{self.scan_type or ""}",
    resolution: "{self.resolution or ""}",
    dpi: "{self.dpi or ""}",

    time_created: "{self.time_created or ""}",
    time_added: "{self.time_added or ""}",
    time_last_modified: "{self.time_last_modified or ""}",
}}"""
