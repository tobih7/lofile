# lool-File Format # CLI Encoder # Meta Data # Tag #

from loolclitools import getch, out

from lofile.core.shared import TAG_MAX_LENGTH, TAG_VALID_CHARS


class Tag:
    def _set_tag(self):

        tag = [*self.tag] if self.tag is not None else []
        rate_limit_reached = False

        out("  Tag: \x1b[96m", flush=True)
        if self.tag is not None:
            out(self.tag.decode("ASCII"), flush=True)

        while (char := ord(getch())) not in (0x03, 0x1B):  # CTRL+C, ESC

            if char in TAG_VALID_CHARS:
                if len(tag) < TAG_MAX_LENGTH:
                    tag.append(char)
                    out(chr(char), flush=True)
                # tag's length incremented above by one so maybe its now full, so new check is needed, else or elif not possible
                if len(tag) == TAG_MAX_LENGTH:
                    if not rate_limit_reached:
                        out(
                            "\x1b[s\r\x1b[2B\x1b[91m  Length limit reached!\x1b[96m\x1b[u",
                            flush=True,
                        )
                        rate_limit_reached = True

            elif char == 0x8 and tag:  # backspace
                tag.pop(-1)
                out("\b \b", flush=True)
                if rate_limit_reached:
                    rate_limit_reached = False
                    out("\x1b[s\r\x1b[2B\x1b[K\x1b[u", flush=True)

            elif char == 0xD:  # = \r = enter
                self.tag = bytes(tag) or None
                break

            elif char in (
                0x0,
                0xE0,
            ):  # keys like F keys, arrow keys, insert, delete, etc.
                getch()  # always another input follows: e.g. F5 is 0x0 and then 0x3F
