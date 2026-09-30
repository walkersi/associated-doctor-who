from enum import Enum
from api.api_config import Config

# logging level and type enums
Level = Enum('Level', [('INIT', 0), ('ALWAYS', 1), ('DEVELOPER', 2), ('VERBOSE', 3)])
# matched to log headers
Type = Enum('TYPE', [('INFO', '[info]'), ('WARN', '\033[93m[warn]'), ('FAIL', '\033[91m[fail]'), ('SUCCESS', '\033[92m[good]')])

class Logger:
    def __init__(self, type, level):
        self.default_type = type
        self.level = level

    # change this logging level based on config line
    def reconfigure(self, config: Config):
        # allow upper/lower case
        logging_mode = config.get(Config.LOGGING_MODE).upper()
        log_enum_map = Level.__members__
        # update the logging mode if it's valid
        if logging_mode in log_enum_map.keys():
            new_mode = log_enum_map.get(logging_mode)
            self.info("Logger reconfiguring from", self.level, "to", new_mode)
            self.level = new_mode
        else:
            self.warn("Couldn't change logging level from bad config entry.")

    def accepts(self, log_level: Level):
        return log_level.value <= self.level.value

    def log(self, *text, type: Type = None, level: Level = Level.ALWAYS):
        if self.accepts(level):
            print(type.value, end=' ')
            for phrase in text:
                print(phrase, end=' ')
            print("\033[0m") # newline, end colour

    def info(self, *text, level: Level = Level.ALWAYS):
        self.log(*text, type=Type.INFO, level=level)

    def warn(self, *text, level: Level = Level.ALWAYS):
        self.log(*text, type=Type.WARN, level=level)

    def fail(self, *text, level: Level = Level.ALWAYS):
        self.log(*text, type=Type.FAIL, level=level)


LOGGER = Logger(Type.INFO, Level.INIT)