from __future__ import annotations
from typing import List

from sqlite3 import connect, threadsafety as sqlite3_threadsafety
import requests
import uuid

from cctv_recanalyzer.core.model import CCTVStream
from cctv_recanalyzer.core.repo import CCTVStreamRepo

class CCTVStreamITSDBRepo(CCTVStreamRepo):

    DB_TABLE_NAME = "cctvstream"
    DELTA_COORD = 0.01
    DIST_EPSILON = 1e-6

    def __init__(self, dbpath: str, apikey: str):
        self._cctvs = []
        self._apikey = apikey
        self._db_table_name = self.DB_TABLE_NAME

        """
        [2024.06.07. sqlite3 스레드 관련 문제 발생, 이성호 작성]
        아래의 에러가 발생했다.
        sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.
        The object was created in thread id 139849893997440 and this is thread id 139849872635584.

        sqlite3를 사용하는데 있어 thread-safety를 확인해야 한다.
        https://docs.python.org/3.11/library/sqlite3.html#sqlite3.threadsafety
        위의 문서를 참고했을 때, sqlite3.threadsafety가 3이면 serialized 상태로,
        멀티 스레드 환경에서 sqlite3 module과 그 connection 또한 멀티스레딩 환경에서 안전하다고 설명한다.

        그리고 에러를 해결하기 위해 connect 메서드를 호출할 때 옵션을 주어야 하는데,
        https://docs.python.org/3/library/sqlite3.html#sqlite3.connect
        If False, the connection may be accessed in multiple threads;
        write operations may need to be serialized by the user to avoid data corruption.
        See threadsafety for more information.
        위의 내용을 참고하면, connect 메서드를 호출할 때 check_same_thread=False 옵션을 주어
        같은 커넥션을 서로 다른 스레드에서 사용할 수 있도록 이를 무시하도록 한다.
        """
        if sqlite3_threadsafety != 3:
            raise Exception("sqlite3 is not thread-safe (not serialized)")

        # sqlite3 DB 연결
        self._conn = connect(dbpath, check_same_thread=False)
        self._init_db()
    
    def _init_db(self):
        """
        아래의 스키마대로 테이블을 생성한다.
        id: UUID
        name: CCTV 이름
        coordx: CCTV 경도
        coordy: CCTV 위도
        avail: 해당 스트림 사용 가능 여부
        """

        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._db_table_name} (
                id TEXT PRIMARY KEY,
                name TEXT,
                coordx REAL,
                coordy REAL,
                avail INTEGER
            )
        """)
        self._conn.commit()

    def _fetch_its(self, x, y):
        """
        ITS 국가교통정보센터 API를 통해 CCTV 목록을 가져온다.
        x, y 좌표를 기준으로 일정(delta) 간격으로 API 요청을 하고, coord와 가장 가까운 CCTV를 찾는다.
        """
        
        # API 호출
        res = requests.get("https://openapi.its.go.kr:9443/cctvInfo", params={
            "apiKey": self._apikey,
            "type": "ex",
            "cctvType": 1,
            "minX": x - self.DELTA_COORD,
            "maxX": x + self.DELTA_COORD,
            "minY": y - self.DELTA_COORD,
            "maxY": y + self.DELTA_COORD,
            "getType": "json"
        })

        if res.status_code != 200:
            raise Exception("API 호출에 실패하였습니다.")

        """
        cctvtype    string  CCTV 유형(1: 실시간 스트리밍(HLS) / 2: 동영상 파일 / 3: 정지 영상)
        cctvurl     string  CCTV 영상 주소
        coordx      string  경도 좌표
        coordy      string  위도 좌표
        cctvformat  string  CCTV 형식
        cctvname    string  CCTV 설치 장소명
        """
        data = res.json()['response']['data']

        # 유클리드 거리를 이용하여 가장 가까운 CCTV를 찾는다.
        min_dist = float("inf")
        min_cctv = None
        for cctv in data:
            cctv_x, cctv_y = float(cctv['coordx']), float(cctv['coordy'])
            dist = (x - cctv_x) ** 2 + (y - cctv_y) ** 2
            if dist < min_dist:
                min_dist = dist
                min_cctv = cctv

        # 거리가 epsilon 이하인 CCTV가 없다면 None을 반환한다.
        if min_dist > self.DIST_EPSILON:
            return None

        return min_cctv

    class CCTVStreamITS(CCTVStream):
        """
        CCTVStream dataclass 클래스를 상속받아 ITS 국가교통정보센터의 CCTV HLS 주소를
        동적으로 가져올 수 있도록 hls 프로퍼티를 재정의한다.
        """

        def __init__(self, repo: CCTVStreamITSDBRepo, *args, **kwargs):
            self._repo = repo
            super().__init__(hls=None, *args, **kwargs)

        @property
        def hls(self) -> str:
            return self._repo._fetch_its(self.coord[0], self.coord[1])['cctvurl']
        
        @hls.setter
        def hls(self, value: str):
            pass

    def create(self, name: str, coord: tuple[float, float]) -> CCTVStream:
        """
        ITS 국가교통정보센터에서는 각 CCTV에 대한 ID 값을 제공하지 않는다.
        그리고 ID를 다른 플랫폼에 의존하는 것은 좋지 않기에,
        UUID를 통해 우리가 직접 ID를 부여하도록 한다.
        """

        return self.CCTVStreamITS(
            repo=self,
            id=str(uuid.uuid4()),
            name=name,
            coord=coord,
            avail=True
        )

    def insert(self, cctv: CCTVStream) -> CCTVStream:
        id = cctv.id
        name = cctv.name
        coordx, coordy = cctv.coord
        avail = 1 if cctv.avail else 0

        self._conn.execute(f"""
            INSERT INTO {self._db_table_name} (id, name, coordx, coordy, avail)
            VALUES (?, ?, ?, ?, ?)
        """, (id, name, coordx, coordy, avail))

        self._conn.commit()
        return cctv

    def update(self, cctv: CCTVStream) -> CCTVStream:
        id = cctv.id
        name = cctv.name
        coordx, coordy = cctv.coord
        avail = 1 if cctv.avail else 0

        cur = self._conn.execute(f"""
            UPDATE {self._db_table_name}
            SET name = ?, coordx = ?, coordy = ?, avail = ?
            WHERE id = ?
        """, (name, coordx, coordy, avail, id))

        # 수정된 데이터가 없는 경우
        if cur.rowcount == 0:
            raise Exception(f"'{id}'에 해당하는 CCTV가 존재하지 않습니다.")
        
        self._conn.commit()

    def delete(self, id: str) -> None:
        cur = self._conn.execute(f"""
            DELETE FROM {self._db_table_name}
            WHERE id = ?
        """, (id,))

        # 삭제된 데이터가 없는 경우
        if cur.rowcount == 0:
            raise Exception(f"'{id}'에 해당하는 CCTV가 존재하지 않습니다.")

        self._conn.commit()

    def find_all(self) -> List[CCTVStream]:
        cur = self._conn.execute(f"""
            SELECT id, name, coordx, coordy, avail
            FROM {self._db_table_name}
        """)

        return [self.CCTVStreamITS(
            self,
            id=row[0],
            name=row[1],
            coord=(row[2], row[3]),
            avail=bool(row[4])
        ) for row in cur.fetchall()]

    def find_by_id(self, id: str) -> CCTVStream:
        cur = self._conn.execute(f"""
            SELECT id, name, coordx, coordy, avail
            FROM {self._db_table_name}
            WHERE id = ?
        """, (id,))
        
        row = cur.fetchone()
        if row is None:
            raise Exception(f"'{id}'에 해당하는 CCTV가 존재하지 않습니다.")
        
        return self.CCTVStreamITS(
            self,
            id=row[0],
            name=row[1],
            coord=(row[2], row[3]),
            avail=bool(row[4])
        )

