import logging

from formatting import ReportOutput
from reporting import ErrorReport, ThreatReport

logger = logging.getLogger(__name__)

class FileHTMLOutput(ReportOutput):
    def __init__(self, filename):
        """ Create a new FileHTMLOutput formatter.

        Argument(s):
            filename:           -- The current file path to the HTML file.
        """
        self._filename = filename

    def __enter__(self):
        logger.debug(f"[+] Generating HTML output: {self._filename}")
        self._file = open(self._filename, "w")
        self._file.write(self.getHTMLOpening())
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        #self._file.write(f"<tr><td>{site.Target}</td><td>{site.TargetType}</td><td>{site.FriendlyName}</td><td>No results found</td></tr>\n")
        self._file.write(self.getHTMLClosing())
        self._file.close()
        logger.debug(f"{self._filename} Generated")

    def printResult(self, item):
        """ Formats information report correctly and prints it to an output file using HTML markup.

        Argument(s):
            item --     Data point to report.

        Return value(s):
            Nothing is returned from this Method.
        """
        if isinstance(item, ThreatReport):
            self._file.write(f"<tr><td>{item.Target}</td><td>{item.TargetType}</td><td>{item.Source.FriendlyName}</td><td>{item.Entry.ReportString}:{"No results found" if item.Message is None or len(item.Message) <= 0 else item.Message}</td></tr>\n")

    def getHTMLOpening(self):
        """ Creates HTML markup to provide correct formatting for initial HTML file requirements.

        Argument(s):
            No arguments required.

        Return value(s):
            string -- contains opening HTML markup information for HTML output file.
        """
        return """<style type="text/css">
    #table-3 {
        border: 1px solid #DFDFDF;
        background-color: #F9F9F9;
        width: 100%;
        -moz-border-radius: 3px;
        -webkit-border-radius: 3px;
        border-radius: 3px;
        font-family: Arial,"Bitstream Vera Sans",Helvetica,Verdana,sans-serif;
        color: #333;
    }
    #table-3 td, #table-3 th {
        border-top-color: white;
        border-bottom: 1px solid #DFDFDF;
        color: #555;
    }
    #table-3 th {
        text-shadow: rgba(255, 255, 255, 0.796875) 0px 1px 0px;
        font-family: Georgia,"Times New Roman","Bitstream Charter",Times,serif;
        font-weight: normal;
        padding: 7px 7px 8px;
        text-align: left;
        line-height: 1.3em;
        font-size: 14px;
    }
    #table-3 td {
        font-size: 12px;
        padding: 4px 7px 2px;
        vertical-align: top;
    }res
    h1 {
        text-shadow: rgba(255, 255, 255, 0.796875) 0px 1px 0px;
        font-family: Georgia,"Times New Roman","Bitstream Charter",Times,serif;
        font-weight: normal;
        padding: 7px 7px 8px;
        text-align: Center;
        line-height: 1.3em;
        font-size: 40px;
    }
    h2 {
        text-shadow: rgba(255, 255, 255, 0.796875) 0px 1px 0px;
        font-family: Georgia,"Times New Roman","Bitstream Charter",Times,serif;
        font-weight: normal;
        padding: 7px 7px 8px;
        text-align: left;
        line-height: 1.3em;
        font-size: 16px;
    }
    h4 {
        text-shadow: rgba(255, 255, 255, 0.796875) 0px 1px 0px;
        font-family: Georgia,"Times New Roman","Bitstream Charter",Times,serif;
        font-weight: normal;
        padding: 7px 7px 8px;
        text-align: left;
        line-height: 1.3em;
        font-size: 10px;
    }
</style>
<html>
    <body>
        <title> Automater Results </title>
        <h1> Automater Results </h1>
        <table id="table-3">
            <tr>
            <th>Target</th>
            <th>Type</th>
            <th>Source</th>
            <th>Result</th>
            </tr>
"""

    def getHTMLClosing(self):
        """ Creates HTML markup to provide correct formatting for closing HTML file requirements.

        Argument(s):
            No arguments required.

        Return value(s):
            string -- contains closing HTML markup information for HTML output file.
        """
        return """        </table>
        <br><br>
        <p>Created using Automater.py <a href="https://github.com/madrang/MadDefense-Automater">https://github.com/madrang/MadDefense-Automater</a></p>
    </body>
</html>"""
