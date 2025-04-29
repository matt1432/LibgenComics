"""

Basic testing script for libgen-api.
Runs through a number of searches using different parameters, outputs results to terminal.

Run -
python3 test.py

"""


from libgen_api_comicvine.libgen_search import LibgenSearch
import json

id = 32296


# helper function to print first title if it exists.
def print_results(titles_array):
    print(json.dumps(titles_array[0], indent=1) if len(titles_array) else "No results.")
    print("\n\n--- END OF OUTPUT ---\n\n")


# test comicvine series id search
# should print a result for the book specified at the top of the file.
t = LibgenSearch()
print("\n>>>\tSearching for Comicvine ID: " + str(id))

titles = t.search_comicvine_id(id, 1)
print_results(titles)
