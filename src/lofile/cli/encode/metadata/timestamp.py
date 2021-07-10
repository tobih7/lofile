# lool-File Format # CLI Encoder # Meta Data # Timestamp #

from loolclitools import Selector


class Timestamp:

    def _set_timestamp(self):
        try:
            self.timestamp = not Selector(("Yes", "No"), "Include creation date and time?", print_result=False, start_pos=int(not self.timestamp)).pos
        except KeyboardInterrupt:
            return
