import re
from dataclasses import dataclass
from datetime import datetime

from libgencomics.common import CONSTANTS, parse_value

from .edition import Edition
from .libgen_object import LibgenObject


@dataclass
class ResultFile(LibgenObject):
    issue: Edition | None

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

    def __init__(
        self,
        *,
        id: int,
        libgen_site_url: str,
        issue: Edition | None = None,
        response: str | None = None,
    ):
        super().__init__(
            id=id,
            url=libgen_site_url + CONSTANTS.RESULT_FILE_REQUEST,
            response=response,
        )

        file_results = list(self.json_obj.values())[0]

        self.issue = issue

        if "broken" not in file_results or file_results["broken"] != "N":
            self.broken = True
        else:
            md5 = parse_value(file_results, "md5", str)

            if md5 is not None:
                self.download_link = f"{libgen_site_url}/get.php?md5={md5}"

                locator = parse_value(file_results, "locator", str)

                self.filename = None if locator is None else locator.split("\\")[-1]

                self.extension = parse_value(file_results, "extension", str)
                self.releaser = parse_value(file_results, "releaser", str)

                self.scan_type = parse_value(file_results, "scan_type", str)
                if (
                    not self.scan_type
                    and self.filename
                    and self.filename.lower().count("(digital)")
                ):
                    self.scan_type = "digital"

                    if not self.releaser:
                        match = re.search(r"\(([^()]+)\)\.cb.$", self.filename)
                        if match and match.group(1).lower() != "digital":
                            self.releaser = match.group(1)

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

    def __json__(self) -> dict[str, str | int | None]:
        return super().__to_json__(
            [
                "download_link",
                "dpi",
                "extension",
                "filename",
                "filesize",
                "id",
                "pages",
                "releaser",
                "resolution",
                "scan_type",
                "time_added",
                "time_created",
                "time_last_modified",
            ]
        )

    def __str__(self) -> str:
        if self.broken:
            return """{ "broken": true }"""
        else:
            return super().__str__()
