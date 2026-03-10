"""
"""
import logging
import subprocess
import types

from inputs import AbstractContent, SourceDescription, TargetList
from parsing import ContentParser
from reporting import ErrorReport, ThreatReport
from tool import Tool

from utilities import Utils

logger = logging.getLogger(__name__)

class CmdTools(Tool):
    """
    """
    def __init__(self):
        self._cmds = {}

    @property
    def Commands(self):
        """
        """
        return self._cmds if self._cmds else None

    def loadXML(self, filename, xmltree, sourcelist = None, **kwargs):
        for cmd_element in xmltree.iter(tag = "cmd"):
            cmd_name = cmd_element.get("name")
            if not isinstance(cmd_name, str) or len(cmd_name) <= 0:
                raise ConfigError("Command name is missing!", key_name = "cmd.name")
            if sourcelist.index("*") < 0 and sourcelist.index(cmd_name) < 0:
                continue
            if (cmd_element.get("disable")):
                logger.debug(f"Skipping {filename}:{cmd_name} disabled. {cmd_element.get("disable")}")
                continue
            logger.debug(f"Reading {filename}:{cmd_name}...")
            site = self._cmds.get(cmd_name)
            site_args = Command.buildFromXML(cmd_element, **kwargs)
            if site:
                site.loadArgs(**site_args)
            else:
                site = Command(**site_args)
                self._cmds.update(**{ site.FriendlyName: site })
            for src_element in cmd_element.findall("source"):
                src_type = src_element.get("type")
                site.Sources.update(**{
                    src_type: SourceDescription(**{
                        "source": src_element.text
                        , "type": src_type
                    })
                })
            for content_element in cmd_element.findall("content"):
                content_parser = ContentParser.buildFromXML(content_element)
                site.Parsers.append(content_parser)
        return self

    def getReport(self, cmd, target):
        if isinstance(cmd, str):
            logger.debug(f"Getting content from {cmd}")
            cmd = self.Commands[cmd]
        else:
            logger.debug(f"Getting content from {cmd.FriendlyName}")
        cmdContent = cmd.getContent(target)
        if not cmdContent:
            logger.debug(f"No content returned by {cmd.FriendlyName}")
            yield None
        elif isinstance(cmdContent, ErrorReport):
            yield cmdContent
        else:
            for report in cmd.parseContent(cmdContent, target):
                #if isinstance(report, ThreatReport):
                #    report.TargetType = target.Type
                yield report

    def run(self, target, **kwargs):
        cmds_dict = self.Commands
        if not cmds_dict: return None
        for cmd_name in cmds_dict:
            for report in self.getReport(cmds_dict[cmd_name], target):
                yield report

class Command(AbstractContent):
    PROPS_MAP = {
        "_friendlyName": "friendlyname"
        , "_name": "name"
        , "_delay": "delay"
        , "_botOutputRequested": "botoutputrequested"
        , "_sources": "sources"
    }
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loadArgs(**kwargs)
        if not hasattr(self, "_friendlyName"):
            raise ValueError("'name' argument is missing!")

    def loadArgs(self, **kwargs):
        for propName in Command.PROPS_MAP:
            Utils.copyattr(self, propName, kwargs, Command.PROPS_MAP[propName])
        return self

    @classmethod
    def buildFromXML(cls, site_element, **kwargs):
        siteArgs = {
            "friendlyname": site_element.get("name")
            , "name": site_element.get("short")
        }
        for argName in kwargs:
            siteArgs[argName] = kwargs[argName]
        return siteArgs

    @property
    def FriendlyName(self):
        """ Returns the string representing a friendly string name.

        Return value(s):
            string -- representing friendly name for a tag for reporting.
        """
        return self._friendlyName

    @property
    def Name(self):
        """ Returns the short string representing a name.

        Return value(s):
            string -- representing a name for a Site for reporting.
        """
        if self._name is None:
            return self._friendlyName
        return self._name

    def getContent(self, target, source = None):
        if source is None:
            target_type = TargetList.identifyTargetType(target, tools = Tool.getList())
            source = self.Sources.get(target_type, self.Sources.get("*"))
            if source is None:
                logger.debug(f"[-] Skipping {self.FriendlyName}, {target_type} not supported.")
                return None

        #if self._delay:
        #    time.sleep(self._delay)
        logger.debug(f"[*] running {self.FriendlyName}")

        cmdArgs = source.withTarget(target).split(" ")
        proc = subprocess.run(cmdArgs, stdout = subprocess.PIPE
                                     , stderr = subprocess.STDOUT)
        procstr = proc.stdout.decode(encoding="utf8")
        if proc.returncode != 0:
            logger.error(f"{self.FriendlyName} failed, exitcode {proc.returncode}\n{procstr}\n")
            return ErrorReport(message = f"{self.FriendlyName} failed, exitcode {proc.returncode}")
        return procstr

    def parseContent(self, content, target):
        if len(self.Parsers) <= 0:
            logger.warning(f"Command '{self.FriendlyName}' has no parsers.")
            yield content
        else:
            try:
                foundContent = False
                for parser in self.Parsers:
                    for content in parser.parseContent(content, target):
                        foundContent = True
                        if isinstance(content, dict):
                            yield ThreatReport(source = self, **content)
                        else:
                            yield content
                if not foundContent:
                    yield ErrorReport(f"No content found using {self.FriendlyName}")
            except:
                logger.exception(f"Error while parsing {self.FriendlyName}")
                yield ErrorReport(f"[-] Cannot scrape {self.FriendlyName}")
