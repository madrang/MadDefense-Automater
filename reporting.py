class AbstractReport(object):
    def __init__(self, **kwargs):
        self._data = { str(name).lower(): kwargs[name] for name in kwargs }

    def __str__(self):
        strlist = []
        for prop_name, prop_val in self._data.items():
            strlist.append(f"{prop_name}: {prop_val}")
        return ", ".join(strlist)

    def update(self, **kwargs):
        self._data.update(**kwargs)

    def setdefault(self, key, default):
        return self._data.setdefault(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def required(self, *args):
        for arg in args:
            if not str(arg).lower() in self._data:
                raise ValueError(f"Attribute '{arg}' can't be found!")

    def __getattr__(self, name):
        if name == "_data":
            super().__getattr__(name)
        else:
            name = str(name).lower()
            return self._data.get(name)

    def __setattr__(self, name, value):
        if name == "_data":
            super().__setattr__(name, value)
        else:
            name = str(name).lower()
            self._data[name] = value

    def __dir__(self):
        for item in super().__dir__():
            yield item
        for item in self._data.keys():
            yield item

    def __contains__(self, obj):
        if obj in self._data:
            return True
        if hasattr(self, o):
            return True
        return False

class ErrorReport(AbstractReport):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.required("message")

    def __init__(self, message, **kwargs):
        super().__init__(Message = message, **kwargs)
        self.required("message")

    def __str__(self):
        return f"{self.Message}"

class ThreatReport(AbstractReport):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.required("Source", "TargetType", "Target", "Entry", "Message")

    def __init__(self, source, **kwargs):
        super().__init__(Source = source, **kwargs)
        self.required("Source", "TargetType", "Target", "Entry", "Message")

    def __str__(self):
        return f"{self.Message}"
