from datasets.story_loader import load_stories
from datasets.os_utils import create_nested_directory
from datasets.serialise import serialise_to_file
from api.logger import Logger, Level, Type

#
# classes for performing counting operations over the attributes of multiple
# DictLike objects (e.g. Story)
#

OUTPUT_PATH = "analysis/counts/"
OUTPUT_FILE_DEFAULT = "counts"
SCHEMA_VERSION = "v1.0.5" # v1.0.4 supports classed grouping; v1.0.5 supports class count
DEFAULT_PARENT_CLASSIFICATION = ""
GROUP_COUNT_FIELD = "count"

LOGGER = Logger(Type.INFO, Level.DEVELOPER)

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
    # field_parent_getter is for classifying objects by class, should return a value representing group (or be None)
    def __init__(self, objects: list[object], field_getters: list[NamedLookup], field_parent_getter: NamedLookup = None):
        self.objects = objects
        self.getters = field_getters
        # used to decide which sub-count to group by
        self.field_parent_getter = field_parent_getter 
        if not field_parent_getter:
            self.field_parent_getter = NamedLookup("", lambda _: DEFAULT_PARENT_CLASSIFICATION) # group arbitrarily
        # map aliased fields to a collection of every single value (inc duplicates)
        self.attributes = {}
        # map class' alias fields to dictionaries of their discrete values mapped to number
        # of occurrences in objects dataset
        self.counts = {}
        self.attributes = {}

    # scan list of objects (e.g. all stories) and acquire all the values that
    # appear in the list
    def scan_dataset(self):
        # go through every object
        for object in self.objects:
            # check the general class of this object
            object_class = self.field_parent_getter.get(object)
            if object_class not in self.attributes:
                self.attributes[object_class] = {GROUP_COUNT_FIELD: 0}
            # increment the group counter (how many in this subset?)
            self.attributes[object_class][GROUP_COUNT_FIELD] += 1
            
            for getter in self.getters:
                # collect this attributes values
                name = getter.name
                values = getter.get(object)
                if name not in self.attributes[object_class]:
                    self.attributes[object_class][name] = []
                self.attributes[object_class][name] += values

    # processes counted attributes into dict of their discrete totals
    def count_attributes(self):
        for object_class, categories in self.attributes.items():
            # transfer the group counter to the final output
            total_in_class = self.attributes[object_class].pop(GROUP_COUNT_FIELD)
            self.counts[object_class] = {GROUP_COUNT_FIELD: total_in_class}
            for category, items in categories.items():
                if category not in self.counts[object_class]:
                    self.counts[object_class][category] = {}
                for item in items:
                    if item not in self.counts[object_class][category]:
                        self.counts[object_class][category][item] = 1
                    else:
                        self.counts[object_class][category][item] += 1

    def write_to_file(self, file_name):
        # serialise the counts dictionary and write it to the given file
        # if counts are ungrouped, write the nested entries instead
        if len(self.counts) == 1 and DEFAULT_PARENT_CLASSIFICATION in self.counts:
            self.counts = self.counts[DEFAULT_PARENT_CLASSIFICATION]
        # make the output path if it does not exist
        create_nested_directory(OUTPUT_PATH)
        # create file path
        path = f"{OUTPUT_PATH}/{file_name}.{SCHEMA_VERSION}.json"
        serialise_to_file(self.counts, path, pretty=True)

    # run full counter pipeline
    def process_dataset(self, output_file=OUTPUT_FILE_DEFAULT):
        self.scan_dataset()
        self.count_attributes()
        self.write_to_file(output_file)

def main():

    LOGGER.info("Counter recovering stories from disk")
    # load the stories from disk and count the fields
    stories = load_stories()
    # check the current schema of the story object
    sample = stories[0]
    # define which attributes to count and how to retrieve their values
    # only count attributes whose values are lists.
    LOGGER.info("Initialising count criteria")
    attributes = sample.get_attribute_names(predicate = lambda _, v: isinstance(v, list))
    counting_attributes = [NamedLookup(attribute) for attribute in attributes]
    LOGGER.info("Beginning count")
    Counter(stories, counting_attributes, field_parent_getter=NamedLookup("show")).process_dataset()
    LOGGER.info("Finished attribute-value count and written to disk")

if __name__=='__main__':
    main()