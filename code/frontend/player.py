from tardis.tardis_types import Story
from datasets.story_loader import load_stories
from frontend.guesser import guess_story
import random

class Player:
    def __init__(self):
        self.points = 20
        self.guesses = []
        self.target = random.choice(load_stories())

    def get_points(self):
        return self.points

    def get_guesses(self):
        return self.guesses

    def add_guess(self, guess):
        self.guesses.append(guess)
    
    def deduct_points(self, points):
        self.points -= points

    def display_score(self):
        print("Similarity score:", self.guesses[-1].get_score())
    
    def guess(self):
        guess = guess_story(self.target)
        self.add_guess(guess)
        self.deduct_points(1)
        self.display_score()

    def take_turn(self):
        print("You have", self.points, "points remaining.")
        self.guess()

    def play_game(self):
        while self.points > 0:
            self.take_turn()
            if self.guesses[-1].get_name() == self.target.get_name():
                print("Congratulations! You guessed the story correctly!")
                break
        if self.points <= 0:
            print("Game over! You've run out of points.")
            print("The correct story was:", self.target.get_name())

player = Player()
player.play_game()