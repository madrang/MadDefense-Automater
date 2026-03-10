""" The tool.py module provides tools lookup
    for those tools based on the xml config file and the arguments sent in to the Automater.

Class(es):
    ToolFacade  -- Class used to run the automation necessary to retrieve information and parse results.
    Tool        -- Parent Class used to setup tools and manage information retrieval.

Function(s):
    No global exportable functions are defined.

Exception(s):
    No exceptions exported.
"""
from abc import ABC, abstractmethod
import logging
import types

from utilities import Utils

logger = logging.getLogger(__name__)

class ToolFacade:
    """ ToolFacade provides a Facade to run the multiple requirements needed to
            automate information retrieval and content parsing processes.

    Public Method(s):
        runAutomation
        (Property) Tools

    Instance variable(s):
        _sites
    """
    def __init__(self):
        """ Class constructor.
        Simply creates a blank list and assigns it to
        instance variable _sites that will be filled with retrieved info
        from sites defined in the xml configuration file.

        Argument(s):
            No arguments are required.
        """
        self._tools = {}

    def dictConfig(self, configname, config, sourcelist):
        return self

    def loadJSON(self, filename, sourcelist = None, **kwargs):
        if sourcelist is None:
            sourcelist = ["*"]
        config = Utils.getJSONDict(filename)
        self.dictConfig(config, sourcelist)
        return self

    def loadXML(self, filename, sourcelist = None, **kwargs):
        if sourcelist is None:
            sourcelist = ["*"]
        logger.debug(f"Reading {filename}...")
        xmltree = Utils.getXMLTree(filename)
        if not xmltree: return None
        toolsclslist = Tool.getList()
        for toolcls in toolsclslist:
            tool_name = toolcls.__name__
            tool = self._tools.get(tool_name)
            if tool and hasattr(tool, "loadXML"):
                logger.debug(f"Updating {tool_name}")
                tool.loadXML(filename, xmltree, sourcelist)
            elif hasattr(toolcls, "fromXML"):
                logger.debug(f"Creating {tool_name}")
                tool = toolcls.fromXML(filename, xmltree, sourcelist)
                if not tool:
                    logger.debug(f"Skipped {tool_name}")
                    continue
                if tool == NotImplemented:
                    logger.warning(f"Skipped '{tool_name}' NotImplemented!")
                    continue
                self._tools.update(**{ tool_name: tool })
        return self

    @property
    def Tools(self):
        """ Checks the instance variable _tools is empty or None.
            Returns _tools (the tools list) or None if it is empty.

        Return value(s):
            list -- of Tool objects or its subordinates.
            None -- if _tools is empty or None.
        """
        return None if self._tools is None or len(self._tools) == 0 else self._tools

    def run(self, tool, target, **kwargs):
        if isinstance(tool, str):
            logger.debug(f"Running {tool}")
            tool = self.Tools[tool]
        else:
            logger.debug(f"Running {tool.__class__.__name__}")
        content = tool.run(target, **kwargs)
        if not content:
            return None
        if isinstance(content, list):
            return content
        if not isinstance(content, types.GeneratorType):
            return [content]
        generator_list = [content]
        contentlist = []
        while generator_list:
            content_generator = generator_list.pop()
            for content in content_generator:
                if isinstance(content, types.GeneratorType):
                    logger.warning(f"Tool '{tool.__class__.__name__}' is returning nested generators!")
                    generator_list.append(content)
                else:
                    contentlist.append(content)
        #TODO content filters
        return contentlist

    def runAll(self, targetlist, **kwargs):
        """ Run all registered tools.

        Argument(s):
            targetlist          -- list of strings representing targets to be investigated.
                                    Targets can be IP Addresses, MD5 hashes, or hostnames.

        Return value(s):
            list -- of reports.
        """
        if not isinstance(targetlist, list): raise ValueError("targetlist is not a list!")
        tools_dict = self.Tools
        for target in targetlist:
            for tool_name in tools_dict:
                contentlist = self.run(tools_dict[tool_name], target, **kwargs)
                if not contentlist:
                    continue
                for content in contentlist:
                    if not content: continue
                    yield content

class Tool(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def run(self, target, **kwargs):
        return NotImplemented

    @classmethod
    def fromXML(cls, filename, xmltree, sourcelist = None, **kwargs):
        return cls().loadXML(filename, xmltree, sourcelist, **kwargs)

    @abstractmethod
    def loadXML(self, filename, xmltree, sourcelist = None, **kwargs):
        return NotImplemented

    @classmethod
    def getList(cls):
        subclasses = set()
        worklist = [cls]
        while worklist:
            parentcls = worklist.pop()
            for childcls in parentcls.__subclasses__():
                if childcls in subclasses:
                    continue
                subclasses.add(childcls)
                worklist.append(childcls)
        return subclasses
