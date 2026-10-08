from datasets.story_loader import load_stories
from tardis.tardis_types import Story
from analysis.counter import NamedLookup
from analysis.read_counts import load_counts
import math
import random

def compare_stories(target_story: Story, current_story: Story):
    # find the attributes for each story
    counting_attributes = [
        NamedLookup("name", lambda s: s.get_name()),
        NamedLookup("locations", lambda s: s.get_locations()),
        NamedLookup("tropes", lambda s: s.get_tropes()),
        NamedLookup("characters", lambda s: s.get_characters()),
        NamedLookup("writers", lambda s: s.get_writers()),
    ]
    target_attributes = get_attributes(target_story, counting_attributes)
    current_attributes = get_attributes(current_story, counting_attributes)

    # find overlapping attributes
    overlapping_attributes = {}
    for key in target_attributes:
        if key != "name": # we don't care about name overlapping
            overlapping_attributes[key] = []
            if key in current_attributes:
                for attribute in target_attributes[key]:
                    if attribute in current_attributes[key]:
                        overlapping_attributes[key].append(attribute)
    return overlapping_attributes

def get_attributes(story: Story, counting_attributes: list[NamedLookup]):
    attributes = {}
    for getter in counting_attributes:
        attributes[getter.name] = getter.get(story)
    return attributes

# find story object by slug
def find_story(stories: list[Story], story_slug: str):
    for story in stories:
        if story.slug == story_slug:
            return story
    return None

def compute_similarity(overlapping_attributes):
    #print(overlapping_attributes)
    counts = load_counts()
    similarity_score = 0
    highest_score = (None, 0)
    for key in overlapping_attributes:
        for attribute in overlapping_attributes[key]:
            # the more common an attribute is, the less it contributes to the similarity score
            # tropes scale faster than other attributes as they tend to be less meaningful
            if key == "trope": 
                base = 0.8
            else:
                base = 0.95
                adding_score = base ** counts[key][attribute]
            similarity_score += adding_score
            if adding_score > highest_score[1]:
                highest_score = (attribute, adding_score)
    return similarity_score, highest_score

def compare_random_stories():
    stories = load_stories()
    story1 = random.choice(stories)
    story2 = random.choice(stories)
    #print(story1.get_name(), "vs", story2.get_name())
    #print(compute_similarity(compare_stories(story1, story2)))
    return story1, story2, compute_similarity(compare_stories(story1, story2))[0]

def find_algorithm_stats():
    highest = 0
    average = 0
    total = 0
    highest_stories = [None, None]
    for i in range(1000):
        story1, story2, similarity_score = compare_random_stories()
        if story1 != story2: # make sure it isn't just the same story being compared to itself
            if similarity_score > highest:
                highest = similarity_score
                highest_stories = [story1, story2]
            average += similarity_score
            total += 1
    print("Stories:", highest_stories[0].get_name(), "vs", highest_stories[1].get_name())
    print("Average similarity score:", average / total)
    print("Highest similarity score:", highest)