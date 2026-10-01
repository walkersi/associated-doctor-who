from tardis.tardis_types import Story
from serialise import deserialise_from_file
from story_preprocessor import OUTPUT_PATH as INPUT_PATH
from os import listdir
from os.path import isfile, join

def get_all_files_in_directory(dir):
    return [item for item in listdir(dir) if isfile(join(dir, item))]

def load_story(story_file):
    return deserialise_from_file(story_file, Story)

def load_stories(directory=INPUT_PATH):
    files = get_all_files_in_directory(directory)
    # filter out anything thats not a json that might also be in there
    json_files = filter(lambda f: f.endswith("json"), files)
    # and load all the stories
    return [load_story(directory + file) for file in json_files]