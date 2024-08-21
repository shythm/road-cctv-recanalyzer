import os
import threading
from uuid import uuid4
from dataclasses import dataclass

import cv2
import pandas as pd
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from deep_sort_realtime.deep_sort.track import Track

from core.srv import TaskService
from core.model import TaskItem, TaskParamMeta, TaskState, TaskOutput, TaskCancelException, EntityNotFound
from core.repo import TaskItemRepository, TaskOutputRepository


@dataclass
class Detection:
    frame: int
    objid: int
    clsid: int
    x: int
    y: int


class YOLOv8DeepSORTTackingTaskSrv(TaskService):
    _confidence_threshold_default = 0.6
    _cancel_req: dict[str, bool] = {}

    def __init__(
            self, task_repo: TaskItemRepository, model_path: str,
            outputs_path: str, output_repo: TaskOutputRepository):

        self._task_repo = task_repo
        self._model_path = model_path
        self._outputs_path = outputs_path
        self._output_repo = output_repo

    def get_name(self) -> str:
        return "CCTV 객체 추적 (YOLOv8 + DeepSORT)"

    def get_params(self) -> list[dict]:
        return [
            TaskParamMeta(
                name="targetname", desc="분석할 CCTV 영상", accept=["video/mp4"]),
            TaskParamMeta(
                name="confidence", desc="신뢰도 임계값", accept=["float"], optional=True),
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

        def task_func():
            nonlocal confidence, targetname, fps, task
            cap = None
            cap_out = None

            try:
                model = YOLO(model=self._model_path)
                tracker = DeepSort(max_age=10)

                cap = cv2.VideoCapture(os.path.join(self._outputs_path, targetname))
                if not cap.isOpened():
                    raise Exception('Error opening video file')

                frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                frame_total_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                frame_num = 0
                fourcc = cv2.VideoWriter.fourcc(*'mp4v')

                video_out_path = os.path.join(self._outputs_path, f"{task.id}.mp4")
                cap_out = cv2.VideoWriter(video_out_path, fourcc, fps, (frame_width, frame_height))

                results_path = os.path.join(self._outputs_path, f"{task.id}.csv")
                results: list[Detection] = []

                self._task_repo.update(task.id, TaskState.STARTED, "준비가 완료되어 객체 추적을 시작합니다.")

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    if self._cancel_req.get(task.id, False):
                        raise TaskCancelException("객체 추적이 요청에 의해 중단되었습니다.")

                    # https://docs.ultralytics.com/modes/predict/
                    detection = model.predict(source=[frame], conf=confidence, verbose=False)[0]

                    # for update deepsort tracker
                    raw_detections: list[tuple[list[float | int], float, str]] = []

                    for data in detection.boxes.data.tolist():
                        # data : [xmin, ymin, xmax, ymax, confidence_score, class_id]
                        xmin, ymin, xmax, ymax = map(int, data[:4])
                        width = xmax - xmin
                        height = ymax - ymin
                        confidence_score = float(data[4])
                        detection_class = int(data[5])

                        # [left, top, width, height], confidence, detection_class
                        raw_detections.append(([xmin, ymin, width, height],
                                              confidence_score, detection_class))

                    tracks: list[Track] = tracker.update_tracks(raw_detections, frame=frame)
                    for track in tracks:
                        if not track.is_confirmed():
                            continue

                        track_id = track.track_id
                        class_id = track.det_class

                        xmin, ymin, xmax, ymax = map(int, track.to_ltrb())
                        x = (xmin + xmax) // 2
                        y = (ymin + ymax) // 2

                        # draw box
                        green = (0, 255, 0)
                        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), green, 2)
                        cv2.circle(frame, (x, y), radius=2, color=green, thickness=-1)
                        cv2.putText(frame, str(track_id), (xmin, ymin - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, green, 2)

                        # save detection
                        results.append(Detection(
                            frame=frame_num, objid=track_id, clsid=class_id, x=x, y=y))

                    frame_num += 1
                    cap_out.write(frame)
                    task.progress = frame_num / frame_total_count

                df = pd.DataFrame([vars(result) for result in results])
                df.to_csv(results_path, index=False)

                # save outputs
                self._output_repo.save(TaskOutput(
                    name=f"{task.id}.csv",
                    type="text/csv",
                    desc=f"{task.params['cctv']} 객체 추적 결과",
                    taskid=task.id,
                    metadata=task.params,
                ))
                self._output_repo.save(TaskOutput(
                    name=f"{task.id}.mp4",
                    type="video/mp4",
                    desc=f"{task.params['cctv']} 객체 추적 영상",
                    taskid=task.id,
                    metadata=task.params,
                ))

                task.progress = 1.0
                # update task state
                self._task_repo.update(task.id, TaskState.FINISHED, "객체 추적이 완료되었습니다.")

            except TaskCancelException as e:
                self._task_repo.update(task.id, TaskState.CANCELED, str(e))
            except Exception as e:
                self._task_repo.update(task.id, TaskState.FAILED, str(e))

            finally:
                if cap is not None and cap.isOpened():
                    cap.release()
                if cap_out is not None and cap_out.isOpened():
                    cap_out.release()

        thread = threading.Thread(target=task_func)
        thread.start()
        return task

    def stop(self, id: str):
        req = self._cancel_req.get(id)
        if req is None:
            raise EntityNotFound(f"녹화 작업이 존재하지 않습니다.")
        self._cancel_req[id] = True
