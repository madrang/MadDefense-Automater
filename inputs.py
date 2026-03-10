"""
The inputs.py module represents some form of all inputs to the Automater program to include target files,
        and the standard config file - sites.xml.
Any addition to Automater that brings any other input requirement should be programmed in this module.

Class(es):
TargetFile          -- Provides a representation of a file containing target
                            strings for Automater to utilize.
SourceDescription   -- Provides a representation of sources for the tools.xml configuration file.

Function(s):
No global exportable functions are defined.

Exception(s):
No exceptions exported.
"""
from abc import ABC, abstractmethod
import hashlib
import logging
import re
import requests
from requests.exceptions import ConnectionError, HTTPError
import os

from utilities import Utils

logger = logging.getLogger(__name__)

class AbstractContent(ABC):
    def __init__(self, **kwargs):
        self._sources = {}
        self._parsers = []

    @abstractmethod
    def loadArgs(self, **kwargs):
        return NotImplemented

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

    @property
    def Sources(self):
        """ Returns a dictionary of sources keyed by types for the current site.

        Return value(s):
            dict -- representing the sources of the site.
        """
        return self._sources

    @property
    def Parsers(self):
        return self._parsers

    @abstractmethod
    def parseContent(self, content, target):
        return NotImplemented

class SourceDescription:
    def __init__(self, **kwargs):
        self.loadArgs(**kwargs)

    def loadArgs(self, **kwargs):
        if not Utils.copyattr(self, "_type", kwargs, "type"):
            raise ValueError("'type' argument is missing!")
        if not Utils.copyattr(self, "_source", kwargs, "source"):
            raise ValueError("'source' argument is missing!")

    @property
    def Source(self):
        return self._source

    @property
    def Type(self):
        """ Returns the target type information whether that be ip, md5, or hostname.

        Return value(s):
            string -- defined as ip, md5, or hostname.
        """
        return self._type

    def withTarget(self, target):
        """ Returns the string representing the Full URL which is the domain URL plus querystrings
                and other information required to retrieve the information being investigated.

        Return value(s):
            string -- representing the full URL of the site including querystring information and any other info required.
        """
        return self._source.replace("%TARGET%", str(target))

class TargetDescription:
    def __init__(self, **kwargs):
        self.loadArgs(**kwargs)

    def __str__(self):
        return self._target

    def loadArgs(self, **kwargs):
        if not Utils.copyattr(self, "_target", kwargs, "target"):
            raise ValueError("'target' argument is missing!")
        if not isinstance(self._target, str):
            raise ValueError(f"'target' argument '{self._target}' is not a string!")
        if not Utils.copyattr(self, "_type", kwargs, "type"):
            self._type = TargetList.identifyTargetType(self._target)

    @property
    def Target(self):
        return self._target

    @property
    def Type(self):
        """ Returns the target type information whether that be ip, md5, or hostname.

        Return value(s):
            string -- defined as ip, md5, or hostname.
        """
        return self._type

class TargetList(object):
    """ TargetList provides Class Methods to manage informations from a targets list

    Public Method(s):
        (Class Method) TargetList
        (Class Method) isIPorIPList
        (Class Method) getTarget

    Instance variable(s):
        No instance variables.
    """
    _ipRangePrefix = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}")
    _ipRangeDash = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}-\d{1,3}")
    _ipAddress = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
    _replacements = [
        ["[.]", "."]
      , ["{.}", "."]
      , ["(.)", "."]
    ]

    @classmethod
    def fromFile(cls, filename):
        """ Opens a file for reading.
                Returns each string from each line of a single or multi-line file.

        Argument(s):
            filename -- string based name of the file that will be retrieved and parsed.

        Return value(s):
            List of string(s) found in a single or multi-line file.
        """
        with open(filename) as file:
            return cls.normalize(file.readlines())

    @classmethod
    def isIP(cls, target):
        """ Checks if an input string is an IP Address or if it is an IP Address in CIDR or dash notation.
            Returns True if IP Address or CIDR/dash. Returns False if not.

        Argument(s):
            target -- string target provided as the first argument to the program.

        Return value(s):
            Boolean
        """
        ipRgeFind = re.findall(cls._ipRangePrefix, target)             # IP Address range using prefix syntax
        if ipRgeFind is not None and len(ipRgeFind) > 0:
            return True

        ipRgeDashFind = re.findall(cls._ipRangeDash, target)
        if ipRgeDashFind is not None and len(ipRgeDashFind) > 0:
            return True

        ipFind = re.findall(cls._ipAddress, target)
        if ipFind is not None and len(ipFind) > 0:
            return True

        return False

    @classmethod
    def getTargetsIP(cls, target):
        """ Determines whether the target provided is an IP Address or an IP Address in dash notation.
            Then creates a list that can be utilized as targets by the program.
            Returns a list of string IP Addresses that can be used as targets.

        Argument(s):
            target -- string target provided as the first argument to the program.

        Return value(s):
            Iterator of string(s) representing IP Addresses.
        """
        # IP Address range using prefix syntax
        #TODO Implement this...

        # IP Address range seperated with a dash
        ipRgeDashFind = re.findall(cls._ipRangeDash, target)
        if ipRgeDashFind is not None and len(ipRgeDashFind) > 0:
            iplist = target[:target.index("-")].split(".")
            iplast = target[target.index("-") + 1:]
            if int(iplist[3]) < int(iplast):
                for lastoctet in range(int(iplist[3]), int(iplast) + 1):
                    yield target[:target.rindex(".") + 1] + str(lastoctet)
            else:
                yield target[:target.rindex(".") + 1] + str(iplist[3])

        else: # it's just an IP address at this point
            yield target

    @classmethod
    def identifyTargetType(cls, target, tools = None):
        """ Checks the target information provided to determine if it is a(n)
        IP Address in standard; CIDR or dash notation, or an MD5 hash, or a string hostname.
        Returns a string md5 if MD5 hash is identified. Returns the string ip if any IP Address format is found.
        Returns the string hostname if neither of those two are found.

        Argument(s):
            target -- string representing the target provided as the first argument to the program when Automater is run.

        Return value(s):
            string
        """
        if isinstance(target, TargetDescription):
            return target.Type

        ipAddress = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        ipFind = re.findall(ipAddress, target)
        if ipFind is not None and len(ipFind) > 0:
            return "ip"

        md5 = re.compile("[a-fA-F0-9]{32}", re.IGNORECASE)
        md5Find = re.findall(md5, target)
        if md5Find is not None and len(md5Find) > 0:
            return "md5"

        if tools:
            for tool in tools:
                if hasattr(tool, "identifyTargetType"):
                    target_type = tool.identifyTargetType(target)
                    if target_type: return target_type

        return "hostname"

    @classmethod
    def normalize(cls, targets):
        if not isinstance(targets, list):
            raise ValueError("targets is not a list!")
        targetlist = []
        for tgt in targets:
            if isinstance(tgt, TargetDescription):
                targetlist.append(tgt)
                continue
            tgt = Utils.replaceAll(str(tgt).strip(), *cls._replacements)
            if cls.isIP(tgt):
                targetlist.extend([TargetDescription(target = t) for t in cls.getTargetsIP(tgt)])
            elif len(tgt) > 0:
                targetlist.append(TargetDescription(target = tgt))
        return targetlist
