"""
testing cctvrecorder_ffmpeg.py using unittest
"""

import unittest

from cctv_recanalyzer.srv.cctvrecorder_ffmpeg import CCTVRecorderFFmpeg
from cctv_recanalyzer.repo.cctvstream_its_db import CCTVStreamITSDBRepo
from cctv_recanalyzer.repo.cctvrecord_db import CCTVRecordDBRepo

from cctv_recanalyzer.core.model import CCTVRecord, CCTVRecordState

from datetime import datetime, timedelta
import os
import time
import cv2

class TestCCTVRecorderFFmpeg(unittest.TestCase):
    def setUp(self):
        # read apikey from `api.key` file
        with open("api.key", "r") as f:
            apikey = f.read().strip()

        self.output_path = "../output"
        self.db_path = "test_srv_cctvrecorder_ffmpeg.db"
        stream_repo = CCTVStreamITSDBRepo(self.db_path, apikey)
        record_repo = CCTVRecordDBRepo(self.db_path)

        self.recorder = CCTVRecorderFFmpeg(
            stream_repo=stream_repo,
            record_repo=record_repo,
            output_path=self.output_path
        )

        # create sample stream
        self.cctv1 = stream_repo.create("[서해안선] 서평택", (126.868976, 36.997973))
        stream_repo.insert(self.cctv1)
        self.cctv2 = stream_repo.create("[서해안선] 서해주탑", (126.838330, 36.950560))
        stream_repo.insert(self.cctv2)

    def tearDown(self):
        self.recorder.stop()
        os.remove(self.db_path)
        
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
            self.cctv1.id, datetime.now(), datetime.now() + timedelta(hours=1)
        )
        self.assertIsInstance(record, CCTVRecord)

        jobs = self.recorder.get_all()
        self.assertIn(record, jobs)
        self.assertEqual(record.state, CCTVRecordState.PENDING)

        self.recorder.cancel(record.id)
        time.sleep(self.recorder.SCHEDULE_INTERVAL * 2)
        self.assertEqual(record.state, CCTVRecordState.CANCELED)

    def test_submit_wait(self):
        """
        녹화 작업을 제출하고, 작업이 완료되기를 기다린다.
        """
        seconds = 5
        record = self.recorder.submit(
            self.cctv2.id, datetime.now(), datetime.now() + timedelta(seconds=seconds)
        )
        self.assertIsInstance(record, CCTVRecord)

        time.sleep(seconds + self.recorder.SCHEDULE_INTERVAL * 2)
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
            self.cctv1.id, datetime.now(), datetime.now() + timedelta(hours=1)
        )
        self.assertIsInstance(record, CCTVRecord)

        jobs = self.recorder.get_all()
        self.assertIn(record, jobs)
        self.assertEqual(record.state, CCTVRecordState.PENDING)

        self.recorder.cancel(record.id)
        time.sleep(self.recorder.SCHEDULE_INTERVAL * 2)
        self.recorder.remove(record.id)
        time.sleep(self.recorder.SCHEDULE_INTERVAL * 2)
        self.assertNotIn(record, self.recorder.get_all())

    def test_multiple_submit(self):
        """
        여러 개의 작업을 제출하고, 작업이 완료되기를 기다린다.
        """
        seconds = 5
        record1 = self.recorder.submit(
            self.cctv1.id, datetime.now(), datetime.now() + timedelta(seconds=seconds * 2)
        )
        record2 = self.recorder.submit(
            self.cctv2.id, datetime.now() + timedelta(seconds=2), datetime.now() + timedelta(seconds=2 + seconds)
        )

        time.sleep(seconds * 2 + self.recorder.SCHEDULE_INTERVAL * 2)
        self.assertEqual(record1.state, CCTVRecordState.FINISHED)
        self.assertEqual(record2.state, CCTVRecordState.FINISHED)

        self.assertTrue(os.path.exists(record1.path))
        self.assertTrue(os.path.exists(record2.path))

        self._assert_duration(record1.path, seconds * 2)
        self._assert_duration(record2.path, seconds)

if __name__ == "__main__":
    unittest.main()