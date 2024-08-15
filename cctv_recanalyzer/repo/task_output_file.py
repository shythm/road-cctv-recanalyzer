import json
import threading
from dataclasses import asdict

from core.model import TaskOutput
from core.repo import TaskOutputRepository

class TaskOutputFileRepo(TaskOutputRepository):
    _lock = threading.Lock()

    def __init__(self, json_path: str):
        self._json_path = json_path
        self._outputs: list[TaskOutput] = []
        self._load_data()

    def _load_data(self):
        try:
            with open(self._json_path, "r") as f:
                json_data = f.read()
                self._outputs = TaskOutput.schema().loads(json_data, many=True)
        except FileNotFoundError:
            pass

    def _save_data(self):
        data = TaskOutput.schema().dumps(self._outputs, many=True)
        with open(self._json_path, "w") as f:
            json.dump(json.loads(data), f, ensure_ascii=False, indent=2)

    def save(self, output: TaskOutput):
        with self._lock:
            self._outputs.append(output)
            self._save_data()

    def get(self, taskid: str) -> list[TaskOutput]:
        with self._lock:
            ret = []
            for output in self._outputs:
                if output.taskid == taskid:
                    ret.append(TaskOutput(**asdict(output)))
            return ret

    def get_all(self) -> list[TaskOutput]:
        with self._lock:
            return [TaskOutput(**asdict(output)) for output in self._outputs]

    def delete(self, taskid: str):
        with self._lock:
            self._outputs = [output for output in self._outputs if output.taskid != taskid]
            self._save_data()
