from game.game import Game
from tardis.tardis_types import Show
from game.compare_stories import compute_similarity, compare_stories, find_story
from datasets.serialise import serialise_to_file

game = Game()
all_stories = {}
for story in game.stories:
    target_score, _ = compute_similarity(compare_stories(story, story, game), game.counts, game.shows, game.trope_weights)
    current_story = {}
    for other_story in game.stories:
        similarities = compute_similarity(compare_stories(story, other_story, game),game.counts, game.shows, game.trope_weights)
        score = similarities[0]
        trope_scores = similarities[1]["tropes"]
        current_story[other_story.slug] = {"similarity": (score / target_score) * 100, "tropes": sorted(trope_scores, key=lambda item: item[1], reverse=True)}
    all_stories[story.slug + " (Ranked)"] = dict(sorted(current_story.items(), key=lambda item: item[1]["similarity"], reverse=True))

serialise_to_file(all_stories, "rankings/story_rankings_with_tropes.json", True)

all_stories = {}
for story in game.stories:
    target_score, _ = compute_similarity(compare_stories(story, story, game), game.counts, game.shows, game.trope_weights)
    current_story = {}
    for other_story in game.stories:
        score = compute_similarity(compare_stories(story, other_story, game),game.counts, game.shows, game.trope_weights)[0]
        current_story[other_story.slug] = (score / target_score) * 100
    all_stories[story.slug + " (Ranked)"] = dict(sorted(current_story.items(), key=lambda item: item[1], reverse=True))

serialise_to_file(all_stories, "rankings/story_rankings.json", True)