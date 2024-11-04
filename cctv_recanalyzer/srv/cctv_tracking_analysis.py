import json
import math
import os
import threading
import traceback
from uuid import uuid4

import cv2
import numpy as np
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


def find_closest_rectangle(lt, lb, rt, rb, ratio):
    # 하단 가로 변의 길이 구하기
    width = int(math.sqrt((lb[0] - rb[0]) ** 2 + (lb[1] - rb[1]) ** 2))
    # 비율에 따라 세로 변의 길이 구하기
    height = int(width * ratio)

    points = [(0, 0), (0, height), (width, 0), (width, height)]
    return points, width, height


def interpolate_persp_data(persp_df: pd.DataFrame) -> pd.DataFrame:
    """
    추적된 객체에 대하여 두 프레임 사이의 거리가 1보다 큰 경우, 중간 프레임에 대하여 보간을 수행합니다.
    """
    # create new dataframe
    df = pd.DataFrame(columns=["objid", "frame"])

    # interpolate missing frame
    for objid in persp_df["objid"].unique():
        temp_df: pd.DataFrame = persp_df[persp_df["objid"] == objid]
        frames = temp_df["frame"].sort_values().values

        col_frame = np.arange(frames[0], frames[-1] + 1)  # min, max + 1
        df = pd.concat(
            [df, pd.DataFrame({"objid": objid, "frame": col_frame})], ignore_index=True
        )

    # join tracking data
    df = df.join(
        persp_df.set_index(["objid", "frame"]), on=["objid", "frame"], how="left"
    )

    # interpolate missing class with the same class
    df["clsid"] = df.groupby("objid")["clsid"].ffill().bfill()

    # interpolate missing x, y with linear interpolation
    df["x"] = (
        df.groupby("objid")["x"]
        .apply(lambda x: x.interpolate(method="linear"))
        .reset_index(drop=True)
    )
    df["y"] = (
        df.groupby("objid")["y"]
        .apply(lambda x: x.interpolate(method="linear"))
        .reset_index(drop=True)
    )

    # interpolate missing pos_x, pox_y with linear interpolation
    df["perspx"] = (
        df.groupby("objid")["perspx"]
        .apply(lambda x: x.interpolate(method="linear"))
        .reset_index(drop=True)
    )
    df["perspy"] = (
        df.groupby("objid")["perspy"]
        .apply(lambda x: x.interpolate(method="linear"))
        .reset_index(drop=True)
    )

    return df


class CCTVTrackingAnalysisTaskSrv(TaskService):

    def __init__(
        self,
        task_repo: TaskItemRepository,
        outputs_path: str,
        output_repo: TaskOutputRepository,
    ):

        self._task_repo = task_repo
        self._outputs_path = outputs_path
        self._output_repo = output_repo

    def get_name(self) -> str:
        return "차량 추적 데이터 분석"

    def get_params(self) -> list[TaskParamMeta]:
        return [
            TaskParamMeta(
                name="trackdata", desc="추적 데이터(csv)", accept=["text/detection"]
            ),
            TaskParamMeta(name="roi", desc="ROI 좌표", accept=["json"]),
            TaskParamMeta(name="roadwidth", desc="도로 너비(m)", accept=["float"]),
            TaskParamMeta(name="roadheight", desc="도로 길이(m)", accept=["float"]),
        ]

    def get_tasks(self) -> list[TaskItem]:
        return self._task_repo.get_by_name(self.get_name())

    def del_task(self, id: str):
        self._task_repo.delete(id)
        self._output_repo.delete(id)

    def start(self, params: dict[str, str]) -> TaskItem:
        # get csv file path
        trackdata = params["trackdata"]

        # get road width and height
        roadwidth = float(params["roadwidth"])  # meter
        roadheight = float(params["roadheight"])  # meter

        # get src points [lt, lb, rt, rb]
        roi = params["roi"]
        srcpoints: list[tuple[int, int]] = [
            (int(x), int(y)) for x, y in json.loads(roi)
        ]

        # determine dst points
        dstpoints, roiwidth, roiheight = find_closest_rectangle(
            *srcpoints, ratio=roadheight / roadwidth
        )

        # get csv(input) metadata
        track_metadata = self._output_repo.get_by_name(trackdata).metadata

        # determine output metadata
        metadata = {
            "trackdata": trackdata,
            "srcpoints": json.dumps(srcpoints),
            "dstpoints": json.dumps(dstpoints),
            "roadwidth": str(roadwidth),
            "roadheight": str(roadheight),
            "fps": track_metadata.get("fps", "30"),
            "targetname": track_metadata.get("targetname", "N/A"),
            "confidence": track_metadata.get("confidence", "N/A"),
            "cctv": track_metadata.get("cctv", "N/A"),
            "startat": track_metadata.get("startat", "N/A"),
            "endat": track_metadata.get("endat", "N/A"),
        }

        task = TaskItem(
            id=str(uuid4()),
            name=self.get_name(),
            params=metadata,
            state=TaskState.STARTED,
            reason="준비가 완료되어 차량 추적 데이터 분석을 시작합니다.",
            progress=0.0,
        )
        self._task_repo.add(task)

        def task_func():
            nonlocal task
            nonlocal srcpoints, dstpoints, trackdata
            nonlocal roiwidth, roiheight, roadwidth, roadheight

            try:
                # calculate perspective transform matrix
                matrix = cv2.getPerspectiveTransform(
                    np.array(srcpoints, dtype=np.float32),
                    np.array(dstpoints, dtype=np.float32),
                )

                # read tracking data
                df = pd.read_csv(os.path.join(self._outputs_path, trackdata))

                # perspective transform tracking data
                df["_src"] = list(zip(df["x"], df["y"]))
                df["_dst"] = df["_src"].apply(
                    lambda p: cv2.perspectiveTransform(
                        np.array([[p]], dtype=np.float32), matrix
                    )[0][0]
                )
                df["perspx"] = df["_dst"].apply(lambda p: p[0])
                df["perspy"] = df["_dst"].apply(lambda p: p[1])
                df = df.drop(columns=["_src", "_dst"])

                # filter out of range data(roi)
                df = df[(df["perspx"] >= 0) & (df["perspx"] < roiwidth)]
                df = df[(df["perspy"] >= 0) & (df["perspy"] < roiheight)]

                # interpolate missing data
                df = interpolate_persp_data(df)

                # sort by objid, frame
                df = df.sort_values(by=["objid", "frame"], ascending=[True, True])

                # calculate speed
                delta_frame = 5
                fps = int(task.params["fps"])
                delta_time = delta_frame / fps  # sec
                meter_per_pixel = roadheight / roiheight  # meter/pixel
                for objid in df["objid"].unique():
                    spds: pd.Series = df[df["objid"] == objid]["perspy"]
                    spds = spds.diff(
                        periods=delta_frame
                    )  # it assume that data is sorted by frame
                    spds = (spds * (meter_per_pixel / delta_time)) * 3.6  # km/h
                    df.loc[df["objid"] == objid, "speed"] = spds

                # save result
                result_csv_path = os.path.join(self._outputs_path, f"{task.id}.csv")
                df.to_csv(result_csv_path, index=False)
                self._output_repo.save(
                    TaskOutput(
                        name=f"{task.id}.csv",
                        type="text/csv",
                        desc=f"{task.params['cctv']} 객체 추적 데이터 분석 결과",
                        taskid=task.id,
                        metadata=task.params,
                    )
                )

                task.progress = 0.5  # 50%

                # save perspective video
                cap = cv2.VideoCapture(
                    os.path.join(self._outputs_path, task.params["targetname"])
                )
                cap_size = (roiwidth, roiheight)
                fourcc = cv2.VideoWriter.fourcc(*"mp4v")
                cap_out = cv2.VideoWriter(
                    os.path.join(self._outputs_path, f"{task.id}.mp4"),
                    fourcc,
                    fps,
                    cap_size,
                )

                trail_history = {}
                frame_idx = 0
                while cap.isOpened():
                    ret, frame = cap.read()
                    if ret == False:
                        break

                    # points
                    frame_points = df[df["frame"] == frame_idx]
                    identities = frame_points["objid"].values

                    # remove tracked point from buffer if object is lost
                    for key in list(trail_history.keys()):
                        if key not in identities:
                            trail_history.pop(key)

                    # perspective transform
                    persp = cv2.warpPerspective(frame, matrix, cap_size)

                    # draw trails
                    for _, _row in frame_points.iterrows():
                        _id = _row["objid"]
                        _perspx = int(_row["perspx"])
                        _perspy = int(_row["perspy"])

                        trail: list = trail_history.get(_id, [])
                        trail.append((_perspx, _perspy))
                        trail_history[_id] = trail

                        # draw trail
                        for i in range(1, len(trail)):
                            cv2.line(persp, trail[i - 1], trail[i], (0, 255, 0), 1)

                    cap_out.write(persp)
                    frame_idx += 1

                cap.release()
                cap_out.release()
                self._output_repo.save(
                    TaskOutput(
                        name=f"{task.id}.mp4",
                        type="video/mp4",
                        desc=f"{task.params['cctv']} 항공뷰 객체 추적 영상",
                        taskid=task.id,
                        metadata=task.params,
                    )
                )

                self._task_repo.update(
                    task.id, TaskState.FINISHED, "분석이 완료되었습니다."
                )

            except Exception as e:
                self._task_repo.update(
                    task.id, TaskState.FAILED, traceback.format_exc()
                )

        threading.Thread(target=task_func).start()
        return task

    def stop(self, id: str):
        pass
