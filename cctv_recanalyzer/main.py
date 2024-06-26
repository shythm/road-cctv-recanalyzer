import os
from dotenv import load_dotenv
from flask import Flask

from cctv_recanalyzer.core.repo import CCTVStreamRepo, CCTVRecordRepo

from cctv_recanalyzer.repo.cctvstream_its_db import CCTVStreamITSDBRepo
from cctv_recanalyzer.repo.cctvrecord_db import CCTVRecordDBRepo
from cctv_recanalyzer.srv.cctvrecorder_ffmpeg import CCTVRecorderFFmpeg
from cctv_recanalyzer.http.cctvstream import CCTVStreamView
from cctv_recanalyzer.http.cctvrecorder import CCTVRecorderView

load_dotenv()
def get_env_force(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f'{key} is not set')
    return value

SQLITE3_DB_PATH = get_env_force('SQLITE3_DB_PATH')
ITS_API_KEY = get_env_force('ITS_API_KEY')
RECORD_OUTPUT_PATH = get_env_force('RECORD_OUTPUT_PATH')
LISTEN_PORT = int(os.getenv('LISTEN_PORT', 8080))
DEBUG_MODE = os.getenv('PRODUCTION') != 'production'

stream_repo: CCTVStreamRepo = CCTVStreamITSDBRepo(SQLITE3_DB_PATH, ITS_API_KEY)
record_repo: CCTVRecordRepo = CCTVRecordDBRepo(SQLITE3_DB_PATH)
cctv_recorder = CCTVRecorderFFmpeg(stream_repo, record_repo, RECORD_OUTPUT_PATH)

if __name__ == "__main__":
    app = Flask(__name__)

    # add endpoints
    CCTVStreamView(stream_repo).inject(app, '/cctvstream')
    CCTVRecorderView(cctv_recorder).inject(app, '/record')

    app.run(host='0.0.0.0', port=LISTEN_PORT, debug=DEBUG_MODE, use_reloader=False)
