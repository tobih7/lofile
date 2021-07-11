# lool # lool-File Format # shared components #


# ===  IMPORTS  === #
from enum import Enum
from io import DEFAULT_BUFFER_SIZE
from os import getenv
from pathlib import Path, PurePath
from time import perf_counter
from zlib import compressobj, decompressobj
from datetime import datetime
from typing import Callable, Final, Optional, Union, Tuple, BinaryIO

# 3rd party
from Crypto.Cipher import AES  # pip install pycryptodome


# ===  CONSTANTS  === #
NONETYPE: Final = type(None)  # to reduce function calls
DESCRIPTION_MAX_LENGTH: Final = 512
TAG_MAX_LENGTH: Final = 64
TAG_VALID_CHARS: Final = frozenset(
    b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ "
)


class DataType(Enum):
    Raw = 0
    JSON = 1
    Archive = 2
    PyScript = 3


class LogLvl(Enum):
    INFO = 0
    WARN = 1
    ERROR = 2


# ===  EXCEPTIONS  === #
class LofileError(Exception):
    def __str__(self):
        return self.__doc__.format(*self.args)


class InvalidDirectory(LofileError):
    'The directory "{}" does not exist.'


class ExtractionDirectoryExistsError(LofileError):
    'The extraction directory "{}" already exists.'


class InvalidTimestamp(LofileError):
    "Tried to convert an invalid timestamp."


class JsonToBinError(LofileError):
    "{}"


class BinToJsonError(LofileError):
    "Error while converting binary data to JSON data: {}"


class DecodeError(LofileError):
    "{}"


class EncodeError(LofileError):
    "{}"


class BinaryToFilesError(LofileError):
    "{}"


# ===  TIMEFORMAT  === #
def timeformat(time: Union[int, float]) -> str:  # Works perfectly! Do not touch!
    assert isinstance(time, (int, float))
    return (
        str(
            (
                f"{h} hour{'s' if h > 1 else ''}, "
                if (h := int(time // 3600)) > 0
                else ""
            )
            + (
                f"{m} minute{'s' if m > 1 else ''}, "
                if (m := int(time % 3600 // 60)) > 0
                else ""
            )
            + (
                f"{s} second{'s' if s > 1 else ''}, "
                if (s := int(time % 3600 % 60)) > 0
                else ""
            )
            + (
                f"{ms} millisecond{'s' if ms > 1 else ''}, "
                if (ms := int(round(time % 3600 % 60 % 1, 3) * 1000)) > 0
                else ""
            )
        )
        .strip()[:-1][::-1]
        .replace(",", " and"[::-1], 1)[::-1]
        if round(time, 3) > 0
        else "0 milliseconds"
    )


# ===  INT <-> BINARY  === #
def int_to_binary(num: int, /, offset: int = 1) -> bytes:
    assert isinstance(num, int)
    base = 256 - offset
    digits = []
    if num == 0:
        digits = [0]
    else:
        while num:
            digits.insert(0, num % base)
            num //= base
    return bytes([i + offset for i in digits])


def binary_to_int(num: bytes, /, offset: int = 1) -> int:
    assert isinstance(num, bytes)
    base = 256 - offset
    num = [i - offset for i in num]
    return sum((base ** i * n) for (i, n) in enumerate(num[::-1]))


# ===  TIMESTAMP <-> BINARY  === #
def timestamp_to_binary(t: Union[int, float] = None) -> bytes:
    t = t or datetime.now().timestamp()
    assert isinstance(t, (int, float))
    return int_to_binary(int(t))


def binary_to_timestamp(data: bytes) -> datetime:
    assert isinstance(data, bytes)
    return datetime.fromtimestamp(binary_to_int(data))


# ===  ATTRIBUTES <-> BINARY  === #
def attrib_to_binary(encryption: bool, compression: bool, datatype: DataType) -> bytes:
    assert isinstance(encryption, bool)
    assert isinstance(compression, bool)
    assert isinstance(datatype, DataType)
    return bytes([int(encryption) + int(compression) * 2 + datatype.value * 4])


def binary_to_attrib(byte: int) -> Tuple[bool, bool, DataType]:
    assert isinstance(byte, int)
    if not byte >= 0:
        raise ValueError("invalid datatype")
    return (
        bool(byte % 2),
        bool(byte // 2 % 2),
        DataType(byte // 4),
    )  # if datatype is invalid also ValueError is raised


# ===  COMPRESSION  === #
def compress(inputfile: BinaryIO, outputfile: BinaryIO, level: int = 9) -> None:
    c = compressobj(level=level, memLevel=9)
    while buf := inputfile.read(DEFAULT_BUFFER_SIZE):
        outputfile.write(c.compress(buf))
    outputfile.write(c.flush())


# ===  DECOMPRESSION  === #
def decompress(inputfile: BinaryIO, outputfile: BinaryIO) -> None:
    c = decompressobj()
    while buf := inputfile.read(DEFAULT_BUFFER_SIZE):
        outputfile.write(c.decompress(buf))
    outputfile.write(c.flush())


# ===  ENCRYPTION  === #
def encrypt(
    inputfile: BinaryIO, outputfile: BinaryIO, key: bytes, init_vector: bytes
) -> None:
    aes = AES.new(key, AES.MODE_CBC, init_vector)
    while buf := inputfile.read(DEFAULT_BUFFER_SIZE):
        if len(buf) != DEFAULT_BUFFER_SIZE:
            fill = 16 - len(buf) % 16
            buf += fill * bytes([fill])
        outputfile.write(aes.encrypt(buf))


# ===  DECRYPTION  === #
def decrypt(
    inputfile: BinaryIO, outputfile: BinaryIO, key: bytes, init_vector: bytes
) -> None:
    aes = AES.new(key, AES.MODE_CBC, init_vector)
    while buf := inputfile.read(DEFAULT_BUFFER_SIZE):
        buf = aes.decrypt(buf)
        if len(buf) != DEFAULT_BUFFER_SIZE:
            buf = buf[: -buf[-1]]
        outputfile.write(buf)


# ===  BASE CLASS  === #
# both (encoder and decoder) inherit from this

# init with no args
# reusable with different files (.write(file, data) or .read(file, ?password))


class BaseClass:

    # ===  INIT  === #
    def __init__(self) -> None:

        # INTERNAL ATTRIBUTES #
        self.__tempfile_dir: Optional[Path] = None
        self.__starttime: float = perf_counter()
        self.__took: Optional[float] = None
        self.__logger: Optional[Callable[[str, LogLvl], None]] = lambda msg, lvl: print(
            f"[{lvl.name}] - {msg}"
        )

    # ===  ENTER  === #
    def __enter__(self):  # for context manager
        return self

    # ===  EXIT  === #
    def __exit__(self, exception_type, exception_value, traceback):

        self.__took = perf_counter() - self.__starttime

        # normal exit, no errors
        if exception_type is None:
            self.log(f"finished in {self.took}")

        elif exception_type.__base__ is LofileError:
            self.log(str(exception_value), LogLvl.ERROR)
            return False  # if False: with-statement: exception is raised

    # ===  OTHER  === #
    def log(
        self, msg: str, lvl: LogLvl = LogLvl.INFO
    ):  # may be used by caller, from outside
        if not isinstance(msg, str):
            raise TypeError("argument 'msg': expected type str")
        if not isinstance(lvl, LogLvl):
            raise TypeError("argument 'lvl': expected type LogLvl")
        if self.__logger is not None:
            self.__logger(msg, lvl)

    def reset_timer(self):  # useful for CLI, after inputs the time can be reset to zero
        self.__starttime = perf_counter()

    def subtract_from_took(
        self, value: Union[int, float]
    ):  # if e.g. inputs etc. are used inside the context manager, this is useful
        self.__starttime -= value

    def _get_default_tempfile_dir(
        self, filepath
    ) -> Path:  # default tempfile location depends on input/output file
        if self.tempfile_dir:  # if custom dir was set return it
            return self.tempfile_dir
        stdtmp = Path(getenv("TMP")).resolve()
        try:
            filepth = Path(filepath).resolve()
        except OSError:  # path may be 'nul' or some other "invalid parameter"
            return stdtmp
        return stdtmp if stdtmp.drive == filepth.drive else filepth.parent

    # ===  PROPERTIES  === #

    # TOOK #
    @property
    def took_int(self) -> int:
        return (
            self.__took or perf_counter() - self.__starttime
        )  # if __took is None, __exit__ was not called yet (or wont be at all); timer cant be stopped

    @property
    def took(self) -> str:
        return timeformat(self.took_int)

    # took_int and took are read-only, no setter functions

    # LOGGER #
    @property
    def logger(self) -> Callable[[str, str], None]:
        return self.__logger

    @logger.setter
    def logger(self, value):
        if value is None:
            self.__logger = None
        elif not callable(value):
            raise TypeError("logger: expected function")
        else:
            self.__logger = value

    # TEMPFILE DIRECTORY #
    @property
    def tempfile_dir(self) -> Path:
        return self.__tempfile_dir

    @tempfile_dir.setter
    def tempfile_dir(self, value):
        if not isinstance(value, (str, bytes, PurePath, NONETYPE)):
            raise TypeError(
                "tempfile_dir: expected path-like or None (str, bytes, pathlib.Path)"
            )
        elif value == None:
            self.__tempfile_dir = None
        else:
            value = Path(value).resolve()
        if not value.is_dir():
            raise ValueError("tempfile_dir: expected a valid existing directory")
        else:
            self.__tempfile_dir = value
