"""
testing cctvrecorder_ffmpeg.py using unittest
"""

import sys

sys.path.append("..")

import os
import time
import unittest
from datetime import datetime, timedelta

import cv2
from core.model import CCTVRecord, CCTVRecordState
from repo.cctvrecord_db import CCTVRecordDBRepo
from repo.cctvstream_its_db import CCTVStreamITSDBRepo
from srv.cctvrecorder_ffmpeg import CCTVRecorderFFmpeg


class UnitTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # read apikey from `api.key` file
        with open("api.key", "r") as f:
            apikey = f.read().strip()

        cls.db_path = "test_srv_cctvrecorder_ffmpeg.db"
        stream_repo = CCTVStreamITSDBRepo(cls.db_path, apikey)
        record_repo = CCTVRecordDBRepo(cls.db_path)

        cls.recorder = CCTVRecorderFFmpeg(
            stream_repo=stream_repo,
            record_repo=record_repo,
            output_path="output",
            logging_path="log",
        )
        cls.recorder.start()
        cls.interval = cls.recorder.SCHEDULE_INTERVAL

        # create sample stream
        cls.cctv = [
            stream_repo.create("[서해안선] 서평택", (126.868976, 36.997973)),
            stream_repo.create("[서해안선] 서해주탑", (126.838330, 36.950560)),
        ]
        for cctv in cls.cctv:
            stream_repo.insert(cctv)

    @classmethod
    def tearDownClass(cls):
        cls.recorder.stop()
        os.remove(cls.db_path)

    def _assert_duration(self, path: str, duration: int):
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()

        # epsillon: 0.1초의 오차를 허용
        self.assertAlmostEqual(frame_count / fps, duration, delta=0.1)

    def test_submit_cancel(self):
        """
        작업을 제출하고 제출된 작업이 제대로 조회되는지 확인한다. 확인 후 작업을 취소한다.
        제출할 작업의 시작 시간은 1시간 뒤로 설정한다.
        """
        record = self.recorder.submit(
            UnitTester.cctv[0].id, datetime.now(), datetime.now() + timedelta(hours=1)
        )
        self.assertIsInstance(record, CCTVRecord)

        jobs = UnitTester.recorder.get_all()
        self.assertIn(record, jobs)
        self.assertEqual(record.state, CCTVRecordState.PENDING)

        UnitTester.recorder.cancel(record.id)
        time.sleep(UnitTester.interval * 2)
        self.assertEqual(record.state, CCTVRecordState.CANCELED)

    def test_submit_wait(self):
        """
        녹화 작업을 제출하고, 작업이 완료되기를 기다린다.
        """
        seconds = 5
        record = UnitTester.recorder.submit(
            UnitTester.cctv[1].id,
            datetime.now(),
            datetime.now() + timedelta(seconds=seconds),
        )
        self.assertIsInstance(record, CCTVRecord)

        time.sleep(seconds + UnitTester.interval * 2)
        self.assertEqual(record.state, CCTVRecordState.FINISHED)

        # check if the file is created
        self.assertTrue(os.path.exists(record.path))
        self._assert_duration(record.path, seconds)

    def test_submit_remove(self):
        """
        작업을 제출하고 제출된 작업이 제대로 조회되는지 확인한다. 확인 후 작업을 삭제한다.
        제출할 작업의 시작 시간은 1시간 뒤로 설정한다.
        """
        record = self.recorder.submit(
            UnitTester.cctv[0].id, datetime.now(), datetime.now() + timedelta(hours=1)
        )
        self.assertIsInstance(record, CCTVRecord)

        jobs = self.recorder.get_all()
        self.assertIn(record, jobs)
        self.assertEqual(record.state, CCTVRecordState.PENDING)

        self.recorder.cancel(record.id)
        time.sleep(UnitTester.interval * 2)
        self.recorder.remove(record.id)
        time.sleep(UnitTester.interval * 2)
        self.assertNotIn(record, self.recorder.get_all())

    def test_multiple_submit(self):
        """
        여러 개의 작업을 제출하고, 작업이 완료되기를 기다린다.
        """
        seconds = 5
        record1 = self.recorder.submit(
            UnitTester.cctv[0].id,
            datetime.now(),
            datetime.now() + timedelta(seconds=seconds * 2),
        )
        record2 = self.recorder.submit(
            UnitTester.cctv[1].id,
            datetime.now() + timedelta(seconds=2),
            datetime.now() + timedelta(seconds=2 + seconds),
        )

        time.sleep(seconds * 2 + UnitTester.interval * 2)
        self.assertEqual(record1.state, CCTVRecordState.FINISHED)
        self.assertEqual(record2.state, CCTVRecordState.FINISHED)

        self.assertTrue(os.path.exists(record1.path))
        self.assertTrue(os.path.exists(record2.path))

        self._assert_duration(record1.path, seconds * 2)
        self._assert_duration(record2.path, seconds)


if __name__ == "__main__":
    unittest.main()
