# intermediate representations of stories used during preprocessing
from dataclasses import dataclass
from tardis.tardis_types import Story

@dataclass
class StubStory: # a story before API hit
    slug: str
    show: str

# constants that match fields in the API response itself
TITLE = "title"
SLUG = "slug"
WRITERS = "writer"
TROPES = "tropes"
CHARACTERS = "characters"
CAST = "actors"
LOCATIONS = "locations"
TIME_TRAVEL = "time_travel"
# collects the fields that map to lists of dicts of named API objects 
# (that have slugs and english names)
SLUGGED_OBJECT_GROUPS = [TROPES, CHARACTERS, CAST, LOCATIONS, TIME_TRAVEL]
# collects the fields that map to lists of just the plaintext english, no slug
PLAINTEXT_OBJECT_GROUPS = [WRITERS]

@dataclass
class CategorisedRich: # an API response bundled with the CSV show categorisation
    story: dict
    show: str

    # extracts slugs from grouped items with slugs (e.g. tropes)
    def extract(self, field):
        return self.extract_slugs_from_object_group(self.story[field])

    def extract_slugs_from_object_group(self, group):
        return [item[SLUG] for item in group]

    def get_title(self):
        return self.story[TITLE]

    def get_slug(self):
        return self.story[SLUG]

    def get_writers(self):
        return self.story[WRITERS]

    def get_tropes(self):
        return self.extract(TROPES)

    def get_characters(self):
        return self.extract(CHARACTERS)

    def get_cast(self):
        return self.extract(CAST)

    def get_locations(self):
        return self.extract(LOCATIONS)

    def get_time_travel(self):
        return self.extract(TIME_TRAVEL)

    def get_show(self):
        return self.show

    # converts this story to an application-level Story object
    def get_as_story(self) -> Story:
        return Story(self.get_slug(), self.get_title(), self.get_writers(),
                     self.get_tropes(), self.get_cast(), self.get_characters(),
                     self.get_locations(), self.get_time_travel(), self.get_show())