from datasets.story_loader import load_stories

OUTPUT_PATH = "analysis/counts/"
SCHEMA_VERSION = "_v1.0.0"

class Counter:
    def __init__(self):
        self.stories = load_stories()
        self.attributes = {"location": [], "trope": [], "writer": [], "character": []}
        self.counts = {"location": {}, "trope": {}, "writer": {}, "character": {}}

    def get_items(self):

        for story in self.stories:
            for character in story.characters:
                self.attributes["character"].append(character)
            for trope in story.tropes:
                self.attributes["trope"].append(trope)
            for writer in story.writers:
                self.attributes["writer"].append(writer)
            for location in story.locations:
                self.attributes["location"].append(location)

    def get_count(self):
        for category, items in self.attributes.items():
            for item in items:
                if item not in self.counts[category]:
                    self.counts[category][item] = 1
                else:
                    self.counts[category][item] += 1

    def create_file(self, filename, category):
        with open(OUTPUT_PATH + filename + SCHEMA_VERSION + ".txt", "w") as f:
            for item, count in self.counts[category].items():
                f.write(f"  {item}: {count}\n")

def main():
    counter = Counter() 
    counter.get_items()
    counter.get_count()
    counter.create_file("location_counts", "location")
    counter.create_file("trope_counts", "trope")
    counter.create_file("writer_counts", "writer")
    counter.create_file("character_counts", "character")

main()