import asyncio

from libgencomics import LibgenSearch

with open(".api") as file:
    api_key = file.read().replace("\n", "")

id = 118545


def print_results(arr):
    for elem in arr:
        print(elem)


# test comicvine series id search
t = LibgenSearch()
print("\n>>>\tSearching for Comicvine ID: " + str(id))


async def main():
    try:
        titles = await t.search_comicvine_id(
            api_key=api_key,
            id=id,
            issue_number=3,
            libgen_site_url="https://libgen.la",
            libgen_series_id=377565,
        )
        print_results(titles)
    except KeyboardInterrupt:
        print("\nExiting program...")
        exit(0)


asyncio.run(main())
