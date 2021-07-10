# lool-File Format # CLI Encoder # Meta Data # Description #

from loolclitools import Selector, console_input, notepad_input, out, vline

from lofile.core.shared import DESCRIPTION_MAX_LENGTH


class Description:

    def _set_description(self):

        if self.description is None:
            self.__ask_description()

        else:
            out(vline(), "\r\x1b[4C\x1b[96m  Current Description  \x1b[0m\n", *("  " + line for line in self.description.decode().splitlines(keepends=True)), "\n", vline(), "\n\n")
            try:
                s = Selector(("clear description", "new description", "back"), print_result=False).pos
            except KeyboardInterrupt:
                return
            if s == 0:
                self.description = None
            elif s == 1:
                self.__ask_description()



    def __ask_description(self):
        hint = f"The description can have a maximum length of {DESCRIPTION_MAX_LENGTH} bytes."

        if Selector(("notepad input", "console input"), "Data Source:", print_result=False).pos: # == 1
            out("\x1b[s")
            description = console_input(header=hint).encode("UTF-8")
            out("\x1b[u")
        else: # == 0
            description = notepad_input("description", header=hint + "\nAlso NUL-bytes are forbidden.").read()

        try:
            self.description = description[:DESCRIPTION_MAX_LENGTH]

        except ValueError: # e.g. NUL-bytes
            pass # just ignore the error and do nothing; no description will be saved
