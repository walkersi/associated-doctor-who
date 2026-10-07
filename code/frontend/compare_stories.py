from datasets.story_loader import load_stories
from tardis.tardis_types import Story

def compare_stories(target_story: Story, current_story: Story):
    target_attributes = {"writers": target_story.get_writers()}
    current_attributes = {"writers": current_story.get_writers()}

stories = load_stories()
compare_stories(stories[0], stories[1])