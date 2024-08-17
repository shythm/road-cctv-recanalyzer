from abc import ABC, abstractmethod
from core.model import TaskItem, TaskParamMeta

class TaskService(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_params(self) -> list[TaskParamMeta]:
        pass

    @abstractmethod
    def get_tasks(self) -> list[TaskItem]:
        pass

    @abstractmethod
    def del_task(self, id: str):
        pass

    @abstractmethod
    def start(self, params: dict[str, str]) -> TaskItem:
        pass

    @abstractmethod
    def stop(self, id: str):
        pass
