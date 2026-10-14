import datasets.data_extraction as data
from datasets.serialise import serialise_to_file
from tardis.tardis_types import Story, Show
from api.logger import Logger, Level, Type
from datasets.story_transients import StubStory, CategorisedRich
from datasets.os_utils import create_nested_directory
from datasets.manual_hinting import add_hints
from datasets.slug_map import GeneratingSlugMap
from api.api_connection import APIConnection, APIRequest

# code for automatically gathering rich texts for all of a certain 
# story type from the local csv source
# and processing into jsons stored in filesystem
# that can be loaded into Story objects (see story_loader.py)
# --> story filenames in format "[output path]/episode-slug.VERSION.json"

OUTPUT_PATH = "datasets/processed/stories/"
SCHEMA_VERSION = "v1.0.4" # v1.0.1 supports time_travel in schema, 
#  v1.0.3 supports full multi-show categorisation
# v1.0.4 filters out reconstructions properly
# logger for this part of the system
LOGGER = Logger(type=Type.INFO, level=Level.DEVELOPER)

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

# given a record, determines which Show string it maps to
def categorise_story_show(record: dict):
    # given a record, which show (see tardis_types) is it?
    # assumes post-filtration dataset
    match (record[RANGE]):
        case "Doctor Who":
            if record[SERIES].startswith("Classic"):
                return Show.CLASSIC
            else:
                return Show.NEW_WHO
        case "Sarah Jane Adventures":
            return Show.SARAH_JANE_ADVENTURES
        case "Torchwood":
            return Show.TORCHWOOD
        case "Class":
            return Show.CLASS
        case "The Worlds of Doctor Who":
            if record[SERIES].startswith("The War Between"):
                return Show.WAR_BETWEEN
    return None
        

def should_keep_record(record: dict):
    # keep record when its TV [New/Classic, Class/SJA/Torchwood/War Between]

    # useful functions for searching quicker
    start_with_any_of = lambda cur, matches: any([cur.startswith(match) for match in matches])
    does_not_end_with = lambda cur, match: not cur.endswith(match)
    does_not_contain = lambda cur, match: match not in cur

    # series filter is based on CSV format:
    #  - Doctor Who S[6] or S[pecials] or S[eason One]
    #  - 60th Anniversary is listed separately
    #  - Classic [Who Season ...], assuming episode name doesn't end in "Reconstruction"

    new_who_filter = (
        {MEDIA: "TV", RANGE: "Doctor Who", SERIES: ["Doctor Who S", "60th Anniversary Specials"]},
        {SERIES: start_with_any_of}
    )
    # classic except telesnap reconstructions
    classic_who_filter = (
        {MEDIA: "TV", RANGE: "Doctor Who", SERIES: ["Classic"], TITLE: "Reconstruction"},
        {SERIES: start_with_any_of, TITLE: does_not_contain}
    )
    # torchwood/sja/class, except Alien Files
    major_spin_off_filter = (
        {MEDIA: "TV", RANGE: ["Torchwood", "Sarah Jane", "Class"], TITLE: "Sarah Jane's Alien Files"},
        {RANGE: start_with_any_of, TITLE: does_not_contain}
    )
    # stupid series
    minor_spin_off_filter = (
        {MEDIA: "TV", RANGE: "The Worlds of Doctor Who", SERIES: "The War Between the Land and the Sea"}, {}
    )
    # ordered for efficiency
    searches = [ new_who_filter, classic_who_filter, major_spin_off_filter, minor_spin_off_filter ]

    # check record against each filter
    for field_matches, compares in searches:
        match = data.record_matches(record, field_matches, compares=compares)
        if match:
            return True

    return False

def load_all_stub_stories() -> list[StubStory]:
    records = data.open_csv_as_dict("datasets/raw/tardis-guide-everything.csv")
    records = map(reprocess_record, records)
    records = filter(should_keep_record, records)
    return [StubStory(r[SLUG], categorise_story_show(r)) for r in records]

def save_story(story: Story):
    file_path = OUTPUT_PATH + story.slug + "." + SCHEMA_VERSION + ".json"
    serialise_to_file(story, file_path)


def main():
    # load a list of the new who tardis guide slug IDs using the CSV file
    stubs = load_all_stub_stories()
    LOGGER.info("Loaded slugs from CSV, n=", len(stubs))
    # connect to API
    api = APIConnection()

    # collect together rich story responses
    riches = []
    for stub in stubs:
        # send tardis guide requests for each rich story description
        rich_story = api.get(APIRequest(f"story/{stub.slug}"))
        # bundle with the show field
        riches.append(CategorisedRich(rich_story, stub.show))

    LOGGER.info("Gathered rich story API responses, n=", len(riches))
    # disconnect from API
    api.close()

    # process the stories into application objects
    stories = [rich.get_as_story() for rich in riches]
    LOGGER.info("Created story objects, n=", len(stories))

    # create a map of slugs to localised names for easy lookup
    slug_map = GeneratingSlugMap(riches)
    slug_map.save_to_file()

    # apply manual hinting to them
    add_hints(stories)
    LOGGER.info("Applied manual hints")

    # make sure the target path exists
    create_nested_directory(OUTPUT_PATH)
    # and write them to the filesystem
    for story in stories:
        save_story(story)

if __name__=='__main__':
    main()