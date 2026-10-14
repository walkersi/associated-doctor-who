# uses tardis guide to preprocess mappings for slugs (of tropes etc) to English names (for UI display)
from datasets.os_utils import create_nested_directory
from datasets.story_transients import CategorisedRich
from datasets.story_transients import PLAINTEXT_OBJECT_GROUPS, SLUGGED_OBJECT_GROUPS
from tardis.tardis_types import Show
from datasets.serialise import serialise_to_file, deserialise_from_file

OUTPUT_PATH = "datasets/processed/slugs/"
DEFAULT_FILE = "slug_map_english.json"
MANUAL_MAPPINGS_FILE_PATH = "datasets/raw/manual_names.json"

# maps API-context slugs in application-context fields to their names
class AbstractSlugMap:
    def __init__(self, file: str = DEFAULT_FILE):
        self.file_path = OUTPUT_PATH + file
        self.slug_dict = {}
        # generate the file path in case it does not exist
        create_nested_directory(OUTPUT_PATH)

    # makes an arbitrary unique id for a slug given the context of its field (e.g. "tropes")
    def make_id(self, field, slug):
        return f"{field}:{slug}"

# slug map loaded from file
# use this for application-time slug lookup
class SlugMap(AbstractSlugMap):
    def __init__(self, file: str = DEFAULT_FILE):
        super().__init__(file=file)
        self.load_slug_map()
        
    # loads the preprocessed slug map from file
    def load_slug_map(self):
        self.slug_dict = deserialise_from_file(self.file_path)

    # where category is from the story_transients API lookup types
    def get_english_name(self, category, slug):
        id = self.make_id(category, slug)
        if id in self.slug_dict:
            return self.slug_dict[id]
        else:
            return slug # slug lookup failed

# generates a slug map from API response text and manual additives
# use during preprocessing
class GeneratingSlugMap(AbstractSlugMap):
    def __init__(self, riches: list[CategorisedRich], file: str = DEFAULT_FILE):
        super().__init__(file=file)
        # map all the riches slugs
        for rich in riches:
            self.map_slugs_in_rich(rich)
        # add mappings for the show names
        self.add_show_mappings()
        # lastly, augment with names for the manually-added tropes/etc
        self.add_manual_mappings()

    def add_show_mappings(self):
        # map all the [non tardis guide] slugs for shows too
        for show in Show.ALL_SHOWS:
            self.add_mapping("show", show.slug, show.translation)


    def add_manual_mappings(self):
        # load manually written mappings from the name file
        manual_map = deserialise_from_file(MANUAL_MAPPINGS_FILE_PATH, dict)
        if not manual_map:
            print("Manual slug-name map file could not be processed.") # TODO should use logger
            return
        # add them to the dictionary directly
        for key, value in manual_map.items():
            self.slug_dict[key] = value

    def add_mapping(self, category: str, slug: str, name: str):
        self.slug_dict[self.make_id(category, slug)] = name

    def map_slugs_in_field(self, api_story: str, field: str):
        # get a list of dict Tardis Guide named slug objects
        slugged_objects = api_story[field]
            
        for slugged in slugged_objects:
            slug = slugged["slug"]
            name = slugged["name"]
            # stores the slug->name mappings
            self.add_mapping(field, slug, name)
    
    def map_slugs_in_rich(self, rich: CategorisedRich):
        # examine the API response itself
        api_story = rich.story

        for field in SLUGGED_OBJECT_GROUPS:
            self.map_slugs_in_field(api_story, field)

        # for completeness, map the plaintext to themselves 
        # (so that they can still be looked up by application code in a homogenous way)
        for field in PLAINTEXT_OBJECT_GROUPS:
            for name in api_story[field]:
                self.add_mapping(field, name, name)

    def save_to_file(self):
        serialise_to_file(self.slug_dict, self.file_path, pretty=True)

