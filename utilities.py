""" The utilities.py module handles all utility functions that Automater requires.

Class(es):
    Parser -- Class to handle standard argparse functions with a class-based structure.
    IPWrapper -- Class to provide IP Address formatting and parsing.
    VersionChecker -- Class to check if modifications to any files are available

Function(s):
    No global exportable functions are defined.

Exception(s):
    No exceptions exported.
"""
import hashlib
import logging
import os
import requests

import json
from xml.etree.ElementTree import ElementTree

DEFAULT_HASH = "md5"

class ConfigError(Exception):
    """Raised when a specific configuration key is invalid or missing."""
    def __init__(self, message, config_name = None, key_name = None):
        super().__init__(message)
        self.config_name = config_name
        self.key_name = key_name

class LoggingContext:
    def __init__(self, logger, level = None, handler = None, close = True):
        self.logger = logger
        self.level = level
        self.handler = handler
        self.close = close

    def __enter__(self):
        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        if self.handler:
            self.logger.addHandler(self.handler)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.handler:
            self.logger.removeHandler(self.handler)
        if self.handler and self.close:
            self.handler.close()
        # implicit return of None => don't swallow exceptions

class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def close(self):
        pass

    def flush(self):
        pass

    def write(self, message):
        if not message or message == "\n": return
        for msg in str(message).splitlines():
            self.logger.log(self.level, msg)

class TTSHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        cmd = [ "espeak", "-s150", "-ven+f3", msg ]         # Speak slowly in a female English voice
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE
                                , stderr=subprocess.STDOUT)
        p.communicate()                                     # wait for the program to finish

class Utils:
    """
    """
    @classmethod
    def applydefault(cls, obj, **kwargs):
        for item_name, item_val in kwargs.items():
            if isinstance(obj, dict):
                obj.setdefault(item_name, item_val)
            elif not hasattr(obj, item_name):
                setattr(obj, item_name, item_val)

    @classmethod
    def copyattr(cls, obj, obj_name, src, src_name = None, default = None):
        if src_name is None:
            src_name = obj_name
        try:
            if default is None:
                newVal = src.get(src_name) if isinstance(src, dict) else getattr(src, src_name)
            else:
                newVal = src.get(src_name, default) if isinstance(src, dict) else getattr(src, src_name, default)
            if newVal is None:
                return False
            if isinstance(obj, dict):
                obj.update(**{ obj_name: newVal })
            else:
                setattr(obj, obj_name, newVal)
            return True
        except:
            return False

    @classmethod
    def fileExists(cls, filename):
        """ Checks if a file exists.
            Returns boolean representing if file exists.

        Argument(s):
            No arguments are required.

        Return value(s):
            Boolean
        """
        return os.path.exists(filename) and os.path.isfile(filename)

    @classmethod
    def getModifiedFiles(cls, webprefix, filelist, pathprefix = "", proxy = None):
        modifiedfiles = []
        for filename in filelist:
            md5local = Utils.getHashOfLocalFile(pathprefix + filename)
            md5remote = Utils.getHashOfRemoteFile(webprefix + filename, proxy)
            if md5local != md5remote:
                modifiedfiles.append(filename)
        return modifiedfiles if len(modifiedfiles) > 0 else None

    @classmethod
    def getHashOfLocalFile(cls, filename, hashname = DEFAULT_HASH):
        hashFn = getattr(hashlib, hashname)
        with open(filename, "rb") as f:
            return hashFn(f.read()).hexdigest()

    @classmethod
    def getHashOfRemoteFile(cls, location, hashname = DEFAULT_HASH, proxy = None):
        hashFn = getattr(hashlib, hashname)
        if isinstance(proxy, str):
            proxy = { "https": proxy, "http": proxy }
        resp = requests.get(location, proxies = proxy, verify = False, timeout = 5)
        resp.raise_for_status()
        return hashFn(resp.content).hexdigest()

    @classmethod
    def getRemoteFile(cls, location, filename, proxy = None):
        if isinstance(proxy, str):
            proxy = {"https": proxy, "http": proxy}
        resp = requests.get(location, proxies = proxy, verify = False, timeout = 5)
        resp.raise_for_status()
        chunk_size = 65535
        md5Hash = hashlib.md5()
        with open(filename, "wb") as fd:
            for chunk in resp.iter_content(chunk_size):
                fd.write(chunk)
                md5Hash.update(chunk)
        return md5Hash.hexdigest()

    @classmethod
    def getJSONDict(cls, filename):
        if not Utils.fileExists(filename):
            logging.getLogger(f"{cls.__name__}.getJSONDict").warning(f"File '{filename}' not found!")
            return None
        try:
            with open(filename) as f:
                return json.load(f)
        except:
            logging.getLogger(f"{cls.__name__}.getJSONDict").exception(
                f"There was an error reading from the '{filename}' file.\n"\
                f"Please check that the '{filename}' file is present and correctly formatted.")

    @classmethod
    def getXMLTree(cls, filename):
        """ Opens a config file for reading.
            Returns XML Elementree object representing XML Config file.

        Argument(s):
            No arguments are required.

        Return value(s):
            ElementTree
        """
        if not Utils.fileExists(filename):
            logging.getLogger(f"{cls.__name__}.getXMLTree").warning(
                f"File '{filename}' not found!")
            return None
        try:
            with open(filename) as f:
                return ElementTree(file = f)
        except:
            logging.getLogger(f"{cls.__name__}.getXMLTree").exception(
                f"There was an error reading from the '{filename}' input file.\n"\
                f"Please check that the '{filename}' file is present and correctly formatted.")

    @classmethod
    def replaceAll(cls, s, *items):
        for it in items:
            s = str(s).replace(it[0], it[1])
        return s
