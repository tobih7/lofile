# lool-File Format # CLI Encoder # Raw-Data #

from loolclitools import Selector, console_input, notepad_input

from lofile.cli.shared import DataOrigin


class Raw:

    def _data_raw(self, /, method=None, data=None):
        s = Selector(("file", "notepad input", "console input"), "Data Source:", print_result=False).pos if method is None else method
        if s == 0:
            self.dataorigin = (DataOrigin.File,)
            return self._askfile()
        elif s == 1:
            self.dataorigin = (DataOrigin.NotepadInput,)
            return notepad_input("raw_data", data=data)
        elif s == 2:
            self.dataorigin = (DataOrigin.ConsoleInput,)
            return console_input()
