from os import listdir
from os.path import isfile, join
from pathlib import Path

def get_all_files_in_directory(dir: str):
    return [item for item in listdir(dir) if isfile(join(dir, item))]

def create_nested_directory(dir: str):
    Path(dir).mkdir(parents=True, exist_ok=True)