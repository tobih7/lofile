# lool-File Format # CLI #

import sys
from os import path as ospath
from time import perf_counter

from .excepthook import ExceptHook
from lofile.core import Encoder, Decoder, __version__
from loolclitools import InteractiveConsole, Selector, flush, out, pause

__all__ = ["main"]


def main(*, dev: bool = False):

    # -----===========-----
    #      PREPERATION
    # -----===========-----

    sys.excepthook = ExceptHook(dev=dev)

    # inject some permanent globals to potential interactive consoles
    InteractiveConsole.permanent_globals.update(
        Encoder=Encoder,
        Decoder=Decoder,
        __version__=__version__,
        startup_duration=perf_counter(),
    )

    # already defined here because of command line argument support
    option = None
    filepath = None

    # parse command line arguments
    if len(sys.argv) == 3 and sys.argv[1] == "decode":
        if ospath.exists(sys.argv[2]) and ospath.isfile(sys.argv[2]):
            option = 1
            filepath = sys.argv[2]
        else:
            print("File does not exist!")
            pause()
            raise SystemExit(1)

    # print start message
    out(
        "\x1bc\x1b[H\x1b[J\x1b[2;3H\x1b[94m"
        f"lofile CLI \x1b[90m[v{__version__}]\x1b[0m\x1b[4H"
    )
    flush()

    # ask for option of not determinable by command line arguments
    try:

        if option == None:
            option = Selector(
                ("encode", "decode", None, "more", "exit"), print_result=False
            )

        if option == 0:  # encode
            from .encode import encode

            encode()

        elif option == 1:  # decode
            from .decode import decode

            # decode(filepath)
            raise NotImplementedError

        elif option == 2:  # more
            s = Selector(
                ("install lofile", "uninstall lofile", "exit"), print_result=False
            )
            if s == 0:  # install
                from .install import installer

                installer()
            elif s == 1:  # uninstall
                from .install import uninstaller

                uninstaller()
            elif s == 2:  # exit
                raise SystemExit

        elif option == 3:  # exit
            raise SystemExit

        pause()

    except KeyboardInterrupt:
        out("\x1b[91m\x1b[2CCanceled by user!\x1b[0m\n")
        raise KeyboardInterrupt
