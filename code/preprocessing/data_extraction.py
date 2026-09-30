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

# returns tuple of the records, then any header listing
def open_csv(path: str, has_header=True):
    header = None

    with open(path, newline='') as csv_file:
        reader = csv.reader(csv_file)
        # skip the header line if required
        if has_header:
            header = reader.__next__()
        # then read the whole thing into records
        return [record for record in reader], header

def main():

    records, header = open_csv("resources/doctor-who-tv/tardis-guide.export-for-wiki.csv")

    print(records)
    print(header)

    allowed_series_prefixes = ["Doctor Who"]

    #map(lambda r: slug_from_url(), records)

    #api = TardisGuide()

    #x = api.get_story_rich("story/the-satan-pit")
    #print(x)

    #api.close()


if __name__=='__main__':
    main()