import json
from api.logger import LOGGER, Level
from api.api_exceptions import APIKeyFileInvalid
from api.api_config import Config

#
# Note: depends on api-key.json file in same directory, containing "id" client id and "secret" client secret
# ALWAYS gitignore this api-key.json file
#
# TLDR:
# store {"id":"....", "secret": "....."} in api-key.json
# make APIKey() object

class APIKey:
    def __init__(self, config: Config):
        # todo improve error structure
        try:
            with open(config.get(Config.API_KEY_FILE)) as key_file:
                key_data = json.load(key_file)
                # check file format
                if not (key_data and key_data["id"] and key_data["secret"]):
                    raise APIKeyFileInvalid("Key file format was invalid")
                # unpack client credentials from file
                self.public_id = key_data["id"]
                self.secret_key = key_data["secret"]
                self.config = config
        except APIKeyFileInvalid as exc:
            raise exc
        except Exception:
            raise APIKeyFileInvalid("Error while opening or reading api-key.json.")

    # as a HTTP header in dict form
    def as_header(self):
        return {"Authorization": f"{self.config.get(Config.API_KEY_TYPE)} {self.secret_key}"}
