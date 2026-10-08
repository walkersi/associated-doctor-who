from tardis.tardis_types import Story
from frontend.compare_stories import compare_stories, compute_similarity, find_story
from datasets.story_loader import load_stories
import random

def guess_story(target: Story):

    best_score = 0
    best_guess = None
    stories = load_stories()
    guess = None
    while guess is None or guess.get_name() != target.get_name():
        error = True
        while error:
            guess = find_story(stories, input("Enter a story to guess: "))
            if guess is None:
                print("Story not found. Please try again.")
            else:
                error = False
        overlapping_attributes = compare_stories(target, guess)
        score, best_attribute = compute_similarity(overlapping_attributes)
        print("Similarity score:", score)
    print("You guessed the story!")

guess_story(random.choice(load_stories()))