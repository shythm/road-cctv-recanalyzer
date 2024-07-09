from core.srv import CCTVRecorder
from core.repo import CCTVRecordRepo, CCTVStreamRepo
from core.model import CCTVRecord, CCTVRecordState

from dataclasses import dataclass
from datetime import datetime
from typing import List
import time
import subprocess
import threading
import signal
import uuid
import os

@dataclass
class CCTVRecordFFmpeg(CCTVRecord):
    ffmpeg: subprocess.Popen = None
    stdout = None
    stderr = None

class CCTVRecorderFFmpeg(CCTVRecorder):
    """
    ffmpeg 유틸리티를 이용하여 CCTV 영상을 녹화하는 서비스를 제공한다.
    """

    FFMPEG_BIN = 'ffmpeg'
    SCHEDULE_INTERVAL = 1
    
    def __init__(self,
                 stream_repo: CCTVStreamRepo, record_repo: CCTVRecordRepo,
                 output_path: str, logging_path: str=None):
        
        self._stream_repo = stream_repo
        self._record_repo = record_repo
        self._output_path = output_path # 녹화 파일을 저장할 경로
        self._logging_path = logging_path # 로그 파일을 저장할 경로(없으면 로그 파일을 저장하지 않는다.)

        self._jobs: List[CCTVRecordFFmpeg] = [] # 녹화 중인 작업을 저장하는 리스트
        self._cancel_req: List[CCTVRecordFFmpeg] = [] # 녹화 취소 요청을 저장하는 리스트
        self._running = True

        # output_path 디렉토리가 존재하지 않는 경우 생성한다.
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # logging_path 디렉토리가 존재하지 않는 경우 생성한다.
        if logging_path and not os.path.exists(logging_path):
            os.makedirs(logging_path)

    def start(self):
        self._thread = threading.Thread(target=self._schedule)
        self._thread.start()

    def stop(self):
        self._running = False
        self._thread.join()

    def _close_job(self, job: CCTVRecordFFmpeg):
        if job.stdout:
            job.stdout.close()
            job.stdout = None
        if job.stderr:
            job.stderr.close()
            job.stderr = None

    def _schedule(self):
        """
        일정 시간 간격으로 녹화 작업을 스케줄링한다.
        녹화 시작 시간이 되면 녹화 작업을 시작하며, 녹화 종료 시간이 되면 녹화 작업을 종료한다.
        """
        while (self._running):
            try:
                for job in self._jobs:

                    if job.state == CCTVRecordState.PENDING:
                        """
                        PENDING -> STARTED
                        조건: 녹화 시작 시각 <= 현재 시각
                        행위: ffmpeg을 이용하여 CCTV 녹화 작업을 시작한다.
                        """
                        if job.startat <= datetime.now():
                            cctv = self._stream_repo.find_by_id(job.cctvid)
                            seconds = (job.endat - job.startat).seconds
                            job.startat = datetime.now()
                            if self._logging_path:
                                job.stdout = open(os.path.join(self._logging_path, f'{job.id}.out'), 'w')
                                job.stderr = open(os.path.join(self._logging_path, f'{job.id}.err'), 'w')

                            # call ffmpeg: ffmpeg -i <HLS_URL> -c copy -t <DURATION> <OUTPUT_PATH>
                            job.ffmpeg = subprocess.Popen(
                                [self.FFMPEG_BIN, '-i', cctv.hls, '-c', 'copy', '-t', str(seconds), job.path],
                                stdout=job.stdout if job.stdout else subprocess.DEVNULL,
                                stderr=job.stderr if job.stderr else subprocess.DEVNULL,
                                stdin=subprocess.DEVNULL,
                            )
                            job.state = CCTVRecordState.STARTED

                    elif job.state == CCTVRecordState.STARTED:
                        # progress 갱신
                        job.progress = (datetime.now() - job.startat).seconds / (job.endat - job.startat).seconds
                        job.progress = min(1.0, job.progress)

                        if job in self._cancel_req:
                            """
                            STARTED -> CANCELING
                            조건: 녹화 취소 요청이 들어온 경우
                            행위: ffmpeg 프로세스에 SIGINT 시그널을 보내 녹화를 취소한다.
                            """
                            job.ffmpeg.send_signal(signal.SIGINT)
                            job.endat = datetime.now()
                            job.state = CCTVRecordState.CANCELING

                        elif job.endat <= datetime.now():
                            """
                            STARTED -> FINISHING
                            조건: 녹화 종료 시각 <= 현재 시각
                            행위: ffmpeg 프로세스에 SIGTERM 시그널을 보내 녹화를 종료한다.
                            """
                            job.ffmpeg.send_signal(signal.SIGTERM)
                            job.endat = datetime.now()
                            job.state = CCTVRecordState.FINISHING

                        elif job.ffmpeg.poll() is not None:
                            """
                            STARTED -> FAILED, FINISHED
                            조건: ffmpeg 프로세스가 위의 조건에 해당하지 않고 종료된 경우
                            행위: 리턴값을 확인하여 녹화 상태를 갱신한다.
                            """
                            if job.ffmpeg.returncode != 0:
                                job.state = CCTVRecordState.FAILED
                            else:
                                job.state = CCTVRecordState.FINISHED

                    elif job.state == CCTVRecordState.CANCELING:
                        """
                        CANCLEING -> CANCELED
                        조건: ffmpeg이 종료된 경우
                        행위: 녹화 파일을 제거한다.
                        """
                        if job.ffmpeg.poll():
                            if os.path.exists(job.path):
                                os.remove(job.path)
                            self._cancel_req.remove(job)
                            job.state = CCTVRecordState.CANCELED

                    elif job.state == CCTVRecordState.FINISHING:
                        """
                        FINISHING -> FINISHED
                        조건: ffmpeg이 종료된 경우
                        """
                        if job.ffmpeg.poll():
                            self._record_repo.insert(job)
                            self._jobs.remove(job)
                            job.state = CCTVRecordState.FINISHED

                    elif job.state == CCTVRecordState.CANCELED:
                        self._close_job(job)

                    elif job.state == CCTVRecordState.FINISHED:
                        self._close_job(job)

                    elif job.state == CCTVRecordState.FAILED:
                        self._close_job(job)

            except Exception as e:
                print(e)

            time.sleep(self.SCHEDULE_INTERVAL)

        # self._running이 False가 되면 스케줄링을 종료한다. 그리고 ffmpeg 프로세스들도 종료한다.
        for job in self._jobs:
            if job.ffmpeg:
                job.ffmpeg.send_signal(signal.SIGTERM)
        
        print("Waiting for all ffmpeg processes to finish...")
        for job in self._jobs:
            if job.ffmpeg:
                job.ffmpeg.wait()
                if os.path.exists(job.path):
                    os.remove(job.path)
            self._close_job(job)

    def get_all(self) -> List[CCTVRecord]:
        return self._jobs

    def submit(self, cctvid: str, start_time: datetime, end_time: datetime) -> CCTVRecord:
        if end_time <= start_time or end_time <= datetime.now():
            raise Exception("녹화 시간 설정이 잘못되었습니다.")

        new_id = str(uuid.uuid4())
        job = CCTVRecordFFmpeg(
            id=new_id,
            cctvid=cctvid,
            reqat=datetime.now(),
            startat=start_time,
            endat=end_time,
            path=os.path.join(self._output_path, f'{new_id}.mp4'),
            state=CCTVRecordState.PENDING,
            progress=0.0
        )

        self._jobs.append(job)
        return job

    def cancel(self, id: str):
        job = next((job for job in self._jobs if job.id == id), None)
        if job is None:
            raise Exception(f"{id} 작업을 찾을 수 없습니다.")

        job.state = CCTVRecordState.CANCELED

    def remove(self, id: str):
        job = next((job for job in self._jobs if job.id == id), None)
        if job is None:
            raise Exception(f"{id} 작업을 찾을 수 없습니다.")
        if job.state != CCTVRecordState.CANCELED:
            raise Exception(f"{id} 작업이 취소되지 않았기에 삭제할 수 없습니다. 현재 상태: {job.state}")
        
        self._jobs.remove(job)

    def stop(self):
        self._running = False
        self._thread.join()
