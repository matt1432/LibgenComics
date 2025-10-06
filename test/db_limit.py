import asyncio

from libgencomics import LibgenSearch

with open(".api") as file:
    api_key = file.read().replace("\n", "")

cv_id = 2127


def print_results(arr):
    for elem in arr:
        print(elem)


# test comicvine series id search
t = LibgenSearch()
print("\n>>>\tSearching for Comicvine ID: " + str(cv_id))


async def main():
    try:
        titles = await t.search_comicvine_id(
            api_key=api_key,
            id=cv_id,
            issue_number=None,
            libgen_site_url="https://libgen.la",
            libgen_series_id=105809,
        )
        print_results(titles)
    except KeyboardInterrupt:
        print("\nExiting program...")
        exit(0)


asyncio.run(main())
