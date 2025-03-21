import os
import threading
from dataclasses import dataclass
from queue import Queue
from uuid import uuid4

import cv2
import pandas as pd
from core.model import (
    EntityNotFound,
    TaskCancelException,
    TaskItem,
    TaskOutput,
    TaskParamMeta,
    TaskState,
)
from core.repo import TaskItemRepository, TaskOutputRepository
from core.srv import TaskService
from deep_sort_realtime.deep_sort.track import Track
from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO


@dataclass
class Detection:
    frame: int
    objid: int
    clsid: int
    x: int
    y: int


class YOLOv8DeepSORTTackingTaskSrv(TaskService):

    def __init__(
        self,
        task_repo: TaskItemRepository,
        model_path: str,
        outputs_path: str,
        output_repo: TaskOutputRepository,
    ):

        self._confidence_threshold_default = 0.6
        self._cancel_req: dict[str, bool] = {}
        self._task_queue = Queue()  # Queue to manage task execution

        self._task_repo = task_repo
        self._model_path = model_path
        self._outputs_path = outputs_path
        self._output_repo = output_repo

        # Start worker thread
        self._worker_thread = threading.Thread(target=self._task_worker)
        self._worker_thread.start()

    def _task_worker(self):
        while True:
            task = self._task_queue.get()  # Blocks until a task is available
            if task:
                self._run_task(task)
                self._task_queue.task_done()

    def _run_task(self, task: TaskItem):
        if self._cancel_req.get(task.id, False):
            self._task_repo.update(
                task.id, TaskState.CANCELED, "객체 추적이 취소되었습니다."
            )
            return

        confidence = float(task.params["confidence"])
        targetname = task.params["targetname"]
        fps = int(task.params["fps"])
        cap = None
        cap_out = None

        try:
            model = YOLO(model=self._model_path)
            tracker = DeepSort(
                max_iou_distance=0.3, max_age=20, n_init=2, max_cosine_distance=0.2
            )

            cap = cv2.VideoCapture(os.path.join(self._outputs_path, targetname))
            if not cap.isOpened():
                raise Exception("Error opening video file")

            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_total_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_num = 0
            fourcc = cv2.VideoWriter.fourcc(*"mp4v")

            video_out_tmp = "/tmp/cctv-yolov8-deepsort.mp4"
            cap_out = cv2.VideoWriter(
                video_out_tmp, fourcc, fps, (frame_width, frame_height)
            )

            results_path = os.path.join(self._outputs_path, f"{task.id}.csv")
            results: list[Detection] = []

            self._task_repo.update(
                task.id, TaskState.STARTED, "준비가 완료되어 객체 추적을 시작합니다."
            )

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if self._cancel_req.get(task.id, False):
                    raise TaskCancelException("객체 추적이 요청에 의해 중단되었습니다.")

                # https://docs.ultralytics.com/modes/predict/
                detection = model.predict(
                    source=[frame], conf=confidence, verbose=False
                )[0]
                if detection.boxes is None:
                    continue

                # for update deepsort tracker
                raw_detections: list[tuple[list[int], float, int]] = []

                for data in detection.boxes.data.tolist():
                    # data : [xmin, ymin, xmax, ymax, confidence_score, class_id]
                    xmin, ymin, xmax, ymax = map(int, data[:4])
                    width = xmax - xmin
                    height = ymax - ymin
                    confidence_score = float(data[4])
                    detection_class = int(data[5])

                    # [left, top, width, height], confidence, detection_class
                    raw_detections.append(
                        ([xmin, ymin, width, height], confidence_score, detection_class)
                    )

                tracks: list[Track] = tracker.update_tracks(raw_detections, frame=frame)
                for track in tracks:
                    if not track.is_confirmed():
                        continue

                    track_id = track.track_id
                    class_id = track.det_class

                    xmin, ymin, xmax, ymax = map(int, track.to_ltrb())  # type: ignore
                    x = (xmin + xmax) // 2
                    y = (ymin + ymax) // 2

                    # draw box
                    green = (0, 255, 0)
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), green, 2)
                    cv2.circle(frame, (x, y), radius=2, color=green, thickness=-1)
                    cv2.putText(
                        frame,
                        str(track_id),
                        (xmin, ymin - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        green,
                        2,
                    )

                    # save detection
                    results.append(
                        Detection(
                            frame=frame_num, objid=track_id, clsid=class_id, x=x, y=y
                        )
                    )  # type: ignore

                frame_num += 1
                cap_out.write(frame)
                task.progress = frame_num / frame_total_count

            # save results
            df = pd.DataFrame([vars(result) for result in results])
            df.to_csv(results_path, index=False)

            # using ffmpeg to convert mp4 video
            cap_out.release()
            ffmpeg_ret = os.system(
                f"ffmpeg -y -i {video_out_tmp} -vcodec libx264 {os.path.join(self._outputs_path, task.id)}.mp4"
            )
            if ffmpeg_ret != 0:
                raise Exception("There was an error converting the video file.")

            # save outputs
            self._output_repo.save(
                TaskOutput(
                    name=f"{task.id}.csv",
                    type="text/csv",
                    desc=f"{task.params['cctv']} 객체 추적 결과",
                    taskid=task.id,
                    metadata=task.params,
                )
            )
            self._output_repo.save(
                TaskOutput(
                    name=f"{task.id}.mp4",
                    type="video/mp4",
                    desc=f"{task.params['cctv']} 객체 추적 영상",
                    taskid=task.id,
                    metadata=task.params,
                )
            )

            task.progress = 1.0
            # update task state
            self._task_repo.update(
                task.id, TaskState.FINISHED, "객체 추적이 완료되었습니다."
            )

        except TaskCancelException as e:
            self._task_repo.update(task.id, TaskState.CANCELED, str(e))
        except Exception as e:
            self._task_repo.update(task.id, TaskState.FAILED, str(e))

        finally:
            if cap is not None and cap.isOpened():
                cap.release()
            if cap_out is not None and cap_out.isOpened():
                cap_out.release()

    def get_name(self) -> str:
        return "CCTV 객체 추적 (YOLOv8 + DeepSORT)"

    def get_params(self) -> list[TaskParamMeta]:
        return [
            TaskParamMeta(
                name="targetname", desc="분석할 CCTV 영상", accept=["video/mp4"]
            ),
            TaskParamMeta(
                name="confidence", desc="신뢰도 임계값", accept=["float"], optional=True
            ),
        ]

    def get_tasks(self) -> list[TaskItem]:
        return self._task_repo.get_by_name(self.get_name())

    def del_task(self, id: str):
        self._task_repo.delete(id)
        self._output_repo.delete(id)

    def start(self, params: dict[str, str]) -> TaskItem:
        targetname = params["targetname"]
        confidence = float(params.get("confidence", self._confidence_threshold_default))

        fps = 30
        tmp_cap = cv2.VideoCapture(os.path.join(self._outputs_path, targetname))
        if tmp_cap.isOpened():
            fps = int(tmp_cap.get(cv2.CAP_PROP_FPS))
        tmp_cap.release()

        target_metadata = self._output_repo.get_by_name(targetname).metadata
        metadata = {
            "targetname": targetname,
            "confidence": str(confidence),
            "fps": str(fps),
            "cctv": target_metadata.get("cctv", "N/A"),
            "startat": target_metadata.get("startat", "N/A"),
            "endat": target_metadata.get("endat", "N/A"),
        }

        task = TaskItem(
            id=str(uuid4()),
            name=self.get_name(),
            params=metadata,
            state=TaskState.PENDING,
            reason="작업이 제출되었습니다.",
            progress=0.0,
        )
        self._task_repo.add(task)
        self._cancel_req[task.id] = False
        self._task_queue.put(task)

        return task

    def stop(self, id: str):
        req = self._cancel_req.get(id)
        if req is None:
            raise EntityNotFound(f"녹화 작업이 존재하지 않습니다.")
        self._cancel_req[id] = True
        self._task_repo.update(
            id, TaskState.PENDING, "객체 추적 중지 요청이 접수되었습니다."
        )
