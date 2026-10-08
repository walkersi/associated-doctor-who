from dataclasses import dataclass
from enum import Enum


# represents a show -> these are NOT from the tardis guide API
class Show(Enum):
    NEW_WHO = "new-who"
    CLASSIC = "classic-who"
    TORCHWOOD = "torchwood"
    SARAH_JANE_ADVENTURES = "sja"
    CLASS = "class"

# application-relevant representation of storys from tardisguide database
@dataclass
class Story:

    slug: str # unique human-readable ID from tardisguide
    title: str # actual title
    writers: list[str] # list of writer names
    tropes: list[str] # lists of slugs
    cast: list[str]
    characters: list[str]
    locations: list[str]
    time_travel: list[str]
    show: str = Show.NEW_WHO # where the string is a value of Show

    # get an attribute by its string name
    def get(self, dict_id):
        return self.__dict__[dict_id]