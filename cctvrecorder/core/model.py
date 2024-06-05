from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# CCTV 정보를 담는 데이터 클래스
# 고유한 CCTV ID를 정의하고, 이에 따른 CCTV 이름, HLS 주소, 좌표 등을 저장한다.
@dataclass
class CCTVStream:
    id: str
    name: str
    coord: tuple[float, float]
    hls: str = field(repr=False, default=None)
    avail: bool = field(repr=False, default=True)

    """
    <왜 모델을 만드는가?, 이성호, 20240528>
    CCTVStream 클래스는 누가 인스턴스화 하는가? 아마 CCTVStreamRepo 레포지토리 클래스를 만들어
    CCTVStream의 인스턴스를 생성하는 식으로 코드를 작성할 수 있을 것이다.
        레포지토리 레이어(클래스)를 두는 이유:
        1. DB(저장소)와 연동 후 데이터를 가져오거나 저장하는 로직을 분리
        2. DB(저장소)에 있는 내용이 우리가 원하는 형태의 데이터가 아닐 경우, 이를 가공하는 작업을 분리
    그렇다면 레포지토리 레이어에서 생성한 데이터의 구체적인 형태가 필요한데, 이를 위해 해당 데이터 클래스를 정의해야 할 것이다.

    그러나 꼭 이래야만 하는가?
    CCTVStream 클래스를 구체화하여 가져올 수 있는 방법은 없을까?
    CCTVStream 클래스의 static 메서드로 get_all 등과 같은 DB 레이어와 통신하는 메서드를 정의하고,
    각 인스턴스를 통해 update, delete 등의 연산을 수행할 수 있지 않을까?

    물론 그렇게 해도 좋겠지만, 이는 객체지향 프로그래밍의 원칙에 어긋나 보인다.
    바로 SRP(Single Responsibility Principle)을 위반하는 것이다.
    이에 모델과 레포지토리를 분리하여, 각각의 역할에 집중하도록 하는 것이 좋아 보인다.
    """

    def __eq__(self, other):
        return self.id == other.id


# CCTVRecord의 상태를 정의하는 열거형
class CCTVRecordState(Enum):
    PENDING = 1     # 녹화의 시작을 기다리는 상태
    STARTED = 2     # 녹화가 시작된 상태
    CANCELD = 3     # 녹화가 사용자에 의해 취소된 상태
    FINISHED = 4    # 녹화가 완료된 상태
    UNKNOWN = 5     # 알 수 없는 오류로 녹화 상태를 알 수 없을 때


# CCTV 녹화 정보를 담는 데이터 클래스
# 녹화된 CCTV 영상의 위치, 녹화 시작/종료 시간 등을 저장한다.
@dataclass
class CCTVRecord:
    id: str
    cctvid: str
    reqat: datetime
    startat: datetime
    endat: datetime
    state: CCTVRecordState
    path: str
    srcid: str

    def __eq__(self, other):
        return all([
            self.id == other.id,
            self.cctvid == other.cctvid,
            self.reqat.replace(microsecond=0) == other.reqat.replace(microsecond=0),
            self.startat.replace(microsecond=0) == other.startat.replace(microsecond=0),
            self.endat.replace(microsecond=0) == other.endat.replace(microsecond=0),
            self.state == other.state,
            self.path == other.path,
            self.srcid == other.srcid
        ])
