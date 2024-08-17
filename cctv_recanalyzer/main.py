import os

from util import get_env_force
from fastapi import FastAPI, APIRouter, Request, Depends, Query, responses
from typing import Optional, Type
from pydantic import create_model, BaseModel, Field

from core.model import CCTVStream, TaskItem, TaskOutput, EntityNotFound
from core.repo import CCTVStreamRepository, TaskItemRepository, TaskOutputRepository
from core.srv import TaskService

from repo.cctv_stream_its import CCTVStreamITSRepo
from repo.task_output_file import TaskOutputFileRepo
from repo.task_item_file import TaskItemJsonRepo
from srv.cctv_record_ffmpeg import CCTVRecordFFmpegTaskSrv
from srv.cctv_yolov8_deepsort import YOLOv8DeepSORTTackingTaskSrv

JSON_DB_STORAGE = get_env_force('JSON_DB_STORAGE')
ITS_API_KEY = get_env_force('ITS_API_KEY')
TASK_OUTPUT_PATH = get_env_force('TASK_OUTPUT_PATH')
LISTEN_PORT = int(os.getenv('LISTEN_PORT', '8080'))

os.makedirs(TASK_OUTPUT_PATH, exist_ok=True)

cctv_stream_repo: CCTVStreamRepository = CCTVStreamITSRepo(
    os.path.join(JSON_DB_STORAGE, 'cctv_stream.json'), ITS_API_KEY)
task_item_repo: TaskItemRepository = TaskItemJsonRepo(
    os.path.join(JSON_DB_STORAGE, 'tasks.json'),
    fix_invalid_state=True
)
task_output_repo: TaskOutputRepository = TaskOutputFileRepo(
    os.path.join(JSON_DB_STORAGE, 'task_output.json')
)

cctv_record_srv: TaskService = CCTVRecordFFmpegTaskSrv(
    task_repo=task_item_repo,
    cctv_stream_repo=cctv_stream_repo,
    outputs_path=TASK_OUTPUT_PATH,
    output_repo=task_output_repo,
)
cctv_tracking_srv: TaskService = YOLOv8DeepSORTTackingTaskSrv(
    task_repo=task_item_repo,
    model_path='yolov8l.pt',
    outputs_path=TASK_OUTPUT_PATH,
    output_repo=task_output_repo,
)


def create_task_router(task_service: TaskService) -> APIRouter:
    def read_task_list() -> list[TaskItem]:
        return task_service.get_tasks()

    start_query_params = {}
    for param in task_service.get_params():
        start_query_params[param.name] = (
            Optional[str] if param.optional else str,
            Field(Query(None if param.optional else ..., description=param.desc)),
        )
    StartQueryModel: Type[BaseModel] = create_model('StartTaskParams', **start_query_params)

    def start_task(params: StartQueryModel = Depends()) -> TaskItem:  # type: ignore
        # remove None values
        params = params.dict()
        params = {k: v for k, v in params.items() if v is not None}
        return task_service.start(params=params)

    def stop_task(taskid: str):
        return task_service.stop(taskid)

    def delete_task(taskid: str):
        return task_service.del_task(taskid)

    router = APIRouter()
    tags = [task_service.get_name()]

    router.add_api_route("", read_task_list, methods=['GET'], tags=tags)
    router.add_api_route("/start", start_task, methods=['POST'], tags=tags)
    router.add_api_route("/stop/{taskid}", stop_task, methods=['POST'], tags=tags)
    router.add_api_route("/{taskid}", delete_task, methods=['DELETE'], tags=tags)

    return router


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


app.include_router(create_task_router(cctv_record_srv), prefix="/task/record")
app.include_router(create_task_router(cctv_tracking_srv), prefix="/task/tracking")


@app.get("/output", tags=["task output"])
def read_task_output_list() -> list[TaskOutput]:
    return task_output_repo.get_all()


@app.get("/output/{taskid}", tags=["task output"])
def read_task_output(taskid: str) -> list[TaskOutput]:
    return task_output_repo.get_by_taskid(taskid)


@app.delete("/output/{taskid}", tags=["task output"])
def delete_task_output(taskid: str) -> list[TaskOutput]:
    return task_output_repo.delete(taskid)
