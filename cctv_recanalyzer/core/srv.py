from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from cctv_recanalyzer.core.model import CCTVRecord

class CCTVRecorder(ABC):

    """
    CCTV 관련 녹화/처리 작업을 관리하는 서비스를 정의한다.
    - 내부적으로 스케줄링을 진행할 수도 있고 그렇지 않을 수도 있다.
    - CCTVRecord 모델을 이용하여 상태 관리를 진행한다.
    - FINISHED 상태의 CCTVRecord는 특정한 레포지토리에 저장되어야 한다.
    - 그 외의 상태에 대해서는 메모리 상에서 관리할 수 있도록 한다.
    """
    
    @abstractmethod
    def start(self):
        """
        CCTVRecord 스케줄링 작업을 시작한다.
        """
        pass

    @abstractmethod
    def stop(self):
        """
        CCTVRecord 스케줄링 작업을 중지한다.
        """
        pass

    @abstractmethod
    def get_all(self) -> List[CCTVRecord]:
        """
        제출된 CCTVRecord 목록을 반환한다.
        """
        pass

    @abstractmethod
    def submit(self, cctvid: str, start_time: datetime, end_time: datetime) -> CCTVRecord:
        """
        CCTVRecord 작업을 제출한다.
        """
        pass

    @abstractmethod
    def cancel(self, id: str):
        """
        CCTVRecord 작업을 취소한다.
        """
        pass

    @abstractmethod
    def remove(self, id: str):
        """
        CCTVRecord 작업을 삭제한다.
        """
        pass

    @abstractmethod
    def stop(self):
        """
        CCTVRecord 스케줄링 작업을 중지한다.
        """
        pass