# lool # lool-File Format # Encoder #


# ===  IMPORTS  === #
from os import urandom
from tempfile import TemporaryFile
from hashlib import sha3_256
from io import BufferedReader, BufferedWriter, BytesIO, DEFAULT_BUFFER_SIZE

from typing import BinaryIO, Optional, Union

from lofile.core.shared import (
    BaseClass,
    DESCRIPTION_MAX_LENGTH,
    DataType,
    EncodeError,
    LogLvl,
    NONETYPE,
    TAG_MAX_LENGTH,
    TAG_VALID_CHARS,
    attrib_to_binary,
    compress,
    encrypt,
    timestamp_to_binary,
)
from lofile.core.datatypes.json import json_to_binary
from lofile.core.datatypes.archive import FilesToBinary


# ===  ENCODER  === #
class Encoder(BaseClass):
    def __init__(self) -> None:
        self.__description: Optional[bytes] = None
        self.__timestamp: bool = True
        self.__compress: bool = True
        self.__compression_level: int = 6
        self.__password: Optional[bytes] = None
        self.__password_validation: bool = True
        self.__tag: Optional[bytes] = None
        self.__init_vector: bytes = urandom(16)  # required for encryption
        super().__init__()

    # ===  WRITE  === #
    def write(
        self,
        /,
        file: BinaryIO,
        raw: Union[str, bytes, BufferedReader] = None,
        json: Union[dict, list, str, int, float, bool] = None,
        archive: str = None,
        pyscript: Union[str, bytes, BufferedReader] = None,
    ):

        # verify file argument
        if not isinstance(file, BufferedWriter):
            raise TypeError("argument 'file' must be of type BinaryIO/BufferedWriter (open() in mode \"wb\")")
        self.__file = file  # file is also needed in other methods

        if raw is None and json is None and archive is None and pyscript is None:
            raise ValueError("expected one data argument")
        if [raw, json, archive, pyscript].count(None) != 3:
            raise ValueError("write() only accepts one data argument")

        # DETERMINE DATATYPE AND TYPE CHECK
        if raw is not None:
            if not isinstance(raw, (str, bytes, BufferedReader, NONETYPE)):
                raise TypeError(
                    f'argument raw must be str, bytes or BufferedReader (open() in mode "rb"), not {type(raw).__name__}'
                )
            datatype = DataType.Raw

        elif json is not None:
            # json type errors are handled inside json_to_binary as LofileError
            datatype = DataType.JSON

        elif archive is not None:
            if not isinstance(archive, (str, NONETYPE)):
                raise TypeError(f"argument archive must be path to directory of type str, not {type(archive).__name__}")
            datatype = DataType.Archive

        else:  # pyscript is not None
            if not isinstance(pyscript, (str, bytes, BufferedReader, NONETYPE)):
                raise TypeError(
                    f'argument pyscript must be str, bytes or BufferedReader (open() in mode "rb"), not {type(pyscript).__name__}'
                )
            datatype = DataType.PyScript

        # flush header
        self.log("creating header")
        self.__flushheader(datatype)

        # decide whether to write to temporary file or already to the final file
        if self.__compress or self.__password is not None:  # if theses steps are needed, first create a temporary file
            buffer = TemporaryFile(dir=self._get_default_tempfile_dir(self.__file.name))
        else:  # else directly write the data to the final file
            buffer = self.__file

        # CREATE DATA
        self.log("processing data")

        if datatype is DataType.Raw:  # FIXME: POTENTIAL ERROR: checking for identity, not equality; may be wrong
            if isinstance(raw, str):
                buffer.write(raw.encode("UTF-8"))
            elif isinstance(raw, bytes):
                buffer.write(raw)
            else:  # raw is type BufferedReader
                while buf := raw.read(DEFAULT_BUFFER_SIZE):
                    buffer.write(buf)

        if datatype is DataType.JSON:
            buffer.write(json_to_binary(json))

        if datatype is DataType.Archive:
            for i in FilesToBinary(archive, self.log):
                if isinstance(i, bytes):
                    buffer.write(i)
                elif isinstance(i, Exception):
                    self.log(str(i), LogLvl.WARN)

        if datatype is DataType.PyScript:
            raise NotImplementedError

        # COMPRESS
        if self.__compress:
            # decide whether to write to temporary file or already to the final file
            if (
                self.__password is not None
            ):  # if this is the last step (so no encryption) directly write to the final file
                compressed_buf: TemporaryFile = TemporaryFile(dir=self._get_default_tempfile_dir(self.__file.name))
            else:
                compressed_buf = self.__file
            self.log("compressing data")
            buffer.seek(0)
            compress(buffer, compressed_buf, level=self.__compression_level)

            # replace old buffer with the new compressed buffer if needed
            if self.__password is not None:
                buffer.close()
                del buffer
                buffer = compressed_buf

        # ENCRYPT
        if self.__password is not None:
            encrypted_buf = self.__file
            self.log("encrypting data")
            buffer.seek(0)
            encrypt(buffer, encrypted_buf, self.__password, self.__init_vector)

        # CLEAN UP
        buffer.close()
        self.__file.close()

    # ===  HEADER  === #
    def __flushheader(
        self, datatype: DataType
    ):  # datatype is known first when write() is called, so write() (which btw calls this method) passes the datatype

        # ATTRIBUTE #
        self.__file.write(attrib_to_binary(self.__password is not None, self.__compress, datatype))

        # DESCRIPTION #
        if self.__description:
            self.__file.write(b"\x01" + self.__description + b"\x00")

        # TIMESTAMP #
        if self.__timestamp:
            self.__file.write(b"\x02" + timestamp_to_binary() + b"\x00")

        # ENCRYPTION (INIT VECTOR) #
        if self.__password is not None:
            self.__file.write(b"\x03" + self.__init_vector)

            # PASSWORD VALIDATION #
            # indentation is correct here!
            if self.__password_validation:
                encrypt(
                    BytesIO(pv_data := urandom(64)),
                    pv_enc_data := BytesIO(),
                    self.__password,
                    self.__init_vector,
                )
                pv_enc_data.seek(0)
                self.__file.write(
                    b"\x04" + pv_data + pv_enc_data.read()
                )  # 64 + 16 (padding, needed by decrypt(), even though it's obsolete in this case)
                del (
                    pv_data,
                    pv_enc_data,
                )  # no need to close BytesIO objects, __del__ should do that

        # TAG #
        if self.__tag:
            self.__file.write(b"\x05" + self.__tag + b"\x00")

        self.__file.write(b"\x00")

    # ===  PROPERTIES  === #

    # DESCRIPTION #
    @property
    def description(self) -> Optional[bytes]:
        return self.__description

    @description.setter
    def description(self, value):
        if not isinstance(value, (bytes, NONETYPE)):
            raise TypeError(f"description: expected bytes or None")
        elif value is None or len(value) == 0:  # ignore empty string; if its not None it will be type bytes
            self.__description = None
        elif len(value) > DESCRIPTION_MAX_LENGTH:
            raise ValueError(f"description: maximum length is {DESCRIPTION_MAX_LENGTH}, got {len(value)}")
        elif 0 in value:
            raise ValueError("description: invalid character: 0-byte")
        else:
            self.__description = value

    # TIMESTAMP #
    @property
    def timestamp(self) -> bool:
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, value):
        if not isinstance(value, bool):
            raise TypeError("timestamp: expected bool")
        self.__timestamp = value

    # COMPRESS #
    @property
    def compress(self) -> bool:
        return self.__compress

    @compress.setter
    def compress(self, value):
        if not isinstance(value, bool):
            raise TypeError("compress: expected bool")
        self.__compress = value

    # COMPRESSION LEVEL #
    @property
    def compression_level(self) -> int:
        return self.__compression_level

    @compression_level.setter
    def compression_level(self, value):
        if not isinstance(value, int):
            raise TypeError("compression_level: expected int")
        elif value < 1 or value > 9:
            raise ValueError("compression_level: value must be in range 1 to 9")
        self.__compression_level = value

    # PASSWORD #
    # password is unreadable, no getter function
    @property().setter
    def password(self, value):
        if not isinstance(value, (bytes, NONETYPE)):
            raise TypeError("password: expected bytes or None")
        self.__password = sha3_256(value).digest() if value is not None else None

    @property
    def is_password(self) -> bool:
        return self.__password is not None

    # PASSWORD VALIDATION #
    @property
    def password_validation(self) -> bool:
        return self.__password_validation

    @password_validation.setter
    def password_validation(self, value):
        if not isinstance(value, bool):
            raise TypeError("password_validation: expected bool")
        self.__password_validation = value

    # TAG #
    @property
    def tag(self) -> Optional[bytes]:
        return self.__tag

    @tag.setter
    def tag(self, value):
        if not isinstance(value, (bytes, NONETYPE)):
            raise TypeError("tag: expected bytes or None")
        elif value is None:
            self.__tag = None
        elif len(value) > TAG_MAX_LENGTH:  # must be bytes
            raise ValueError(f"tag: maximum length is {TAG_MAX_LENGTH}, got {len(value)}")
        elif invalid_chars := set(value).difference(TAG_VALID_CHARS):
            raise ValueError(f"description: invalid characters: {repr(bytes(sorted(invalid_chars)))[2:-1]}")
        else:
            self.__tag = value

    # INIT VECTOR #
    @property
    def init_vector(self) -> bytes:
        return self.__init_vector

    @init_vector.setter
    def init_vector(self, value):
        if not isinstance(value, bytes):
            raise TypeError("init_vector: expected bytes")
        elif len(value) != 16:
            raise ValueError("init_vector: expected length of 16")
        self.__init_vector = value
