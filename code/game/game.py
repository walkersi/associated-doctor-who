from game.guesser import guess_story
import random
from datasets.story_loader import load_stories
from tardis.tardis_types import Show
from game.compare_stories import compute_similarity, compare_stories
from game.guesser import Guess
from analysis.read_counts import load_counts

class Game:
    def __init__(self):
        self.points = 100
        self.guesses = []
        self.counts = load_counts()
        self.most_recent_guess = None
        self.shows = [Show.NEW_WHO, Show. CLASSIC]
        self.stories = [s for s in load_stories() if s.show in self.shows]
        self.already_hinted = []
        self.target = random.choice(self.stories)
        self.target_score = compute_similarity(compare_stories(self.target, self.target), self.counts, self.shows)[0]

    def get_points(self):
        return self.points

    def get_guesses(self):
        return self.guesses

    def add_guess(self, guess: Guess):
        # if it's the first guess, just add it to the list
        if self.guesses == []:
            self.guesses.append(guess)
        else:
            # insert the guess into the list, sorted based on score (descending order)
            count = 0
            for g in self.guesses:
                if guess.get_score() > g.get_score():
                    break
                count += 1
            self.guesses.insert(count, guess)
        self.most_recent_guess = guess
    
    def deduct_points(self, points):
        self.points -= points

    def display_score(self):
        percentage_score = self.most_recent_guess.get_score() / self.target_score * 100
        print("Similarity score:", percentage_score)

    def hint(self):
        selection = input("Which guess do you want a hint about? 1. Your closest guess 2. Your 2nd closest guess etc. To go back, type anything else. ")
        # if the selection is a number between 1 and the amount of guesses made, call hint_guess
        if selection.isnumeric() and int(selection) > 0 and int(selection) < len(self.guesses) + 1:
            self.hint_guess(self.guesses[int(selection) - 1])
            self.deduct_points(3)
        # otherwise go back to taking your turn
        else: 
            self.take_turn()

    def hint_guess(self, guess: Guess):
        highest = ("", "", 0)
        attributes = guess.get_attributes()
        # find the shared attribute with the highest score 
        for key in attributes:
            for attribute in attributes[key]:
                if attribute[1] > highest[2] and attribute[0] not in self.already_hinted:
                    # save the key (like "Character"), the specific attribute (like "Clara Oswald") and the score.
                    highest = (key, attribute[0], attribute[1])
        if highest[2] == 0:
            print(f"There are no similarities (that you haven't already hinted) between {guess.get_name()} and the target story!")
        else:
            print(f"{highest[0]}: {highest[1]} is the most unique feature (that you haven't already hinted) shared by {guess.get_name()} and the target story!")
            self.already_hinted.append(highest[1])

    
    def guess(self):
        guess = guess_story(self.target, self)
        self.add_guess(guess)
        self.deduct_points(1)
        self.display_score()

    def take_turn(self):
        print("You have", self.points, "points remaining.")
        selection = ""
        while selection not in ["1", "2"]:
            selection = input("1. Guess or 2. Hint? ")
            if selection == "1":
                self.guess()
            elif selection == "2":
                self.hint()
            else:
                print("Invalid selection.")

    def play_game(self):
        while self.points > 0:
            self.take_turn()
            if self.most_recent_guess.get_name() == self.target.title:
                print("Congratulations! You guessed the story correctly!")
                break
        if self.points <= 0:
            print("Game over! You've run out of points.")
            print("The correct story was:", self.target.title)
            

game = Game()
game.play_game()