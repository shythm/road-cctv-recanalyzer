"""
testing CCTVRecordDBRepo in cctvrecord_db.py
"""
import os
import unittest
from datetime import datetime, timedelta
import uuid
import random

import sys
sys.path.append('..')
from core.model import CCTVRecordBase
from repo.cctvrecord_db import CCTVRecordDBRepo

class CCTVRecordDBRepoTest(unittest.TestCase):

    def setUp(self):
        self._dbpath = "./cctvrecord_db_test.db"
        self.repo = CCTVRecordDBRepo(self._dbpath)

    def tearDown(self):
        if os.path.exists(self._dbpath):
            os.remove(self._dbpath)

    def _create_record(self):
        newid = str(uuid.uuid4())
        cctvid = str(uuid.uuid4())

        return CCTVRecordBase(
            id=newid,
            cctvid=cctvid,
            reqat=datetime.now(),
            startat=datetime.now(),
            endat=datetime.now() + timedelta(hours=1),
            path=f"/tmp/test{random.randint(0, 100)}.mp4",
            custom="this is custom field"
        )

    def test_insert(self):
        record = self._create_record()
        self.repo.insert(record)

        saved_record = self.repo.find_by_id(record.id)
        self.assertEqual(saved_record, record)

    def test_remove(self):
        record = self._create_record()
        self.repo.insert(record)
        saved_record = self.repo.find_by_id(record.id)
        self.assertEqual(saved_record, record)

        # 데이터를 삭제하고, 다시 조회했을 때 None이 반환되는지 확인
        self.repo.delete(saved_record.id)
        with self.assertRaises(Exception):
            self.repo.find_by_id(saved_record.id)

        # 없는 데이터를 삭제하려고 할 때
        with self.assertRaises(Exception):
            self.repo.delete("non-exist-id")

    def test_update(self):
        record = self._create_record()
        self.repo.insert(record)
        saved_record = self.repo.find_by_id(record.id)
        self.assertEqual(saved_record, record)

        # 데이터를 수정하고, 다시 조회했을 때 수정된 데이터가 반환되는지 확인
        record.path = "/tmp/updated.mp4"
        self.repo.update(record)
        saved_record = self.repo.find_by_id(record.id)
        self.assertEqual(saved_record, record)

        # 없는 데이터를 수정하려고 할 때
        record.id = "non-exist-id"
        with self.assertRaises(Exception):
            self.repo.update(record)

    def test_find_all(self):
        record1 = self._create_record()
        record2 = self._create_record()
        record3 = self._create_record()

        self.repo.insert(record1)
        self.repo.insert(record2)
        self.repo.insert(record3)

        records = self.repo.find_all()
        self.assertTrue(record1 in records)
        self.assertTrue(record2 in records)
        self.assertTrue(record3 in records)
        self.assertTrue(len(records) == 3)

if __name__ == "__main__":
    unittest.main()
