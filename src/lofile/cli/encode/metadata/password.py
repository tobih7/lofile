# lool-File Format # CLI Encoder # Meta Data # Password #

import os
from loolclitools import Selector, askinput, flush, out, vline


class Password:

    def _set_password(self):

        if not self.is_password:
            self.__ask_password()

        else:
            try:
                s = Selector(("remove password", "new password", None, "initialization vector", "password validation", None, "back"), print_result=False).pos
            except KeyboardInterrupt:
                return

            if s == 0:
                self.password = None

            elif s == 1:
                self.__ask_password()

            elif s == 2:
                out(vline(), "\r\x1b[4C\x1b[96m  Current Initialization Vector  \x1b[0m")
                out("\n\n  ", repr(self.init_vector)[2:-1],
                    "\n\n  ", " ".join(("0" + hex(i)[2:])[-2:].upper() for i in self.init_vector))
                # UTF-8 representation
                try:
                    if bytes(ord(i) for i in self.init_vector.decode()) != self.init_vector:
                        # if the binary and the UTF-8 decoded representations differ, show this:
                        out("\n\n  UTF-8 decoded: ", self.init_vector.decode())
                except UnicodeDecodeError:
                    pass
                out("\n\n", vline(), "\n\n")

                try:
                    iv_sel = Selector(("enter as text", "enter as hexadecimal numbers", "random", None, "cancel"), print_result=False).pos
                except KeyboardInterrupt:
                    pass

                def iverr(msg):
                    out("\n  \x1b[91m\x1b[K", msg, "\x1b[0m\r\x1b[2A\x1b[K")
                    flush()

                # enter as text
                if iv_sel == 0:
                    out("\x1b[u  The initialization vector must have a length of 16.\n  Unicode characters will be encoded to UTF-8.\n\n")
                    while True:
                        try:
                            iv = askinput()
                        except KeyboardInterrupt:
                            break
                        else:
                            if len(iv.encode()) != 16:
                                iverr(f"Invalid length: {len(iv.encode())}")
                                flush()
                            else:
                                self.init_vector = iv.encode()
                                break

                # enter as hexadecimal numbers
                elif iv_sel == 1:
                    out("\x1b[u  The initialization vector must have a length of 16.\n\n  Expected syntax: \x1b[93m00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F\x1b[0m\n\n")
                    while True:
                        try:
                            iv = askinput()
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
                                    self.init_vector = iv
                                    break

                # random
                elif iv_sel == 2:
                    self.init_vector = os.urandom(16)

            elif s == 3:
                out("  If password validation is enabled a hash will be stored in the file header.\n" \
                    "  This hash can be used by the decoder to check a given password.\n" \
                    "  If it's missing, decoding with a wrong password will work, but the data will be invalid.\n\n" \
                    "  For maximum security this should be disabled, but it's not really a risk.\n\n" \
                    "  Currently: \x1b[93m", "enabled" if self.password_validation else "disabled", "\x1b[0m\n\n")

                try:
                    self.password_validation = not Selector(("Yes", "No"), "Use password validation?", print_result=False, start_pos=int(not self.password_validation)).pos
                except KeyboardInterrupt:
                    return



    def __ask_password(self):
        while True:
            try:
                pswd = askinput("Password: ", is_password=True).encode()
                out("\x1b[J", flush=True)
                if pswd == askinput("Confirm password: ", is_password=True).encode():
                    self.password = pswd
                    break
                else:
                    out("\x1b[91m  The passwords do not match!\x1b[0m\r\x1b[A\x1b[K\x1b[A\x1b[K")

            except KeyboardInterrupt:
                break
