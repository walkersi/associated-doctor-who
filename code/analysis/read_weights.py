from datasets.serialise import deserialise_from_file
FILENAME = "analysis/trope_weights.json"

def load_weights():
    weight_dict = deserialise_from_file(FILENAME, dict)
    return weight_dict