import csv
# code for extracting and re-formatting csvs

# renames the given key in this dict with the new_key name
# if key not present, returns false, otherwise true
# optionally applies transformation function to the value that
# the key corresponds to, in form v' = f(v)
def rename_key(record: dict, key: str, new_key: str, transform=None):
    # reject nonexistent keys
    if not key in record:
        return False
    # temporarily copy value and apply the transformation function if supplied
    value = record[key]
    if transform:
        value = transform(value)
    # rename key
    del record[key]
    record[new_key] = value
    return True

# given a {str, _} dictionary, reformats such that:
#  all keys in cull_keys are removed
#  all keys in key_swaps are renamed to their corresponding mapping
#    with the values in the record transformed with any provided function
#  transforms maps the ORIGINAL keys to the used transformation function
# skips keys *silently* for any cull_keys that are invalid (not in record)
# skips key swaps *silently* for any non existent entries
def rename_all(record: dict, cull_keys: list[str], key_swaps: dict[str, str], transforms=None):
    # no transforms supplied
    if not transforms:
        transforms = {}
    # remove relevant keys
    for key in cull_keys:
        if key in record:
            del record[key]
    # rename all the listed keys
    for key, new_key in key_swaps.items():
        # get the relevant transform if present
        transform = None if key not in transforms else transforms[key]
        rename_key(record, key, new_key, transform=transform)
    
    return record

# returns True if this record's values match the given criteria
# if a key present in record is not given it key_values, result is unaffected
#  (i.e. if key_values is {}, always returns True)
# assumes all keys in key_values are present in record
# where compare functions are predicates in the form f(current_value, match_value)
#  and compares is a dict of these functions mapped from match keys
def record_matches(record: dict, key_values: dict, compares=None):
    # safe empty iterable
    if not compares:
        compares = {}

    # check all supplied keys for matches
    for key, value in key_values.items():
        # use equals as the default comparison, or select provided
        compare = (lambda x, y: x == y) if key not in compares else compares[key]
        print(key, "func", compare, "values:", record[key], "and", value)
        if not compare(record[key], value):
            # not a match
            return False

    return True
        

# returns records as dictionary with given header or the first line as header if None
def open_csv_as_dict(path: str, header: list = None):
    header = None

    with open(path, newline='') as csv_file:
        reader = csv.reader(csv_file)
        # read the header line as the CSV format if not provided
        if not header:
            header = reader.__next__()
        # then read the whole thing into records
        records = [record for record in reader]
        # convert to dicts
        dict_records = []
        for record in records:
            dictified = {}
            for field, value in zip(header, record):
                dictified[field] = value
            dict_records.append(dictified)
        return dict_records