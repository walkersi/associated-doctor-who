from datasets.story_loader import load_stories
from tardis.tardis_types import Story, Show
import random

def compare_stories(target_story: Story, current_story: Story, game) -> dict[str, set]:
    # find the attributes for each story, ignoring these
    # note: these should match attrib names in Story
    ignore_fields = ["title", "slug", "show", "cast"]
    # predicate for keeping only comparable fields
    required_only = lambda name, _: name not in ignore_fields
    # get comparable fields
    target_attributes = target_story.get_attribute_subset(predicate=required_only)
    current_attributes = current_story.get_attribute_subset(predicate=required_only)

    # find overlapping values per field
    overlapping_attributes = {"show": compare_show(target_story, current_story, game.shows, game.counts)}
    for key in target_attributes:
        # if one of the stories has a different schema, skip incongruent attributes
        if key not in current_attributes:
            continue
        # extract the set of slugs that this attribute contains
        target_attribute = set(target_attributes[key])
        current_attribute = set(current_attributes[key])
        # set intersection is the overlap
        overlapping_attributes[key] = current_attribute.intersection(target_attribute)
  
    return overlapping_attributes

# find story object by slug
def find_story(stories: list[Story], story_slug: str):
    for story in stories:
        if story.slug == story_slug:
            return story
    return None

def compute_similarity(overlapping_attributes: dict[str, set], counts, shows):
    #print(overlapping_attributes)
    similarity_score = 0
    all_scores = {}
    for key in overlapping_attributes:
        all_scores[key] = []
        for attribute in overlapping_attributes[key]:
            match key:
                # tropes scale faster than other attributes as they tend to be less meaningful
                case "tropes":
                    base = 0.8
                # There are not many time travel options, so it should scale slowly.
                case "time_travel":
                    base = 0.99
                case "show":
                    adding_score = overlapping_attributes[key][attribute]
                case _:
                    base = 0.95
            # the adding score is a base to the power of the number of times an attribute appears across the dataset
            # the more common an attribute is, the less it contributes to the similarity score
            if key != "show":
                adding_score = base ** find_true_count(counts, shows, key, attribute)
            similarity_score += adding_score
            # the attribute and how much of the similarity score it contributed is kept track of, for every attribute per guess
            all_scores[key].append((attribute, adding_score))
    return similarity_score, all_scores

def compare_show(target_story, current_story, shows, counts):

    # if there's only one show, it shouldn't add to the similarity score
    if len(shows) == 1:
        return {"no match": 0}
    else:
        t_show = target_story.show
        c_show = current_story.show 
        # if there's more than one show, check if it's an identical match
        if t_show == c_show:
            return {target_story.show: 0.99 ** counts[t_show]["count"]}
        # if there's exactly two shows and it's not a match, return 0. Similartiy between different shows doesn't matter.
        elif len(shows) == 2:
            return {"no match": 0}
        # after this point, there are more than two shows.
        # if one show is new who and one is classic, return 0.5 as they are both similar in terms of being mainline tv.
        elif set([t_show, c_show]) == set([Show.NEW_WHO, Show.CLASSIC]):
            return {"tv": 0.99 ** (counts[t_show]["count"] + counts[c_show]["count"])}
        # if t_show and c_show are both spinoffs (a "subset" of the spinoff set) then return 0.7 
        elif set([t_show, c_show]).issubset(Show.SPINOFFS):
            spinoff_counts = 0
            for spinoff in Show.SPINOFFS:
                if spinoff in shows:
                    spinoff_counts += counts[spinoff]["count"] 
            return {"spinoff": 0.99 ** spinoff_counts}
        else: 
            return {"no match": 0}

def find_true_count(counts, allowed_shows, key, attribute):
    # add up the count across all shows
    total = 0
    for show in allowed_shows:
        # some writers or characters won't appear in certain shows, so ignore them
        try:
            total += counts[show][key][attribute] 
        except:
            total += 0
    return total

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