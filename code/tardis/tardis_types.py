from dataclasses import dataclass

# container to represent shows -> these are NOT from the tardis guide API
class Show:
    ALL_SHOWS = set()

    def __init__(self, slug, translation):
        self.slug = slug
        self.translation = translation
        Show.ALL_SHOWS.add(self)

    def __hash__(self):
        return hash(self.slug)

    def __eq__(self, other):
        if isinstance(other, Show):
            return self.slug == other.slug
        return other == self.slug
# arbitrary constants to identify and translate shows themselves
Show.NEW_WHO = Show("new-who", "New Who")
Show.CLASSIC = Show("classic-who", "Classic Who")
Show.TORCHWOOD = Show("torchwood", "Torchwood")
Show.SARAH_JANE_ADVENTURES = Show("sja", "Sarah Jane Adventures")
Show.CLASS = Show("class", "Class")
Show.WAR_BETWEEN = Show("twatblast", "The War Between the Land and the Sea")
# lists representing key groups of shows
Show.SPINOFFS = [Show.TORCHWOOD, Show.SARAH_JANE_ADVENTURES, Show.CLASS, Show.WAR_BETWEEN]
Show.MAIN_SHOW = [Show.NEW_WHO, Show.CLASSIC]

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

    def has_attribute(self, name):
        return name in self.__dict__

    def get_attribute_by_name(self, name):
        return self.__dict__[name]
        

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
    show: str # where the string is a slug value of Show