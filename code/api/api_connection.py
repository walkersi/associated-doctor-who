import requests
from datetime import datetime, timedelta
from time import sleep
from api.logger import LOGGER, Level
from api.api_locker import APIKey
from api.api_cache import APICache
from api.api_exceptions import *
from api.api_config import *

class Backoff:
    def __init__(self, wait_seconds: float):
        # backoff until given time elapsed
        self.until = datetime.now() + timedelta(milliseconds=(wait_seconds*1000))

    # returns remaining time in seconds
    def remaining_seconds(self):
        return max(0, (self.until - datetime.now()).total_seconds())

    # sleeps calling thread until this backoff has elapsed
    def wait_for(self):
        remaining = self.remaining_seconds()
        if remaining:
            sleep(remaining)

    # returns true if this duration has elapsed
    def elapsed(self):
        return datetime.now() > self.until

# represents an API request to lookup
class APIRequest:
    def __init__(self, endpoint: str, parameters: dict = None, obey_rate_limit: bool = True):
        self.endpoint = endpoint
        self.parameters = {} if not parameters else parameters
        self.obey_rate_limit = True

    def get_normalised_endpoint(self, config):
            # get configured api endpoint root
            root = config.get(Config.API_ENDPOINT)
    
            # slice off leading path "/"
            if self.endpoint[0] == "/":
                self.endpoint = self.endpoint[1:]
            # allow inclusion of API endpoint already present
            if self.endpoint.startswith(root):
                return self.endpoint
            elif ":" in self.endpoint:
                # but reject any other endpoint (regardless of protocol)
                raise APIEndpointRejectedException("Endpoint " + self.endpoint + " is not allowed.")
    
            return root + self.endpoint

    def get_endpoint(self):
        return self.endpoint

    def get_parameters(self):
        return self.parameters

    def obeys_rate_limit(self):
        return self.obey_rate_limit


class APIConnection:
    def __init__(self):
        # to pace API requests so that minute-rates are not exceeded
        self.timings_backoff = None
        self.hard_limit_backoff = None
        # load the config file into an object and do validation
        self.config = load_config()
        # switch the logger to the configured mode
        LOGGER.reconfigure(self.config)
        # load the API key from external json
        self.key = APIKey(self.config)
        # load the api cache
        self.cache = APICache(self.config)
        # when returning a 200 from the API, this (optional) config value is
        # used to grab a field from the response to use as the actual data (i.e. to ignore metadata)
        self.automatic_subfield = self.config.get(Config.API_AUTOMATIC_SUBFIELD)

    # returns true if/when ready for request
    def rate_wait(self):
        if self.hard_limit_backoff:
            # currently backing off, don't send request
            if not self.hard_limit_backoff.elapsed():
                return False
            # clear any backoff and continue
            self.hard_limit_backoff = None
        
        # wait the normal gap if needed
        if self.timings_backoff:
            self.timings_backoff.wait_for()

        self.timings_backoff = Backoff(self.config.get(Config.REQUEST_GAP_SECONDS))

        return True

    #
    # send an API query to tardis guide. returns None if limited or error
    # (i.e. to respond to rate limit requirements) if rate_limit == True
    # Blocks until safe to send request
    #
    # where endpoint is WITHIN the api, e.g. "stories"
    # raises: APIEndpointRejectedException if supplied bad endpoint
    # APIRateLimitedException if response contains 429
    # 
    def get(self, request: APIRequest):

        
        # unpack API request details
        endpoint = request.get_endpoint()
        params = request.get_parameters()
        obeys_rate_limit = request.obeys_rate_limit()
        
        # check the cache
        cached_response = self.cache.get_cached_response(endpoint, params)
        if cached_response:
            LOGGER.info('Cache hit for', endpoint, level=Level.VERBOSE)   
            return cached_response

        # apply rate limit
        if obeys_rate_limit:
            LOGGER.info("API waiting for client-throttle rate limit", level=Level.VERBOSE)
            if not self.rate_wait():
                return None

        # send API request to tardisguide
        LOGGER.info('Sending API request at', datetime.now(), 'to', endpoint, level=Level.DEVELOPER)
        LOGGER.info('Request with params', params, level=Level.VERBOSE)    
        response = requests.get(request.get_normalised_endpoint(self.config), 
                                headers=self.key.as_header(), params=params, 
                                timeout=self.config.get(Config.REQUEST_TIMEOUT_SECONDS))
        LOGGER.info('Received API Response at', datetime.now(), 'from', endpoint, level=Level.VERBOSE)
        
        # check response for 429 rate limiting error
        if response.status_code == 429:
            self.hard_limit_backoff = Backoff(self.config.get(Config.BACKOFF_AFTER_429_SECONDS))
            raise APIRateLimitedException("429 received; API Key is rate limited. Waiting...", 429)

        # return response
        elif response.status_code == 200:
            # extract response data
            api_response = response.json()
            if self.automatic_subfield:
                # remove metadata if necessary
                api_response = api_response[self.automatic_subfield]
            # cache it then return
            self.cache.add_entry(endpoint, params, response.text)
            return api_response
        elif response.status_code >= 400:
            # raise general error
            raise APIResponseException(f"Error code {response.status_code} received from server.", response.status_code, endpoint, params, response.json())

        # no response or error found
        return None

    # please for the love of god remember to call this
    def close(self):
        # save the cache file
        if self.cache:
            self.cache.close()