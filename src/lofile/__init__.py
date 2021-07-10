# lool #

'''
    The lofile package!
'''

__all__ = ['main', 'Encoder', 'Decoder', '__version__', 'LofileError']

from .core import Encoder, Decoder, __version__, LofileError

def main(*, dev: bool = False):
    from .cli import main
    main(dev=dev)
