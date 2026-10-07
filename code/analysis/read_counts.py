from analysis.counter import SCHEMA_VERSION, OUTPUT_PATH
ATTRIBUTES = ["location", "trope", "writer", "character"]

def read_file(attribute):
    counts = {}
    with open(OUTPUT_PATH + attribute + "_counts" + SCHEMA_VERSION + ".txt", "r") as f:
        for line in f:
            item, count = line.strip().split(": ")
            counts[item] = int(count)
    return counts

def get_counts():
    results = {}
    for attribute in ATTRIBUTES:
        counts = read_file(attribute)
        results[attribute] = counts
    return results