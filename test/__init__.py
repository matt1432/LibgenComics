import asyncio

from libgencomics import LibgenSearch

with open(".api") as file:
    api_key = file.read().replace("\n", "")


def print_results(arr):
    for elem in arr:
        print(elem)


def run_test(
    *,
    cv_id: int,
    libgen_series_id: int | None,
    issue_number: float | tuple[float, float] | None,
    search_unsorted: bool = True,
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
            )
            print_results(titles)
        except KeyboardInterrupt:
            print("\nExiting program...")
            exit(0)

    asyncio.run(_run_test())
