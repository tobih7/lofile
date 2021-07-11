# lool # lool-File Format # Archive-Datatype #


# ===  IMPORTS  === #
from os import makedirs, mkdir, path as ospath, walk
from io import DEFAULT_BUFFER_SIZE
from typing import BinaryIO, Callable, List, Optional

from lofile.core.shared import (
    BinaryToFilesError,
    ExtractionDirectoryExistsError,
    InvalidDirectory,
    LogLvl,
    binary_to_int,
    int_to_binary,
)


# ===  ARCHIVE ENCODER  === #
class FilesToBinary:
    def __init__(self, path: str, /, logger: Optional[Callable] = None):
        assert isinstance(path, str)
        self.path = ospath.normpath(path)
        self.errors = list()
        self.files: List[str] = list()

        if logger is None:
            self._log = lambda a, b: None
        elif not callable(logger):
            raise ValueError("argument logger: expected callable or None")
        else:
            self._log = logger

        if not ospath.exists(self.path):
            raise InvalidDirectory(self.path)
        self.path = ospath.realpath(self.path)

        for (dirpath, dirnames, filenames) in walk(self.path):
            if not dirnames and not filenames:
                self.files.append(ospath.relpath(dirpath, self.path) + ospath.sep)
            for i in filenames:
                self.files.append(ospath.join(ospath.relpath(dirpath, self.path), i))

    def __iter__(
        self, ignore_errors: bool = False
    ):  # returns the data in bytes-object blocks of maximum DEFAULT_BUFFER_SIZE bytes
        for i in self.files:
            self._log(f"copying: {i}", LogLvl.INFO)

            realpath = ospath.join(self.path, i)

            # directorys
            if i[-1] == ospath.sep:
                yield b"\x02" + self.binpath(i) + b"\x00"

            # files
            else:
                try:
                    file = open(realpath, "rb")
                except (FileNotFoundError, PermissionError, OSError) as error:
                    self.errors.append(error)
                    if not ignore_errors:
                        yield error
                else:
                    try:  # sometimes an error is first raised on calling file.read # ka y
                        file.seek(
                            0, 2
                        )  # move to EOF so that current pos equals file size
                        yield self.binpath(i) + b"\x00" + int_to_binary(
                            file.tell()
                        ) + b"\x00"
                        file.seek(0, 0)  # move back to pos 0
                        while buf := file.read(DEFAULT_BUFFER_SIZE):
                            yield buf
                    except (FileNotFoundError, PermissionError, OSError) as error:
                        self.errors.append(error)
                        if not ignore_errors:
                            yield error

    @staticmethod
    def binpath(path: str) -> bytes:
        return ospath.normpath(path).encode("UTF-8")


# ===  ARCHIVE DECODER  === #
class BinaryToFiles:
    class Path:
        def __init__(self):
            self.path: str = None
            self.length: int = None
            self.offset: int = None
            self.is_dir: bool = False

        def __repr__(self):
            return (
                "<" + ("Directory " if self.is_dir else "File ") + repr(self.path) + ">"
            )

    def __init__(self, file: BinaryIO):
        self.file = file
        self.__files: List[self.Path] = list()

        while True:
            start = file.read(1)
            file.seek(file.tell() - 1)

            if start == b"":
                break

            elif start == b"\x02":  # directory
                f = self.Path()
                f.path = self.__read_until_zero()[
                    1:
                ].decode()  # [1:] because directorys start with 0x02
                f.is_dir = True
                self.__files.append(f)

            else:  # file
                f = self.Path()
                f.path = self.__read_until_zero().decode()
                f.length = binary_to_int(self.__read_until_zero())
                f.offset = file.tell()
                self.__files.append(f)
                file.seek(file.tell() + f.length)

        file.seek(0)

    def __read_until_zero(self) -> bytes:
        data = bytes()
        while (char := self.file.read(1)) != b"\x00":
            if not char:  # if EOF
                raise BinaryToFilesError("unexpected EOF")
            data += char
        return data

    def extract_all(self, directory: str):
        assert isinstance(directory, str)
        directory = ospath.normpath(directory)
        try:
            mkdir(directory)
        except FileExistsError:
            raise ExtractionDirectoryExistsError(directory)

        for i in self.__files:
            self.extract(i, directory)

    def extract(self, fileobj: Path, path: str, directly: bool = False):
        assert isinstance(fileobj, self.Path)
        assert isinstance(path, str)
        if fileobj.is_dir:
            makedirs(ospath.join(path, fileobj.path))
        else:
            if not directly:
                makedirs(
                    ospath.join(path, ospath.split(fileobj.path)[0]), exist_ok=True
                )
            with open(
                ospath.join(
                    path, ospath.split(fileobj.path)[1] if directly else fileobj.path
                ),
                "wb",
            ) as file:
                self.file.seek(fileobj.offset)
                for _ in range(fileobj.length // DEFAULT_BUFFER_SIZE):
                    file.write(self.file.read(DEFAULT_BUFFER_SIZE))
                file.write(self.file.read(fileobj.length % DEFAULT_BUFFER_SIZE))

    @property
    def files(self):
        return self.__files.copy()
