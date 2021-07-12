# lool-File Format # CLI Encoder # JSON-Data #

from json import loads, JSONDecodeError
from loolclitools import (
    Selector,
    console_input,
    get_cursor_position,
    notepad_input,
    out,
)

from lofile.cli.shared import DataOrigin


class JSON:
    def _data_json(self, /, editing=False, data=None):

        method = (
            Selector(
                ("file", "notepad input", "console input"),
                "Data Source:",
                print_result=False,
            ).pos
            if not editing
            else 1
        )  # 1 = notepad_input

        if method == 2:
            out("\x1b[?1049h")

        start_pos = get_cursor_position()
        err = originpath = None

        while True:

            if method == 0:
                if err:
                    out("  ", "\n  ".join(err.splitlines()), "\n\n")
                fileobj = self._askfile()
                data = fileobj.read()
                originpath = fileobj.name
                fileobj.close()

            elif method == 1:
                fileobj = notepad_input(
                    filename="json_data",
                    suffix=".json",
                    header=(f"{err}\n\n" if err else "") + "\x1b[90mLeave the file empty to cancel.",
                    data=data,
                )
                data = fileobj.read()
                fileobj.close()

            elif method == 2:
                data = console_input(header=err, alt_buf=False)

            try:
                data = loads(data)

            except JSONDecodeError as exc:
                try:
                    line = exc.doc.splitlines()[exc.lineno - 1]
                except IndexError:  # no data received
                    if method == 0:
                        err = "\x1b[91mThe file is empty!"
                        continue
                    elif method == 1:
                        start_pos.apply()
                        out(f"\x1b[J\x1b[91m  The file is empty. Assuming request to cancel.\x1b[0m\n\n")
                        raise KeyboardInterrupt
                    elif method == 2:  # assume user wanted to exit, instead if submitting
                        raise KeyboardInterrupt

                err = (
                    f"Error in line {exc.lineno}: \x1b[91m{exc.msg}!\x1b[0m\n\n"
                    f"{line[:exc.colno-1].lstrip()}\x1b[91m{line[exc.colno-1:].rstrip()}"
                )

            except UnicodeDecodeError:
                err = "\x1b[91mInvalid encoding! Unable to parse data."

            else:  # no error
                break

            # handle error generally, if no error occured else block would have already returned
            start_pos.apply()
            out("\x1b[J")

        if method == 2:
            out("\x1b[?1049l")

        self.dataorigin = (
            (DataOrigin.File, originpath),
            (DataOrigin.NotepadInput,),
            (DataOrigin.ConsoleInput,),
        )[method]
        return data
