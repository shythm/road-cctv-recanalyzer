import json
import threading
from datetime import datetime

from core.model import TaskItem, TaskState, EntityNotFound
from core.repo import TaskItemRepository

class TaskItemJsonRepo(TaskItemRepository):
    _lock = threading.Lock()
    _tasks: list[TaskItem] = []

    def __init__(self, json_path: str, fix_invalid_state: bool = True):
        self._json_path = json_path
        self._init_tasks()

        if fix_invalid_state:
            # fix invalid state
            for task in self._tasks:
                if task.state == TaskState.PENDING or task.state == TaskState.STARTED:
                    task.state = TaskState.FAILED
                    task.reason = "작업이 예기치 않게 종료되었습니다."
            self._save_tasks()

    def _init_tasks(self):
        try:
            # deserialize from json file
            with open(self._json_path, "r") as f:
                data = json.load(f)
                self._tasks = [TaskItem(
                    id=task['id'],
                    name=task['name'],
                    params=task['params'],
                    state=TaskState(task['state']),
                    reason=task['reason'],
                    progress=task['progress'],
                    createdat=datetime.fromisoformat(task['createdat'])
                ) for task in data]
        except FileNotFoundError:
            pass

    def _save_tasks(self):
        # serialize to json file
        data = [{
            'id': task.id,
            'name': task.name,
            'params': task.params,
            'state': task.state.value,
            'reason': task.reason,
            'progress': task.progress,
            'createdat': task.createdat.isoformat(),
        } for task in self._tasks]

        with open(self._json_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, task: TaskItem):
        with self._lock:
            self._tasks.append(task)
            self._save_tasks()
            return task
        
    def get(self, id: str) -> TaskItem:
        with self._lock:
            for task in self._tasks:
                if task.id == id:
                    return task
            raise EntityNotFound("작업을 찾을 수 없습니다.")
        
    def get_by_name(self, name: str) -> list[TaskItem]:
        with self._lock:
            return [task for task in self._tasks if task.name == name]

    def update(self, id: str, state: TaskState, reason: str) -> TaskItem:
        with self._lock:
            for task in self._tasks:
                if task.id == id:
                    task.state = state
                    task.reason = reason
                    self._save_tasks()
                    return task
            raise EntityNotFound("작업을 찾을 수 없습니다.")
        
    def delete(self, id: str):
        with self._lock:
            self._tasks = [task for task in self._tasks if task.id != id]
            self._save_tasks()
