# application-relevant representation of storys from tardisguide database
class Story:

    # where tropes/cast/characters/locations are all slugs
    def __init__(self, slug: str, name: str, writers: list[str], tropes: list[str], cast: list[str], characters: list[str], locations: list[str]):
        self.slug = slug
        self.name = name
        self.writers = writers
        self.tropes = tropes
        self.cast = cast
        self.characters = characters
        self.locations = locations
    
    def get_name(self):
        return self.name

    def get_tropes(self):
        return self.tropes

    def get_slug(self):
        return self.slug

    def get_cast(self):
        return self.cast

    def get_characters(self):
        return self.characters

    def get_locations(self):
        return self.locations

    def get_writers(self):
        return self.writers