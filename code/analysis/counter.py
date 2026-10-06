from datasets.story_loader import load_stories

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

counter = Counter() 
counter.get_items()
counter.get_count()
print(counter.counts)
