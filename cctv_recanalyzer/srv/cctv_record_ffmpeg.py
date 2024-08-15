import os
import signal
import threading
import json
import time
import subprocess
import dataclasses
from uuid import uuid4
from datetime import datetime

from util import get_logger
from core.srv import TaskService
from core.repo import TaskOutputRepository, CCTVStreamRepository
from core.model import TaskItem, TaskState, TaskParamMeta, TaskOutput, TaskCancelException, EntityNotFound

class CCTVRecordFFmpegTaskSrv(TaskService):
    _lock = threading.Lock()

    def __init__(
            self, tasks_json_path: str, outputs_path: str, 
            cctv_stream_repo: CCTVStreamRepository, output_repo: TaskOutputRepository):

        self._tasks_json_path = tasks_json_path
        self._outputs_path = outputs_path
        self._cctv_stream_repo = cctv_stream_repo
        self._output_repo = output_repo
        self._logger = get_logger(__name__)

        self._tasks: list[TaskItem] = []
        self._cancel_req: dict[str, bool] = {}

        self._init_tasks()

    def _init_tasks(self):
        try:
            with open(self._tasks_json_path, "r") as f:
                json_data = f.read()
                self._tasks = TaskItem.schema().loads(json_data, many=True)

            for task in self._tasks:
                # fix invalid state
                if task.state == TaskState.PENDING or task.state == TaskState.STARTED:
                    task.state = TaskState.FAILED
                    task.reason = "녹화 중에 작업이 예기치 않게 종료되었습니다."

            self._save_tasks()
        except FileNotFoundError:
            pass

    def _save_tasks(self):
        data = TaskItem.schema().dumps(self._tasks, many=True)
        with open(self._tasks_json_path, "w") as f:
            json.dump(json.loads(data), f, ensure_ascii=False, indent=2)

    def _add_task_state(self, task: TaskItem):
        with self._lock:
            self._tasks.append(task)
            self._cancel_req[task.id] = False
            self._save_tasks()

    def _update_task_state(self, id: str, state: TaskState, reason: str):
        with self._lock:
            for task in self._tasks:
                if task.id == id:
                    task.state = state
                    task.reason = reason
                    self._save_tasks()
                    break
            else:
                raise EntityNotFound(f"녹화 작업이 존재하지 않습니다. id={id}")

    def get_name(self) -> str:
        return "CCTV 녹화"
    
    def get_params(self) -> list[TaskParamMeta]:
        return [
            TaskParamMeta("cctv", "CCTV 이름", ["str"]),
            TaskParamMeta("startat", "녹화 시작 시간", ["datetime"]),
            TaskParamMeta("endat", "녹화 종료 시간", ["datetime"]),
        ]
    
    def get_tasks(self) -> list[TaskItem]:
        with self._lock:
            return [TaskItem(**dataclasses.asdict(task)) for task in self._tasks]
        
    def del_task(self, id: str):
        pass

    def start(self, **kwargs) -> TaskItem:
        cctv = self._cctv_stream_repo.get_by_name(kwargs['cctv'])
        startat: datetime = kwargs['startat']
        endat: datetime = kwargs['endat']

        task = TaskItem(
            id=str(uuid4()),
            name=f"{cctv.name} 녹화",
            params={
                "cctv": cctv.name,
                "startat": startat.isoformat(),
                "endat": endat.isoformat(),
            },
            state=TaskState.PENDING,
            reason="",
            progress=0.0
        )
        self._add_task_state(task)

        def task_func():
            try:
                # 녹화 대기
                while True:
                    now = datetime.now()
                    if now >= endat:
                        raise ValueError(f"현 시각이 녹화 종료 시각을 지났습니다.")
                    elif now >= startat:
                        break

                    if self._cancel_req.get(task.id, False):
                        raise TaskCancelException(f"녹화가 요청에 의해 취소되었습니다.")
                    time.sleep(1)

                hls = self._cctv_stream_repo.get_hls(cctv)
                duration = (endat - datetime.now()).seconds
                output_path = os.path.join(self._outputs_path, f"{task.id}.mp4")
                stdout = open(os.path.join(self._outputs_path, f"{task.id}.out"), 'w')
                stderr = open(os.path.join(self._outputs_path, f"{task.id}.err"), 'w')

                # 녹화 시작
                # call ffmpeg: ffmpeg -i <HLS_URL> -c copy -t <DURATION> <OUTPUT_PATH>
                ffmpeg = subprocess.Popen(
                    ["ffmpeg", "-i", hls, "-c", "copy", "-t", str(duration), output_path],
                    stdout=stdout,
                    stderr=stderr,
                    stdin=subprocess.DEVNULL,
                )

                self._update_task_state(task.id, TaskState.STARTED, "녹화 시작 시간이 되어 녹화 중에 있습니다.")
                while ffmpeg.poll() is None:
                    task.progress = (datetime.now() - startat).seconds / (endat - startat).seconds
                    task.progress = min(1.0, task.progress)

                    if self._cancel_req.get(task.id, False):
                        ffmpeg.send_signal(signal.SIGTERM)
                        raise TaskCancelException(f"녹화가 요청에 의해 취소되었습니다.")
                    time.sleep(1)

                # 녹화 정리
                retcode = ffmpeg.returncode
                stdout.close()
                stderr.close()

                now = datetime.now()
                output_mp4 = TaskOutput(
                    taskid=task.id,
                    name=f"{task.id}.mp4",
                    type="video/mp4",
                    desc=f"{cctv.name} 녹화 영상",
                    createdat=now
                )
                self._output_repo.save(output_mp4)
                output_stdout = TaskOutput(
                    taskid=task.id,
                    name=f"{task.id}.out",
                    type="text/stdout",
                    desc=f"{cctv.name} 녹화 stdout",
                    createdat=now
                )
                self._output_repo.save(output_stdout)
                output_stderr = TaskOutput(
                    taskid=task.id,
                    name=f"{task.id}.err",
                    type="text/stderr",
                    desc=f"{cctv.name} 녹화 stderr",
                    createdat=now
                )
                self._output_repo.save(output_stderr)

                if retcode != 0:
                    raise Exception(f"녹화 중 오류가 발생하였습니다.")
                
                task.progress = 1.0
                self._update_task_state(task.id, TaskState.FINISHED, "녹화가 완료되었습니다.")

            except TaskCancelException as e:
                self._update_task_state(task.id, TaskState.CANCELED, str(e))
            except Exception as e:
                self._update_task_state(task.id, TaskState.FAILED, str(e))

        thread = threading.Thread(target=task_func)
        thread.start()
        return task

    def stop(self, id: str):
        with self._lock:
            req = self._cancel_req.get(id)
            if req is None:
                raise EntityNotFound(f"녹화 작업이 존재하지 않습니다. id={id}")
            self._cancel_req[id] = True

