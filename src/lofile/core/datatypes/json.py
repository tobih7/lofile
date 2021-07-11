# lool # lool-File Format # JSON-Datatype #


# ===  IMPORTS  === #
from json import dumps

from lofile.core.shared import *


# ===  JSON ENCODER  === #
def json_to_binary(obj: object) -> bytes:
    try:
        dumps(obj)
    except TypeError as error:
        raise JsonToBinError(error)

    binlen = lambda obj: int_to_binary(len(obj)) + b"\x00"

    def obj_to_binary(obj: object):
        if obj is None:
            return b"\x01"
        elif isinstance(obj, bool):
            return b"\x02\x01" if obj else b"\x02\x00"
        elif isinstance(obj, int):
            return (
                (b"\x03" if obj >= 0 else b"\x04") + int_to_binary(abs(obj)) + b"\x00"
            )
        elif isinstance(obj, float):
            flt = [int_to_binary(abs(int(i))) for i in str(obj).split(".")]
            return (
                (b"\x05" if obj >= 0.0 else b"\x06")
                + flt[0]
                + b"\x00"
                + flt[1]
                + b"\x00"
            )
        elif isinstance(obj, str):
            return b"\x07" + binlen(obj) + obj.encode()
        elif isinstance(obj, list):
            return b"\x08" + binlen(obj) + bytes().join(map(obj_to_binary, obj))
        elif isinstance(obj, dict):
            return (
                b"\x09"
                + binlen(obj)
                + bytes().join(
                    map(obj_to_binary, ([b for a in obj.items() for b in a]))
                )
            )

    return obj_to_binary(obj)


# ===  JSON DECODER  === #
class _bintojson:
    def __init__(self, data):
        if not isinstance(data, bytes):
            raise TypeError("expected bytes")
        if not data:
            raise BinToJsonError("no data")
        self.data = data
        self.obj = self.binary_to_object()
        if self.data:
            raise BinToJsonError("additional data")

    def binary_to_object(self):
        if self.data[0] == 1:
            self.data = self.data[1:]
            return None
        elif self.data[0] == 2:
            obj = bool(self.data[1])
            self.data = self.data[2:]
            return obj
        elif self.data[0] == 3:
            return self.bin_int()
        elif self.data[0] == 4:
            return -self.bin_int()
        elif self.data[0] == 5:
            return self.bin_float()
        elif self.data[0] == 6:
            return -self.bin_float()
        elif self.data[0] == 7:
            length, self.data = self.data.split(b"\x00", 1)
            length = binary_to_int(length[1:])
            string, self.data = self.data[:length], self.data[length:]
            return string.decode()
        elif self.data[0] == 8:
            length, self.data = self.data.split(b"\x00", 1)
            length = binary_to_int(length[1:])
            obj = list()
            for i in range(length):
                obj.append(self.binary_to_object())
            return obj
        elif self.data[0] == 9:
            length, self.data = self.data.split(b"\x00", 1)
            length = binary_to_int(length[1:])
            obj = dict()
            for i in range(length):
                obj.update({self.binary_to_object(): self.binary_to_object()})
            return obj
        else:
            raise BinToJsonError("invalid start of object")

    def bin_int(self):
        obj, self.data = self.data.split(b"\x00", 1)
        return binary_to_int(bytes(obj[1:]))

    def bin_float(self):
        num1, num2, self.data = self.data.split(b"\x00", 2)
        return float(str(".").join([str(binary_to_int(i)) for i in (num1[1:], num2)]))


def binary_to_json(rawdata: bytes) -> object:
    return _bintojson(rawdata).obj
