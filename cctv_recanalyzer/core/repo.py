from abc import ABC, abstractmethod
from core.model import TaskItem, TaskOutput, TaskState, CCTVStream

class TaskItemRepository(ABC):
    @abstractmethod
    def add(self, task: TaskItem):
        pass

    @abstractmethod
    def get(self, id: str) -> TaskItem:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> list[TaskItem]:
        pass

    @abstractmethod
    def update(self, id: str, state: TaskState, reason: str) -> TaskItem:
        pass

    @abstractmethod
    def delete(self, id: str):
        pass

class TaskOutputRepository(ABC):
    @abstractmethod
    def save(self, output: TaskOutput):
        pass

    @abstractmethod
    def get_by_taskid(self, taskid: str) -> list[TaskOutput]:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> TaskOutput:
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
