from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from cctvrecorder.core.model import CCTVStream, CCTVRecord

class CCTVRecorderSrv(ABC):

    """
    CCTV Stream으로부터 영상 주소를 받아와 기억 장치에 저장하는 기능을 제공한다.
    내부적으로 스케줄링을 진행하고, 스트리밍에 대한 상태 관리를 한다.
    CCTVStream 정보를 가져오는데 있어서는 CCTVStreamReop를 사용,
    파일을 저장하는데 있어서는 CCTVRecordRepo를 사용한다.
    """
    
    @abstractmethod
    def get_all(self) -> List[CCTVRecord]:
        """
        CCTV 녹화 상태를 반환한다.
        """
        pass

    @abstractmethod
    def submit(self, cctv: CCTVStream, start_time: datetime, end_time: datetime) -> CCTVRecord:
        """
        CCTV 녹화를 요청한다.
        """
        pass

    @abstractmethod
    def cancel(self, id: str):
        """
        CCTV 녹화를 취소한다.
        """
        pass

    @abstractmethod
    def remove(self, id: str):
        """
        CCTV 녹화를 삭제한다.
        """
        pass