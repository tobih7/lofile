# lool-File Format # CLI #

import sys
from os import path as ospath
from time import perf_counter

from lofile.core import Encoder, Decoder, __version__
from .loolclitools import InteractiveConsole, Selector, flush, out, pause_and_exit

__all__ = ['main']


def main(*, dev: bool = False):

    # -----=================-----
    #      EXCEPTION HANDLER
    # -----=================-----
    def excepthook(type_, value, traceback):

        # this may not be done yet
        from ctypes import cdll, c_ulong, POINTER
        (kernel32:=cdll.kernel32).GetConsoleMode(handle:=kernel32.GetStdHandle(c_ulong(-11)), mode:=POINTER(c_ulong)(c_ulong(int())))
        kernel32.SetConsoleMode(handle, c_ulong(4 | mode.contents.value))
        del cdll, c_ulong, POINTER, kernel32, handle, mode

        sys.stdout.write("\x1b[!p") # soft reset the terminal
        sys.stdout.flush()

        # preperation
        from os import get_terminal_size
        vline = "\x1b[91m\x1b(0" + "q" * (get_terminal_size().columns - 1) + "\x1b(B\x1b[0m\n"

        def pause():
            print(end="\n  Press any key to exit . . . ", flush=True)
            from msvcrt import kbhit
            try:
                from lofile.cli.loolclitools import getch, InteractiveConsole
                # inject this into the interactive console
                InteractiveConsole.temporary_globals["traceback"] = lambda: sys.__excepthook__(type_, value, traceback)
            except:
                from msvcrt import getch
            finally:
                while kbhit(): getch() # discard waiting input
                getch()
                print()

        # KeyboardInterrupt: just exit
        if type_ is KeyboardInterrupt:
            pause()
            return

        sys.stdout.flush()
        sys.stdout.write("\x1bc") # completely reset the terminal
        sys.stdout.flush()

        if type_ is ModuleNotFoundError:
            # check whether 3rd party modules are not installed
            try:
                from pkg_resources import working_set
            except ModuleNotFoundError:
                pass
            else:
                if not "pycryptodome" in {pkg.key for pkg in working_set}:
                    from msvcrt import getch
                    print("\n  Cannot start lofile due to missing third-party module \"pycryptodome\".")
                    print(end="\n  Do you want to install it? [y/n] ", flush=True)
                    while True:
                        if (c := getch()).lower() == b"y":
                            from subprocess import DEVNULL, call
                            print(end="\n\n  Installing ... ", flush=True)
                            cmd = [sys.executable, "-m", "pip", "install", "pycryptodome"]
                            call(cmd, stdout=DEVNULL, stderr=DEVNULL)
                            try: # check if installation was successfull
                                __import__("Crypto")
                            except ModuleNotFoundError:
                                print("\r  Installation failed!\n  The command which failed is:", " ".join(cmd))
                                pause()
                                return
                            else:
                                print("\r  Installed successfully!")
                                if sys.argv[0].endswith(".exe"):
                                    call(sys.argv)
                                else:
                                    call([sys.executable] + sys.argv)
                                return

                        elif c.lower() == b"n":
                            print("\n\n  Installation skipped.")
                            pause()
                            return

        if dev:
            from io import StringIO
            sys.stderr = StringIO()
            print(f"\r{vline}\n  Development-Mode is enabled, therefore showing unhandled exceptions:\n")
            sys.__excepthook__(type_, value, traceback)
            sys.stderr.seek(0)
            print("  ", "\n\n".join(sys.stderr.read().replace("\n", "\n  ").rsplit("\n", 2)[:-1]), "\n\n", vline, "\n\n\n", vline, "\x1b[4A", sep="", end="", flush=True)
            sys.stderr = sys.__stderr__ # not really required but why not
            pause()
            print(end="\n\n\x1b[J", flush=True)

        else:
            print(f"\r\x1b[J{vline}\n  An unexpected error occured and lofile crashed!\n\n\n\n{vline}\x1b[5A", flush=True)
            pause()
            print(end="\n\n\x1b[J", flush=True)

    sys.excepthook = excepthook


    # -----===========-----
    #      PREPERATION
    # -----===========-----

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
    if len(sys.argv) == 3 and sys.argv[1] == "decode":
        if ospath.exists(sys.argv[2]) and ospath.isfile(sys.argv[2]):
            option = 1
            filepath = sys.argv[2]
        else:
            print("File does not exist!")
            pause_and_exit()
            raise SystemExit(1)

    # print start message
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

