from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# CCTV 정보를 담는 데이터 클래스
# 고유한 CCTV ID를 정의하고, 이에 따른 CCTV 이름, HLS 주소, 좌표 등을 저장한다.
@dataclass
class CCTVStream:
    id: str
    name: str
    coord: tuple[float, float]
    avail: bool


@dataclass
class CCTVRecordBase:
    """
    DB에 저장되는 CCTV 녹화(또는 영상처리) 정보를 담는 데이터 클래스
    """
    id: str
    cctvid: str
    reqat: datetime
    startat: datetime
    endat: datetime
    path: str
    custom: str # CCTVRecorder Specific

    def __eq__(self, other) -> bool:
        return self.id == other.id


class CCTVRecordState(Enum):
    """
    CCTV 녹화(또는 영상처리) 상태를 정의하는 열거형
    """
    PENDING = 0     # 녹화의 시작을 기다리는 상태
    STARTED = 10    # 녹화가 시작된 상태
    CANCELING = 20  # 녹화가 취소되는 중인 상태
    CANCELED = 21   # 녹화가 사용자에 의해 취소된 상태
    FINISHING = 30  # 녹화가 완료되는 중인 상태
    FINISHED = 31   # 녹화가 완료된 상태
    FAILED = 40     # 녹화가 실패한 상태
    UNKNOWN = 99    # 알 수 없는 오류로 녹화 상태를 알 수 없을 때

@dataclass
class CCTVRecord(CCTVRecordBase):
    """
    CCTV 녹화(또는 영상처리) 정보를 담는 데이터 클래스
    녹화(또는 영상처리)된 CCTV 영상의 위치, 녹화 시작/종료 시간 등을 저장한다.
    """
    state: CCTVRecordState
    progress: float
