# Allows extra trope/etc information to be loaded from manually created file 
# and added to the preprocessed dataset to modify its final state
# For sampling reasons, all Stories should be of identical schema
from tardis.tardis_types import Story
from datasets.serialise import deserialise_from_file

MANUAL_FILE_PATH = "datasets/raw/manual.json"
ADD_VALUES = "add"
REMOVE_VALUES = "remove"
ANY_SELECTOR = "*"
SUBSET_SELECTOR = "&"
SLUGS_SUBSET = "_slugs"

# returns a map of all slugs of stories to their story object for lookup
def slug_map(stories: list[Story]):
    slugs_to_stories = {}
    for story in stories:
        slug = story.slug
        assert not slug in slugs_to_stories, f"Duplicate slug {slug} detected in preprocessed stories"
        slugs_to_stories[slug] = story
    return slugs_to_stories

# returns true if slug written in file is a valid selector (e.g. a slug, or *)
def valid_slug(slug: str, story_map: dict[str, Story]):
    return slug in story_map or slug == ANY_SELECTOR or slug.startswith(SUBSET_SELECTOR)

# a rule that matches the overall operation (e.g. 'add') with a function
# that describes what to do with the values to (add) to attribute
# in the form f(attribute_of_object, value) -> None
class Rule:
    def __init__(self, id: str, field_processor):
        self.id = id
        self.field_processor = field_processor
    

# applies specified rule to dataset
def apply_rule(rule: Rule, manual: dict, stories: list[Story], story_map: dict[str, Story]):
    # no work specified in file
    if rule.id not in manual:
        return

    slugs = manual[rule.id]
    schema_sample: Story = stories[0]

    # check validity of slugs
    for slug in slugs:
        assert valid_slug(slug, story_map), f"Slug {slug} from manual file is invalid"
        # check validity of slug fields
        for field in slugs[slug]:
            assert (schema_sample.has_attribute(field) or field == SLUGS_SUBSET), f"Field {field} does not exist in Story schema"

    # process each slug
    for slug in slugs:
        # check what this slug selector refers to
        if slug == ANY_SELECTOR:
            selected_stories = stories
        elif slug.startswith(SUBSET_SELECTOR):
            assert isinstance(slugs[slug][SLUGS_SUBSET], list), f"Subset {slug} requires list of slugs in {SLUGS_SUBSET} field"
            selected_stories = []
            for actual_slug in slugs[slug][SLUGS_SUBSET]:
                assert actual_slug in story_map, f"Slug {actual_slug} not found"
                selected_stories.append(story_map[actual_slug])
            # remove the subset group so it doesn't get picked up as a field
            del slugs[slug][SLUGS_SUBSET]
        else:
            selected_stories = [story_map[slug]]
        
        # every field gets updated with set values
        for field in slugs[slug]:
            values = slugs[slug][field]
            # apply rule to every story that matches selector
            for story in selected_stories:
                attribute = story.get_attribute_by_name(field)
                # allow "" or ["", "", ...] as values
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    # add all, or just one if scalar
                    try:
                        rule.field_processor(attribute, value)
                    except ValueError:
                        # e.g. from trying to remove where it does not exist
                        pass

# main method - loads manual file and applies modifications to given story list
def add_hints(stories: list[Story]) -> list[Story]:
    # load the manual file
    manual = deserialise_from_file(MANUAL_FILE_PATH, dict)
    story_map = slug_map(stories)

    add = Rule(ADD_VALUES, lambda attrib, value: attrib.append(value))
    remove = Rule(REMOVE_VALUES, lambda attrib, value: attrib.remove(value))
    # apply the changes
    apply_rule(add, manual, stories, story_map)
    apply_rule(remove, manual, stories, story_map)
    return stories