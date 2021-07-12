# lool # lool-File Format # Python Script #


# ===  IMPORTS  === #
from typing import Callable, List, Optional, Tuple

from lofile.core.shared import NONETYPE


# ===  PYTHON SCRIPT EXECUTION INTERFACE  === #
# when executing (exec()) the script, an object of this class will be contained inside globals()
class PyScriptInterface:
    def __init__(self) -> None:
        self.__init: str = None  # name of the function to run initially
        self.__entrypoints: List[Tuple[str, str]] = []  # the functions to ask for when decoding
        self.__description: Optional[str] = None  # initially printed description

    def init(self, func) -> Callable:
        """This decorator marks the function, which will be executed initially."""
        if not callable(func):
            raise TypeError("parameter 'func' needs to be a function")
        self.__init = func.__name__
        return func

    def entrypoint(self, func, name: Optional[str] = None) -> Callable:
        """
        This decorator marks a function as a possible entry point.
        All these functions will be available for selection when the .lo file is decoded.
        If only one entrypoint is defined, it will be automatically executed, without asking.

        `name` - this optional parameter sets the text to display in the selection (when decoding, and asking what to run)
        """

        if not callable(func):
            raise TypeError("parameter 'func' needs to be a function")
        if not isinstance(name, (NONETYPE, str)):
            raise TypeError("parameter 'name' needs to be type str or None")

        self.__entrypoints.append((func.__name__, name))

        return func

    @property
    def description(self) -> Optional[str]:
        return self.__description

    @description.setter
    def description(self, value) -> None:
        if not isinstance(value, (NONETYPE, str)):
            raise TypeError("expected type str or None")
        self.__description = value


# TODO: py_script may also be pyz file, so whole modules (3rd party) could be stored in there

# move to cli
def execute_script(script: bytes):

    psi = PyScriptInterface()

    g = {"__name__": "__main__", "lofile": psi}

    try:
        exec(
            script, g
        )  # TODO: first compile() then exec, so errors can be reported even before executing: sth. like opening file: and the errors like file is empty, but script is invalid
    except:
        ...  # TODO #

    else:
        if psi.description:
            ...
