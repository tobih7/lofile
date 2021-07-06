# lool CLI Tools #

__version__ = "1.2.3" # last edit: 22.03.2021

__all__ = ["enable_ANSI_esc_seq", "getch", "CursorPosition", "get_cursor_position", "out", "flush",
           "yesno", "param", "vline", "Selector", "askinput", "askpath", "console_input", "notepad_input",
           "pause_and_exit", "Timer", "InteractiveConsole"]

import sys
import os
from io import BufferedReader
from getpass import getpass
from time import perf_counter
from codeop import CommandCompiler
from pprint import pprint
from msvcrt import getch as _getch, kbhit
from typing import Any, List, NamedTuple, Optional



# ===  CONSTANTS  === #
NOTEPAD_PATH = os.path.join(os.getenv("windir"), "System32", "notepad.exe")



# ===  INITIALIZATION FUNCTION  === #
def enable_ANSI_esc_seq() -> None:
    from ctypes import cdll, c_ulong, POINTER
    kernel32 = cdll.kernel32
    handle = kernel32.GetStdHandle(c_ulong(-11))
    mode = POINTER(c_ulong)(c_ulong(0))
    kernel32.GetConsoleMode(handle, mode)
    kernel32.SetConsoleMode(handle, c_ulong(4 | mode.contents.value))

enable_ANSI_esc_seq()



# ===  MODIFIED GETCH  === #
def getch() -> bytes:
    """just like msvcrt.getch but CTRL+I + CTRL+C will open an interactive console"""
    char = _getch()
    if char == b"\x09" and _getch() == b"\x03": # CTRL + I and CTRL + C
        InteractiveConsole()
    else:
        InteractiveConsole.temporary_globals.clear()
    return char


# ===  CURSOR POSITION  === #
class CursorPosition(NamedTuple):
    x: int
    y: int
    def apply(self):
        out(f"\x1b[{self.y};{self.x}H")
def get_cursor_position() -> CursorPosition:
    data = []
    print(end="\x1b[6n", flush=True)
    while (char := _getch()) != b"R":
        if not char in (b"\x1b", b"["):
            data.append(char)
    return CursorPosition(*map(int, reversed(b"".join(data).split(b";"))))


# ===  OUTPUT FUNCTIONS  === #
def out(*text: Any, sep: str = "", flush: bool = False) -> None:
    sys.stdout.write(sep.join(map(str, text)))
    if flush:
        sys.stdout.flush()
def flush() -> None:
    sys.stdout.flush()


# ===  ADVANCED OUTPUT  === #
def yesno(obj: object) -> str:
    return "Yes" if obj else "No"

def param(name: str, value: str, ljust: int = None) -> None:
    name += ": "
    if ljust:
        name = name.ljust(ljust)
    out(f"\x1b[0m\x1b[2C{name}\x1b[96m{value}\x1b[0m\n")

def vline() -> str:
    return "\x1b(0" + "q" * (os.get_terminal_size().columns - 1) + "\x1b(B"



# ===  SELECTOR  === #
class Selector: # use sys.stdout.write instead of out here for performance reasons
    def __init__(self, entries: List[str], title: str = None, select: str = ">", print_result: bool = True, start_pos: int = None):
        """`entries` - Each None or "" will be a blank line."""

        entries = tuple(i or None for i in entries) # replace "" with None; None means empty line
        self.entries = tuple(i for i in entries if i) # remove all empty lines (None)
        self.title = title
        self.select = (" " if self.title is not None else "") + select # add space if title is used; looks better
        self.__highest_index = len(self.entries)-1
        self.__entry_prefix = f"\x1b[{len(self.select) + 3}C"
        self.__title_end = f"\x1b[A\x1b[{len(title) + 3}C" if title is not None else "\x1b[2C"
        self.__empty_line_indexes = set()
        entries = list(entries)
        for _ in range(entries.count(None)): # not possible with list/set comprehension: indexes and size have to change during iteration
            self.__empty_line_indexes.add(entries.index(None) - 1)
            entries.remove(None)
        self.pos = self.prev = 0
        self.__prev_terminal_size = os.get_terminal_size().lines

        sys.stdout.write("\x1b[0m\x1b[?25l")

        if title is not None:
            sys.stdout.write(f"\x1b[2C{title}\n")

        self.__init_options()

        if start_pos:
            self.pos = start_pos
            self.__update()

        while True:
            self.__update()
            char = getch()

            if char in (b"\xe0", b"\x00"): # xe0 e.g. conhost, x00 e.g. VS integrated shell, OpenSSH
                char = getch()
                if char == b'H': self.__up() # arrow up
                elif char == b'P': self.__down() # arrow down
                self.__update()

            elif char == b"w": self.__up()
            elif char == b"s": self.__down()

            # numbers
            elif char in b"123456789":
                if self.__select_element(int(char)): # pos was changed
                    break

            elif char == b"\r": # enter
                break

            elif char in (b"\x03", b"\x1b"): # CTRL+C, ESC
                sys.stdout.write("\x1b[?25h\x1b[u")
                sys.stdout.write(f"\x1b[J{self.__title_end}\x1b[91mcanceled\x1b[0m\n" if print_result else (f"\x1b[A\x1b[J" if title is not None else f"\x1b[J"))
                flush()
                raise KeyboardInterrupt

        # exit Selector
        self.result = self.entries[self.pos]
        sys.stdout.write("\x1b[u\x1b[?25h")
        if print_result:
            sys.stdout.write(f"\x1b[J{self.__title_end}\x1b[96m{self.entries[self.pos]}\x1b[0m\n")
        else:
            sys.stdout.write(f"\x1b[A\x1b[J" if title is not None else f"\x1b[J")
            flush() # no new line at the end so flushing is required


    def __up(self) -> None:
        self.pos = self.__highest_index if self.pos == 0 else self.pos - 1

    def __down(self) -> None:
        self.pos = 0 if self.pos == self.__highest_index else self.pos + 1

    def __select_element(self, num) -> bool:
        # 0th position == 1st element
        if num - 1 <= self.__highest_index:
            self.pos = num - 1
            return True # return True if position was changed
        return False

    def __init_options(self) -> None:
        sys.stdout.write("\r\x1b[s")
        flush()
        for i, entry in enumerate(self.entries):
            sys.stdout.write(f"{self.__entry_prefix}\x1b[0m{entry}\n")
            if i in self.__empty_line_indexes:
                sys.stdout.write("\n")
        sys.stdout.write("\x1b[u")

    def __update(self) -> None:
        if self.__prev_terminal_size != os.get_terminal_size().lines:
            sys.stdout.write("\x1b[J")
            self.__init_options()
            sys.stdout.write("\x1b[u")

        if self.prev > 0: # go to previous position
            sys.stdout.write(f"\x1b[{self.__real_pos(self.prev)}B")
        sys.stdout.write(f"{self.__entry_prefix}\x1b[1K\x1b[0m{self.entries[self.prev]}") # print unselect position

        sys.stdout.write("\x1b[u")
        if self.pos > 0: # go to selected position
            sys.stdout.write(f"\x1b[{self.__real_pos(self.pos)}B")
        sys.stdout.write(f"  \x1b[97m{self.select} \x1b[96m{self.entries[self.pos]}\x1b[0m") # print selected position

        sys.stdout.write(f"\x1b[u")
        flush()
        self.prev = self.pos
        self.__prev_terminal_size = os.get_terminal_size().lines


    def __real_pos(self, pos: int) -> int: # calculate real position in console with empty lines
        return (pos + sum(i < pos for i in self.__empty_line_indexes)) if self.__empty_line_indexes else pos # adds up bools so ones and zeros

    def __eq__(self, obj: object) -> bool:
        return obj == self.pos



# ===  ADVANCED INPUT  === #
def askinput(prompt: str = "", is_password: bool = False) -> str:
    out("\x1b[0m")
    try:
        result = (getpass if is_password else input)(f"\x1b[2C{prompt}\x1b[96m")
    except (KeyboardInterrupt, EOFError):
        out("\x1b[J\x1b[0m\x1b[2D") # when keybintrpt is thrown "canceled" message is prefixed with \x1b[2C therfore first moving back (\x1b[2D)
        raise KeyboardInterrupt
    else:
        out("\x1b[0m")
        flush()
        return result


# ===  INPUT FOR PATHS  === #
def askpath(prompt: str, /, must_be_file: bool = False, must_be_dir: bool = False) -> str:
    out("\x1b[0m\x1b[s")
    err = lambda msg: out(f"\x1b[B\x1b[2C\x1b[J\x1b[91m{msg}\x1b[0m\x1b[u\x1b[K")
    while True:
        filepath = askinput(prompt)
        # remove " and ' from start and end
        if filepath and filepath[0] in ('"', "'") and filepath[-1] in ('"', "'"):
            filepath = filepath[1:-1]
        # validate
        if not filepath:
            out("\x1b[A\x1b[K")
            continue
        elif not os.path.exists(filepath):
            err(f"This " + ("file" if must_be_file else "directory" if must_be_dir else "path") + " does not exist!")
        elif must_be_file and not os.path.isfile(filepath):
            err(f"The specified path is not a file!")
        elif must_be_dir and not os.path.isdir(filepath):
            err(f"The specified path is not a directory!")
        else:
            out("\x1b[0m\x1b[J")
            return filepath


# ===  RAW INPUT  === #
def console_input(header: str = None, alt_buf: bool = True) -> str:
    """If `alt_buf` is False, no alternative buffer will be created.
    This should only be used e.g. in loops, where still an alternative buffer is created, before
    the loop, and exited after the loop. This is useful because instead each time console_input
    is called the alternative buffer would be destroyed and recreated, which is not necessary.
    """

    if alt_buf:
        out("\x1b[?1049h", flush=True)

    begin = get_cursor_position().y

    HEADER = lambda: "".join((f"\x1b[s\x1b[{begin}H", vline(), ("\n  " + "\n  ".join(header.splitlines()) + "\n") if header else "",
        "\n  \x1b[93mPress F6 and then Enter in an empty line or CTRL+C to finish.\x1b[0m\n", vline(), "\x1b[u"))

    start_pos = HEADER().count("\n") + begin + 2
    out(f"\x1b[{start_pos}H", flush=True)

    text = []
    prev_pos = None
    try:
        while True:
            if prev_pos != os.get_terminal_size():
                out(f"\x1b[s\x1b[{start_pos}H\x1b[1J\x1b[u", HEADER(), f"\x1b[{start_pos};{os.get_terminal_size().lines-1}r\x1b[u")
                prev_pos = os.get_terminal_size()
            text.append(input("\x1b[2C"))
    except (KeyboardInterrupt, EOFError):
        pass

    out("\x1b[?1049l" if alt_buf else (f"\n{vline()}\n\n"), flush=True)
    return "\n".join(text)


# ===  NOTEPAD INPUT  === #
def notepad_input(filename: str, header: Optional[str] = None, suffix: str = ".txt", data: Optional[bytes] = None, notepad_path: os.PathLike = NOTEPAD_PATH) -> BufferedReader:
    from subprocess import Popen, CREATE_NEW_CONSOLE, CREATE_BREAKAWAY_FROM_JOB, TimeoutExpired
    from tempfile import mktemp

    start_pos = get_cursor_position().y

    file = mktemp(prefix=filename + "_", suffix=suffix)
    with open(file, "wb") as f:
        if data:
            f.write(data)

    out("\x1b[?25l")

    if header:
        out(vline(), "\n\n  ", "\n  ".join(header.splitlines()), "\n\n\x1b[0m")

    out(vline(), "\n\n\x1b[s"
        "  \x1b[93mWaiting for notepad to terminate . . .\n\n"
        f"  \x1b[0mFilename: \x1b[96m%temp%\\{os.path.split(file)[1]}\n\n"
        "  \x1b[90mPress CTRL+C to force continue.\n\n\x1b[0m", vline(),
        flush=True)

    process = Popen([notepad_path, file], creationflags=CREATE_NEW_CONSOLE | CREATE_BREAKAWAY_FROM_JOB)
    try:
        process.wait(.5) # if this fails, the process terminated within the 500 ms
    except TimeoutExpired: # but when the timeout expires, this loop waits for the process to finish but alo listens for CTRL+C
        while True:
            try:
                process._wait(.25)
            except TimeoutExpired:
                continue
            except KeyboardInterrupt:
                break
            else:
                break
    else:
        out("\x1b[u\x1b[4B\x1b[K  \x1b[90mThe process terminated too quickly, assuming the file was handeled in another instance."
            "\x1b[u\x1b[K  \x1b[93mPress any key to continue . . . \x1b[?25h", flush=True)
        getch()
    finally:
        out(f"\x1b[{start_pos}H\x1b[J\x1b[?25h", flush=True)

    return open(os.open(file, os.O_RDONLY | os.O_BINARY | os.O_TEMPORARY), "rb")




# ===  PAUSE === #
def pause_and_exit():
    out("\n\x1b[0mPress any key to exit . . . ")
    flush()
    while kbhit(): getch() # discard waiting input
    getch()
    out("\n")
    flush()


# ===  TIMER  === #
class Timer:
    time = .0

    def start(self):
        self.__start = perf_counter()

    def stop(self) -> float:
        t = self.__start - perf_counter()
        self.time += t
        return t



# ===  INTERACTIVE CONSOLE  === #
class InteractiveConsole:
    """`permanent_globals`: these items will be available in each interactive console
    `temporary_globals`: these items will be only available within the next interactive console
    If `temporary_globals` is changed before calling loolclitools.getch(), no matter if an
    interactive console was started or not, the dictionary will be cleared."""

    permanent_globals = {}
    temporary_globals = {}

    def __init__(self, g: Optional[dict] = None):

        self.compile = CommandCompiler()

        # create globals
        self.g = g or {}
        self.g.update(self.permanent_globals)
        self.g.update(self.temporary_globals)
        self.temporary_globals.clear()
        self.g.update({
            "__name__": "__main__",
            "__loader__": __loader__,
            "__builtins__": self.__builtins()
        })

        self._init()

        # main loop
        self.mainloop = True
        while self.mainloop:

            # get input
            try:
                self.cmd = input("\x1b[0m>>> ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            out("\x1b[0m", flush=True)

            # validate input, check for custom commands
            if not self.cmd:
                out("\r\x1b[A")
                continue

            elif self.cmd == "!help":
                out("\n"
                    "  \x1b[92mList of all custom commands:\n\n"
                    "   \x1b[0m- \x1b[97mcls, clear            \x1b[90mclears the screen\n"
                    "   \x1b[0m- \x1b[97mexit, quit            \x1b[90mexits\n"
                    "   \x1b[0m- \x1b[97m!rerender             \x1b[90museful if console was resized; may solve issues with scrolling then\n"
                    "   \x1b[0m- \x1b[97m!reload               \x1b[90mrestart whole interactive console\n"
                    "\n  \x1b[90mAlso try using pprint() or pp() instead of the print() function.\n")

            elif self.cmd in ("cls", "clear"):
                out("\x1b[7H\x1b[J\x1b[6H", flush=True)

            elif self.cmd == "!rerender":
                out("\x1b[?1049l")
                self._init()
                continue

            elif self.cmd == "!reload":
                out("\x1b[?1049l")
                InteractiveConsole()
                return

            elif self.cmd in ("exit", "quit"):
                break

            else: # execute
                self._execute()

            # end of each loop iteration
            out("\n")

        # end of init
        out("\x1b!p\x1b[?1049l", flush=True)


    @staticmethod
    def _init():
        out("\x1b[?1049h\x1b[94m", vline(), "\x1b[97m\n\n  Interactive Console\n\x1b[90m  CTRL+C to exit, '!help' for help.\n\n\x1b[94m", vline(), "\x1b[0m\n\x1b[7;r\x1b[7H", flush=True)


    def _execute(self):
        try: # execution
            code = self.compile(self.cmd, "<input>", "single")

            if code is None: # more input needed
                self.cmd += "\n" + input("\x1b[0m... ")
                self._execute()
                return

            exec(code, self.g)

        except SystemExit:
            self.mainloop = False

        except BaseException as exc:
            out("\x1b[91m", type(exc).__name__, f"\x1b[90m:\x1b[0m {exc.args[0]}" if len(exc.args) > 0 else "", "\x1b[0m\n")


    def __builtins(self) -> object:
        builtins = __import__("builtins") # forced re-import

        builtins.pprint = builtins.pp = pprint

        def exit():
            self.mainloop = False
        builtins.exit = builtins.quit = exit

        return builtins
