""" The siteinfo.py module provides site lookup
    for those sites based on the xml config file and the arguments sent in to the Automater.

Class(es):
    WebTools -- Class used to run the automation necessary to retrieve site information and store results.
    Site -- Parent Class used to store sites and information retrieved.

Function(s):
    No global exportable functions are defined.

Exception(s):
    No exceptions exported.
"""
from abc import ABC, abstractmethod
import logging
import requests
import re
import time
from requests.exceptions import ConnectionError

from inputs import AbstractContent, SourceDescription, TargetList
from utilities import ConfigError, Utils
from reporting import ErrorReport, ThreatReport
from tool import Tool
from parsing import ContentParser

logger = logging.getLogger(__name__)
requests.packages.urllib3.disable_warnings()

class WebTools(Tool):
    """ WebTools provides a Facade to run the multiple requirements needed
            to automate the sites retrieval and content parsing processes.

    Public Method(s):
        run
        (Property) Sites

    Instance variable(s):
        _sites
    """
    def __init__(self):
        """ Class constructor.
        Simply creates a blank list and assigns it to instance variable _sites that will be filled with retrieved info
            from sites defined in the xml configuration file.

        Argument(s):
            No arguments are required.
        """
        self._sites = {}

    @property
    def Sites(self):
        """ Checks the instance variable _sites is empty or None.
            Returns _sites (the site list) or None if it is empty.

        Return value(s):
            list -- of Site objects or its subordinates.
            None -- if _sites is empty or None.
        """
        return None if self._sites is None or len(self._sites) == 0 else self._sites

    @classmethod
    def fromXML(cls, filename, xmltree, sourcelist = None, **kwargs):
        return cls().loadXML(filename, xmltree, sourcelist, **kwargs)

    def loadXML(self, filename, xmltree, sourcelist = None, **kwargs):
        for site_element in xmltree.iter(tag = "site"):
            site_name = site_element.get("name")
            if not isinstance(site_name, str) or len(site_name) <= 0:
                raise ConfigError("Site name is missing!", key_name="site.name")
            if sourcelist.index("*") < 0 and sourcelist.index(site_name) < 0:
                continue
            logger.debug(f"Reading {filename}:{site_name}...")
            site = self._sites.get(site_name)
            site_args = Site.buildFromXML(site_element, **kwargs)
            if site:
                site.loadArgs(**site_args)
            else:
                site = Site(**site_args)
                self._sites.update(**{ site.FriendlyName: site })
            for src_element in site_element.findall("source"):
                src_type = src_element.get("type")
                site.Sources.update(**{
                    src_type: SourceDescription(**{
                        "source": src_element.text
                        , "type": src_type
                    })
                })
            for content_element in site_element.findall("content"):
                content_parser = ContentParser.buildFromXML(content_element)
                site.Parsers.append(content_parser)
        return self

    def getReport(self, site, target):
        if isinstance(site, str):
            logger.debug(f"Getting content from {site}")
            site = self.Sites[site]
        else:
            logger.debug(f"Getting content from {site.FriendlyName}")
        respContent = site.getContent(target)
        if not respContent:
            yield ErrorReport(f"No content returned by {site.DomainURL}")
        elif isinstance(respContent, ErrorReport):
            yield respContent
        else:
            for report in site.parseContent(respContent, target):
                if isinstance(report, ThreatReport):
                    report.TargetType = target.Type
                yield report

    def run(self, target, **kwargs):
        sites_dict = self.Sites
        for site_name in sites_dict:
            site = sites_dict[site_name]
            #TODO self.runSiteElement(webretrievedelay, proxy, siteelement, targetlist, sourcelist, useragent, botoutputrequested)
            for report in self.getReport(site, target):
                yield report

class Site(AbstractContent):
    """ Site is the parent object that represents each site used for retrieving information.
        Site stores the results discovered from each web site discovered when running Automater.

    Public Method(s):
        (Class Method) buildFromXML
        (Class Method) buildStringOrListfromXML
        (Class Method) buildDictionaryFromXML
        (Property) WebRetrieveDelay
        (Property) ReportString
        (Property) FriendlyName
        (Property) RegEx
        (Property) BotOutputRequested
        (Property) Sources
        (Property) ImportantPropertyString
        (Property) Params
        (Setter) Params
        (Property) Headers
        (Property) UserAgent
        (Property) Method
        getContent

    Instance variable(s):
        _sites
        _domainUrl
        _webretrievedelay
        _userAgent
        _fullURL
        _botOutputRequested
        _params
        _headers
        _results
    """
    PROPS_MAP = {
        "_friendlyName": "friendlyname"
        , "_name": "name"
        , "_domainUrl": "domainurl"
        , "_webretrievedelay": "webretrievedelay"
        , "_userAgent": "useragent"
        , "_proxy": "proxy"
        , "_botOutputRequested": "botoutputrequested"
        , "Params": "params"  # call the helper method to clean %TARGET% from params string
        , "Headers": "headers"  # call the helper method to clean %TARGET% from params string
        , "PostData": "postdata"
        , "_sources": "sources"
    }
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._botOutputRequested = False
        self._headers = None
        self._params = None
        self._postdata = None
        self._webretrievedelay = None
        self._userAgent = "CITDB/1.0"
        self._proxy = None
        self.loadArgs(**kwargs)
        if not hasattr(self, "_friendlyName"):
            raise ValueError("'name' argument is missing!")
        if not hasattr(self, "_domainUrl"):
            raise ValueError("'domainurl' argument is missing!")

    def loadArgs(self, **kwargs):
        """ Class constructor.
            Sets the instance variables based on input from the arguments supplied
                when Automater is run and what the xml config file stores.

        Argument(s):
            fullurl -- string
            domainurl -- string
            target -- the target that will be used to gather information on.
            targettype -- the targettype as defined. Either ip, md5, or hostname.
            friendlyname -- string or list of strings
            regex -- the regex
            ReportString -- string or list of strings
            useragent -- the user-agent string that will be utilized when submitting
                            information to or requesting information from a website
            botoutputrequested -- true or false representation of whether the -b option was used when running the program.
                                    If true, it slims the output so a bot can be used and the output is minimalized.
            importantproperty -- string
            params -- string or list
            webretrievedelay -- the amount of seconds to wait between site retrieve calls.
                                    Default delay is 2 seconds.
            proxy -- will set a proxy to use (eg. proxy.example.com:8080).
            headers -- string or list
            postdata -- dict holding data required for posting values to a site. by default = None
        """
        for propName in Site.PROPS_MAP:
            Utils.copyattr(self, propName, kwargs, Site.PROPS_MAP[propName])
        #self.Params = kwargs["params"]  # call the helper method to clean %TARGET% from params string
        #self.Headers = kwargs["headers"]  # call the helper method to clean %TARGET% from params string
        #TODO ContentParser()
        #self._parsers
        return self

    @classmethod
    def buildFromXML(cls, site_element, **kwargs):
        """ Utilizes the Class Methods within this Class to build the Site object.
            Returns a Site object that defines results returned during the web retrieval investigations.

        Argument(s):
            site_element -- the XML site element object that will be used as the start element.
            webretrievedelay -- the amount of seconds to wait between site retrieve calls.
                                    Default delay is 2 seconds.
            proxy -- sets a proxy to use in the form of proxy.example.com:8080.
            targettype -- the targettype as defined. Either ip, md5, or hostname.
            target -- the target that will be used to gather information on.
            useragent -- the string utilized to represent the user-agent when web requests or submissions are made.
            botoutputrequested -- true or false representing if a minimalized output will be required for the site.

        Return value(s):
            Site object.
        """
        siteArgs = {
            "friendlyname": site_element.get("name")
            , "name": site_element.get("short")
            , "domainurl": site_element.get("domain")
            #TODO Implement parameters!
            #, "params": Site.buildDictionaryFromXML(site_element, "params")
            #, "headers": Site.buildDictionaryFromXML(site_element, "headers")
            #, "postdata": Site.buildDictionaryFromXML(site_element, "postdata")
        }
        for argName in kwargs:
            siteArgs[argName] = kwargs[argName]
        return siteArgs

    @property
    def WebRetrieveDelay(self):
        """ Returns the string representation of the number of seconds that will be delayed between site retrievals.

        Return value(s):
            string -- representation of an integer that is the delay in
            seconds that will be used between each web site retrieval.
        """
        return self._webretrievedelay

    @property
    def Proxy(self):
        """ Returns the string representation of the proxy used.

        Return value(s):
            string -- representation of the proxy used
        """
        return self._proxy

    @property
    def DomainURL(self):
        """ Returns the string representing the Domain URL which is required to retrieve the information being investigated.

        Return value(s):
            string -- representing the URL of the site.
        """
        return self._domainUrl

    @property
    def BotOutputRequested(self):
        """ Returns a true if the -b option was requested when the program was run.
        This identifies if the program is to run a more silent version of output during the run to
                help bots and other small format requirements.

        Return value(s):
            boolean -- True if the -b option was used and am more silent output is required.
                        False if normal output should be utilized.
        """
        return self._botOutputRequested

    @property
    def Params(self):
        """ Determines if web Parameters were set for this specific site.
            Returns the string representing the Parameters using the _params instance variable or returns None
                    if the instance variable is empty or not set.

        Return value(s):
            string -- representation of the Parameters from the _params instance variable.
        """
        return None if self._params is None or len(self._params) == 0 else self._params

    @Params.setter
    def Params(self, params):
        """ Determines if Parameters were required for this specific site.
            If web Parameters were set, this places the target into the parameters
                where required marked with the %TARGET% keyword in the xml config file.

        Argument(s):
            params -- dictionary representing web Parameters required.
        """
        self._params = None if params is None or len(params) <= 0 else params

    @property
    def Headers(self):
        """ Determines if Headers were set for this specific site.
            Returns the string representing the Headers using the _headers instance variable or returns
                None if the instance variable is empty or not set.

        Return value(s):
            string -- representation of the Headers from the _headers instance variable.
        """
        return None if self._headers is None or len(self._headers) == 0 else self._headers

    @Headers.setter
    def Headers(self, headers):
        """ Determines if Headers were required for this specific site.
            If web Headers were set, this places the target into the headers where required or
                marked with the %TARGET% keyword in the xml config file.

        Argument(s):
            headers -- dictionary representing web Headers required.
        """
        self._headers = None if headers is None or len(headers) <= 0 else headers

    @property
    def PostData(self):
        """ Determines if PostData was set for this specific site.
            Returns the dict representing the PostHeaders using the _postdata instance variable
                or returns None if the instance variable is empty or not set.

        Return value(s):
            dict -- representation of the PostData from the _postdata instance variable.
        """
        return None if self._postdata is None or len(self._postdata) == 0 else self._postdata

    @PostData.setter
    def PostData(self, postdata):
        """ Determines if post data was required for this specific site.
            If postdata is set, this ensures %TARGET% is stripped if necessary.

        Argument(s):
            postdata -- dictionary representing web postdata required.
        """
        self._postdata = None if postdata is None or len(postdata) <= 0 else postdata

    @property
    def UserAgent(self):
        """ Returns string representing the user-agent that will be used when requesting or submitting information to a web site.
            This is a user-provided string implemented on the command line at execution or provided by default
                if not added during execution.

        Return value(s):
            string -- representation of the UserAgent from the _userAgent instance variable.
        """
        return self._userAgent

    @property
    def Method(self):
        """ Determines if a method (GET or POST) was established for this specific site.
                Defaults to GET

        Return value(s):
            string -- representation of the method used to access the site GET or POST.
        """
        return "GET" if self._postdata is None or len(self._postdata) == 0 else "POST"

    def getHeaderParamProxyInfo(self, target):
        headers = {} if self._headers is None else self._headers.copy()
        for key in headers:
            if headers[key] == "%TARGET%":
                headers[key] = target
        headers["User-agent"] = self.UserAgent

        params = None if self._params is None else self._params.copy()
        if params and len(params) > 0:
            for key in params:
                if params[key] == "%TARGET%":
                    params[key] = target

        proxy = { "https": self.Proxy, "http": self.Proxy } if self.Proxy else None

        return headers, params, proxy

    def parseContent(self, content, target):
        """ Retrieves a list of information retrieved from the sites defined in the xml configuration file.
            Returns the list of found information from the sites being used as resources
                or returns None if the site cannot be discovered.

        Argument(s):
            content -- string representation of the web site being used as a resource.
            target -- string

        Return value(s):
            list -- information found from a web site being used as a resource.
        """
        try:
            foundContent = False
            for parser in self.Parsers:
                for content in parser.parseContent(content, target):
                    foundContent = True
                    content["Site"] = self.Name if self.BotOutputRequested else self.FriendlyName
                    yield content
            if not foundContent:
                yield ErrorReport(f"No content found at {self.DomainURL}")
        except:
            logger.exception(f"Error while parsing {self.DomainURL}")
            yield ErrorReport(f"[-] Cannot scrape {self.DomainURL}")

    def getContent(self, target, source = None):
        """ Attempts to retrieve a string from a web site.
            String retrieved is the entire web site including HTML markup.
            Requests via proxy if --proxy option was chosen during execution of the Automater.
            Returns a string that contains entire web site being used as a resource including HTML markup information.

        Argument(s):
            No arguments are required.

        Return value(s):
            string -- contains entire web site being used as a resource including HTML markup information.
        """
        if source is None:
            target_type = TargetList.identifyTargetType(target, tools = Tool.getList())
            source = self.Sources.get(target_type, self.Sources.get("*"))
            if source is None:
                logger.debug(f"[-] Skipping {self.DomainURL}, {target_type} not supported.")
                return None

        headers, params, proxy = self.getHeaderParamProxyInfo(target)
        fullURL = source.withTarget(target)
        reqArgs = {
              "url": fullURL
            , "headers": headers
            , "params": params
            , "proxies": proxy
            , "verify": False
        }

        if self._webretrievedelay:
            time.sleep(self._webretrievedelay)

        logger.debug(f"[*] Checking {self.DomainURL}")
        try:
            if self.Method == "POST":
                postdata = self.PostData.copy()
                for key in postdata:
                    if postdata[key] == "%TARGET%":
                        postdata[key] = target
                reqArgs["data"] = postData
                logger.debug(f"[-] {self.DomainURL} requires a submission for {target}."\
                                " Submitting now, this may take a moment.")
                resp = requests.post(**reqArgs)
            else:
                reqArgs["timeout"] = 5
                resp = requests.get(**reqArgs)
            responseStringContent = resp.content.decode(encoding = "utf8")
            logger.debug(f"{fullURL}\n\nContent: {responseStringContent}")
            resp.raise_for_status()
            return responseStringContent
        except ConnectionError as ce:
            return ErrorReport(f"[-] Cannot connect to {fullURL}. Connection error {ce}")
        except:
            logger.exception(f"Cannot connect to {fullURL}")
            return ErrorReport(f"[-] Cannot connect to {fullURL}")
