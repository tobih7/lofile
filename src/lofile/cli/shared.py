# lool-File Format # CLI # shared components #

__all__ = ["DataOrigin", "logger"]

from enum import Enum
from loolclitools import out
from lofile.core.shared import LogLvl

# ===  CONSTANTS  === #
LJUST = 15


class DataOrigin(Enum):
    File = 0
    NotepadInput = 1
    ConsoleInput = 2


# colorized logger
def logger(msg: str, lvl: LogLvl):
    if lvl is LogLvl.INFO:
        out("\r\x1b[K  \x1b[93m", msg.capitalize(), " ... \x1b[0m")
    elif lvl is LogLvl.WARN:
        out("\r\x1b[K  \x1b[0mWarning: \x1b[91m", msg.capitalize(), "! \x1b[0m\n")
    elif lvl is LogLvl.ERROR:
        out("\r\x1b[K  \x1b[0mError: \x1b[91m", msg.capitalize(), "! \x1b[0m\n")
