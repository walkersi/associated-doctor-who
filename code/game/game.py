from game.player import Player
from datasets.story_loader import load_stories
from tardis.tardis_types import Show

# encapsulating class to store player object and stories once loaded
# because loading the stories from disk every guess is bad
class Game:
    def __init__(self):
        # filter gameplay, e.g. for new who
        self.stories = [s for s in load_stories() if s.show in [Show.NEW_WHO]]
        self.player = Player(self)
                
    def run(self):
        self.player.play_game()

# static reference to the entire game hierarchy
GAME = None

if __name__=="__main__":
    GAME = Game()
    GAME.run()