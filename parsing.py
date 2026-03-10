from abc import ABC, abstractmethod
import logging
import re
import json

logger = logging.getLogger(__name__)

class ContentParser:
    """ ContentParser is the child object that represents each piece of content a tool returns.
            Reads results discovered from a tool.

    Public Method(s):
        (Property) ReportString
        (Property) FriendlyName
        (Property) Type
        buildFromXML
        parseContent

    Instance variable(s):
        _childs
        _type
    """
    def __init__(self, **kwargs):
        """ Class constructor.
            Sets the instance variables based on input from the arguments supplied when Automater is run
                    and what the xml config file stores.

        Argument(s):
            reportstring -- string or list of strings
            friendlyname -- string or list of strings
            regex -- the regex
            importantproperty -- string
        """
        self._type = kwargs["type"]
        if self._type is None or len(self._type) <= 0:
            raise ConfigError(f"ContentParser type {self._type} is empty.", key_name = "ContentParser.type")
        self._childs = kwargs["childs"]
        if self._childs is None or len(self._childs) <= 0:
            raise ConfigError(f"ContentParser has no childs.", key_name = "ContentParser.childs")

    @classmethod
    def buildFromXML(cls, element, **kwargs):
        element_type = element.get("type")
        childs = element.findall("entry")
        if childs is None or len(childs) <= 0:
            raise ConfigError(f"Content has no entry.", key_name = "content/entry")
        if element_type == "regex":
            childs = [ RegexContent.buildFromXML(c, **kwargs) for c in childs ]
        elif element_type == "json":
            childs = [ JSONContent.buildFromXML(c, **kwargs) for c in childs ]
        else: raise ConfigError(f"Content type {element_type} is unknown.", key_name = "type")
        return ContentParser(type = element_type, childs = childs)

    @property
    def Type(self):
        """ Returns the string representing the type of parser.

        Return value(s):
            string -- representing the type of content parser
        """
        return self._type

    def parseContent(self, content, target):
        """ Retrieves a list of information retrieved from the sites defined in the xml configuration file.
            Returns the list of found information from the sites being used as resources
                or returns None if the site cannot be discovered.

        Argument(s):
            content -- string representation of the web site being used as a resource.

        Return value(s):
            matchObj -- information found from a web site being used as a resource.
        """
        for parser in self._childs:
            res = parser.parseContent(content, target)
            if not res: continue
            if isinstance(res, str):
                res = { "Message": res }
            if isinstance(res, dict):
                res["Entry"] = parser
                res["Target"] = target
                if hasattr(target, "Type"):
                    res["TargetType"] = target.Type
            yield res

class RegexContent(ContentParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def buildFromXML(cls, element, **kwargs):
        return RegexEntry.buildFromXML(element, **kwargs)

class JSONContent(ContentParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def buildFromXML(cls, element, **kwargs):
        return JSONEntry.buildFromXML(element, **kwargs)

class ContentEntry(ABC):
    def __init__(self, **kwargs):
        if kwargs is None or len(kwargs) == 0:
            raise ValueError("kwargs is missing or empty.")
        self._reportstring = kwargs["name"]
        if self._reportstring is None or len(self._reportstring) == 0:
            raise ConfigError(f"ContentEntry has no name.", key_name = "ContentEntry/name")
        self._name = kwargs["short"]
        if self._name is None or len (self._name) == 0:
            self._name = self._reportstring

    @abstractmethod
    def __str__(self):
        return NotImplemented

    @classmethod
    def readXML(cls, argsobj, element):
        argsobj["name"] = element.get("name")
        argsobj["short"] = element.get("short")
        return argsobj

    @property
    def Name(self):
        """ Returns the short string representing a name.

        Return value(s):
            string -- representing a name for a ContentEntry for reporting.
        """
        return self._reportstring if self._name is None else self._name

    @property
    def ReportString(self):
        """ Returns the string representing a report string tag that precedes reporting information
                so the user knows what specifics are being found.

        Return value(s):
            string -- representing a tag for reporting information.
        """
        return self._reportstring

    @abstractmethod
    def parseContent(self, content, target):
        return NotImplemented

class JSONEntry(ContentEntry):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._path = kwargs["path"]

    def __str__(self):
        return str(this._path)

    @classmethod
    def readXML(cls, argsobj, element):
        argsobj = ContentEntry.readXML(argsobj, element)
        argsobj["path"] = element.text
        return argsobj

    @classmethod
    def buildFromXML(cls, element, **kwargs):
        kwargs = cls.readXML(kwargs, element)
        return cls(**kwargs)

    def parseContent(self, content, target):
        if isinstance(content, str):
            content = json.loads(content)

        path = self._path
        if isinstance(path, str):
            path.split(".")

        for p in path:
            p = p.replace("%TARGET%", str(target))
            if not p in content: return None
            content = content[p]

        #if isinstance(content, dict):
        #TODO formatting...
        if isinstance(content, list):
            content = ", ".join(content)
        return {
            "Entry": self
            , "Message": str(content)
            , "Target": target
        }

class RegexEntry(ContentEntry):
    """ Class constructor.

    Argument(s):
        short -- string
        name -- string
        regex -- the regex
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.RegEx = kwargs["regex"]

    def __str__(self):
        return str(this._regex)

    @classmethod
    def readXML(cls, argsobj, element):
        argsobj = ContentEntry.readXML(argsobj, element)
        argsobj["regex"] = element.text
        return argsobj

    @classmethod
    def buildFromXML(cls, element, **kwargs):
        kwargs = cls.readXML(kwargs, element)
        return cls(**kwargs)

    @property
    def RegEx(self):
        """ Returns string representing the regex being investigated.

        Return value(s):
            string -- representation of the Regex from the _regex instance variable.
        """
        return self._regex

    @RegEx.setter
    def RegEx(self, regex):
        """ Determines if the parameter has characters and assigns it to the instance variable _regex
                if it does after replacing the target information where the keyword %TARGET% is used.
        This keyword will be used in the xml configuration file where the user
                wants the target information to be placed in the regex.

        Argument(s):
            regex -- string representation of regex pulled from the xml file in the regex entry XML tag.
        """
        self._regex = "" if regex is None or len(regex) <= 0 or not isinstance(regex, str) else regex

    def parseContent(self, content, target):
        """ Retrieves a list of information retrieved from the sites defined in the xml configuration file.
            Returns the list of found information from the sites being used as resources
                or returns None if the site cannot be discovered.

        Argument(s):
            content -- string representation of the web site being used as a resource.

        Return value(s):
            list -- information found from a web site being used as a resource.
        """
        regex = self._regex.replace("%TARGET%", str(target))
        matches = re.findall(regex, content, re.IGNORECASE)
        if not matches: return None
        return {
            "Entry": self
            , "Message": ", ".join(matches) if isinstance(matches, list) else str(matches)
            , "Target": target
        }
