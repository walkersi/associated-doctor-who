from tardis.tardis_types import Story
from serialise import deserialise_from_file
from story_preprocessor import OUTPUT_PATH as INPUT_PATH
from story_preprocessor import VERSION, LOGGER
from os import listdir
from os.path import isfile, join

def get_all_files_in_directory(dir):
    return [item for item in listdir(dir) if isfile(join(dir, item))]

def load_story(story_file: str):
    if story_file.endswith(f".{VERSION}.json"):
        return deserialise_from_file(story_file, Story)
    
    LOGGER.warn("Couldn't load", story_file, "due to schema verison mismatch - skipped.")
    return None

def load_stories(directory=INPUT_PATH):
    files = get_all_files_in_directory(directory)
    # filter out anything thats not a json that might also be in there
    json_files = filter(lambda f: f.endswith("json"), files)
    # and load all the stories
    stories = []
    for file in json_files:
        story = load_story(directory + file)
        # only append if loading successful
        if story:
            stories.append(json_files)

    return stories