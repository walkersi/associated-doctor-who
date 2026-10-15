import requests
from datetime import datetime, timedelta
from time import sleep, monotonic
from api.logger import LOGGER, Level
from api.api_locker import APIKey
from api.api_cache import APICache
from api.api_exceptions import *
from api.api_config import *
from datasets.serialise import serialise
import asyncio


# imposes rate limit and 429-backoff synchronised across
# concurrent requests
class RateLimit:
    def __init__(self, config: Config):
        self.interval = config.get(Config.REQUEST_GAP_SECONDS)
        self.backoff_after_429 = config.get(Config.BACKOFF_AFTER_429_SECONDS)
        self.next_allowed = 0.0
        # prevent two requests from firing in same interval
        self.lock = asyncio.Lock()

    async def wait_for(self):
        async with self.lock:
            delay = self.next_allowed - monotonic()

            # sleep to apply limit
            if delay > 0:
                await asyncio.sleep(delay)

            # schedule next request from now
            self.next_allowed = monotonic() + self.interval

    # call when a 429 is received: imposes a large, hard backoff on subsequent gets
    def hard_backoff(self):
        self.next_allowed = monotonic() + self.backoff_after_429
        

# represents an API request to lookup
class APIRequest:
    # endpoint is *within* the API, e.g. story/the-unquiet-dead
    # bundled data is just arbitrary data that is useful for passing ahead to later 
    # processing steps in batched calls
    def __init__(self, endpoint: str, parameters: dict = None, bundled_data = None):
        self.endpoint = endpoint
        self.parameters = {} if not parameters else parameters
        self.bundled_data = bundled_data
        # used in asynchronous operations to retrieve a return value easily
        self.response = None

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

    def get_bundled_data(self):
        return self.bundled_data


class APIConnection:
    def __init__(self):
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

        # open a session for persistent HTTP (no handshaking)
        self.session = requests.Session()
        # add the authorisation key as a default header
        self.session.headers.update(self.key.as_header())

        # limit concurrent workers
        self.semaphore = asyncio.Semaphore(self.config.get(Config.MAX_REQUESTS_IN_FLIGHT))
        # limit rate
        self.rate_limit = RateLimit(self.config)

        # logging is important :)
        LOGGER.info(f"Rate limit configured to {self.config.get(Config.REQUEST_GAP_SECONDS)}s gap", level=Level.DEVELOPER)

    # returns true if the requests exists in the API cache (and is valid)
    # note: this therefore validates any corresponding entry and may drop it
    def request_exists_in_cache(self, request: APIRequest):
        return self.cache.check_for_entry_without_validating(
            request.get_endpoint(), request.get_parameters())

    #
    # send an API query to tardis guide. returns None if limited or error
    # (i.e. to respond to rate limit requirements) if rate_limit == True
    #
    # where endpoint is WITHIN the api, e.g. "stories"
    # raises: APIEndpointRejectedException if supplied bad endpoint
    # APIRateLimitedException if response contains 429
    # 

    # send a request (allowing for synchronised rate limiting)
    # returns the request context with the response field populated by the API response
    async def get(self, request: APIRequest) -> APIRequest:
        # check cache for response and return it
        cached_response = self.cache.get_cached_response(
            request.get_endpoint(), request.get_parameters())
        if cached_response:
            LOGGER.info('Cache hit for', request.get_endpoint(), level=Level.VERBOSE)
            request.response = cached_response
            return request
        
        # wait until there are not more than [n] packets
        # in flight, and the rate limit delay has been observed
        async with self.semaphore:
            await self.rate_limit.wait_for()
            # send the API request
            return await self.send_api_request(request)

    # send many requests as fast as possible whilst within rate limit
    async def get_many(self, requests: list[APIRequest]) -> list[APIRequest]:
        return await asyncio.gather(
            *(self.get(request) for request in requests))


    async def send_api_request(self, request: APIRequest) -> APIRequest:
        # unpack API request details
        endpoint = request.get_endpoint()
        params = request.get_parameters()
        
        # send API request to (tardisguide)
        LOGGER.info('Sending API request at', datetime.now(), 'to', endpoint, level=Level.DEVELOPER)
        LOGGER.info('Request with params', params, level=Level.VERBOSE)
        
        # send concurrently
        response = await asyncio.to_thread(
            self.send_http_request, request.get_normalised_endpoint(self.config), params
        )
        LOGGER.info('Received API Response at', datetime.now(), 'from', endpoint, level=Level.VERBOSE)
        
        # check response for 429 rate limiting error
        if response.status_code == 429:
            self.rate_limit.hard_backoff()
            LOGGER.warn(f"Received 429 from API when endpoint={endpoint}, details:" +   
                f"headers={dict(response.headers)}; " +
                f"body={response.text}", level=Level.ALWAYS)
            raise APIRateLimitedException("429 received; API Key is rate limited. Waiting...", 429)

        # return response
        elif response.status_code == 200:
            # extract response data
            api_response = response.json()
            if self.automatic_subfield:
                # remove metadata if necessary
                api_response = api_response[self.automatic_subfield]
            # cache it
            self.cache.add_entry(endpoint, params, serialise(api_response))
            # store in the request for asynchronous access then return
            request.response = api_response
            return request
        elif response.status_code >= 400:
            # raise general error
            raise APIResponseException(f"Error code {response.status_code} received from server.", response.status_code, endpoint, params, response.json())

        # no response or error found
        return None

    def send_http_request(self, target: str, params: dict):
        return self.session.get(
            target,
            params=params, 
            timeout=self.config.get(Config.REQUEST_TIMEOUT_SECONDS))

    # please for the love of god remember to call this
    def close(self):
        # save the cache file
        if self.cache:
            self.cache.close()
        # close the persistent HTTP session
        if self.session:
            self.session.close()