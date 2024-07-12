from core.repo import CCTVRecordRepo
from core.model import CCTVRecordBase, CCTVRecordState

from sqlite3 import connect, threadsafety as sqlite3_threadsafety
from util import str_to_datetime, datetime_to_str

class CCTVRecordDBRepo(CCTVRecordRepo):

    DB_TABLE_NAME = "cctvrecord"

    def __init__(self, dbpath: str):
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
        custom: 녹화 서비스에 따른 추가 정보
        """
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.DB_TABLE_NAME} (
                id TEXT PRIMARY KEY,
                cctvid TEXT,
                reqat TEXT,
                startat TEXT,
                endat TEXT,
                path TEXT,
                custom TEXT
            )
        """)
        self._conn.commit()

    def find_all(self) -> list[CCTVRecordBase]:
        cur = self._conn.execute(f"""
            SELECT id, cctvid, reqat, startat, endat, path, custom
            FROM {self.DB_TABLE_NAME}                     
        """)

        return [CCTVRecordBase(
            id=row[0],
            cctvid=row[1],
            reqat=str_to_datetime(row[2]),
            startat=str_to_datetime(row[3]),
            endat=str_to_datetime(row[4]),
            path=row[5],
            custom=row[6]
        ) for row in cur.fetchall()]

    def find_by_id(self, id: str) -> CCTVRecordBase:
        cur = self._conn.execute(f"""
            SELECT id, cctvid, reqat, startat, endat, path, custom
            FROM {self.DB_TABLE_NAME}
            WHERE id = ?
        """, (id,))

        row = cur.fetchone()
        if row is None:
            raise Exception(f"'{id}'에 해당하는 CCTV 녹화 정보가 존재하지 않습니다.")
        
        return CCTVRecordBase(
            id=row[0],
            cctvid=row[1],
            reqat=str_to_datetime(row[2]),
            startat=str_to_datetime(row[3]),
            endat=str_to_datetime(row[4]),
            path=row[5],
            custom=row[6]
        )

    def insert(self, record: CCTVRecordBase) -> CCTVRecordBase:
        self._conn.execute(f"""
            INSERT INTO {self.DB_TABLE_NAME} (id, cctvid, reqat, startat, endat, path, custom)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            record.id,
            record.cctvid,
            datetime_to_str(record.reqat),
            datetime_to_str(record.startat),
            datetime_to_str(record.endat),
            record.path,
            record.custom
        ))

        self._conn.commit()
        return record

    def update(self, record: CCTVRecordBase) -> CCTVRecordBase:
        cur = self._conn.execute(f"""
            UPDATE {self.DB_TABLE_NAME}
            SET cctvid = ?, reqat = ?, startat = ?, endat = ?, path = ?, custom = ?
            WHERE id = ?
        """, (
            record.cctvid,
            datetime_to_str(record.reqat),
            datetime_to_str(record.startat),
            datetime_to_str(record.endat),
            record.path,
            record.custom,
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