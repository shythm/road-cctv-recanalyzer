from cctv_recanalyzer.core.repo import CCTVRecordRepo
from cctv_recanalyzer.core.model import CCTVRecord, CCTVRecordState

from sqlite3 import connect, threadsafety as sqlite3_threadsafety
from typing import List
from datetime import datetime

class CCTVRecordDBRepo(CCTVRecordRepo):

    DB_TABLE_NAME = "cctvrecord"

    def __init__(self, dbpath: str):

        # sqlite3 connection thread-safe checking
        # see https://docs.python.org/3.11/library/sqlite3.html#sqlite3.threadsafety
        # multi-threading 환경에서의 connection 관련 내용은 cctvstream_its_db.py 참고
        if sqlite3_threadsafety != 3:
            raise Exception("sqlite3 is not thread-safe (not serialized)")

        # sqlite3 DB 연결
        self._conn = connect(dbpath, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        """
        아래의 스키마대로 테이블을 생성한다.
        id: UUID
        cctvid: CCTVStream 모델의 id
        reqat: 녹화 요청 시간
        startat: 녹화 시작 시간
        endat: 녹화 종료 시간
        path: 녹화 파일 경로
        state: 녹화 상태
        progress: 녹화 진행률
        """
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.DB_TABLE_NAME} (
                id TEXT PRIMARY KEY,
                cctvid TEXT,
                reqat TEXT,
                startat TEXT,
                endat TEXT,
                path TEXT,
                state INTEGER DEFAULT {CCTVRecordState.FINISHED.value},
                progress REAL DEFAULT 1.0
            )
        """)
        self._conn.commit()

    def _datetime_to_str(self, dt: datetime) -> str:
        # 국제 표준 포맷인 ISO 8601 형식으로 변환
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    
    def _str_to_datetime(self, dtstr: str) -> datetime:
        return datetime.strptime(dtstr, "%Y-%m-%dT%H:%M:%S")

    def find_all(self) -> List[CCTVRecord]:
        cur = self._conn.execute(f"""
            SELECT id, cctvid, reqat, startat, endat, path, state, progress
            FROM {self.DB_TABLE_NAME}                     
        """)

        return [CCTVRecord(
            id=row[0],
            cctvid=row[1],
            reqat=self._str_to_datetime(row[2]),
            startat=self._str_to_datetime(row[3]),
            endat=self._str_to_datetime(row[4]),
            path=row[5],
            state=CCTVRecordState(row[6]),
            progress=row[7]
        ) for row in cur.fetchall()]

    def find_by_id(self, id: str) -> CCTVRecord:
        cur = self._conn.execute(f"""
            SELECT id, cctvid, reqat, startat, endat, path, state, progress
            FROM {self.DB_TABLE_NAME}
            WHERE id = ?
        """, (id,))

        row = cur.fetchone()
        if row is None:
            return None
        
        return CCTVRecord(
            id=row[0],
            cctvid=row[1],
            reqat=self._str_to_datetime(row[2]),
            startat=self._str_to_datetime(row[3]),
            endat=self._str_to_datetime(row[4]),
            path=row[5],
            state=CCTVRecordState(row[6]),
            progress=row[7]
        )

    def insert(self, record: CCTVRecord) -> CCTVRecord:
        self._conn.execute(f"""
            INSERT INTO {self.DB_TABLE_NAME} (id, cctvid, reqat, startat, endat, path, state, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.id,
            record.cctvid,
            self._datetime_to_str(record.reqat),
            self._datetime_to_str(record.startat),
            self._datetime_to_str(record.endat),
            record.path,
            record.state.value,
            record.progress
        ))

        self._conn.commit()
        return record

    def update(self, record: CCTVRecord) -> CCTVRecord:
        cur = self._conn.execute(f"""
            UPDATE {self.DB_TABLE_NAME}
            SET cctvid = ?, reqat = ?, startat = ?, endat = ?, path = ?, state = ?, progress = ?
            WHERE id = ?
        """, (
            record.cctvid,
            self._datetime_to_str(record.reqat),
            self._datetime_to_str(record.startat),
            self._datetime_to_str(record.endat),
            record.path,
            record.state.value,
            record.progress,
            record.id
        ))

        # 수정된 데이터가 없는 경우
        if cur.rowcount == 0:
            raise Exception(f"'{record.id}'에 해당하는 CCTV 녹화 정보가 존재하지 않습니다.")
        
        self._conn.commit()
        return record

    def delete(self, id: str):
        cur = self._conn.execute(f"""
            DELETE FROM {self.DB_TABLE_NAME}
            WHERE id = ?
        """, (id,))

        # 삭제된 데이터가 없는 경우
        if cur.rowcount == 0:
            raise Exception(f"'{id}'에 해당하는 CCTV 녹화 정보가 존재하지 않습니다.")

        self._conn.commit()