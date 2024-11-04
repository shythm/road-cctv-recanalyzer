"""
testing CCTVStreamITSDBRepo in cctvstream_its_db.py
"""

import os
import sys
import unittest

import requests

sys.path.append("..")
from cctv_recanalyzer.repo.cctvstream_its_db import CCTVStreamITSDBRepo


class TestCCTVStreamITSDBRepo(unittest.TestCase):

    def setUp(self):
        with open("api.key", "r") as f:
            apikey = f.read().strip()
        self._dbpath = "./repo_cctvstream_its_db_test.db"
        self.repo = CCTVStreamITSDBRepo(self._dbpath, apikey)

    def tearDown(self):
        if os.path.exists(self._dbpath):
            os.remove(self._dbpath)

    def _create_cctvstream(self, example_num=0):
        args = [
            ("[서해안선] 서평택", (126.868976, 36.997973)),
            ("[서해안선] 서해주탑", (126.838330, 36.950560)),
        ]
        return self.repo.create(*args[example_num])

    def test_insert(self):
        stream = self._create_cctvstream()
        self.repo.insert(stream)

        saved_stream = self.repo.find_by_id(stream.id)
        self.assertEqual(saved_stream, stream)

        # 없는 데이터를 조회하려고 할 때
        with self.assertRaises(Exception):
            self.repo.find_by_id("non-exist-id")

    def test_remove(self):
        stream = self._create_cctvstream()
        self.repo.insert(stream)
        saved_stream = self.repo.find_by_id(stream.id)
        self.assertEqual(saved_stream, stream)

        # 데이터를 삭제하고, 다시 조회했을 때 예외가 발생하는지 확인
        self.repo.delete(saved_stream.id)
        with self.assertRaises(Exception):
            saved_stream = self.repo.find_by_id(saved_stream.id)

    def test_update(self):
        stream = self._create_cctvstream()
        self.repo.insert(stream)
        saved_stream = self.repo.find_by_id(stream.id)
        self.assertEqual(saved_stream, stream)

        # 데이터를 수정하고, 다시 조회했을 때 수정된 데이터가 반환되는지 확인
        stream.name = "[서해안선] 서평택(수정)"
        self.repo.update(stream)
        saved_stream = self.repo.find_by_id(stream.id)
        self.assertEqual(saved_stream, stream)

        # 없는 데이터를 수정하려고 할 때
        stream.id = "non-exist-id"
        with self.assertRaises(Exception):
            self.repo.update(stream)

    def test_find_all(self):
        stream1 = self._create_cctvstream(0)
        stream2 = self._create_cctvstream(1)

        self.repo.insert(stream1)
        self.repo.insert(stream2)

        streams = self.repo.find_all()
        self.assertTrue(stream1 in streams)
        self.assertTrue(stream2 in streams)
        self.assertTrue(len(streams) == 2)

    def test_hls_fetch(self):
        stream = self._create_cctvstream()
        self.repo.insert(stream)
        saved_stream = self.repo.find_by_id(stream.id)
        self.assertEqual(saved_stream, stream)

        # request를 통해 hls 주소를 가져오는지 확인
        hls = self.repo.get_hls_by_id(saved_stream.id)
        res = requests.get(hls)
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
