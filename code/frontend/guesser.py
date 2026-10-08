from tardis.tardis_types import Story
from frontend.compare_stories import compare_stories, compute_similarity, find_story
from datasets.story_loader import load_stories

class Guess:
    def __init__(self, guessed_story: Story, score: float, shared_attributes):
        self.guessed_story = guessed_story
        self.score = score
        self.shared_attributes = shared_attributes

    def get_guessed_story(self):
        return self.guessed_story

    def get_score(self):
        return self.score

    def get_attributes(self):
        return self.shared_attributes

    def get_name(self):
        return self.guessed_story.get_name()

def guess_story(target: Story):

    stories = load_stories()
    error = True
    while error:
        guess = find_story(stories, input("Enter a story to guess: "))
        if guess is None:
            print("Story not found. Please try again.")
        else:
            error = False
            guess = Guess(guess, 0, None)
    overlapping_attributes = compare_stories(target, guess.get_guessed_story())
    score, attributes = compute_similarity(overlapping_attributes)
    guess.shared_attributes = attributes
    guess.score = score
    return guess