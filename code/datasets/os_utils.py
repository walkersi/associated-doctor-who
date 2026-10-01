from os import listdir
from os.path import isfile, join

def get_all_files_in_directory(dir: str):
    return [item for item in listdir(dir) if isfile(join(dir, item))]