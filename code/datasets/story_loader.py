from tardis.tardis_types import Story
from datasets.serialise import deserialise_from_file
from datasets.story_preprocessor import OUTPUT_PATH as INPUT_PATH
from datasets.story_preprocessor import SCHEMA_VERSION, LOGGER
from datasets.os_utils import get_all_files_in_directory

def load_story(story_file: str):
    if story_file.endswith(f".{SCHEMA_VERSION}.json"):
        return deserialise_from_file(story_file, Story)
    
    LOGGER.warn("Couldn't load", story_file, "due to schema verison mismatch - skipped.")
    return None

def load_stories(directory: str=INPUT_PATH) -> list[Story]:
    files = get_all_files_in_directory(directory)
    # filter out anything thats not a json that might also be in there
    json_files = filter(lambda f: f.endswith("json"), files)
    # and load all the stories
    stories = []
    for file in json_files:
        story = load_story(directory + file)
        # only append if loading successful
        if story:
            stories.append(story)
        else:
            LOGGER.warn("Couldn't read story from", file, ", skipped")

    return stories