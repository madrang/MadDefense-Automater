import csv
import logging

from formatting import ReportOutput
from reporting import ErrorReport, ThreatReport

logger = logging.getLogger(__name__)

class FileCSVOutput(ReportOutput):
    def __init__(self, filename):
        """ Create a new FileCSVOutput formatter.

        Argument(s):
            filename:           -- The current file path to the CSV file.
        """
        self._filename = filename

    def __enter__(self):
        logger.debug(f"[+] Generating CSV output: {self._filename}")
        self._file = open(self._filename, "w")
        self._csvRW = csv.writer(self._file, quoting = csv.QUOTE_ALL)
        self._csvRW.writerow(["Type", "Target", "Source", "Entry", "Result"])
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.debug(f"{self._filename} Generated")
        self._file.close()

    def printResult(self, item):
        """ Formats site information correctly and prints it to an output file with comma-seperators.

        Argument(s):
            item --     Data point to report.

        Return value(s):
            Nothing is returned from this Method.
        """
        if isinstance(item, str):
            return
        if isinstance(item, ErrorReport):
            return
        if isinstance(item, ThreatReport):
            self._csvRW.writerow([
                item.TargetType, item.Target
            , item.Source.FriendlyName
            , item.Entry.ReportString
            , "No results found" if item.Message is None or len(item.Message) <= 0 else item.Message
            ])
