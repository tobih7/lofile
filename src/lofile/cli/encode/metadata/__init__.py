# lool-File Format # CLI Encoder # Meta Data #

__all__ = ["Metadata"]

from loolclitools import Selector, out, yesno

from .data import Data
from .description import Description
from .tag import Tag
from .timestamp import Timestamp
from .password import Password
from .compress import Compress


class Metadata(Data, Description, Tag, Timestamp, Password, Compress):
    def askmetadata(self):
        self._custom_compression_level_is_set = False  # level is only shown if it was customly set, this attribute is needed

        funcs = (
            self._set_data,
            self._set_description,
            self._set_tag,
            self._set_timestamp,
            self._set_password,
            self._set_compress,
        )

        while True:
            out(
                "\x1b[4;2H\x1b[J", flush=True
            )  # using absolute pos, due to CSI s and CSI u being used inside the loop
            s = Selector(
                ("\x1b[92mconfirm and proceed", None, *self.parsed_metadata()),
                print_result=False,
            ).pos
            if s == 0:
                return
            funcs[s - 1]()

    # ===  PARSING  === #
    def parsed_metadata(self):
        yield "Data\x1b[24m:                 " + self.datatype.name
        yield None
        yield "Description\x1b[24m:          " + self.__parsed_description()
        yield "Tag\x1b[24m:                  " + (
            self.tag.decode() if self.tag is not None else "\x1b[96mNo"
        )
        yield f"Store Timestamp\x1b[24m:      \x1b[96m{yesno(self.timestamp)}"
        yield None
        yield f"Password\x1b[24m:             \x1b[96m{yesno(self.is_password)}"
        yield "Compress\x1b[24m:             " + self.__parsed_compress()

        f"\x1b[96m{yesno(self.compress)} \x1b[90m(level = {self.compression_level})"

    def __parsed_description(self):
        if not self.description:
            return "\x1b[96mNo"
        return (
            "\x1b[0m"
            + (dsc := self.description.splitlines())[0][:32].decode()
            + (" \x1b[90m... " if len(dsc[0]) > 32 or len(dsc) > 1 else "")
            + (
                f"({len(dsc)-1} more line" + ("s" if len(dsc) - 1 > 1 else "") + ")"
                if len(dsc) > 1
                else ""
            )
        )

    def __parsed_compress(self):
        if self._custom_compression_level_is_set:
            return f"\x1b[96m{yesno(self.compress)} \x1b[90m(level = {self.compression_level})"
        return f"\x1b[96m{yesno(self.compress)}"
