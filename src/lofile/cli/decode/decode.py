# lool-File Format # CLI Decoder #

from io import DEFAULT_BUFFER_SIZE
from lofile.core.shared import DataType
from os import chdir, path as ospath
from shutil import copyfileobj
from json import dumps
from loolclitools import (
    Selector,
    Timer,
    askinput,
    askpath,
    flush,
    out,
    param,
    vline,
    yesno,
)

from lofile.core import LofileError, Decoder
from lofile.cli.shared import LJUST, logger


def decode(filepath: str):
    timeouts = Timer()

    if filepath == None:  # else: already defined via command line argument
        filepath = askpath("File: ", must_be_file=True)
        out("\r\x1b[A\x1b[K")
    filepath = ospath.abspath(filepath)
    path, file = ospath.split(filepath)
    param("Path", path)
    param("File", file)
    del path, file
    out("\n")

    chdir(ospath.split(filepath)[0])

    try:
        with Decoder(open(filepath, "br")) as decoder:
            decoder.logger = None

            if decoder.description is not None:
                description = (
                    decoder.description.replace(b"\r\n", b"\n")
                    .decode("UTF-8")
                    .replace("\n", f"\n\x1b[{LJUST + 2}C")
                )
                param("Description", description, LJUST)
                if "\n" in description:
                    out("\n")

            if decoder.timestamp is not None:
                param("Timestamp", decoder.timestamp, LJUST)

            if decoder.tag is not None:
                param("Tag", decoder.tag.decode(), LJUST)

            param("Datatype", decoder.datatype.name, LJUST)

            param("Compressed", yesno(decoder.iscompressed), LJUST)
            param("Encrypted", yesno(decoder.isencrypted), LJUST)
            out("\n")

            if decoder.isencrypted:
                timeouts.start()
                decoder.password = askinput("Password: ", True).encode()
                timeouts.stop()
                out("\x1b[A\x1b[J")

            # change logger to show messages while decoding
            decoder.logger = logger

            out("  \x1b[93mDecoding ... \x1b[0m", flush=True)
            data = decoder.getdata()
            out("\r\x1b[J")
            decoder.logger = None

            # ===  RAW  === #
            if decoder.datatype == DataType.Raw:
                timeouts.start()
                s = Selector(
                    ("print to console", "save to file", "nothing"),
                    "What to do with the data?",
                    "->",
                    False,
                )
                timeouts.stop()

                # PRINT TO CONSOLE #
                if s == 0:
                    timeouts.start()
                    escaped = (
                        Selector(("raw", "escaped"), "How to print?", "->", False) == 1
                    )
                    timeouts.stop()
                    out("\x1b[2CData:\n" + vline() + "\n")
                    while buf := data.read(DEFAULT_BUFFER_SIZE):
                        out(str(buf)[2:-1] if escaped else buf.decode("ANSI"))
                        flush()
                    out("\n" + vline() + "\n")

                # SAVE TO FILE #
                elif s == 1:
                    path = filepath + ".raw.txt"
                    i = 0
                    while ospath.exists(path):
                        i += 1
                        path = filepath + f".{i}.raw.txt"
                    out("\x1b[2C\x1b[93mSaving ... ")
                    flush()
                    copyfileobj(data, open(path, "wb"))
                    out("\r\x1b[K")
                    param("Data saved to", path)

                # NOTHING #
                elif s == 2:
                    out("\x1b[A")

            # ===  JSON  === #
            elif decoder.datatype == DataType.JSON:
                timeouts.start()
                s = Selector(
                    ("print to console", "save to file", "nothing"),
                    "What to do with the data?",
                    "->",
                    False,
                )
                timeouts.stop()
                # SAVE TO FILE OR PRINT TO CONSOLE #
                if s != 2:
                    timeouts.start()
                    formatted = (
                        Selector(
                            ("Yes", "No"),
                            "Format data? (indentation, etc.)",
                            "->",
                            False,
                        )
                        == 0
                    )
                    timeouts.stop()
                    json_data = (
                        dumps(data, indent=4)
                        if formatted
                        else dumps(data, separators=(",", ":"))
                    )

                    # PRINT TO CONSOLE #
                    if s == 0:
                        out(
                            "\x1b[2C"
                            + ("Formatted data" if formatted else "Data")
                            + ":\n"
                            + vline()
                            + "\n"
                        )
                        out(json_data, "\n" + vline() + "\n")

                    # SAVE TO FILE #
                    elif s == 1:
                        path = filepath + ".json"
                        i = 0
                        while ospath.exists(path):
                            i += 1
                            path = filepath + f".{i}.json"
                        out("\x1b[2C\x1b[93mSaving ... ")
                        flush()
                        with open(path, "w") as file:
                            file.write(json_data)
                        out("\r\x1b[K")
                        param(
                            "Data "
                            + ("formatted and " if formatted else "")
                            + "saved to",
                            path,
                        )

                # NOTHING #
                elif s == 2:
                    out("\x1b[A")

            # ===  ARCHIVE  === #
            elif decoder.datatype == DataType.Archive:

                # functions have to be defined for decoding this datatype to reduce duplicated code
                # some options will be selectable multiple times
                # self-explanatory...

                # PREPERATION #
                def extract_all():
                    timeouts.start()
                    path = askpath("Path: ")
                    timeouts.stop()
                    out("\x1b[A\x1b[J\x1b[2C\x1b[93mExtracting ... ")
                    flush()
                    path = ospath.realpath(
                        ospath.normpath(
                            ospath.join(
                                path, ospath.splitext(ospath.split(filepath)[1])[0]
                            )
                        )
                    )
                    data.extract_all(path)
                    out("\r\x1b[K")
                    param("Files extracted to", path)

                def list_all_files():
                    max_path_length = max(len(i.path) for i in data.files)
                    out("\x1b[2C\x1b[96mList of all files:\x1b[0m\n")
                    elements = {}
                    for i in data.files:
                        if not i.is_dir:
                            elements[i.path] = f"{i.length:,d}", "byte" + (
                                "s" if i.length != 1 else ""
                            )
                        else:
                            elements[i.path + "\\"] = "0", "items"
                    max_num_length = max(
                        len(i[0]) for i in elements.values()
                    )  # max length of x bytes, items
                    for i in sorted(elements.keys(), key=str.casefold):
                        out(
                            f"\x1b[3C- {i}".ljust(max_path_length + 10),
                            f"\x1b[90m{elements[i][0].rjust(max_num_length)} {elements[i][1]}\x1b[0m\n",
                        )
                    out("\n")

                def list_root_directory():
                    dirs = (
                        {}
                    )  # contains each directory, each value is the number of subdirs and files inside the directory
                    files = (
                        {}
                    )  # contains each file, each value is the length (size) of the file
                    empty_dirs = []  # empty_dirs contains each empty dir once
                    for i in data.files:
                        path = i.path.partition(ospath.sep)
                        if path[
                            1
                        ]:  # if the path has subdirs or subfiles path[1] is "\\", so not empty
                            if path[0] in dirs.keys():  # increment counter
                                dirs[path[0]] += 1
                            else:  # create element
                                dirs[path[0]] = 1
                        else:  # else if path[1] is empty: path is file bc no subdirs or subfiles; but my be also empty dir
                            if i.is_dir:
                                empty_dirs.append(i.path)
                            else:
                                files[i.path] = i.length

                    elements = {}

                    for i in sorted(dirs.keys(), key=str.casefold):
                        elements[i + "\\"] = f"{dirs[i]:,d}", "item" + (
                            "s" if dirs[i] != 1 else ""
                        )
                    for i in empty_dirs:
                        elements[i + "\\"] = "0", "items"
                    for i in sorted(files.keys(), key=str.casefold):
                        elements[i] = f"{files[i]:,d}", "byte" + (
                            "s" if files[i] != 1 else ""
                        )

                    max_path_length = len(max(elements.keys(), key=len))

                    max_num_length = max(
                        len(i[0]) for i in elements.values()
                    )  # max length of x bytes, items

                    out("\x1b[2C\x1b[96mList of the root directory:\x1b[0m\n")

                    for i in elements.keys():
                        out(
                            f"\x1b[3C- {i}".ljust(max_path_length + 10),
                            f"\x1b[90m{elements[i][0].rjust(max_num_length)} {elements[i][1]}\x1b[0m\n",
                        )
                    out("\n")

                # funtion to check whether an spicific path exists in the archive
                filepaths_in_archive = {i.path: i for i in data.files if not i.is_dir}

                def ask_file_in_archive():
                    err = lambda msg: out(
                        f"\x1b[B\x1b[2C\x1b[J\x1b[91m{msg}\x1b[0m\x1b[u\x1b[K"
                    )
                    while True:
                        selected_file = askinput("File: ")
                        if not selected_file in filepaths_in_archive.keys():
                            err(f"This file does not exist!")
                        else:
                            out("\x1b[0m\x1b[J")
                            return filepaths_in_archive[selected_file]

                # function containing the loop, which is used after a directory listing
                def enter_after_list_loop():
                    while True:
                        timeouts.start()
                        s = Selector(
                            (
                                "extract all",
                                "extract specific file",
                                "list all files",
                                "list root directory",
                                "exit",
                            ),
                            print_result=False,
                        )
                        timeouts.stop()

                        # EXTRACT ALL #
                        if s == 0:
                            extract_all()
                            break

                        # EXTRACT SPECIFIC FILE #
                        elif s == 1:
                            timeouts.start()
                            selected_file = ask_file_in_archive()
                            path = askpath(f"Path: ")
                            timeouts.stop()
                            out("\x1b[2A\x1b[0m\x1b[J")

                            final_filepath = ospath.realpath(
                                ospath.normpath(
                                    ospath.join(
                                        path, ospath.split(selected_file.path)[1]
                                    )
                                )
                            )

                            if ospath.exists(final_filepath):
                                param("Cannot extract file to", final_filepath)
                                if ospath.isdir(final_filepath):
                                    param("Error", "The path is an existing directory!")

                                elif ospath.isfile(final_filepath):
                                    param("Error", "The specified file already exists!")
                                    out("\n")
                                    timeouts.start()
                                    overwrite = (
                                        Selector(
                                            ("Yes", "No"),
                                            "Overwrite?",
                                            print_result=False,
                                        )
                                        == 0
                                    )
                                    timeouts.stop()
                                    if overwrite:
                                        out("\x1b[2C\x1b[93mExtracting ... ")
                                        data.extract(selected_file, path, directly=True)
                                        out("\r\x1b[3A\x1b[J")
                                        param("File extracted to", final_filepath)
                                    else:
                                        out("\x1b[A")

                                else:  # links etc.
                                    param("Error", "The path is unavailable!")

                            else:
                                out("\x1b[2C\x1b[93mExtracting ... ")
                                data.extract(selected_file, path, directly=True)
                                out("\r\x1b[K")
                                param("File extracted to", final_filepath)

                            out("\n")

                        # LIST ALL FILES #
                        elif s == 2:
                            list_all_files()

                        # LIST ROOT DIRECTORY #
                        elif s == 3:
                            list_root_directory()

                        # EXIT #
                        elif s == 4:
                            out("\x1b[A")
                            break

                # START
                timeouts.start()
                s = Selector(
                    ("extract all", "list all files", "list root directory", "exit"),
                    print_result=False,
                )
                timeouts.stop()

                if s == 0:
                    extract_all()

                elif s == 1:
                    list_all_files()
                    enter_after_list_loop()

                elif s == 2:
                    list_root_directory()
                    enter_after_list_loop()

                elif s == 3:
                    out("\x1b[A")

            # the Timer "timeouts" stores all timeouts caused by userinputs
            # before exiting the context-manager this time is subtracted from the internal timer of the Decoder object
            decoder.subtract_from_took(timeouts.time)

            decoder.logger = None  # prevent from logging took time

        out("\n")
        param("Took", decoder.took)

    except LofileError as err:
        # when an LofileError occurs, and a logger is defined, it will be just logged
        # but if there is no logger defined at the time, the Decoder will raise an normal Exception
        logger(str(err), "ERROR")

    except KeyboardInterrupt:
        out("\r\x1b[K  \x1b[91mThe operation was canceled by the user!\x1b[0m\n")
