# lool-File Format # CLI Encoder # Meta Data # Compress #

from loolclitools import Selector, out


class Compress:
    def _set_compress(self):

        try:
            cmprs = Selector(
                ("Yes", "No", None, "Yes, with custom compression level", None, "back"),
                print_result=False,
            ).pos

        except KeyboardInterrupt:
            return

        if cmprs == 0:
            self.compress = True
            self._custom_compression_level_is_set = False

        elif cmprs == 1:
            self.compress = False
            self._custom_compression_level_is_set = False

        elif cmprs == 2:
            out(
                "  The default value is 6.\n\n  Simply pressing a number is possible.\n\n"
            )
            try:
                self.compression_level = (
                    Selector(
                        ("1", "2", "3", "4", "5", "6", "7", "8", "9"),
                        "Compression Level:",
                        print_result=False,
                        start_pos=self.compression_level - 1,
                    ).pos
                    + 1
                )
            except KeyboardInterrupt:
                return
            self.compress = True
            self._custom_compression_level_is_set = True
