# lool-File Format # CLI Encoder #

from loolclitools import out

from lofile.core import Encoder
from lofile.core.shared import DataType, LofileError

from .metadata import Metadata
from .data import Data


class encode(Encoder, Metadata, Data):
    def __init__(self):
        super().__init__()
        self.datatype = DataType.Raw
        self.dataorigin = None
        self.data = None

        try:

            # first ask for data
            self.askdata()

            # next ask for meta data
            self.askmetadata()

            # last ask for save location
            ...

        except LofileError as err:
            out("\r\x1b[K  \x1b[0mError: \x1b[91m", str(err).capitalize(), "! \x1b[0m\n")
