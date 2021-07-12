# lool # lool-File Format # Decoder #


# ===  IMPORTS  === #
from tempfile import TemporaryFile
from hashlib import sha3_256
from datetime import datetime
from zlib import error as zlib_error
from os import devnull
from io import BufferedReader, BytesIO

from typing import Any, BinaryIO, Optional

from lofile.core.shared import (
    BaseClass,
    DESCRIPTION_MAX_LENGTH,
    DataType,
    DecodeError,
    LogLvl,
    NONETYPE,
    TAG_MAX_LENGTH,
    binary_to_attrib,
    binary_to_timestamp,
    decompress,
    decrypt,
)
from lofile.core.datatypes.json import binary_to_json
from lofile.core.datatypes.archive import BinaryToFiles


# ===  DECODER  === #
class Decoder(BaseClass):

    # reading header at initialization
    def __init__(self) -> None:
        self.__description: Optional[bytes] = None
        self.__timestamp: Optional[datetime] = None
        self.__tag: Optional[bytes] = None
        self.__aes_init_vector: Optional[bytes] = None
        self.__password: Optional[bytes] = None

        super().__init__()

    # READ #
    def read(self, file: BinaryIO, password: Optional[bytes] = None) -> Any:

        # verify file argument
        if isinstance(file, BytesIO):
            file.name = devnull  # BytesIO has no name, because it is not an actual file, but name (so the path) is needed to decide
            # where to create the temporary files; when it is devnull the default %tmp% directory is used
        elif not isinstance(file, BufferedReader):
            raise TypeError("argument 'file' must be of type BinaryIO/BufferedReader (open() in mode \"rb\")")
        self.__file = file  # file is also needed in other methods

        if (
            password is not None
        ):  # if it is None, file may be unencrypted, but maybe the password was already set via attribute
            self.password = password  # type validation happens here

        # ===  READ HEADER  === #

        # ATTRIBUTE #
        try:
            self.__isencrypted, self.__iscompressed, self.__datatype = binary_to_attrib(file.read(1)[0])
        except IndexError:
            raise DecodeError("file is empty")
        except ValueError:
            raise DecodeError("invalid data in header")
        # check for password
        if self.__isencrypted and self.__password is None:
            raise DecodeError("password required")

        # DESCRIPTION #
        if file.read(1) == b"\x01":
            self.__description = self.__read_until_zero()
            if len(self.__description) > DESCRIPTION_MAX_LENGTH:
                raise DecodeError("description is too long")
        else:
            file.seek(file.tell() - 1)

        # TIMESTAMP #
        if file.read(1) == b"\x02":
            self.__timestamp: datetime = self.__read_until_zero()
            try:
                self.__timestamp = binary_to_timestamp(self.__timestamp)
            except:
                raise DecodeError("invalid timestamp")
        else:
            file.seek(file.tell() - 1)

        # AES INIT VECTOR #
        if file.read(1) == b"\x03":
            self.__aes_init_vector = file.read(16)
            if len(self.__aes_init_vector) != 16:
                raise DecodeError("unexpected EOF")
            if not self.__isencrypted:
                self.log(
                    "AES initialization vector is present, but file seems to be unencrypted",
                    LogLvl.WARN,
                )
        else:
            file.seek(file.tell() - 1)

        # PASSWORD VALIDATION #
        if file.read(1) == b"\x04":
            self.__password_validation_data = file.read(64)
            self.__password_validation_enc_data = file.read(
                80
            )  # 64 + 16 (padding, needed by decrypt(), even though it's obsolete in this case)
        else:
            file.seek(file.tell() - 1)

        # TAG #
        if file.read(1) == b"\x05":
            self.__tag = self.__read_until_zero()
            if len(self.__tag) > TAG_MAX_LENGTH:
                raise DecodeError("tag is too long")
        else:
            file.seek(file.tell() - 1)

        # END OF OPTIONAL DATA #
        if file.read(1) != b"\x00":
            raise DecodeError("header was never terminated")

        # PARSE DATA #

        # DECRYPT #
        if self.__isencrypted:
            # VALIDATE PASSWORD #
            if self.__password_validation_enc_data is not None:
                decrypt(
                    BytesIO(self.__password_validation_enc_data),
                    pv_data := BytesIO(),
                    self.__password,
                    self.__aes_init_vector,
                )
                pv_data.seek(0)
                if self.__password_validation_data != pv_data.read():
                    raise DecodeError("invalid password")
                del pv_data

            self.log("decrypting data")
            decrypted_buf: TemporaryFile = TemporaryFile(dir=self._get_default_tempfile_dir(self.__file.name))
            decrypt(self.__file, decrypted_buf, self.__password, self.__aes_init_vector)
            decrypted_buf.seek(0)
            self.__file.close()
            self.__file = decrypted_buf

        # DECOMPRESS #
        if self.__iscompressed:
            self.log("decompressing data")
            decompressed_buf: TemporaryFile = TemporaryFile(dir=self._get_default_tempfile_dir(self.__file.name))
            try:
                decompress(self.__file, decompressed_buf)
            except zlib_error:
                raise DecodeError("decompression failed")
            decompressed_buf.seek(0)
            self.__file.close()
            self.__file = decompressed_buf

        # FINALLY RETURN DATA #

        if self.__datatype is DataType.Raw:
            data = self.__file

        elif self.__datatype is DataType.JSON:
            data = binary_to_json(self.__file.read())

        elif self.__datatype is DataType.Archive:
            data = BinaryToFiles(self.__file)

        elif self.__datatype is DataType.PyScript:
            data = ...  # TODO: implement

        self.log("proccessing data")
        return data

    # READ UNTIL ZERO #
    def __read_until_zero(self) -> bytes:
        data = bytes()
        while (char := self.__file.read(1)) != b"\x00":
            if not char:  # if EOF
                raise DecodeError("unexpected EOF")
            data += char
        return data

    # ===  PROPERTIES  === #

    # PASSWORD #
    @property().setter  # password is unreadable, no getter function
    def password(self, value):
        if not isinstance(value, (bytes, NONETYPE)):
            raise TypeError("expected bytes or None")
        self.__password = sha3_256(value).digest() if value is not None else None

    # IS ENCRYPTED #
    @property
    def isencrypted(self) -> bool:
        return self.__isencrypted

    # IS COMPRESSED #
    @property
    def iscompressed(self) -> bool:
        return self.__iscompressed

    # DATATYPE #
    @property
    def datatype(self) -> DataType:
        return self.__datatype

    # DESCRIPTION #
    @property
    def description(self) -> Optional[bytes]:
        return self.__description

    # TIMESTAMP #
    @property
    def timestamp(self) -> Optional[datetime]:
        return self.__timestamp

    # AES INIT VECTOR #
    @property
    def aes_init_vector(self) -> Optional[bytes]:
        return self.__aes_init_vector

    # TAG #
    @property
    def tag(self) -> Optional[bytes]:
        return self.__tag
