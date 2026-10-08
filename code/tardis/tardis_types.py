from dataclasses import dataclass
from enum import Enum


# represents shows -> these are NOT from the tardis guide API
NEW_WHO = "new-who"
CLASSIC = "classic-who"
TORCHWOOD = "torchwood"
SARAH_JANE_ADVENTURES = "sja"
CLASS = "class"

# represents an object whose attribute names are semantically meaningful
class DictLike:
    # get an attribute by its string name
    def get(self, key: str):
        return self.__dict__[key]

    # returns iterator of attribute names for which the predicate holds
    # where predicate is in form p(attribute_name, attribute_value)
    # returns all if no predicate provided
    def get_attribute_names(self, predicate=None) -> list[str]:
        return [name for name, _ in self.get_attribute_subset(predicate=predicate).items()]

    # returns a subset of this object's attributes for which the predicate holds
    # in form p(attribute_name, value)
    def get_attribute_subset(self, predicate=None) -> dict:
        # default predicate, subset is set
        if not predicate:
            predicate = lambda n, v: True
        # collect valid attributes
        subset = {}
        # check if predicate holds for each attrib
        for name, value in self.__dict__.items():
            if predicate(name, value):
                subset[name] = value

        return subset
        


# application-relevant representation of storys from tardisguide database
@dataclass
class Story(DictLike):

    slug: str # unique human-readable ID from tardisguide
    title: str # actual title
    writers: list[str] # list of writer names
    tropes: list[str] # lists of slugs
    cast: list[str]
    characters: list[str]
    locations: list[str]
    time_travel: list[str]
    show: str = NEW_WHO # where the string is a value of Show

    