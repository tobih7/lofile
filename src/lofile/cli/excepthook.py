# lool-File Format # CLI # Exception Handler #

import sys


class ExceptHook:
    def __init__(self, dev: bool = False):
        self.dev = dev

    def __call__(self, type_, value, traceback):
        self.type_, self.value, self.traceback = type_, value, traceback

        # init ANSI escape sequences, loolclitools may no be imported yet
        from ctypes import cdll, c_ulong, POINTER

        (kernel32 := cdll.kernel32).GetConsoleMode(
            handle := kernel32.GetStdHandle(c_ulong(-11)),
            mode := POINTER(c_ulong)(c_ulong(int())),
        )
        kernel32.SetConsoleMode(handle, c_ulong(4 | mode.contents.value))
        del cdll, c_ulong, POINTER, kernel32, handle, mode

        sys.stdout.write("\x1b[!p")  # soft reset the terminal
        sys.stdout.flush()

        # some preperation
        from os import get_terminal_size

        vline = (
            "\x1b[91m\x1b(0"
            + "q" * (get_terminal_size().columns - 1)
            + "\x1b(B\x1b[0m\n"
        )

        # KeyboardInterrupt: just exit
        if type_ is KeyboardInterrupt:
            self.pause()
            return

        sys.stdout.flush()
        sys.stdout.write("\x1bc")  # completely reset the terminal
        sys.stdout.flush()

        if type_ is ModuleNotFoundError:
            try:
                from pkg_resources import working_set
            except ModuleNotFoundError:
                pass
            else:
                missing = {"pycryptodome", "loolclitools"}.difference(
                    {pkg.key for pkg in working_set}
                )

                if missing:  # else: proceed below with 'unexpected error'
                    print(
                        "\n  Missing third-party module"
                        + ("s:" if len(missing) > 1 else ":"),
                        ", ".join(missing),
                    )
                    self.pause()
                    return

        if self.dev:
            from io import StringIO

            sys.stderr = StringIO()
            print(
                f"\r{vline}\n  Development-Mode is enabled, "
                "therefore showing unhandled exceptions:\n"
            )
            sys.__excepthook__(type_, value, traceback)
            sys.stderr.seek(0)
            print(
                "  ",
                "\n\n".join(
                    sys.stderr.read().replace("\n", "\n  ").rsplit("\n", 2)[:-1]
                ),
                "\n\n",
                vline,
                "\n\n\n",
                vline,
                "\x1b[4A",
                sep="",
                end="",
                flush=True,
            )
            sys.stderr = sys.__stderr__  # not really required but why not
            self.pause()
            print(end="\n\n\x1b[J", flush=True)

        else:
            print(
                f"\r\x1b[J{vline}\n  An unexpected error occured and lofile crashed!\n\n\n\n{vline}\x1b[5A",
                flush=True,
            )
            self.pause()
            print(end="\n\n\x1b[J", flush=True)

    def pause(self) -> None:
        sys.stdout.write("\n  Press any key to exit . . . ")
        sys.stdout.flush()
        try:
            from msvcrt import kbhit
        except ModuleNotFoundError:  # non win32

            def kbhit():
                return False

        try:
            from loolclitools import getch, InteractiveConsole

            InteractiveConsole.temporary_globals[
                "traceback"
            ] = lambda: sys.__excepthook__(self.type_, self.value, self.traceback)

        except:
            try:
                from msvcrt import getch
            except ModuleNotFoundError:  # non win32
                getch = input

        finally:
            while kbhit():
                getch()  # discard waiting input
            getch()
            print()
