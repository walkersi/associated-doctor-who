from api.api_config import Config
from api.logger import LOGGER, Level
import re, hashlib, csv, json, os
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

# json dictionary keys
ENTRY_ENDPOINT = "endpoint" # where endpoint is a regex
ENTRY_EXPIRY_SECONDS = "expiry_seconds"

# defines rules for and methods to cache and invalidate values
# where the cached values are strings
class APICache:

    @dataclass
    class EntryValue:
        file: str
        expires: datetime

    def __init__(self, config: Config):
        # get the ordered list for caching endpoints
        self.cache_config = config.get(Config.REQUEST_CACHE)
        # get the name of the main cache file
        self.cache_file = config.get(Config.API_CACHE_FILE)
        # get the name of the directory where the api responses will cache
        self.cache_directory = config.get(Config.API_CACHE_DIR) + "/"

        # create the empty cache structure
        Path(self.cache_directory).mkdir(parents=True, exist_ok=True)

        # get the cache line separator character from the config
        self.separator_char = config.get(Config.API_CACHE_SEPARATOR_CHAR)
        # map (endpoint:params) to (file, expiry_datetime)
        self.cache: dict[str, APICache.EntryValue] = {}
        # load the cache from the file
        self.load_cache(self.cache_file)

    # call when done!!!
    def close(self):
        self.save_cache(self.cache_file)

    # figure out how long this given endpoint should be cached for
    def determine_cache_rule(self, endpoint):
        for entry in self.cache_config:
            endpoint_regex = entry[ENTRY_ENDPOINT]
            # check for endpoint match
            if re.search(endpoint_regex, endpoint):
                expiry_time = entry[ENTRY_EXPIRY_SECONDS]
                if expiry_time == 0:
                    # if listed in config as 0, specifically do not cache this endpoint
                    return None
                elif expiry_time == -1:
                    # -1 means cache indefinitely (arbitrarily long)
                    return 2147483647 # 68 years
                return expiry_time
        return None # no caching of this entry

    # adds given response to cache, overwriting any preexisting value
    # returns True if cached (this endpoint is cacheable), False otherwise
    def add_entry(self, endpoint: str, params: dict, response: str):
        # find the cache expiry rule for the given endpoint
        expiry_seconds = self.determine_cache_rule(endpoint)
        if not expiry_seconds:
            # caching is not enabled for this endpoint
            return False
        # create the cache key
        entry_key = self.to_entry_string(endpoint, params)
        # get a hash string for the filename of this cache entry
        hasher = hashlib.sha1()
        hasher.update(entry_key.encode())
        file_name = hasher.hexdigest()
        # figure out the timestamp for invalidation
        expires_at = datetime.now() + timedelta(seconds=expiry_seconds)
        # write to in-memory cache
        self.cache[entry_key] = APICache.EntryValue(file_name, expires_at)
        # and create the cached response
        with open(self.cache_directory + file_name, "w+") as cache_entry:
            cache_entry.write(response)

        return True

    # remove entry if it is expired (note: ASSUMES IT EXISTS)
    # returns true if entry still valid
    def validate(self, entry_key: str):
        if self.cache[entry_key].expires <= datetime.now():
            # remove the entry and the file, it's out of date
            del self.cache[entry_key]
            self.delete_if_exists(self.cache_directory + entry_key)
            LOGGER.info(f"Dropped expired cache entry {entry_key}", level=Level.VERBOSE)
            return False
        return True

    # check cache for an up-to-date entry with given endpoint and params
    # return the value of the entry, or none
    # will remove an expired entry if found
    def check_for_entry(self, endpoint: str, params: dict = None):
        entry_key = self.to_entry_string(endpoint, params)
        if entry_key in self.cache:
            if self.validate(entry_key):
                return self.cache[entry_key]
        return None

    # returns the cached response to an endpoint/param API lookup, if it exists
    def get_cached_response(self, endpoint: str, params: dict = None):
        entry = self.check_for_entry(endpoint, params)
        if entry == None:
            # not in cache
            return None

        # TODO security of this cache - what if external file tampered with?
        # check for external cache file
        try:
            with open(self.cache_directory + entry.file, "r") as cache_entry:
                # read as json object
                return json.load(cache_entry)
        except FileNotFoundError:
            # file has been deleted externally
            LOGGER.warn("Dropped API Cache entry due to external deletion: endpoint", 
                        endpoint, "file", entry.file, level=Level.DEVELOPER)
            # so delete from the main cache file
            del self.cache[self.to_entry_string(endpoint, params)]
            # and return no entry found
            return None

    # convert combination of request endpoint and parameters to single consistent string
    def to_entry_string(self, endpoint: str, params: dict):
        if params:
            # separate each parameter out into a consistent order
            sep = self.separator_char
            param_string = sep.join([str(q) + sep + str(a) for q, a in sorted(params.items())])
            return endpoint + sep + param_string
        # no params so no separator needed
        return endpoint

    # remove any expired entries in the cache (warning: time consuming!)
    def remove_expired(self):
        now = datetime.now()
        for key, value in self.cache.items():
            if value.expires <= now:
                del self.cache[key]

    def load_cache(self, cache_file):

        LOGGER.info("Loading cache from", cache_file, level=Level.DEVELOPER)
        # create the cache file if this is the first run or it got deleted
        if not self.create_if_not_exists(cache_file):
            return

        # timestamp to check for expiry
        now = datetime.now()
        # read the main cache map csv
        with open(cache_file, "r+", newline='') as main_cache:
            entry_reader = csv.reader(main_cache)
            for entry in entry_reader:
                # extract this line and convert data types
                endpoint_params, file_name, expiry = entry
                expiry = datetime.fromisoformat(expiry)
                # add to in-memory cache
                self.cache[endpoint_params] = APICache.EntryValue(file_name, expiry)
                # drop and delete expired entries
                self.validate(endpoint_params)

    def save_cache(self, cache_file):
        LOGGER.info("Saving cache to", cache_file, level=Level.DEVELOPER)
        # rewrite the main cache map csv
        with open(cache_file, "w+", newline='') as main_cache:
            entry_writer = csv.writer(main_cache)
            for endpoint_params, value in self.cache.items():
                # convert to string to write
                file_name = value.file
                expiry = value.expires.isoformat()
                # add to cache file
                entry_writer.writerow([endpoint_params, file_name, expiry])
        

    # creates given file if it does not exist in filesystem
    # returns True if file already existed, false otherwise
    def create_if_not_exists(self, cache_file):
        # create the given file iff it does not already exist
        try:
            with open(cache_file):
                return True
        except FileNotFoundError:
            with open(cache_file, "w+", newline=''):
                return False

    def delete_if_exists(self, cache_file):
        if os.path.exists(cache_file):
            # if the file exists, remove it
            os.remove(cache_file)
            return True
        return False