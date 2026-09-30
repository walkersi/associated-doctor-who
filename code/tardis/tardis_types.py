# application-relevant representation of storys from tardisguide database
class Story:

    def __init__(self, name: str, writers: list[str], tropes: list[str], cast: list[str]):
        self.name = name
        self.writers = writers
        self.tropes = tropes
        self.cast = cast
    
    def get_name(self):
        return self.name
    
    def get_writers(self):
        return self.writers