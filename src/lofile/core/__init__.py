# lool # lool-File Format #

'''

    lool-File Format

    started: Q2 20

'''

__version__ = '1.0'

__all__ = ['Encoder', 'Decoder', '__version__', 'LofileError']

from lofile.core._encoder import Encoder
from lofile.core._decoder import Decoder
from lofile.core.shared import LofileError
