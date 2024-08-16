import os

from util import get_env_force
from fastapi import FastAPI, HTTPException, Request, responses
from datetime import datetime

from core.model import CCTVStream, TaskItem, TaskOutput, EntityNotFound
from core.repo import CCTVStreamRepository, TaskOutputRepository
from core.srv import TaskService

from repo.cctv_stream_its import CCTVStreamITSRepo
from repo.task_output_file import TaskOutputFileRepo
from srv.cctv_record_ffmpeg import CCTVRecordFFmpegTaskSrv

JSON_DB_STORAGE = get_env_force('JSON_DB_STORAGE')
ITS_API_KEY = get_env_force('ITS_API_KEY')
TASK_OUTPUT_PATH = get_env_force('TASK_OUTPUT_PATH')
LISTEN_PORT = int(os.getenv('LISTEN_PORT', '8080'))

cctv_stream_repo: CCTVStreamRepository = CCTVStreamITSRepo(
    os.path.join(JSON_DB_STORAGE, 'cctv_stream.json'), ITS_API_KEY)
task_output_repo: TaskOutputRepository = TaskOutputFileRepo(
    os.path.join(JSON_DB_STORAGE, 'task_output.json')
)

cctv_record_srv: TaskService = CCTVRecordFFmpegTaskSrv(
    os.path.join(JSON_DB_STORAGE, 'tasks.json'), TASK_OUTPUT_PATH, cctv_stream_repo, task_output_repo
)

app = FastAPI()

######################
# Exception Handlers #
######################

@app.exception_handler(EntityNotFound)
def app_entity_not_found_handler(request: Request, exc: EntityNotFound):
    return responses.JSONResponse(
        status_code=404,
        content={'message': str(exc)}
    )

@app.exception_handler(ValueError)
def app_value_error_handler(request: Request, exc: ValueError):
    return responses.JSONResponse(
        status_code=400,
        content={'message': str(exc)}
    )

@app.exception_handler(Exception)
def app_exception_handler(request: Request, exc: Exception):
    return responses.JSONResponse(
        status_code=500,
        content={'message': str(exc)}
    )


#################
# API Endpoints #
#################

@app.get("/cctv/stream", tags=["cctv stream"])
def read_cctv_stream_list() -> list[CCTVStream]:
    return cctv_stream_repo.get_all()

@app.post("/cctv/stream", tags=["cctv stream"])
def create_cctv_stream(cctvname: str, coordx: float, coordy: float) -> CCTVStream:
    return cctv_stream_repo.save(cctvname, (coordx, coordy))

@app.delete("/cctv/stream/{cctvname}", tags=["cctv stream"])
def delete_cctv_stream(cctvname: str) -> CCTVStream:
    return cctv_stream_repo.delete(cctvname)

@app.get("/task/record", tags=["cctv record task"])
def read_cctv_record_list() -> list[TaskItem]:
    return cctv_record_srv.get_tasks()

@app.get("/task/record/start", tags=["cctv record task"])
def start_cctv_record(cctv: str, startat: datetime, endat: datetime) -> TaskItem:
    return cctv_record_srv.start(cctv=cctv, startat=startat, endat=endat)
    
@app.get("/task/record/stop/{taskid}", tags=["cctv record task"])
def stop_cctv_record(taskid: str):
    return cctv_record_srv.stop(taskid)

@app.delete("/task/record/{taskid}", tags=["cctv record task"])
def delete_cctv_record(taskid: str):
    return cctv_record_srv.del_task(taskid)

@app.get("/output", tags=["task output"])
def read_task_output_list() -> list[TaskOutput]:
    return task_output_repo.get_all()

@app.get("/output/{taskid}", tags=["task output"])
def read_task_output(taskid: str) -> list[TaskOutput]:
    return task_output_repo.get(taskid)

@app.delete("/output/{taskid}", tags=["task output"])
def delete_task_output(taskid: str) -> list[TaskOutput]:
    return task_output_repo.delete(taskid)
