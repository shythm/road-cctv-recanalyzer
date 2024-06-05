from cctvrecorder.core.repo import CCTVRecordRepo
from cctvrecorder.core.model import CCTVRecord, CCTVRecordState

from sqlite3 import connect
from typing import List
from datetime import datetime

class CCTVRecordDBRepo(CCTVRecordRepo):

    DB_TABLE_NAME = "cctvrecord"

    def __init__(self, dbpath: str):
        self._conn = connect(dbpath)
        
        # 만약 테이블이 존재하지 않는다면 생성한다.
        # 이때 state 필드는 녹화 상태를 나타내며, repo에 저장하는 것들은 모두 녹화가 완료된 상태(FINISHED)로 가정한다.
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.DB_TABLE_NAME} (
                id TEXT PRIMARY KEY,
                cctvid TEXT,
                reqat TEXT,
                startat TEXT,
                endat TEXT,
                path TEXT,
                srcid TEXT,
                state INTEGER DEFAULT {CCTVRecordState.FINISHED.value}
            )
        """)

    def _datetime_to_str(self, dt: datetime) -> str:
        # 국제 표준 포맷인 ISO 8601 형식으로 변환
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    
    def _str_to_datetime(self, dtstr: str) -> datetime:
        return datetime.strptime(dtstr, "%Y-%m-%dT%H:%M:%S")

    def find_all(self) -> List[CCTVRecord]:
        cur = self._conn.execute(f"""
            SELECT id, cctvid, reqat, startat, endat, path, srcid, state
            FROM {self.DB_TABLE_NAME}                     
        """)

        return [CCTVRecord(
            id=row[0],
            cctvid=row[1],
            reqat=self._str_to_datetime(row[2]),
            startat=self._str_to_datetime(row[3]),
            endat=self._str_to_datetime(row[4]),
            path=row[5],
            srcid=row[6],
            state=CCTVRecordState(row[7])
        ) for row in cur.fetchall()]

    def find_by_id(self, id: str) -> CCTVRecord:
        cur = self._conn.execute(f"""
            SELECT id, cctvid, reqat, startat, endat, path, srcid, state
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
            srcid=row[6],
            state=CCTVRecordState(row[7])
        )

    def insert(self, record: CCTVRecord) -> CCTVRecord:
        self._conn.execute(f"""
            INSERT INTO {self.DB_TABLE_NAME} (id, cctvid, reqat, startat, endat, path, srcid, state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.id,
            record.cctvid,
            self._datetime_to_str(record.reqat),
            self._datetime_to_str(record.startat),
            self._datetime_to_str(record.endat),
            record.path,
            record.srcid,
            record.state.value
        ))

        self._conn.commit()
        return record

    def update(self, record: CCTVRecord) -> CCTVRecord:
        cur = self._conn.execute(f"""
            UPDATE {self.DB_TABLE_NAME}
            SET cctvid = ?, reqat = ?, startat = ?, endat = ?, path = ?, srcid = ?, state = ?
            WHERE id = ?
        """, (
            record.cctvid,
            self._datetime_to_str(record.reqat),
            self._datetime_to_str(record.startat),
            self._datetime_to_str(record.endat),
            record.path,
            record.srcid,
            record.state.value,
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