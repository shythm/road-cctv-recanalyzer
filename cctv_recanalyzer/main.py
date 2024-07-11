import os

from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime

from core.model import CCTVStream, CCTVRecord
from core.repo import CCTVStreamRepo, CCTVRecordRepo
from core.srv import CCTVRecorder
from repo.cctvstream_its_db import CCTVStreamITSDBRepo
from repo.cctvrecord_db import CCTVRecordDBRepo
from srv.cctvrecorder_ffmpeg import CCTVRecorderFFmpeg

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
cctv_recorder: CCTVRecorder = CCTVRecorderFFmpeg(
    stream_repo, record_repo, RECORD_OUTPUT_PATH, logging_path='logs')

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    cctv_recorder.start()
    try:
        yield
    finally:
        cctv_recorder.stop()

app.router.lifespan_context = lifespan

@app.get('/cctv', tags=['CCTV List'], response_model=list[CCTVStream])
async def get_cctv_list():
    return stream_repo.find_all()

@app.get('/cctv/{cctv_id}', tags=['CCTV List'], response_model=CCTVStream)
def get_cctv(cctv_id: str):
    return stream_repo.find_by_id(cctv_id)

@app.get('/cctv/{cctv_id}/hls', tags=['CCTV List'], response_model=str)
def get_cctv_hls(cctv_id: str):
    return stream_repo.get_hls_by_id(cctv_id)

@app.get('/recorder', tags=['CCTV Recorder'], response_model=list[CCTVRecord])
def get_record_list():
    return cctv_recorder.get_all()

@app.get('/recorder/submit', tags=['CCTV Recorder'], response_model=CCTVRecord)
def start_record(cctv_id: str, start_time: datetime, end_time: datetime):
    return cctv_recorder.submit(cctv_id, start_time, end_time)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=LISTEN_PORT)