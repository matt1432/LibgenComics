import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .lib import attempt_request


@dataclass
class ResultFile:
    id: int
    libgen_api_url: str
    json_obj: Any
    comicvine_series_url: str

    download_link: str
    filename: str
    filesize: int
    pages: int
    extension: str
    releaser: str
    scan_type: str
    resolution: str
    dpi: str

    time_created: datetime
    time_added: datetime
    time_last_modified: datetime

    broken: bool = False

    def __init__(self, id: str, comicvine_url: str):
        self.comicvine_series_url = comicvine_url

        self.id = int(id)
        self.libgen_api_url = f"https://libgen.gs/json.php?object=f&ids={self.id}"
        self.json_obj = json.loads(attempt_request(self.libgen_api_url).text)

        file_results = list(self.json_obj.values())[0]

        if file_results["broken"] != "N":
            self.broken = True
        else:
            self.download_link = f"https://libgen.gl/get.php?md5={file_results['md5']}"
            self.filename = file_results["locator"].split("\\")[-1]
            self.extension = file_results["extension"]
            self.releaser = file_results["releaser"]
            self.scan_type = file_results["scan_type"]
            self.resolution = file_results["scan_size"]
            self.dpi = file_results["dpi"]

            self.filesize = int(file_results["filesize"])
            self.pages = int(file_results["archive_files_pic_count"])

            self.time_created = datetime.fromisoformat(file_results["file_create_date"])
            self.time_added = datetime.fromisoformat(file_results["time_added"])
            self.time_last_modified = datetime.fromisoformat(
                file_results["time_last_modified"]
            )

    def get(self, key: str) -> Any:
        return list(self.json_obj.values())[0][key]

    def __str__(self) -> str:
        if self.broken:
            return "{ broken: true }"
        else:
            return f"""{{
    id: "{str(self.id)}",
    comicvine_series_url: "{self.comicvine_series_url}",

    download_link: "{self.download_link}",
    filename: "{self.filename}",
    filesize: "{self.filesize}",
    pages: "{self.pages}",
    extension: "{self.extension}",
    releaser: "{self.releaser}",
    scan_type: "{self.scan_type}",
    resolution: "{self.resolution}",
    dpi: "{self.dpi}",

    time_created: "{self.time_created}",
    time_added: "{self.time_added}",
    time_last_modified: "{self.time_last_modified}",
}}"""
