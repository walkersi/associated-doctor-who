from tardis.tardis_guide import TardisGuide
import csv

# code for automatically gathering rich texts for all of a certain 
# story type from the local csv source

# extracts the story slug from the tardisguide url
# e.g. https://tardis.guide/story/an-unearthly-child/
# returns an-unearthly-child
def slug_from_url(url: str):
    # slice off ending /
    if url[-1] == '/':
        url = url[:-1]
    # find slash before slug
    before = url.rfind('/')
    return url[before + 1:]

def add_slug(record: dict):
    record["slug"] = slug_from_url(record["TARDIS Guide URL"])
    return record

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

def main():

    records = open_csv_as_dict("datasets/raw/tardis-guide-everything.csv")

    allowed_series_prefixes = ["Doctor Who"]
    
    records = map(add_slug, records)    # todo correct
    records = filter(lambda r: r["Series"].startswith("Doctor Who"), records)

    print([r["slug"] for r in records])
    #map(lambda r: slug_from_url(), records)

    #api = TardisGuide()

    #x = api.get_story_rich("story/the-satan-pit")
    #print(x)

    #api.close()


if __name__=='__main__':
    main()