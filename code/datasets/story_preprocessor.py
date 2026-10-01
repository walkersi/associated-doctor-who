import datasets.data_extraction as data
from serialise import serialise_to_file
from tardis.tardis_guide import TardisGuide
from tardis.tardis_types import Story

# code for automatically gathering rich texts for all of a certain 
# story type from the local csv source

OUTPUT_PATH = "datasets/processed/stories/"

# dict_keys
TITLE = "title"
MEDIA = "media"
RANGE = "range"
SERIES = "series"
SLUG = "slug"

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

def reprocess_record(record: dict):
    cull_keys = ["Tardis Wiki URL", "Broadcast Date", "Internal Story ID"]
    rename_keys = {
        "Story Title": TITLE, "Media": MEDIA, "Range": RANGE, 
        "Series": SERIES, "TARDIS Guide URL": SLUG}
    transforms = {"TARDIS Guide URL": slug_from_url}
    return data.rename_all(record, cull_keys, rename_keys, transforms=transforms)
    
def should_keep_record(record: dict):
    # keep record when its new who TV
    field_matches = {MEDIA: "TV", RANGE: "Doctor Who", SERIES: "Doctor Who S"}
    compares = {SERIES: lambda cur, mat: cur.startswith(mat)}
    return data.record_matches(record, field_matches, compares=compares)

def load_new_who_slugs():
    records = data.open_csv_as_dict("datasets/raw/tardis-guide-everything.csv")
    records = map(reprocess_record, records)
    records = filter(should_keep_record, records)
    return [r[SLUG] for r in records]

def save_story(story: Story):
    file_path = OUTPUT_PATH + story.slug + ".json"
    serialise_to_file(story, file_path)

def main():
    # load a list of the new who tardis guide slug IDs using the CSV file
    slugs = load_new_who_slugs()
    # connect to API
    guide = TardisGuide()
    # request rich story descriptions of all the stories
    riches = [guide.get_story_rich(f"story/{slug}") for slug in slugs]
    # disconnect from API
    guide.close()
    # process the stories into application objects
    stories = [] # TODO
    # and write them to the filesystem
    for story in stories:
        save_story(story)

if __name__=='__main__':
    main()