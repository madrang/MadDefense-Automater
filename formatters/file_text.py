import logging

from formatting import ReportOutput
from reporting import ErrorReport, ThreatReport

logger = logging.getLogger(__name__)

class FileTextOutput(ReportOutput):
    def __init__(self, filename):
        """ Create a new FileTextOutput formatter.

        Argument(s):
            filename:           -- The current file path to the text file.
        """
        self._filename = filename

    def __enter__(self):
        logger.debug(f"[+] Generating text output: {self._filename}")
        self._file = open(self._filename, "w")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        #self._file.write(f"No results in the {site.FriendlyName[index]} category\n")
        #self._file.write(f"{site.ReportString[index]} No results found\n")
        #self._file.write(f"No results found in the {site.FriendlyName}\n")
        logger.debug(f"{self._filename} Generated")
        self._file.close()

    def printResult(self, item):
        """ Formats site information correctly and prints it to an output file in text format.

        Argument(s):
            item --     Data point to report.

        Return value(s):
            Nothing is returned from this Method.
        """
        if not item:
            self._file.write(f"No results found!\n")
            return
        if isinstance(item, str)\
        or isinstance(item, list) or isinstance(item, dict)\
        or isinstance(item, ErrorReport):
            self._file.write(f"{item}\n")
            return

        if isinstance(item, ThreatReport):
            if not hasattr(self, "_target") or self._target != item.Target\
                or not hasattr(self, "_source") or self._source != item.Source:
                self._file.write(f"____________________    {item.Source.FriendlyName} - Results found for: {item.Target}     ____________________\n")
                self._source = item.Source
                self._target = item.Target

            self._file.write(f"{item.Entry.ReportString}: {item.Message}\n")
