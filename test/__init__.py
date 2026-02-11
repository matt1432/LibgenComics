import asyncio

from libgencomics import LibgenSearch, get_annas_archive_download

with open(".api") as file:
    api_key = file.read().replace("\n", "")


def run_test(
    *,
    cv_id: int,
    libgen_series_id: int | None,
    issue_number: float | tuple[float, float] | None,
    search_unsorted: bool = True,
    flaresolverr_url: str | None = None,
) -> None:
    print("\n>>>\tSearching for Comicvine ID: " + str(cv_id))

    t = LibgenSearch()

    async def _run_test():
        try:
            titles = await t.search_comicvine_id(
                api_key=api_key,
                id=cv_id,
                issue_number=issue_number,
                libgen_site_url="https://libgen.la",
                libgen_series_id=libgen_series_id,
                search_unsorted=search_unsorted,
                flaresolverr_url=flaresolverr_url,
            )
            for elem in titles:
                print(elem)
                if flaresolverr_url is not None:
                    print(
                        await get_annas_archive_download(
                            elem,
                            flaresolverr_url,
                            "https://annas-archive.li",
                        )
                    )
        except KeyboardInterrupt:
            print("\nExiting program...")
            exit(0)

    asyncio.run(_run_test())
