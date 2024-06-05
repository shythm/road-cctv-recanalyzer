from cctv_recanalyzer.core.srv import CCTVRecorderSrv
from cctv_recanalyzer.core.repo import CCTVRecordRepo, CCTVStreamRepo
from cctv_recanalyzer.core.model import CCTVStream, CCTVRecord, CCTVRecordState

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

class CCTVRecorderFFmpeg(CCTVRecorderSrv):
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

        # 스케줄링을 위한 쓰레드를 생성한다.
        self._thread = threading.Thread(target=self._schedule)
        self._thread.start()

        # output_path 디렉토리가 존재하지 않는 경우 생성한다.
        if not os.path.exists(output_path):
            os.makedirs(output_path)

    def _ffmpeg_call(self, hls: str, output_path: str) -> subprocess.Popen:
        """
        ffmpeg으로 HLS 녹화를 진행하는 프로세스를 호출한다.
        `ffmpeg -i <HLS_URL> -c copy <OUTPUT_PATH>` 형태의 명령어를 실행한다.
        stdout, stderr는 PIPE로 처리하지 않고, 프로세스를 반환한다.

        [문제점, 이성호, 2024-06-05]
        30초 녹화를 진행했을 때 40초 가량 녹화된다.
        (1) ffmpeg 프로세스가 종료되지 않고 계속해서 녹화를 진행하는 문제가 발생한다.
        (2) hls 특성 상 미리 받아온 선행 영상이 포함되어서 그렇다.
        ffmpeg에서 정해진 시간 동안만 녹화를 진행할 수 있는 방법을 고민해본다.
        """
        return subprocess.Popen(
            [self.FFMPEG_BIN, '-i', hls, '-c', 'copy', output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def _start(self, job: CCTVRecordFFmpeg):
        """
        CCTV 녹화 작업을 시작한다.
        """
        cctv = self._stream_repo.find_by_id(job.cctvid)

        job.startat = datetime.now() # 녹화 시작 시간 기록
        job.ffmpeg = self._ffmpeg_call(cctv.hls, job.path) # ffmpeg 호출
        job.state = CCTVRecordState.STARTED # 녹화 상태 변경

    def _stop(self, job: CCTVRecordFFmpeg):
        """
        CCTV 녹화 작업을 중지한다.
        """
        job.ffmpeg.send_signal(signal.SIGQUIT) # ffmpeg 프로세스에 종료 시그널 전송
        job.endat = datetime.now() # 녹화 종료 시간 기록
        job.state = CCTVRecordState.FINISHED # 녹화 상태 변경

        # jobs 배열에서 녹화 작업을 제거한다.
        self._jobs.remove(job)

        # 녹화 작업을 레포지토리에 저장한다.
        self._record_repo.insert(job)

    def _schedule(self):
        """
        일정 시간 간격으로 녹화 작업을 스케줄링한다.
        녹화 시작 시간이 되면 녹화 작업을 시작하며, 녹화 종료 시간이 되면 녹화 작업을 종료한다.
        """
        while (True):
            # jobs를 순회하며 녹화 작업을 진행한다.
            for job in self._jobs:
                # 녹화 시작 시간이 되면 녹화 작업을 시작한다.
                if job.state == CCTVRecordState.PENDING and job.startat <= datetime.now():
                    self._start(job)
                    continue

                # 녹화 종료 시간이 되면 녹화 작업을 종료한다.
                if job.state == CCTVRecordState.STARTED and job.endat <= datetime.now():
                    self._stop(job)
                    continue

            time.sleep(self.SCHEDULE_INTERVAL)

    def get_all(self) -> List[CCTVRecord]:
        """
        완료된 녹화 작업은 repo에서 가져오고, 진행 중인 녹화 작업은 jobs에서 가져온다.
        """
        recorded_jobs = self._record_repo.find_all()
        jobs = self._jobs # copy를 하지 않고 직접 jobs를 반환하면, jobs에 대한 참조를 반환하게 된다.
        return jobs + recorded_jobs

    def submit(self, cctv: CCTVStream, start_time: datetime, end_time: datetime) -> CCTVRecord:
        """
        녹화 작업을 생성하고, job 스케줄러에 추가한다.
        """
        new_id = str(uuid.uuid4())
        job = CCTVRecordFFmpeg(
            id=new_id,
            cctvid=cctv.id,
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
        """
        녹화 작업을 취소하고, jobs에서 제거한다.
        """
        job = next((job for job in self._jobs if job.id == id), None)
        if job is not None:
            self._jobs.remove(job)

    def remove(self, id: str):
        """
        녹화 작업을 삭제하고, repo에서 제거한다.
        """
        self.cancel(id)
        self._record_repo.delete(id)

if __name__ == '__main__':
    from cctv_recanalyzer.core.model import CCTVStream
    from cctv_recanalyzer.repo.cctvstream_its_db import CCTVStreamITSDBRepo
    from cctv_recanalyzer.repo.cctvrecord_db import CCTVRecordDBRepo

    stream_repo = CCTVStreamITSDBRepo("test.db", "0bae84b50c704db19bac22df144c21b4")
    record_repo = CCTVRecordDBRepo("test.db")

    cctv = stream_repo.create("[서해안선] 서평택", (126.868976, 36.997973))
    stream_repo.insert(cctv)

    recorder = CCTVRecorderFFmpeg(stream_repo, record_repo, './output')
    
    print(recorder.get_all())
    time.sleep(1)

    record = recorder.submit(cctv, datetime.now(), datetime.now() + timedelta(seconds=30))
    print(record)
    time.sleep(1)

    started_time = time.time()
    while (record.state != CCTVRecordState.FINISHED):
        print(record.state, time.time() - started_time)
        time.sleep(1)

    """
    [이성호, 2024-06-05]
    sqlite3에 스레딩 관련 설정을 해주었지만 여전히 
    sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.
    에러가 발생한다.
    이를 해결해야 할 것 같다.
    """

    print(recorder.get_all())
