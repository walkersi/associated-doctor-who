import json
from api.logger import Logger, Level, Type
# TODO integrate rename/cull/repopulate/infer for space efficient serialisation
#from datasets.data_extraction import rename_all

# class for serialising objects to json
# only works for objects where their fields are primitives (bools, ints, floats, str)
# that can be represented in json

LOGGER = Logger(Type.WARN, Level.DEVELOPER)

# serialise an object or data structure (e.g. [], {})
def serialise(possible_object):
    # just serialise as is if data structure
    attribs = possible_object
    if hasattr(possible_object, "__dict__"):
        # extract the attributes to serialise if object
        attribs = possible_object.__dict__
    # serialise
    return json.dumps(attribs)

def deserialise(json_data, target_class):
    # deserialise the json to a dict
    attribs = json.loads(json_data)
    # load the attributes into a new object of target class
    object = target_class.__new__(target_class)
    # load in the attributes if it's class-like
    if hasattr(object, "__dict__"):
        object.__dict__ = attribs
        return object
    # otherwise, the raw structure is fine
    return attribs

# serialise given object or structure to the given file
def serialise_to_file(object_like, path):
    with open(path, "w+") as file:
        file.write(serialise(object_like))

# returns None if file could not be found
def deserialise_from_file(path, target_class):
    try:
        with open(path, "r") as file:
            return deserialise(file.read(), target_class)

    except FileNotFoundError:
        LOGGER.warn("Couldn't find file", path, "to deserialise", level=Level.ALWAYS)
        return None

