import json
import threading
from datetime import datetime

from core.model import TaskOutput
from core.repo import TaskOutputRepository

class TaskOutputFileRepo(TaskOutputRepository):
    _lock = threading.Lock()

    def __init__(self, json_path: str):
        self._json_path = json_path
        self._outputs: list[TaskOutput] = []
        self._load_data()

    def _load_data(self):
        # deserialize from json file
        try:
            with open(self._json_path, "r") as f:
                data = json.load(f)
                self._outputs = [TaskOutput(
                    taskid=output['taskid'],
                    name=output['name'],
                    type=output['type'],
                    desc=output['desc'],
                    createdat=datetime.fromisoformat(output['createdat']),
                    metadata=output.get('metadata', {})
                ) for output in data]
        except FileNotFoundError:
            pass

    def _save_data(self):
        # serialize to json file
        data = [{
            'taskid': output.taskid,
            'name': output.name,
            'type': output.type,
            'desc': output.desc,
            'createdat': output.createdat.isoformat(),
            'metadata': output.metadata,
        } for output in self._outputs]

        with open(self._json_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save(self, output: TaskOutput):
        with self._lock:
            self._outputs.append(output)
            self._save_data()

    def get(self, taskid: str) -> list[TaskOutput]:
        with self._lock:
            ret = []
            for output in self._outputs:
                if output.taskid == taskid:
                    ret.append(output)
            return ret

    def get_all(self) -> list[TaskOutput]:
        with self._lock:
            return [output for output in self._outputs]

    def delete(self, taskid: str):
        with self._lock:
            self._outputs = [output for output in self._outputs if output.taskid != taskid]
            self._save_data()
