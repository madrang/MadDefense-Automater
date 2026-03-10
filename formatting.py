from abc import ABC, abstractmethod

class ReportOutput(ABC):
    @abstractmethod
    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def printResult(self, item):
        return NotImplemented
