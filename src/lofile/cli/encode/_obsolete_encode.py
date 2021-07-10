# lool-File Format # CLI Encoder #


# ===  IMPORTS  === #
import os
from msvcrt import getch
from loolclitools import Selector, askinput, console_input, flush, out, param, vline, yesno

from lofile.cli.shared import logger
from lofile.core import Encoder
from lofile.core.shared import DataType, LofileError, LogLvl, TAG_MAX_LENGTH, TAG_VALID_CHARS



# ===  ENCODE  === #
def encode(filepath: str):

    if filepath == None: # else: already defined via command line argument
        filepath = askpath_and_validate()
        # no need to clean these lines here, will be overwritten in loop

    try:
        with Encoder() as encoder:
            # default/start values
            encoder.logger = None
            datatype = DataType.Raw
            o = 0

            # parsing functions
            def parsed_description() -> str:
                if not encoder.description:
                    # description is None or "", but the Encoder will ignore it if its "", so its basically also None
                    return "\x1b[96mNo"
                else:
                    dsc = encoder.description.splitlines()
                    return "\x1b[0m" + dsc[0][:32].decode() + \
                        (" \x1b[90m... " if len(dsc[0]) > 32 or len(dsc) > 1 else "") + \
                        (f"({len(dsc)-1} more line" + ("s" if len(dsc)-1 > 1 else "") + ")" if len(dsc) > 1 else "")

            def parsed_options() -> str:
                return (
                    f"Output File\x1b[24m:          \x1b[96m{filepath}",
                    f"Datatype\x1b[24m:             \x1b[96m{datatype.name}",
                    "",
                    "Description\x1b[24m:          " + parsed_description(),
                    "Tag\x1b[24m:                  " + (encoder.tag.decode() if encoder.tag is not None else "\x1b[96mNo"),
                    f"Store Timestamp\x1b[24m:      \x1b[96m{yesno(encoder.timestamp)}",
                    "",
                    f"Password\x1b[24m:             \x1b[96m{yesno(encoder.is_password)}",
                    f"Compress\x1b[24m:             \x1b[96m{yesno(encoder.compress)} \x1b[90m(level = {encoder.compression_level})", # TODO: don't show level always; var which is True when custom level is set, even 6, False wenn compression is just enabled
                )

            # loop
            while True:
                out("\x1b[4;2H\x1b[J") # using absolute positions instead of relative ones (via \x1b[u) because \1b[s may be used during the loop and the saved position would be invalid

                o = Selector(("\x1b[92mconfirm and proceed", "", *parsed_options()), print_result=False, start_pos=o).pos
                out("\x1b[4H")


                if o == 0:
                    break

                elif o == 1: # output file
                    path, file = os.path.split(os.path.abspath(filepath))
                    out(vline(), "\r\x1b[4C\x1b[96m  Current Output File  \x1b[0m\n\n")
                    param("Path", path)
                    param("Name", file)
                    out("\n", vline(), "\n\n")
                    del path, file
                    try:
                        s = Selector(("change output file", "back"), print_result=False, can_terminate=False).pos
                    except KeyboardInterrupt:
                        continue
                    if not s: # so 0, index 0 = first option
                        try:
                            filepath = askpath_and_validate(can_terminate=False)
                        except KeyboardInterrupt:
                            continue



                elif o == 2: # datatype
                    try:
                        datatype = DataType[Selector((i.name for i in DataType), "Datatype:", print_result=False, can_terminate=False, start_pos=datatype.value // 4).result]
                    except KeyboardInterrupt:
                        continue

                elif o == 3: # description
                    def set_desc():
                        out("\x1b[s")
                        encoder.description = console_input(header="The description can have a maximum length of 512 bytes.").encode("UTF-8")[:512]
                        out("\x1b[u")

                    if encoder.description is None:
                        set_desc()
                    else:
                        out(vline(), "\r\x1b[4C\x1b[96m  Current Description  \x1b[0m\n", *("  " + line for line in encoder.description.decode().splitlines(keepends=True)), "\n", vline(), "\n\n")
                        try:
                            s = Selector(("clear description", "new description", "back"), print_result=False, can_terminate=False).pos
                        except KeyboardInterrupt:
                            continue
                        else: # this else is not mandatory, aber egal
                            if s == 0:
                                encoder.description = None
                            elif s == 1:
                                set_desc()

                elif o == 4: # tag
                    tag = [*encoder.tag] if encoder.tag is not None else []
                    rate_limit_reached = False
                    out("  Tag: \x1b[96m", flush=True)
                    if encoder.tag is not None:
                        out(encoder.tag.decode("ASCII"), flush=True)

                    while (char := ord(getch())) not in (0x03, 0x1b): # CTRL+C, ESC
                        if char in TAG_VALID_CHARS:
                            if len(tag) < TAG_MAX_LENGTH:
                                tag.append(char)
                                out(chr(char), flush=True)
                            # tag's length incremented above by one so maybe its now full, so new check is needed, else or elif not possible
                            if len(tag) == TAG_MAX_LENGTH:
                                if not rate_limit_reached:
                                    out("\x1b[s\r\x1b[2B\x1b[91m  Length limit reached!\x1b[96m\x1b[u", flush=True)
                                    rate_limit_reached = True

                        elif char == 0x8 and tag:
                            tag.pop(-1)
                            out("\b \b", flush=True)
                            if rate_limit_reached:
                                rate_limit_reached = False
                                out("\x1b[s\r\x1b[2B\x1b[K\x1b[u", flush=True)

                        elif char == 0xD: # = \r = enter
                            encoder.tag = bytes(tag) or None
                            break

                        elif char in (0x0, 0xe0): # keys like F keys, arrow keys, insert, delete, etc.
                            getch() # always another input follows: e.g. F5 is 0x0 and then 0x3F

                elif o == 5: # store timestamp
                    try:
                        encoder.timestamp = not Selector(("Yes", "No"), "Include creation date and time?", print_result=False, can_terminate=False, start_pos=int(not encoder.timestamp)).pos
                    except KeyboardInterrupt:
                        continue

                elif o == 6: # password
                    def set_pswd():
                        while True:
                            try:
                                pswd = askinput("Password: ", is_password=True, can_terminate=False).encode()
                                if pswd == askinput("Confirm password: ", is_password=True, can_terminate=False).encode():
                                    encoder.password = pswd
                                    break
                                else:
                                    out("\n\x1b[91m  The passwords do not match!\x1b[0m\r\x1b[2A\x1b[K\x1b[A\x1b[K")
                            except KeyboardInterrupt:
                                break

                    if not encoder.is_password:
                        set_pswd()

                    else:
                        try:
                            s = Selector(("remove password", "new password", "", "initialization vector", "password validation", "", "back"), print_result=False, can_terminate=False).pos
                        except KeyboardInterrupt:
                            continue
                        else:
                            if s == 0:
                                encoder.password = None

                            elif s == 1:
                                set_pswd()

                            elif s == 2:
                                out(vline(), "\r\x1b[4C\x1b[96m  Current Initialization Vector  \x1b[0m")
                                out("\n\n  ", repr(encoder.init_vector)[2:-1],
                                    "\n\n  ", " ".join(("0" + hex(i)[2:])[-2:].upper() for i in encoder.init_vector))
                                # UTF-8 representation
                                try:
                                    if bytes(ord(i) for i in encoder.init_vector.decode()) != encoder.init_vector:
                                        # if the binary and the UTF-8 decoded representations differ, show this:
                                        out("\n\n  UTF-8 decoded: ", encoder.init_vector.decode())
                                except UnicodeDecodeError:
                                    pass
                                out("\n\n", vline(), "\n\n")

                                try:
                                    iv_sel = Selector(("enter as text", "enter as hexadecimal numbers", "random", "", "cancel"), print_result=False, can_terminate=False).pos
                                except KeyboardInterrupt:
                                    pass
                                else:
                                    def iverr(msg):
                                        out("\n  \x1b[91m\x1b[K", msg, "\x1b[0m\r\x1b[2A\x1b[K")
                                        flush()

                                    # enter as text
                                    if iv_sel == 0:
                                        out("\x1b[u  The initialization vector must have a length of 16.\n  Unicode characters will be encoded to UTF-8.\n\n")
                                        while True:
                                            try:
                                                iv = askinput("", can_terminate=False)
                                            except KeyboardInterrupt:
                                                break
                                            else:
                                                if len(iv.encode()) != 16:
                                                    iverr(f"Invalid length: {len(iv.encode())}")
                                                    flush()
                                                else:
                                                    encoder.init_vector = iv.encode()
                                                    break

                                    # enter as hexadecimal numbers
                                    elif iv_sel == 1:
                                        out("\x1b[u  The initialization vector must have a length of 16.\n\n  Expected syntax: \x1b[93m00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F\x1b[0m\n\n")
                                        while True:
                                            try:
                                                iv = askinput("", can_terminate=False)
                                            except KeyboardInterrupt:
                                                break
                                            else:
                                                try:
                                                    iv = bytes(int(i, 16) for i in iv.split(" ") if i) # the if i will allow multiple spaces as seperator
                                                except ValueError:
                                                    iverr("Parsing Error!")
                                                else:
                                                    if len(iv) != 16:
                                                        iverr(f"Invalid length: {len(iv)}")
                                                        flush()
                                                    else:
                                                        encoder.init_vector = iv
                                                        break

                                    # random
                                    elif iv_sel == 2:
                                        encoder.init_vector = os.urandom(16)

                            elif s == 3:
                                out("  If password validation is enabled a hash will be stored in the file header.\n" \
                                    "  This hash can be used by the decoder to check a given password.\n" \
                                    "  If it's missing decoding with a wrong password will work, but the data will be invalid.\n\n" \
                                    "  For maximum security this should be disabled, but it's not really a risk.\n\n" \
                                    "  Currently: \x1b[93m", "enabled" if encoder.password_validation else "disabled", "\x1b[0m\n\n")

                                try:
                                    encoder.password_validation = not Selector(("Yes", "No"), "Use password validation?", print_result=False, can_terminate=False).pos
                                except KeyboardInterrupt:
                                    continue


                elif o == 7: # compress
                    try:
                        cmprs = Selector(("Yes", "No", "", "Yes, with custom encryption level", "", "back"), print_result=False, can_terminate=False).pos
                    except KeyboardInterrupt:
                        pass
                    else:
                        if cmprs == 0:
                            encoder.compress = True
                        elif cmprs == 1:
                            encoder.compress = False
                        elif cmprs == 2:
                            out("  The default value is 6.\n\n  Simply pressing a number is also possible.\n\n")
                            try:
                                lvl = Selector(("1", "2", "3", "4", "5", "6", "7", "8", "9"), "Compression Level:", print_result=False, can_terminate=False).pos
                            except KeyboardInterrupt:
                                continue
                            else:
                                encoder.compress = True
                                encoder.compression_level = lvl + 1

            # next step: ask data
            ...
            ...
            ...

            # TODO: in encoder and decoder, implement: lofile errors are raised as normal exceptions!
            # now they are logged sometimes, this is bad, program does not stop then, just raise them

            # next step: write data
            out("\x1b[3A", (sep := "\n  \x1b[0m"), *parsed_options(), "\n", sep=sep)

            # change logger to show messages while encoding
            encoder.logger = logger
            encoder.reset_timer()

            # finally create data
            out("  \x1b[93mEncoding ... \x1b[0m", flush=True)
            encoder.write(open(filepath, "wb"), raw=b"ur mom"*1024**2*50, json="")
            out("\r\x1b[J")
            encoder.logger = None # prevent from logging took time


        param("Took", encoder.took)


    except LofileError as err:
        # when an LofileError occurs, and a logger is defined, it will be just logged
        # but if there is no logger defined at the time, the Decoder will raise an normal Exception
        logger(str(err), LogLvl.ERROR)

    except KeyboardInterrupt:
        out("\r\x1b[K  \x1b[91mThe operation was canceled by the user!\x1b[0m\n")






# modified version of loolclitools.askpath (from version 1.2.2 / 06.03.2021)
def askpath_and_validate():
    out("\x1b[0m\x1b[s")
    err = lambda msg: out(f"\x1b[B\x1b[2C\x1b[J\x1b[91m{msg}\x1b[0m\x1b[u\x1b[K")

    while True:
        filepath = askinput("Output File: ").strip()

        # remove " and ' from start and end
        if filepath and filepath[0] in ('"', "'") and filepath[-1] in ('"', "'"):
            filepath = filepath[1:-1]

        # validate
        if not filepath:
            out("\x1b[A\x1b[K")
            continue

        elif os.path.exists(filepath):
            if os.path.isfile(filepath):
                if os.stat(filepath).st_size != 0: # if its not empty: ask to overwrite
                    out("\n\x1b[J")
                    if Selector(("Yes", "No"), "The file already exists! Overwrite?", print_result=False) == 1: # shouldn't overwrite
                        # Selector uses \x1b[s so the saved cursor pos was overridden, return manually
                        out("\x1b[2A\x1b[s\x1b[K")
                        continue
                    else:
                        out("\x1b[1A") # Selector moves down once, go back up
            elif os.path.isdir(filepath):
                err(f"This path is an existing directory!")
                continue
            else:
                err(f"This path is invalid!")
                continue

        elif filepath.endswith(os.path.sep):
            err("The path is a directory, not a file!")
            continue

        # check access
        try:
            open(filepath, "wb").close()
        except FileNotFoundError:
            err("The file's directory does not exist!")
        except PermissionError:
            err("Permission to this path was denied!")
        except OSError as exc:
            err(f"The path is invalid!\n\x1b[2C\x1b[90mError {exc.errno}: {exc.strerror}") # exc.strerror is same as os.strerror(exc.errno)
        else:
            os.remove(filepath) # file will be recreated when needed
            out("\x1b[0m\x1b[J")
            return filepath

