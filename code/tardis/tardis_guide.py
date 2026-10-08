from api.api_connection import API as API
from tardis.tardis_types import *
from api.logger import LOGGER

# workflow:
# construct TardisGuide to connect to API
#  send api requests using object
# call disconnect() once done
#

RANGE_TYPES = ['doctor-who', 'the-worlds-of-doctor-who', 'torchwood', 'bernice-summerfield', 'sarah-jane-adventures', 'class', 'k9', 'faction-paradox', 'blakes-7', 'untempered-whoniverse', 'beyond-the-whoniverse']
MEDIA_TYPES = ['tv', 'audio-drama', 'audiobook', 'book', 'comic', 'short-story', 'movie', 'minisode']

class TardisGuide:
    def __init__(self):
        self.connect()

    def connect(self):
        try:
            self.api = API()
        except Exception as exc:
            LOGGER.fail("Couldn't connect to TardisGuide")
            self.api = None
            raise exc

    def disconnect(self):
        if self.api:
            self.api.close()

    def paginated_get(self, endpoint: str, params: dict):
        params["per_page"] = 20
        params["page"] = 1
        # collated pages
        datas = []

        pages_remain = True
        while pages_remain:
            # request next page
            response = self.api.get(endpoint=endpoint, params=params)
            params["page"] += 1
            pages_remain = params["page"] <= response["meta"]["pagination"]["total_pages"]

            # add the page to the overall collection
            datas += response["data"]

        return datas
        
    # request all stories with specified filters, as shortform jsons (not full story info!)
    def get_all_stories_tldr(self, media_filters: list[str] = None, range_filters: list[str] = None, filters: dict = None) -> list[str]:
        # if no filters were specified, use empty dict
        if not filters:
            filters = {}
        # by default
        if not media_filters:
            media_filters = MEDIA_TYPES # allow all media types
        if not range_filters:
            range_filters = RANGE_TYPES # allow all range types

        # add media and range filters, API wants them comma separated
        filters["media"] = ','.join(media_filters)
        filters["range"] = ','.join(range_filters)

        # get the requested stories from API
        return self.paginated_get("stories", filters)

    # where processor is a function applied to a rich story json to transform it before it is added
    # to the returned list
    def get_all_stories_rich(self, media_filters: list[str] = None, range_filters: list[str] = None, filters: dict = None, processor=lambda s: s):
        # get non-detailed formats
        story_jsons = self.get_all_stories_tldr(media_filters=media_filters, range_filters=range_filters, filters=filters)
        # request each story's detailed format for the average score info
        processed_stories = []
        for story_json in story_jsons:
            # send story api request
            slug = story_json["slug"]
            detailed_json = self.api.get(f"story/{slug}")["data"]
            processed_stories.append(processor(detailed_json))

        return processed_stories

    def get_story_rich(self, story_slug):
        return self.api.get(f"story/{story_slug}")["data"]

    def get_all_writers_with_count(self, media_filters: list[str] = None, range_filters: list[str] = None) -> dict[str]:
        def extract_writer(story_json):
            return ','.join(story_json["writer"])

        all_cowrites = self.get_all_stories_rich(media_filters=media_filters, range_filters=range_filters, processor=extract_writer)
        all_writers = []
        for writers in all_cowrites:
            if ',' in writers:
                extracted_writers = writers.split(',')
                # slice off the end if the writers entry is misformatted
                if extracted_writers[-1] == '':
                    extracted_writers = extracted_writers[:-1]
                # add the writers to the accumulating list
                all_writers += extracted_writers
            elif writers != '':
                # reject no listed writer
                all_writers.append(writers)

        just_writers = list(set(all_writers))
        writers_map = {}
        for writer in just_writers:
            writers_map[writer] = all_writers.count(writer)

        return writers_map

    # uses rich story info to construct application object
    def story_from_json(self, story_json):
        return Story(story_json["slug"], story_json["title"], 
            story_json["writer"], story_json["tropes"], story_json["cast"],
            story_json["characters"], story_json["time_travel"])

    def get_all_stories_by_writer(self, writer: str, media_filters: list[str] = None, range_filters: list[str] = None) -> list[Story]:
        # request each story's detailed format for the average score info
        stories = self.get_all_stories_rich(
            media_filters=media_filters, range_filters=range_filters,
            filters={'writers': writer}, 
            processor=self.story_from_json)
            
        return stories