from api.api_exceptions import *
import json

CONFIG_FILE = "api/api-config.json"

# list of existing config rules
RULES = []
INFERRED_RULES = []

# represents a configurable setting
class ConfigField:
    def __init__(self, name: str):
        self.name = name

# represents named json field in config file which takes a value
class Rule(ConfigField):
    def __init__(self, name: str, default = None):
        super().__init__(name)
        self.default = default
        RULES.append(self)

    def get_name(self):
        return self.name

    def required(self):
        return self.default == None

# represents a rule that is calculated from other rules at config load-time
class InferredRule(ConfigField):
    def __init__(self, name: str, calc_function, *dependencies: ConfigField):
        super().__init__(name)
        self.calc_function = calc_function
        self.dependencies = dependencies
        INFERRED_RULES.append(self)

    # assume the correct value and write it into the config, 
    # based on rules already existing in the config
    def infer(self, config):
        # extract the load-time values of the relevant configured settings
        dependency_values = [config.get(field) for field in self.dependencies]
        # call the calculation function to figure out this property's value
        # call as one arg rather than singleton list if applicable
        if len(dependency_values) == 1:
            dependency_values = dependency_values[0]
        value = self.calc_function(dependency_values)
        # add this rule to the config
        config.set(self, value)

# for array configs that apply the same pattern for different rules, 
# e.g. caching times for different endpoints
class Ruleset(Rule):
    def __init__(self, name: str, *children: str, default = None):
        super().__init__(name, default=default)
        self.children = children

    def valid_ruleset_value(self, ruleset_members: list):
        for rule in ruleset_members:
            # all children are required for each entry
            for child in self.children:
                if child not in rule:
                    return False
        return True

class Config:
    API_KEY_FILE = Rule("api_key_file", default="api/api-key.json")
    API_KEY_TYPE = Rule("api_key_type", default="Bearer")
    API_CACHE_FILE = Rule("api_cache_file", default="api/cache/api-cache.csv")
    API_CACHE_DIR = Rule("api_cache_dump", default="api/cache/api")
    # just needs to be a char that doesn't go in URLs or params
    API_CACHE_SEPARATOR_CHAR = Rule("api_cache_separator", default=":")
    LOGGING_MODE = Rule("logger_mode", default="developer")
    
    MAX_REQUESTS_PER_MINUTE = Rule("max_requests_per_minute")
    REQUEST_GAP_SECONDS = InferredRule("request_gap_seconds", lambda rpm: (1/rpm/60), MAX_REQUESTS_PER_MINUTE)
    API_ENDPOINT = Rule("endpoint_root")
    
    BACKOFF_AFTER_429_SECONDS = Rule("backoff_after_429_seconds")
    REQUEST_TIMEOUT_SECONDS = Rule("request_timeout_seconds", default=30)
    REQUEST_CACHE = Ruleset("cache", "endpoint", "expiry_seconds")

    def __init__(self, config_dict):
        # map matching config keywords to their runtime values
        self.rules = {}
        # select rule values based on presence / defaults
        for rule in RULES:
            if rule.name in config_dict:
                self.rules[rule.name] = config_dict[rule.name]
            elif not rule.required():
                self.rules[rule.name] = rule.default
            else:
                raise APIConfigFileInvalid(rule.name + " missing in config file")
        # calculate all the values for the inferred rules
        for rule in INFERRED_RULES:
            rule.infer(self)

    def get(self, property: ConfigField):
        return self.rules[property.name]

    def set(self, property: ConfigField, value):
        self.rules[property.name] = value


def load_config():
    try:
        with open(CONFIG_FILE, "r") as config_json:
            config_dict = json.load(config_json)
            return  Config(config_dict)
            
    except APIConfigFileInvalid as exc:
        raise exc
    except Exception:
        raise APIConfigFileInvalid("Error opening or reading api-config.json")