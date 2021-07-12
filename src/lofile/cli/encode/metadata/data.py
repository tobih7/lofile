# lool-File Format # CLI Encoder # Meta Data # Data #

import os
from json import dumps
from loolclitools import Selector, get_cursor_position, out, param, vline

from lofile.core.shared import DataType
from lofile.cli.shared import DataOrigin


class Data:
    def _set_data(self):  # change data (editing functionallity)

        self.__start_pos = get_cursor_position()  # this could be absolute position (4th line), but this is safer
        end_header = lambda: out("\n", vline(), "\n\n")

        out(vline(), f"\r\x1b[4C\x1b[96m  {self.datatype.name}  \x1b[0m\n\n")

        try:

            if self.datatype is DataType.Raw:
                if self.dataorigin[0] is DataOrigin.File:
                    path, file = os.path.split(os.path.abspath(self.data.name))
                    param("Origin", "File\n")
                    param("Path", path)
                    param("Name", file)
                    end_header()

                    s = Selector(
                        ("change file", None, "change datatype", "back"),
                        print_result=False,
                    ).pos
                    if s == 0:
                        self.data = self._data_raw(method=0)  # 0 = askfile
                    elif s == 1:
                        self.__reset_data()

                elif self.dataorigin[0] is DataOrigin.NotepadInput:
                    param("Origin", "Notepad Input")
                    end_header()

                    s = Selector(
                        ("edit data with notepad", None, "change datatype", "back"),
                        print_result=False,
                    ).pos
                    if s == 0:
                        self.__gototop()
                        self.data = self._data_raw(method=1, data=self.data.read())  # 1 = notepad_input
                    elif s == 1:
                        self.__reset_data()

                elif self.dataorigin[0] is DataOrigin.ConsoleInput:
                    param("Origin", "Console Input")
                    end_header()

                    s = Selector(
                        ("edit data with notepad", None, "change datatype", "back"),
                        print_result=False,
                    ).pos
                    if s == 0:
                        self.__gototop()
                        self.data = self._data_raw(method=1, data=self.data.encode())  # 1 = notepad_input
                    elif s == 1:
                        self.__reset_data()

            elif self.datatype is DataType.JSON:
                if self.dataorigin[0] is DataOrigin.File:
                    path, file = os.path.split(os.path.abspath(self.dataorigin[1]))
                    param("Origin", "File\n")
                    param("Path", path)
                    param("Name", file)
                    end_header()

                    s = Selector(
                        (
                            "edit data with notepad   \x1b[90m(no effect on original file)",
                            None,
                            "change datatype",
                            "back",
                        ),
                        print_result=False,
                    ).pos
                    if s == 0:
                        self.__edit_json_data()
                    elif s == 1:
                        self.__reset_data()

                if self.dataorigin[0] in (
                    DataOrigin.NotepadInput,
                    DataOrigin.ConsoleInput,
                ):
                    param(
                        "Origin",
                        "Notepad Input" if self.dataorigin[0] == DataOrigin.NotepadInput else "Console Input",
                    )
                    end_header()

                    s = Selector(
                        ("edit data with notepad", None, "change datatype", "back"),
                        print_result=False,
                    ).pos
                    if s == 0:
                        self.__edit_json_data()
                    elif s == 1:
                        self.__reset_data()

        except KeyboardInterrupt:
            pass

        self.__start_pos.apply()  # go back to top
        out("\x1b[J")

    def __gototop(self):
        self.__start_pos.apply()  # go back to top
        out("\x1b[J")

    def __reset_data(self):
        self.__gototop()
        self.askdata()  # main data selector; completely reset data

    def __edit_json_data(self):
        self.__gototop()
        self.data = self._data_json(
            editing=True, data=dumps(self.data, indent="\t").encode()
        )  # editing means notepad input, no other possible input type
