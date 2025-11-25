import json
from dataclasses import dataclass
from typing import Any

from libgencomics.common import attempt_request, check_response_error


@dataclass
class LibgenObject:
    id: int
    libgen_item_url: str
    json_obj: Any

    def __init__(
        self,
        *,
        id: int,
        url: str,
        response: str | None = None,
    ):
        self.id = id
        self.libgen_item_url = f"{url}{self.id}"

        # Checking the passed response is the responsibility of the caller
        _response = response or check_response_error(
            attempt_request(self.libgen_item_url)
        )

        try:
            self.json_obj = json.loads(_response)
        except Exception as e:
            print(_response)
            raise e

    def get(self, key: str) -> Any:
        return list(self.json_obj.values())[0][key]

    def __to_json__(self, attributes: list[str]) -> dict[str, str | int | None]:
        return {
            attr: val
            if isinstance(val := getattr(self, attr, None), int) or val is None
            else str(val)
            for attr in attributes
        }

    def __json__(self) -> dict[str, str | int | None]:
        raise NotImplementedError()

    def __str__(self) -> str:
        return json.dumps(
            self.__json__(),
            indent=4,
            sort_keys=True,
        )
