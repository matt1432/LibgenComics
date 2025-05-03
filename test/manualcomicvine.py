"""

Basic testing script for libgen-api.
Runs through a number of searches using different parameters, outputs results to terminal.

Run -
python3 test.py

"""

import json

from libgencv import LibgenSearch

with open(".api") as file:
    import pycomicvine

    pycomicvine.api_key = file.read().replace("\n", "")

id = 7258


# helper function to print first title if it exists.
def print_results(titles_array):
    for title in titles_array:
        print(json.dumps(title, indent=1))
    print("\n\n--- END OF OUTPUT ---\n\n")


# test comicvine series id search
# should print a result for the book specified at the top of the file.
t = LibgenSearch()
print("\n>>>\tSearching for Comicvine ID: " + str(id))

try:
    titles = t.search_comicvine_id(id, 25)
    print_results(titles)
except KeyboardInterrupt:
    print("\nExiting program...")
    exit(0)
