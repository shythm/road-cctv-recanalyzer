import os
import signal
import threading
import time
import subprocess
from uuid import uuid4
from datetime import datetime

from core.srv import TaskService
from core.repo import TaskItemRepository, TaskOutputRepository, CCTVStreamRepository
from core.model import TaskItem, TaskState, TaskParamMeta, TaskOutput, TaskCancelException, EntityNotFound


class CCTVRecordFFmpegTaskSrv(TaskService):
    _cancel_req: dict[str, bool] = {}

    def __init__(
            self, task_repo: TaskItemRepository, cctv_stream_repo: CCTVStreamRepository,
            outputs_path: str, output_repo: TaskOutputRepository):

        self._task_repo = task_repo
        self._cctv_stream_repo = cctv_stream_repo
        self._outputs_path = outputs_path
        self._output_repo = output_repo

    def get_name(self) -> str:
        return "CCTV 녹화"

    def get_params(self) -> list[TaskParamMeta]:
        return [
            TaskParamMeta("cctv", "CCTV 이름", ["str"]),
            TaskParamMeta("startat", "녹화 시작 시간", ["datetime"]),
            TaskParamMeta("endat", "녹화 종료 시간", ["datetime"]),
        ]

    def get_tasks(self) -> list[TaskItem]:
        return self._task_repo.get_by_name(self.get_name())

    def del_task(self, id: str):
        self._task_repo.delete(id)
        self._output_repo.delete(id)

    def start(self, params: dict[str, str]) -> TaskItem:
        cctv = self._cctv_stream_repo.get_by_name(params['cctv'])
        startat = datetime.fromisoformat(params['startat'])
        endat = datetime.fromisoformat(params['endat'])
        params = {
            "cctv": cctv.name,
            "startat": startat.isoformat(),
            "endat": endat.isoformat(),
        }

        task = TaskItem(
            id=str(uuid4()),
            name=self.get_name(),
            params=params,
            state=TaskState.PENDING,
            reason="녹화 대기 중에 있습니다.",
            progress=0.0
        )
        self._task_repo.add(task)
        self._cancel_req[task.id] = False

        def task_func():
            nonlocal startat, endat, task
            ffmpeg_stdout = None
            ffmpeg_stderr = None

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
                    time.sleep(0.5)

                hls = self._cctv_stream_repo.get_hls(cctv)
                duration = (endat - datetime.now()).seconds
                output_path = os.path.join(self._outputs_path, f"{task.id}.mp4")

                ffmpeg_stdout = open(os.path.join(self._outputs_path, f"{task.id}.log"), "w")
                ffmpeg_stderr = open(os.path.join(self._outputs_path, f"{task.id}.err"), "w")

                # 녹화 시작
                # call ffmpeg: ffmpeg -i <HLS_URL> -c copy -t <DURATION> <OUTPUT_PATH>
                ffmpeg = subprocess.Popen(
                    ["ffmpeg", "-i", hls, "-c", "copy", "-t", str(duration), output_path],
                    stdout=ffmpeg_stdout,
                    stderr=ffmpeg_stderr,
                    stdin=subprocess.DEVNULL,
                )

                self._task_repo.update(task.id, TaskState.STARTED, "녹화 시작 시간이 되어 녹화 중에 있습니다.")
                while ffmpeg.poll() is None:
                    task.progress = (datetime.now() - startat).seconds / (endat - startat).seconds
                    task.progress = min(1.0, task.progress)

                    if self._cancel_req.get(task.id, False):
                        ffmpeg.send_signal(signal.SIGTERM)
                        raise TaskCancelException(f"녹화가 요청에 의해 취소되었습니다.")
                    time.sleep(1)

                # 녹화 정리
                retcode = ffmpeg.returncode

                if retcode == 0:
                    # write recorded video
                    self._output_repo.save(TaskOutput(
                        taskid=task.id,
                        name=f"{task.id}.mp4",
                        type="video/mp4",
                        desc=f"{cctv.name} 녹화 영상",
                        metadata=params,
                    ))
                    # remove stdout, stderr
                    if os.path.exists(ffmpeg_stdout.name):
                        os.remove(ffmpeg_stdout.name)
                    if os.path.exists(ffmpeg_stderr.name):
                        os.remove(ffmpeg_stderr.name)
                else:
                    # write stdout
                    ffmpeg_stdout.close()
                    self._output_repo.save(TaskOutput(
                        taskid=task.id,
                        name=f"{task.id}.out",
                        type="text/stdout",
                        desc=f"{cctv.name} 녹화 stdout",
                        metadata=params,
                    ))
                    # write stderr
                    ffmpeg_stderr.close()
                    self._output_repo.save(TaskOutput(
                        taskid=task.id,
                        name=f"{task.id}.err",
                        type="text/stderr",
                        desc=f"{cctv.name} 녹화 stderr",
                        metadata=params,
                    ))
                    # remove output file
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    raise Exception(f"녹화 중 오류가 발생하였습니다.")

                task.progress = 1.0
                self._task_repo.update(task.id, TaskState.FINISHED, "녹화가 완료되었습니다.")

            except TaskCancelException as e:
                self._task_repo.update(task.id, TaskState.CANCELED, str(e))
            except Exception as e:
                self._task_repo.update(task.id, TaskState.FAILED, str(e))
            finally:
                if ffmpeg_stdout is not None:
                    ffmpeg_stdout.close()
                if ffmpeg_stderr is not None:
                    ffmpeg_stderr.close()

        thread = threading.Thread(target=task_func)
        thread.start()
        return task

    def stop(self, id: str):
        req = self._cancel_req.get(id)
        if req is None:
            raise EntityNotFound(f"녹화 작업이 존재하지 않습니다. id={id}")
        self._cancel_req[id] = True
