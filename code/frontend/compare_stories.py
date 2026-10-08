from datasets.story_loader import load_stories
from tardis.tardis_types import Story
from analysis.counter import NamedLookup

def compare_stories(target_story: Story, current_story: Story):
    counting_attributes = [
        NamedLookup("name", lambda s: s.get_name()),
        NamedLookup("locations", lambda s: s.get_locations()),
        NamedLookup("tropes", lambda s: s.get_tropes()),
        NamedLookup("characters", lambda s: s.get_characters()),
        NamedLookup("writers", lambda s: s.get_writers()),
    ]
    target_attributes = get_attributes(target_story, counting_attributes)
    current_attributes = get_attributes(current_story, counting_attributes)
    overlapping_attributes = {}
    for key in target_attributes:
        if key != "name":
            overlapping_attributes[key] = []
            if key in current_attributes:
                for attribute in target_attributes[key]:
                    if attribute in current_attributes[key]:
                        overlapping_attributes[key].append(attribute)
    print(overlapping_attributes)

def get_attributes(story: Story, counting_attributes: list[NamedLookup]):
    attributes = {}
    for getter in counting_attributes:
        attributes[getter.name] = getter.get(story)
    return attributes

def find_story(stories: list[Story], story_slug: str):
    for story in stories:
        if story.slug == story_slug:
            return story
    return None

stories = load_stories()
compare_stories(find_story(stories, "silence-in-the-library"), find_story(stories, "forest-of-the-dead"))