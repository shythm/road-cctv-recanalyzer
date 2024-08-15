from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
from datetime import datetime
from enum import Enum

class TaskState(Enum):
    UNDEFINED = -1
    PENDING = 0
    STARTED = 1
    CANCELED = 2
    FINISHED = 3
    FAILED = 4

class EntityNotFound(Exception):
    pass

class TaskCancelException(Exception):
    pass

@dataclass
class TaskParamMeta:
    name: str
    desc: str
    accept: list[str] # 허용되는 ResultItem.type 값 또는 Primitive Type
    optional: bool = True

@dataclass
class TaskItem(DataClassJsonMixin):
    id: str
    name: str
    params: dict[str, str]
    state: TaskState | int
    reason: str
    progress: float

@dataclass
class TaskOutput(DataClassJsonMixin):
    taskid: str
    name: str
    type: str
    desc: str
    createdat: datetime

@dataclass
class CCTVStream(DataClassJsonMixin):
    name: str
    coordx: float
    coordy: float
