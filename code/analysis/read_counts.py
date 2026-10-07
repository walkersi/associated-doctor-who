from analysis.counter import SCHEMA_VERSION, OUTPUT_PATH, OUTPUT_FILE_DEFAULT
from datasets.serialise import deserialise_from_file, LOGGER

# returns {{}} of attributes mapped to values mapped to counts
# see counter ATTRIBUTE constants for reading
# or None if unreadable/bad schema version
# or errors if no OS perms or smth
def load_counts(file=OUTPUT_FILE_DEFAULT):
    # deserialise the counts file into a dictionary
    # TODO generalise schema versioning system
    file_name = f"{OUTPUT_PATH}/{file}.{SCHEMA_VERSION}.json"
    count_dict = deserialise_from_file(file_name, dict)
    if not count_dict:
        LOGGER.warn(f"Couldn't load counts file {file}, possible schema version mismatch")
    return count_dict
    