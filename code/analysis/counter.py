from datasets.story_loader import load_stories
from datasets.os_utils import create_nested_directory
from datasets.serialise import serialise_to_file

#
# classes for performing counting operations over the attributes of multiple
# DictLike objects (e.g. Story)
#

OUTPUT_PATH = "analysis/counts/"
OUTPUT_FILE_DEFAULT = "counts"
SCHEMA_VERSION = "v1.0.2" # v1.0.2 supports a more generalised schema counter

# for some specified object type, get a property
# using a function if form f(object) -> attribute
# and associate its value with a set name
# names are useful because it means these can be serialised
# default getter function calls 'object.get(name)' which is viable if
# lookup strings match the object's attribute names
class NamedLookup:
    def __init__(self, name: str, getter = None):
        self.name = name
        if getter:
            self.getter = getter
        else:
            # given some 
            self.getter = lambda o: o.get(name)

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
                # collect this attributes values
                name = getter.name
                values = getter.get(object)
                self.attributes[name] += values

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
        create_nested_directory(OUTPUT_PATH)
        # create file path
        path = f"{OUTPUT_PATH}/{file_name}.{SCHEMA_VERSION}.json"
        serialise_to_file(self.counts, path)

    # run full counter pipeline
    def process_dataset(self, output_file=OUTPUT_FILE_DEFAULT):
        self.scan_dataset()
        self.count_attributes()
        self.write_to_file(output_file)

def main():

    # load the stories from disk and count the fields
    stories = load_stories()
    # check the current schema of the story object
    sample = stories[0]
    # define which attributes to count and how to retrieve their values
    # only count attributes whose values are lists.
    attributes = sample.get_attribute_names(predicate = lambda _, v: isinstance(v, list))
    counting_attributes = [NamedLookup(attribute) for attribute in attributes]
    Counter(stories, counting_attributes).process_dataset()

if __name__=='__main__':
    main()