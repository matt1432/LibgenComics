"""

Basic testing script for libgen-api.
Runs through a number of searches using different parameters, outputs results to terminal.

Run -
python3 test.py

"""

from libgencv import LibgenSearch

with open(".api") as file:
    import pycomicvine

    pycomicvine.api_key = file.read().replace("\n", "")

id = 10379


def print_results(arr):
    for elem in arr:
        print(elem)


# test comicvine series id search
t = LibgenSearch()
print("\n>>>\tSearching for Comicvine ID: " + str(id))

try:
    titles = t.search_comicvine_id(id, "25", "https://libgen.gs/series.php?id=110830")
    print_results(titles)
except KeyboardInterrupt:
    print("\nExiting program...")
    exit(0)
