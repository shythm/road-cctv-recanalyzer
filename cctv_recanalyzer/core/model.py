from dataclasses import dataclass, field
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
    accept: list[str]  # 허용되는 ResultItem.type 값 또는 Primitive Type
    optional: bool = False


@dataclass
class TaskItem:
    id: str
    name: str
    params: dict[str, str]
    state: TaskState | int
    reason: str
    progress: float
    createdat: datetime = field(default_factory=datetime.now)


@dataclass
class TaskOutput:
    name: str  # filename [identifier]
    type: str
    desc: str
    taskid: str
    metadata: dict[str, str]  # custom field
    createdat: datetime = field(default_factory=datetime.now)


@dataclass
class CCTVStream:
    name: str
    coordx: float
    coordy: float
