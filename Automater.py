#!/usr/bin/python3
""" The Automater.py module defines the main() function for Automater.

Parameter Required is:
    target -- List one IP Address (CIDR or dash notation accepted), URL or Hash to query or pass the
                filename of a file containing IP Address info, URL or Hash to query each separated by a newline.

Optional Parameters are:
    -o, --output -- This option will output the results to a file.
    -b, --bot -- This option will output minimized results for a bot.
    -f, --cef -- This option will output the results to a CEF formatted file.
    -w, --web -- This option will output the results to an HTML file.
    -c, --csv -- This option will output the results to a CSV file.
    -d, --delay -- Change the delay to the inputted seconds. Default is 2.
    -s, --source -- Will only run the target against a specific source engine to pull associated domains.
                        Options are defined in the name attribute of the site element in the XML configuration file.
                            This can be a list of names separated by a semicolon.
    --proxy -- This option will set a proxy (eg. proxy.example.com:8080)
    -a --useragent -- Will set a user-agent string in the header of a web request.
                            is set by default to Automater/version
    -V, --vercheck -- This option checks and reports versioning for Automater.
                        Checks each python module in the Automater scope.
                            Default, (no -V) is False
    -r, --refreshxml -- This option refreshes the sites.xml file from the remote GitHub site.
                            Default (no -r) is False.
    -v, --verbose -- This option prints messages to the screen. Default (no -v) is False.

Class(es):
    Automater -- Main module

Function(s):
    main -- Provides the instantiation point for Automater.

Exception(s):
    No exceptions exported.

Fork of https://github.com/1aN0rmus/TekDefense-Automater
    By ian.ahl@tekdefense.com
"""
import logging
import logging.config
import sys
import tempfile
import os
import io

from argument_parser import Parser
from utilities import ConfigError, LoggerWriter, Utils
from tool import ToolFacade, Tool
from reporting import ErrorReport
from outputs import ReportingOutput
from inputs import TargetList

from tools.command import CmdTools
from tools.website import WebTools

__APPNAME__ = "MadDefense-Automater"
__VERSION__ = "0.1.1"
__GITLOCATION__ = "https://github.com/madrang/" + __APPNAME__
__GITFILEPREFIX__ = f"https://raw.githubusercontent.com/madrang/{__APPNAME__}/master/"

__SETTINGSXML__ = "settings.xml"
__TOOLSXML__ = "tools.xml"
__REMOTE_SITESXML_LOCATION__ = __GITFILEPREFIX__ + __TOOLSXML__

class Automater():
    """
    """
    logger = logging.getLogger("Automater")
        #TODO "hasBotOut": "BotOutputRequested"

    def __init__(self, **kwargs):
        self.Proxy = None
        Utils.copyattr(self, "Proxy", kwargs, "proxy")
        Utils.copyattr(self, "Delay", kwargs, "delay", 2)
        Utils.copyattr(self, "UserAgent", kwargs, "useragent", "CITDB/1.0")

    def getResults(self, toolsfac, targets, **kwargs):
        Utils.applydefault(kwargs
            , proxy = self.Proxy
            , delay = self.Delay
            , useragent = "CITDB/1.0"
        )
        targetList = TargetList.normalize(targets)
        return toolsfac.runAll(targetList, **kwargs)

    def refreshRemoteXML(self, checkOnly = False):
        """
            refreshremotexml -- true or false representing if Automater will refresh the tekdefense.xml file on each run.
        """
        localmd5 = None
        try:
            localmd5 = Utils.getHashOfLocalFile(__TOOLSXML__)
        except IOError:
            self.logger.error(f"Local file {__TOOLSXML__} not located."\
                              " Attempting download.")

        remotemd5 = None
        try:
            if checkOnly:
                remotemd5 = Utils.getHashOfRemoteFile(__REMOTE_SITESXML_LOCATION__, proxy = self.Proxy)
            else:
                remotemd5 = Utils.getRemoteFile(__REMOTE_SITESXML_LOCATION__, __TOOLSXML__, proxy = self.Proxy)
        except ConnectionError as ce:
            try:
                self.logger.error(f"Cannot connect to {__REMOTE_SITESXML_LOCATION__}."\
                                 f" Server response is {ce.message[0]} Server error"\
                                 f" code is {ce.message[1][0]}")
            except:
                self.logger.exception(f"Cannot connect to {__REMOTE_SITESXML_LOCATION__} to retreive the {__TOOLSXML__} for use.")
        except HTTPError as he:
            try:
                self.logger.error(f"Cannot connect to {__REMOTE_SITESXML_LOCATION__}."\
                                  f" Server response is {he.message}.")
            except:
                self.logger.exception(f"Cannot connect to {__REMOTE_SITESXML_LOCATION__} to retreive the {__TOOLSXML__} for use.")
        except:
            self.logger.exception(f"Cannot connect to {__REMOTE_SITESXML_LOCATION__} to retreive the {__TOOLSXML__} for use.")

        if not localmd5 or not remotemd5:
            return
        if remotemd5 != localmd5:
            self.logger.error(f"There is an updated remote {__TOOLSXML__} file at {__REMOTE_SITESXML_LOCATION__}."\
                              " Attempting download.")
        else:
            self.logger.error(f"Downloaded remote {__TOOLSXML__} file from {__REMOTE_SITESXML_LOCATION__}.")

    def checkModulesVersion(self):
        """
            Uses MD5 to indicate if any files needs to be updated.
        """
        execpath = os.path.dirname(os.path.realpath(__file__))
        pythonfiles = [f for f in os.listdir(execpath) if os.path.isfile(os.path.join(execpath, f)) and f[-3:] == ".py"]
        try:
            modifiedfiles = Utils.getModifiedFiles(
                        __GITFILEPREFIX__
                        , pythonfiles
                        , proxy = self.Proxy)
            if modifiedfiles is None or len(modifiedfiles) == 0:
                self.logger.debug("All Automater files are up to date")
            else:
                self.logger.warning(f"The following files require update: {", ".join(modifiedfiles)}."\
                                  f"\nSee {__GITLOCATION__} to update these files")
        except:
            self.logger.exception(f"There was an error while checking the version of the Automater files."\
                                 f" Please see {__GITLOCATION__} to check if the files are still online.")
            raise

if __name__ == "__main__":
    """ Serves as the instantiation point to start Automater.

    Argument(s):
        No arguments are required.

    Return value(s):
        Nothing is returned from this Method.
    """
    parser = Parser("IP, URL, and Hash Passive Analysis tool", __VERSION__)

    def filter_maker(level):
        level = getattr(logging, level)

        def filter(record):
            return record.levelno <= level

        return filter

    logConfig = Utils.getJSONDict(parser.LogFilename) if parser.LogFilename else None
    if not logConfig:
        logConfig = {
            "version": 1
          , "disable_existing_loggers": False
          , "formatters": {
                "simple": {
                    "class": "logging.Formatter"
                  , "format": "{name:^24.24}\u2503 {message}" if parser.Verbose else "{message}"
                  , "style": "{"
                }
              , "detailed": {
                    "class": "logging.Formatter"
                  , "datefmt": "%Y-%m-%d %H:%M:%S"
                  , "format": "{asctime:s}:{msecs:03.0f}‖{levelname:^5.8s}=>{name:^24s}-> {message:s}"
                  , "style": "{"
                }
            }
          , "filters": {
                "warnings_and_below": {
                    "()" : f"{__name__}.filter_maker"
                  , "level": "WARNING"
                }
            }
          , "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler"
                  , "level": "DEBUG" if parser.Verbose else "INFO"
                  , "formatter": "simple"
                  , "stream": "ext://sys.stdout"
                  , "filters": [ "warnings_and_below" ]
                }
              , "stderr": {
                    "class": "logging.StreamHandler"
                  , "level": "ERROR"
                  , "formatter": "simple"
                  , "stream": "ext://sys.stderr"
                }
              , "file": {
                    "class": "logging.FileHandler"
                  , "formatter": "detailed"
                  , "filename": os.path.join(tempfile.gettempdir(), __APPNAME__ + ".log")
                  , "mode": "a"
                }
            }
          , "root": {
                "level": "DEBUG"
              , "handlers": [
                    "stderr"
                  , "stdout"
                  , "file"
                ]
            }
        }
    logging.config.dictConfig(logConfig)

    # Logs prints statements by intercepting stdout & stderr.
    sys.stdout = LoggerWriter(logging.getLogger("sys.stdout"), logging.INFO)
    sys.stderr = LoggerWriter(logging.getLogger("sys.stderr"), logging.ERROR)

    automaterObj = Automater(
                    proxy = parser.Proxy
                )

    logger = logging.getLogger(__APPNAME__)
    logger.debug(f"[+] V{__VERSION__} -- Sources: {Utils.getHashOfLocalFile(__TOOLSXML__, hashname = "sha256")}")
    logger.debug(f"[+] Tools: {", ".join([t.__name__ for t in Tool.getList()])}")

    # if no target run and print help
    if not parser.Target:
        logger.fatal("[!] No argument given.")
        parser.print_help()
        sys.exit(1)

    if parser.VersionCheck:
        VersionChecker.checkModules()
    if parser.RefreshRemoteXML:
        automaterObj.refreshRemoteXML()

    # user may only want to run against one source - Use "*" for all sources.
    # is the seed used to check if the user did not enter an s tag
    sourcelist = parser.Source.split(";") if parser.Source else ["*"]

    # a file input capability provides a possibility of multiple lines of targets
    targetlist = []
    if parser.hasInputFile:
        try:
            targetlist.extend(TargetList.fromFile(parser.InputFile))
        except:
            logger.exception("There was an error reading from the target input file.")
            sys.exit(1)
    else:  # one target or list of range of targets added on console
        targetlist.extend(TargetList.normalize([ parser.Target ]))

    toolsfac = ToolFacade()
    try:
        toolsfac.loadXML(__TOOLSXML__, sourcelist)
    except Exception as error:
        raise ConfigError(f"A problem was found in the {__TOOLSXML__} file.\n"\
                        "There appears to be an invalid site entry in the Sites config."
                            , __TOOLSXML__) from error

    if not Utils.fileExists(__SETTINGSXML__):
        with io.open(__SETTINGSXML__, mode = "w") as file:
            file.write("<?xml version=\"1.0\"?>\n<automater_root>\n</automater_root>\n")
    try:
        toolsfac.loadXML(__SETTINGSXML__, sourcelist)
    except Exception as error:
        raise ConfigError(f"A problem was found in the {__SETTINGSXML__} file.\n"\
                        "There appears to be an invalid site entry in the Sites config."
                            , __SETTINGSXML__) from error

    tools = toolsfac.Tools
    if not tools or len(tools) <= 0:
        raise ConfigError(f"Unfortunately there is neither a {__TOOLSXML__} file nor a {__SETTINGSXML__} file that can be utilized for proper parsing.\n"\
                "At least one configuration XML file must be available for Automater to work properly.", __TOOLSXML__)

    reportFormatter = ReportingOutput(tools, parser)
    tools_config = {
        "*": {
           "delay": parser.Delay
        }
        , "": {
           "proxy": parser.Proxy
           , "useragent": parser.UserAgent
        }
        #TODO parser.hasBotOut
    }
    try:
        resultsFound = False
        hasErrors = False
        with reportFormatter.beingReport():
            for reportItem in automaterObj.getResults(toolsfac, targetlist, **tools_config):
                if isinstance(reportItem, ErrorReport):
                    hasErrors = True
                reportFormatter.printResult(reportItem)
                resultsFound = True
        if hasErrors:
            logger.fatal("Failed to complete all tests!")
            sys.exit(3)
        if not resultsFound:
            logger.warning("No results!")
            sys.exit(2)
    except ConfigError as error:
        error.add_note(f"Please see {__GITLOCATION__} for further instructions.")
        raise error
