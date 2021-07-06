# lool # lool-File Format #

#region ===  EXCEPTION HANDLER  ===
import sys
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

    if "--dev" in sys.argv:
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
#endregion

if __name__ == "__main__":
    from .cli import main
    main()
