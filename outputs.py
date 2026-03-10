"""
The outputs.py module represents some form of all outputs from the Automater program to include all variation of output files.
Any addition to the Automater that brings any other output requirement should be programmed in this module.

Class(es):
    SiteDetailOutput -- Wrapper class around all functions that print output from Automater,
                        to include standard output and file system output.

Function(s):
    No global exportable functions are defined.

Exception(s):
    No exceptions exported.
"""
from contextlib import contextmanager, ExitStack
import logging
from operator import attrgetter
import re

from formatting import ReportOutput

from formatters.file_cef import FileCEFOutput
from formatters.file_csv import FileCSVOutput
from formatters.file_html import FileHTMLOutput
from formatters.file_text import FileTextOutput

from reporting import ErrorReport, ThreatReport
from utilities import Utils

OUTPUT_REPLACEMENTS = [
    ["www."  , "www[.]"]
  , ["https:", "h##ps:"]
  , ["http:" , "h##p:" ]
  , ["ftp:"  , "f#p:"  ]
]

class ReportingOutput:
    """ SiteDetailOutput provides the capability to output information using different formats.

    Public Method(s):
        PrintResult    -- Print result reports.

    Instance variable(s):
        _sources            - dictionary storing the data sources availables.
    """
    def __init__(self, sourcesdict, config = None):
        """ Class constructor.
            Stores the incoming list of sites in the _listofsites list.

        Argument(s):
            sourcesdict -- dictionary containing data sources informations.
            config      -- Config object storing program input parameters used when program was run.
        """
        self._sources = sourcesdict
        self.formatters = [
            OutputLog(format = "bot" if config.hasBotOut else "std")
        ]
        if config is None:
            return
        if config.TextOutFile:
            self.formatters.append(
                FileTextOutput(config.TextOutFile)
            )
        if config.CEFOutFile:
            self.formatters.append(
                FileCEFOutput(config.CEFOutFile)
            )
        if config.CSVOutFile:
            self.formatters.append(
                FileCSVOutput(config.CSVOutFile)
            )
        if config.HTMLOutFile:
            self.formatters.append(
                FileHTMLOutput(config.HTMLOutFile)
            )

    @property
    def Sources(self):
        """ Checks instance variable _sources for content.
            Returns _sources if it has content or None if it does not.

        Return value(s):
            _sources          -- dictionary containing sources of results if variable contains data.
        """
        return None if self._sources is None or len(self._sources) == 0 else self._sources

    @contextmanager
    def beingReport(self, header = None, tail = None):
        with ExitStack() as stack:
            formatters = [ stack.enter_context(fmt) for fmt in self.formatters ]
            if header is not None:
                for fmt in formatters:
                    fmt.PrintResult(header)
            yield formatters
            if tail is not None:
                for fmt in formatters:
                    fmt.PrintResult(tail)

    def printResult(self, item):
        for fmt in self.formatters:
            fmt.printResult(item)

class OutputLog(ReportOutput):
    def __init__(self, format = "bot"):
        """ Create a new OutputLog formatter.

        Argument(s):
            format:           -- The current format name to use.
                     bot      -- Minimized output.
        """
        self.format = format
        self._logger = logging.getLogger(__name__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(self, "_target") or self._target is None:
            #print(f"No results in the {site.FriendlyName[index]} category")
            #print(f"{site.ReportString[index]} No results found")
            #print(f"No results found in the {site.FriendlyName}")
            return

    def printResult(self, item):
        """ Calls correct function to ensure site information is printed to the user's standard output correctly.

        Argument(s):
            item --     Report result information to be printed.

        Return value(s):
            Nothing is returned from this Method.
        """
        if self.format == "bot":
            self.PrintToScreenBot(item)
        elif self.format == "std":
            self.PrintToScreen(item)
        else:
            raise ValueError(f"format supported: bot, std. Value: {self.format}")

    def PrintToScreenBot(self, item):
        """ Formats site information minimized and prints it to the user's standard output.

        Argument(s):
            No arguments are required.

        Return value(s):
            Nothing is returned from this Method.
        """
        if not hasattr(self, "_target") or self._target != item.Target:
            self._logger.info(f"**_ Results found for: {site.Target} _**\n")
            self._target = site.Target

        site_importantProperty = site.getImportantProperty()
        sourceurlhasnoreturn = True
        for answer in site_importantProperty:
            if answer is not None and len(answer) > 0:
                sourceurlhasnoreturn = False
        if sourceurlhasnoreturn:
            self._logger.debug(f"[+] {site.SourceURL} No results found")
            return

        if site_importantProperty is None or len(site_importantProperty) == 0:
            self._logger.debug(f"No results in the {site.FriendlyName[index]} category")
            return

        if site_importantProperty[index] is None or len(site_importantProperty[index]) == 0:
            print(f"{site.ReportString[index]} No results found")
            return

        # if it's just a string we don't want it output like a list
        if isinstance(site_importantProperty[index], str):
            print(f"{site.ReportString[index]} {Utils.replaceAll(site_importantProperty, *OUTPUT_REPLACEMENTS)}")

        # must be a list since it failed the isinstance check on string
        else:
            laststring = ""
            for siteresult in site_importantProperty[index]:
                if f"{site.ReportString[index]} {siteresult}" != laststring:
                    print(f"{site.ReportString[index]} {Utils.replaceAll(siteresult, *OUTPUT_REPLACEMENTS)}")
                    laststring = f"{site.ReportString[index]} {siteresult}"

        site_importantProperty = site.getImportantProperty()

        if self._target != site.Target:
            print(f"\n**_ Results found for: {site.Target} _**")
            self._target = site.Target

        if site_importantProperty is None or len(site_importantProperty) == 0:
            print(f"[+] {site.FriendlyName} No results found")
            return

        #if it's just a string we don't want it output like a list
        if isinstance(site_importantProperty, str):
            print(f"{site.ReportString} {Utils.replaceAll(site_importantProperty, *OUTPUT_REPLACEMENTS)}")
        else: # must be a list since it failed the isinstance check on string
            laststring = ""
            for siteresult in site_importantProperty:
                if f"{site.ReportString} {siteresult}" != laststring:
                    print(f"{site.ReportString} {Utils.replaceAll(siteresult, *OUTPUT_REPLACEMENTS)}")
                    laststring = f"{site.ReportString} {siteresult}"

    def PrintToScreen(self, item):
        """ Formats site information correctly and prints it to the user's standard output.

        Argument(s):
            No arguments are required.

        Return value(s):
            Nothing is returned from this Method.
        """
        if isinstance(item, ErrorReport) or not isinstance(item, ThreatReport)\
        or isinstance(item, str):
            print(item)
            return

        if not hasattr(self, "_source") or self._source != item.Source\
            or not hasattr(self, "_target") or self._target != item.Target:
            print(f"____________________    {item.Source.FriendlyName} - Results found for: {item.Target}     ____________________")
            self._source = item.Source
            self._target = item.Target

        print(f"{item.Entry.ReportString}: {Utils.replaceAll(item.Message, *OUTPUT_REPLACEMENTS)}")
