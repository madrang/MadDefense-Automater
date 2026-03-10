""" The argument_parser.py module handles parsing the arguments that Automater requires.

Class(es):
    Parser -- Class to handle standard argparse functions with a class-based structure.

"""
import argparse

from utilities import Utils

class Parser:
    """ Parser represents an argparse object representing the program's input parameters.

    Public Method(s):
        print_help
        (Property) hasBotOut
        (Property) HTMLOutFile
        (Property) TextOutFile
        (Property) CSVOutFile
        (Property) Delay
        (Property) Proxy
        (Property) Target
        (Property) hasInputFile
        (Property) Source
        (Property) InputFile
        (Property) UserAgent

    Instance variable(s):
        _parser
        args
    """

    def __init__(self, desc, version):
        """ Class constructor.
            Adds the argparse info into the instance variables.

        Argument(s):
            desc -- ArgumentParser description.
        """
        self._parser = argparse.ArgumentParser(description = desc)
        self._parser.add_argument("target"
            , help = "List one IP Address (CIDR or dash notation accepted), URL or Hash to query or pass the filename"\
                " of a file containing IP Address info, URL or Hash to query each separated by a newline.")
        self._parser.add_argument("-o", "--output"
            , help = "This option will output the results to a file.")
        self._parser.add_argument("-b", "--bot", action = "store_true"
            , help = "This option will output minimized results for a bot.")
        self._parser.add_argument("-f", "--cef"
            , help = "This option will output the results to a CEF formatted file.")
        self._parser.add_argument("-w", "--web"
            , help = "This option will output the results to an HTML file.")
        self._parser.add_argument("-c", "--csv"
            , help = "This option will output the results to a CSV file.")
        self._parser.add_argument("-d", "--delay", type = int, default = 2
            , help = "This will change the delay to the inputted seconds. Default is 2.")
        self._parser.add_argument("-s", "--source"
            , help = "This option will only run the target against a specific source engine to pull associated domains."\
                    " Options are defined in the name attribute of the site element in the XML configuration file."\
                        " This can be a list of names separated by a semicolon.")
        self._parser.add_argument("--proxy"
            , help = "This option will set a proxy to use (eg. proxy.example.com:8080)")
        self._parser.add_argument("-a", "--useragent", default = f"Automater/{version}"
            , help="This option allows the user to set the user-agent seen by web servers being utilized."\
                    " By default, the user-agent is set to Automater/version")
        self._parser.add_argument("-V", "--vercheck", action = "store_true"
            , help="This option checks and reports versioning for Automater."\
                    " Checks each python module in the Automater scope.")
        self._parser.add_argument("-r", "--refreshxml", action = "store_true"
            , help = "This option refreshes the sites.xml file from the remote GitHub site.")
        self._parser.add_argument("-v", "--verbose", action = "store_true"
            , help = "This option prints debug messages to the screen.")
        self._parser.add_argument("-l", "--log", type = str
            , help = "Set the logging config file to use.")
        self.args = self._parser.parse_args()

    def print_help(self):
        """ Returns standard help information to determine usage for program.

        Argument(s):
            No arguments are required.

        Return value(s):
            string -- Standard argparse help information to show program usage.
        """
        self._parser.print_help()

    @property
    def hasBotOut(self):
        """ Checks to determine if user requested an output file minimized for use with a Bot.
            Returns True if user requested minimized Bot output, False if not.

        Return value(s):
            Boolean
        """
        return True if self.args.bot else False

    @property
    def CEFOutFile(self):
        """ Checks if there is an CEF output requested.
            Returns string name of CEF output file if requested or None if not requested.

        Return value(s):
            string -- Name of an output file to write to system.
            None -- if CEF output was not requested.
        """
        return self.args.cef if self.args.cef else None

    @property
    def CSVOutFile(self):
        """ Checks if there is a comma delimited output requested.
            Returns string name of comma delimited output file if requested or None if not requested.

        Return value(s):
            string -- Name of an comma delimited file to write to system.
            None -- if comma delimited output was not requested.
        """
        return self.args.csv if self.args.csv else None

    @property
    def HTMLOutFile(self):
        """ Checks if there is an HTML output requested.
            Returns string name of HTML output file if requested or None if not requested.

        Return value(s):
            string -- Name of an output file to write to system.
            None -- if web output was not requested.
        """
        return self.args.web if self.args.web else None

    @property
    def TextOutFile(self):
        """ Checks if there is a text output requested.
            Returns string name of text output file if requested or None if not requested.

        Return value(s):
            string -- Name of an output file to write to system.
            None -- if output file was not requested.
        """
        return self.args.output if self.args.output else None

    @property
    def VersionCheck(self):
        """ Checks to determine if the user wants the program to check for versioning.
            By default this is True which means the user wants to check for versions.

        Return value(s):
            Boolean
        """
        return True if self.args.vercheck else False

    @property
    def Verbose(self):
        """ Checks to determine if the user wants the program to send standard output to the screen.

        Return value(s):
            Boolean
        """
        return True if self.args.verbose else False

    @property
    def RefreshRemoteXML(self):
        """ Checks to determine if the user wants the program to grab the sites.xml information each run.

        Return value(s):
            Boolean
        """
        return True if self.args.refreshxml else False

    @property
    def Delay(self):
        """ Returns delay set by input parameters to the program.

        Return value(s):
            string -- String containing integer to tell program how long to delay between each site query.
                        Default delay is 2 seconds.
        """
        return self.args.delay

    @property
    def Proxy(self):
        """ Returns proxy set by input parameters to the program.

        Return value(s):
            string -- String containing proxy server in format server:port, default is none
        """
        return self.args.proxy if self.args.proxy else None

    @property
    def Target(self):
        """ Checks to determine the target info provided to the program.
            Returns string name of target or string name of file or None if a target is not provided.

        Return value(s):
            string -- String target info or filename based on target parameter to program.
        """
        return self.args.target if self.args.target else None

    @property
    def hasInputFile(self):
        """ Checks to determine if input file is the target of the program.
            Returns True if a target is an input file, False if not.

        Argument(s):
            No arguments are required.

        Return value(s):
            Boolean
        """
        return True if Utils.fileExists(self.args.target) else False

    @property
    def Source(self):
        """ Checks to determine if a source parameter was provided to the program.
            Returns string name of source or None if a source is not provided

        Return value(s):
            string -- String source name based on source parameter to program.
            None -- If the -s parameter is not used.
        """
        return self.args.source if self.args.source else None

    @property
    def InputFile(self):
        """ Checks to determine if an input file string representation of a target was provided as a parameter to the program.
            Returns string name of file or None if file name is not provided

        Return value(s):
            string -- String file name based on target filename parameter to program.
            None -- If the target is not a filename.
        """
        return None if not self.Target or not self.hasInputFile() else self.Target

    @property
    def UserAgent(self):
        """ Returns useragent setting invoked by user at command line or the default user agent provided by the program.

        Return value(s):
            string -- Name utilized as the useragent for the program.
        """
        return self.args.useragent

    @property
    def LogFilename(self):
        """ Returns log filename if set.

        Return value(s):
            string -- log config utilized by the program.
        """
        return self.args.log
