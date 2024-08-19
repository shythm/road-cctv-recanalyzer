import os
import json
import threading
from datetime import datetime

from core.model import TaskOutput
from core.repo import TaskOutputRepository


class TaskOutputFileRepo(TaskOutputRepository):
    _lock = threading.Lock()

    def __init__(self, json_path: str, outputs_path: str):
        self._json_path = json_path
        self._outputs_path = outputs_path
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

    def get_by_taskid(self, taskid: str) -> list[TaskOutput]:
        with self._lock:
            return [output for output in self._outputs if output.taskid == taskid]

    def get_by_name(self, name: str) -> TaskOutput:
        with self._lock:
            for output in self._outputs:
                if output.name == name:
                    return output
            raise ValueError(f"TaskOutput not found: {name}")

    def get_all(self) -> list[TaskOutput]:
        with self._lock:
            return [output for output in self._outputs]

    def delete(self, taskid: str):
        deleted: list[TaskOutput] = []
        outputs: list[TaskOutput] = []

        with self._lock:
            for output in self._outputs:
                if output.taskid == taskid:
                    deleted.append(output)
                else:
                    outputs.append(output)

            self._outputs = outputs
            self._save_data()

        for output in deleted:
            path = os.path.join(self._outputs_path, output.name)
            if os.path.exists(path):
                os.remove(path)
