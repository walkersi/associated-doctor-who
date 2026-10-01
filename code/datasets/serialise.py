import json
from api.logger import Logger, Level, Type
# TODO integrate rename/cull/repopulate/infer for space efficient serialisation
#from datasets.data_extraction import rename_all

# class for serialising objects to json
# only works for objects where their fields are primitives (bools, ints, floats, str)
# that can be represented in json

LOGGER = Logger(Type.WARN, Level.DEVELOPER)

def serialise(object):
    attribs = object.__dict__
    return json.dumps(attribs)

def deserialise(json_data, target_class):
    attribs = json.loads(json_data)
    object = target_class.__new__(target_class)
    object.__dict__ = attribs
    return object

def serialise_to_file(object, path):
    with open(path, "w+") as file:
        file.write(serialise(object))

# returns None if file could not be found
def deserialise_from_file(path, target_class):
    try:
        with open(path, "r") as file:
            return deserialise(file.read(), target_class)

    except FileNotFoundError:
        LOGGER.warn("Couldn't find file", path, "to deserialise", level=Level.ALWAYS)
        return None

