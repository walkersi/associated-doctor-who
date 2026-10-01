import json
# TODO integrate rename/cull/repopulate/infer for space efficient serialisation
from data_extraction import rename_all

# class for serialising objects to json
# only works for objects where their fields are primitives (bools, ints, floats, str)
# that can be represented in json

def serialise(object):
    attribs = object.__dict__
    return json.dumps(attribs)

def deserialise(json_data, target_class):
    attribs = json.loads(json_data)
    object = target_class.__new__()
    object.__dict__ = attribs

def serialise_to_file(object, path):
    with open(path, "w+") as file:
        file.write(serialise(object))

# returns None if file could not be found
def deserialise_from_file(path, target_class):
    try:
        with open(path, "r") as file:
            return deserialise(file.read(), target_class)

    except FileNotFoundError:
        return None

