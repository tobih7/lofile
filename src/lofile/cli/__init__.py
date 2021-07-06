# lool-File Format # CLI #

from sys import argv
from os import path as ospath
from time import perf_counter

from lofile.core import Encoder, Decoder, __version__
from .loolclitools import InteractiveConsole, Selector, flush, out, pause_and_exit


def main():

    # inject some permanent globals to potential interactive consoles
    InteractiveConsole.permanent_globals.update(
        Encoder=Encoder,
        Decoder=Decoder,
        __version__=__version__,
        startup_duration=perf_counter()
    )

    # already defined here because of command line argument support
    option = None
    filepath = None

    # parse command line arguments
    if len(argv) == 3 and argv[1] == "decode":
        if ospath.exists(argv[2]) and ospath.isfile(argv[2]):
            option = 1
            filepath = argv[2]
        else:
            print("File does not exist!")
            pause_and_exit()
            raise SystemExit(1)

    # print start message
    flush()
    out(f"\x1bc\x1b[H\x1b[J\x1b[2;3H\x1b[94mlofile CLI \x1b[90m[v{__version__}]\x1b[0m\x1b[4H")
    flush()

    # ask for option of not determinable by command line arguments
    try:

        if option == None:
            option = Selector(("encode", "decode", None, "more", "exit"), print_result=False)

        if option == 0: # encode
            from .encode import encode
            encode()

        elif option == 1: # decode
            from .decode import decode
            decode(filepath)

        elif option == 2: # more
            s = Selector(("install lofile", "uninstall lofile", "exit"), print_result=False)
            if s == 0: # install
                from .install import installer
                installer()
            elif s == 1: # uninstall
                from .install import uninstaller
                uninstaller()
            elif s == 2: # exit
                raise SystemExit

        elif option == 3: # exit
            raise SystemExit

        pause_and_exit()



    except KeyboardInterrupt:
        out("\x1b[91m\x1b[2CCanceled by user!\x1b[0m\n")
        raise KeyboardInterrupt
