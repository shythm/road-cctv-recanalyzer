from cctv_recanalyzer.core.srv import CCTVRecordJobSrv
from cctv_recanalyzer.core.repo import CCTVRecordRepo, CCTVStreamRepo
from cctv_recanalyzer.core.model import CCTVRecord, CCTVRecordState

from dataclasses import dataclass
from datetime import datetime, timedelta
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

class CCTVRecorderFFmpeg(CCTVRecordJobSrv):
    """
    ffmpeg 유틸리티를 이용하여 CCTV 영상을 녹화하는 서비스를 제공한다.
    """

    FFMPEG_BIN = 'ffmpeg'
    SCHEDULE_INTERVAL = 1
    
    def __init__(self, stream_repo: CCTVStreamRepo, record_repo: CCTVRecordRepo, output_path: str):
        self._stream_repo = stream_repo
        self._record_repo = record_repo
        self._output_path = output_path # 녹화 파일을 저장할 경로

        self._jobs: List[CCTVRecordFFmpeg] = [] # 녹화 중인 작업을 저장하는 리스트
        self._running = True

        # 스케줄링을 위한 쓰레드를 생성한다.
        self._thread = threading.Thread(target=self._schedule)
        self._thread.start()

        # output_path 디렉토리가 존재하지 않는 경우 생성한다.
        if not os.path.exists(output_path):
            os.makedirs(output_path)

    def _ffmpeg_call(self, hls: str, output_path: str, seconds: int) -> subprocess.Popen:
        """
        ffmpeg으로 HLS 녹화를 진행하는 프로세스를 호출한다.
        `ffmpeg -i <HLS_URL> -c copy -t <DURATION> <OUTPUT_PATH>` 형태의 명령어를 실행한다.
        stdout, stderr는 PIPE로 처리하지 않고, 프로세스를 반환한다.

        [문제점, 이성호, 2024-06-05]
        30초 녹화를 진행했을 때 40초 가량 녹화된다. 그 원인을 추정해보면 다음과 같다.
        (1) ffmpeg 프로세스가 종료되지 않고 계속해서 녹화를 진행하는 문제가 발생한다.
        (2) hls 특성 상 미리 받아온 선행 영상이 포함되어서 그렇다.
        ffmpeg에서 정해진 시간 동안만 녹화를 진행할 수 있도록 -t 옵션을 추가하여 해결한다.
        """
        return subprocess.Popen(
            [self.FFMPEG_BIN, '-i', hls, '-c', 'copy', '-t', str(seconds), output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def _start_record(self, job: CCTVRecordFFmpeg):
        """
        ffmpeg을 이용하여 CCTV 녹화 작업을 시작한다.
        """
        if job.state != CCTVRecordState.PENDING:
            raise Exception(f"CCTV 녹화 시작은 PENDING 상태에서만 가능합니다. 현재 상태: {job.state}")
        
        cctv = self._stream_repo.find_by_id(job.cctvid)
        seconds = (job.endat - job.startat).seconds

        job.startat = datetime.now() # 녹화 시작 시간 기록
        job.ffmpeg = self._ffmpeg_call(cctv.hls, job.path, seconds) # ffmpeg 호출
        job.state = CCTVRecordState.STARTED # 녹화 상태 변경

    def _end_record(self, job: CCTVRecordFFmpeg):
        """
        ffmpeg에 종료 시그널을 보내 CCTV 녹화 작업을 중지한다.
        """
        if job.state != CCTVRecordState.STARTED:
            raise Exception(f"CCTV 녹화 중지는 STARTED 상태에서만 가능합니다. 현재 상태: {job.state}")
        
        job.ffmpeg.send_signal(signal.SIGQUIT) # ffmpeg 프로세스에 종료 시그널 전송
        job.endat = datetime.now() # 녹화 종료 시간 기록
        job.state = CCTVRecordState.FINISHED # 녹화 상태 변경

    def _cancel_record(self, job: CCTVRecordFFmpeg):
        """
        CCTV 녹화 작업을 취소한다.
        """
        if job.state != CCTVRecordState.CANCELING:
            raise Exception(f"CCTV 녹화 취소는 CANCELING 상태에서만 가능합니다. 현재 상태: {job.state}")

        if job.ffmpeg:
            if job.ffmpeg.poll() is None:
                # ffmpeg 프로세스가 종료되지 않은 경우, 종료 시그널을 전송한다.
                job.ffmpeg.send_signal(signal.SIGINT)
            else:
                # ffmpeg 프로세스가 종료된 경우, 녹화 파일을 삭제한다.
                if os.path.exists(job.path):
                    os.remove(job.path)
                job.state = CCTVRecordState.CANCELED
        else:
            job.state = CCTVRecordState.CANCELED

    def _schedule(self):
        """
        일정 시간 간격으로 녹화 작업을 스케줄링한다.
        녹화 시작 시간이 되면 녹화 작업을 시작하며, 녹화 종료 시간이 되면 녹화 작업을 종료한다.
        """
        while (self._running):
            # jobs를 순회하며 녹화 작업을 진행한다.
            for job in self._jobs:

                # 녹화 시작 시간이 되면 녹화 작업을 시작한다.
                if job.state == CCTVRecordState.PENDING and job.startat <= datetime.now():
                    self._start_record(job)
                    continue

                # 녹화 종료 시간이 되면 녹화 작업을 종료한다.
                if job.state == CCTVRecordState.STARTED and job.endat <= datetime.now():
                    self._end_record(job)
                    continue

                # 녹화 취소 시그널이 발생한 경우, 녹화 작업을 취소한다.
                if job.state == CCTVRecordState.CANCELING:
                    self._cancel_record(job)
                    continue

                # 녹화 작업이 완료된 경우, 레포지토리에 저장한다.
                if job.state == CCTVRecordState.FINISHED:
                    self._record_repo.insert(job)
                    self._jobs.remove(job)
                    continue

            time.sleep(self.SCHEDULE_INTERVAL)

    def get_all(self) -> List[CCTVRecord]:
        return self._jobs # copy를 하지 않고 직접 jobs를 반환하면, jobs에 대한 참조를 반환하게 된다.

    def submit(self, cctvid: str, start_time: datetime, end_time: datetime) -> CCTVRecord:
        new_id = str(uuid.uuid4())
        job = CCTVRecordFFmpeg(
            id=new_id,
            cctvid=cctvid,
            reqat=datetime.now(),
            startat=start_time,
            endat=end_time,
            state=CCTVRecordState.PENDING,
            path=os.path.join(self._output_path, f'{new_id}.mp4'),
            srcid=None
        )

        self._jobs.append(job)
        return job

    def cancel(self, id: str):
        job = next((job for job in self._jobs if job.id == id), None)
        if job is None:
            raise Exception(f"Job with id {id} not found")

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
