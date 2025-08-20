from libgencomics import LibgenSearch

with open(".api") as file:
    api_key = file.read().replace("\n", "")

id = 43539


def print_results(arr):
    for elem in arr:
        print(elem)


# test comicvine series id search
t = LibgenSearch()
print("\n>>>\tSearching for Comicvine ID: " + str(id))

try:
    titles = t.search_comicvine_id(
        api_key, id, 34.2, "https://libgen.la/series.php?id=116815"
    )
    print_results(titles)
except KeyboardInterrupt:
    print("\nExiting program...")
    exit(0)
