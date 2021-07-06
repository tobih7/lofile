# lool-File Format # CLI Encoder # Data #

from lofile.core.shared import DataType
from lofile.cli.loolclitools import Selector, askpath, out

from .raw import Raw
from .json import JSON
from .archive import Archive
from .pyscript import PyScript


class Data(Raw, JSON, Archive, PyScript):

    def askdata(self):
        datatype = DataType[Selector((i.name for i in DataType), "Datatype:", print_result=False, start_pos=self.datatype.value).result]

        self.data = (self._data_raw, self._data_json, self._data_archive, self._data_pyscript)[datatype.value]()
        self.datatype = datatype
        # first store datatype locally, because KeyboardInterrupt may be thrown while trying to get data from user
        # if this happens self.data would not be modifed, so self.datatype should also stay as it was

    # used from parent classes
    def _askfile(self):
        while True:
            try:
                return open(askpath("File: ", must_be_file=True), "rb")
            except PermissionError:
                out("\x1b[B  \x1b[91mPermission to the file was denied!\x1b[0m\x1b[2A\r\x1b[K", flush=True)
            except OSError as exc:
                out(f"\x1b[B  \x1b[91mThe path is invalid!\n\x1b[2C\x1b[90mError {exc.errno}: {exc.strerror}\x1b[0m\x1b[3A\r\x1b[K", flush=True)
