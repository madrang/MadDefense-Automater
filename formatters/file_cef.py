from datetime import datetime
import csv
import logging
import socket

from formatting import ReportOutput
from reporting import ErrorReport

logger = logging.getLogger(__name__)

class FileCEFOutput(ReportOutput):
    cef_Severity = "2"
    cef_fields = [
        " ".join([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            , socket.gethostname()
            ])                               # Prefix
        , "CEF:Version1.1"                  # CEF Version
        , "TekDefense"                      # Vendor
        , "Automater"                       # Product
        , "2.1"                             # Version
        , "0"                               # SignatureID
    ]

    def __init__(self, filename):
        """ Create a new ConsoleOutput formatter.

        Argument(s):
            filename:           -- The current file path to the CEF file.
        """
        self._filename = filename

    def __enter__(self):
        logger.debug(f"[+] Generating CEF output: {self._filename}")
        self._file = open(self._filename, "w")
        csv.register_dialect("escaped"
                            , delimiter = "|"
                            , escapechar = "\\"
                            , doublequote = False
                            , quoting = csv.QUOTE_NONE
                        )
        self._cefRW = csv.writer(self._file, "escaped")
        # self._cefRW.writerow(["Target", "Type", "Source", "Result"])
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.close()
        logger.debug(f"{self._filename} Generated")

    def printResult(self, item):
        """ Formats site information correctly and prints it to an output file in CEF format.
            CEF format specification from http://mita-tac.wikispaces.com/file/view/CEF+White+Paper+071709.pdf
            "Jan 18 11:07:53 host message"
        where message:
            "CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension"

        Argument(s):
            item --     Data point to report.

        Return value(s):
            Nothing is returned from this Method.
        """
        if isinstance(item, str):
            return
        if isinstance(item, ErrorReport):
            return

        pattern = r"^\[\+\]\s+"
        cef_kwargs = {
            "tgt": item.Target
            , "typ": item.TargetType
        }
        cef_kwargs["src"] = item.Entry.ReportString

        if item.Message is None or len(item.Message) <= 0:
            cef_kwargs["res"] = "No results found"
        else:
            cef_kwargs["res"] = item.Message

        self._cefRW.writerow(self.cef_fields + [
                    f"[{",".join([f"{key}={value}" for key, value in cef_kwargs.items()])}]"
                    , "1"
                    , item.Target
                ]
            )
