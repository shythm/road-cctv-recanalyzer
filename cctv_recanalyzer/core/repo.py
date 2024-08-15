from abc import ABC, abstractmethod
from core.model import TaskOutput, CCTVStream

class TaskOutputRepository(ABC):
    @abstractmethod
    def save(self, output: TaskOutput):
        pass

    @abstractmethod
    def get(self, taskid: str) -> list[TaskOutput]:
        pass

    @abstractmethod
    def get_all(self) -> list[TaskOutput]:
        pass

    @abstractmethod
    def delete(self, taskid: str):
        pass

class CCTVStreamRepository(ABC):
    @abstractmethod
    def save(self, name: str, coord: tuple[float, float]) -> CCTVStream:
        pass

    @abstractmethod
    def delete(self, name: str) -> CCTVStream:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> CCTVStream:
        pass

    @abstractmethod
    def get_all(self) -> list[CCTVStream]:
        pass

    @abstractmethod
    def get_hls(self, cctvstream: CCTVStream) -> str:
        pass
