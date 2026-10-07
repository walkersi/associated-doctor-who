from datasets.story_loader import load_stories
from datasets.os_utils import create_nested_directory
from datasets.serialise import serialise_to_file

OUTPUT_PATH = "analysis/counts/"
OUTPUT_FILE_DEFAULT = "counts"
SCHEMA_VERSION = "v1.0.1"

ATTRIBUTE_LOCATIONS = "locations"
ATTRIBUTE_CHARACTERS = "characters"
ATTRIBUTE_WRITERS = "writers"
ATTRIBUTE_TROPES = "tropes"

# for some specified object type, get a property
# using a function if form f(object) -> attribute
# and associate its value with a set name
# names are useful because it means these can be serialised
class NamedLookup:
    def __init__(self, name: str, getter):
        self.name = name
        self.getter = getter

    def get(self, obj: object):
        return self.getter(obj)

# counts up the number of occurences of particular values in given fields
# of some object
class Counter:
    # where objects are a collection of objects of the same type
    # and fields are getter functions to retrieve attribute values
    # where each getter returns a list of something comparable for equality, e.g. [str]
    #   they should also be serialisable things
    def __init__(self, objects: list[object], field_getters: list[NamedLookup]):
        self.objects = objects
        self.getters = field_getters
        # map aliased fields to a collection of every single value (inc duplicates)
        self.attributes = {}
        # map alias fields to dictionaries of their discrete values mapped to number
        # of occurrences in objects dataset
        self.counts = {}
        for getter in self.getters:
            self.attributes[getter.name] = []
            self.counts[getter.name] = {}

    # scan list of objects (e.g. all stories) and acquire all the values that
    # appear in the list
    def scan_dataset(self):
        # go through every object
        for object in self.objects:
            for getter in self.getters:
                name = getter.name
                values = getter.get(object)
                for value in values:
                    self.attributes[name].append(value)

    # processes counted attributes into dict of their discrete totals
    def count_attributes(self):
        for category, items in self.attributes.items():
            for item in items:
                if item not in self.counts[category]:
                    self.counts[category][item] = 1
                else:
                    self.counts[category][item] += 1

    def write_to_file(self, file_name):
        # serialise the counts dictionary and write it to the given file
        # make the output path if it does not exist
        create_nested_directory(file_name)
        # create file path
        path = f"{OUTPUT_PATH}/{file_name}.{SCHEMA_VERSION}.json"
        serialise_to_file(self.counts, path)

    # run full counter pipeline
    def process_dataset(self, output_file=OUTPUT_FILE_DEFAULT):
        self.scan_dataset()
        self.count_attributes()
        self.write_to_file(output_file)

def main():

    # define which attributes to count and how to retrieve their values
    counting_attributes = [
        NamedLookup(ATTRIBUTE_LOCATIONS, lambda s: s.get_locations()),
        NamedLookup(ATTRIBUTE_TROPES, lambda s: s.get_tropes()),
        NamedLookup(ATTRIBUTE_CHARACTERS, lambda s: s.get_characters()),
        NamedLookup(ATTRIBUTE_WRITERS, lambda s: s.get_writers()),
    ]
    # load the stories from disk and count the fields
    stories = load_stories()
    Counter(stories, counting_attributes).process_dataset()
    

if __name__=='__main__':
    main()