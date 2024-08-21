import os

from util import get_env_force
from fastapi import FastAPI, APIRouter, Request, Depends, Query, Response, responses
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
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
from srv.video_output_info import get_video_frame
from srv.cctv_tracking_analysis import CCTVTrackingAnalysisTaskSrv

JSON_DB_STORAGE = get_env_force('JSON_DB_STORAGE')
ITS_API_KEY = get_env_force('ITS_API_KEY')
TASK_OUTPUT_PATH = get_env_force('TASK_OUTPUT_PATH')
LISTEN_PORT = int(os.getenv('LISTEN_PORT', '8080'))

os.makedirs(TASK_OUTPUT_PATH, exist_ok=True)

cctv_stream_repo: CCTVStreamRepository = CCTVStreamITSRepo(
    os.path.join(JSON_DB_STORAGE, 'cctv_stream.json'), ITS_API_KEY)
task_item_repo: TaskItemRepository = TaskItemJsonRepo(
    os.path.join(JSON_DB_STORAGE, 'tasks.json'),
    fix_invalid_state=True)
task_output_repo: TaskOutputRepository = TaskOutputFileRepo(
    os.path.join(JSON_DB_STORAGE, 'task_output.json'), TASK_OUTPUT_PATH)

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
cctv_analysis_srv: TaskService = CCTVTrackingAnalysisTaskSrv(
    task_repo=task_item_repo,
    outputs_path=TASK_OUTPUT_PATH,
    output_repo=task_output_repo,
)


def create_task_router(task_service: TaskService, name: str) -> APIRouter:
    def read_all() -> list[TaskItem]:
        return task_service.get_tasks()

    start_query_params = {}
    for param in task_service.get_params():
        start_query_params[param.name] = (
            Optional[str] if param.optional else str,
            Field(Query(None if param.optional else ..., description=param.desc)),
        )
    StartQueryModel: Type[BaseModel] = create_model('StartTaskParams', **start_query_params)

    def start(params: StartQueryModel = Depends()) -> TaskItem:  # type: ignore
        # remove None values
        params = params.dict()
        params = {k: v for k, v in params.items() if v is not None}
        return task_service.start(params=params)

    def stop(taskid: str):
        return task_service.stop(taskid)

    def delete(taskid: str):
        return task_service.del_task(taskid)

    router = APIRouter()
    tags = ["task", name]

    router.add_api_route("", read_all, methods=['GET'], tags=tags)
    router.add_api_route("/start", start, methods=['POST'], tags=tags)
    router.add_api_route("/stop/{taskid}", stop, methods=['POST'], tags=tags)
    router.add_api_route("/{taskid}", delete, methods=['DELETE'], tags=tags)

    return router


def custom_generate_unique_id(route: APIRoute):
    return f"{'_'.join(route.tags)}_{route.name}"


app = FastAPI(generate_unique_id_function=custom_generate_unique_id)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


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

@app.get("/stream", tags=["stream"], name="read_all")
def read_cctv_stream_list() -> list[CCTVStream]:
    return cctv_stream_repo.get_all()


@app.post("/stream", tags=["stream"], name="create")
def create_cctv_stream(cctvname: str, coordx: float, coordy: float) -> CCTVStream:
    return cctv_stream_repo.save(cctvname, (coordx, coordy))


@app.delete("/stream/{cctvname}", tags=["stream"], name="delete")
def delete_cctv_stream(cctvname: str) -> CCTVStream:
    return cctv_stream_repo.delete(cctvname)


app.include_router(create_task_router(cctv_record_srv, "record"), prefix="/task/record")
app.include_router(create_task_router(cctv_tracking_srv, "tracking"), prefix="/task/tracking")
app.include_router(create_task_router(cctv_analysis_srv, "analysis"), prefix="/task/analysis")


@app.get("/output", tags=["output"], name="read_all")
def read_task_output_list() -> list[TaskOutput]:
    return task_output_repo.get_all()


@app.get("/output/name/{name}", tags=["output"], name="read_by_name")
def read_task_output_by_name(name: str) -> TaskOutput:
    return task_output_repo.get_by_name(name)


@app.get("/output/{taskid}", tags=["output"], name="read_by_taskid")
def read_task_output(taskid: str) -> list[TaskOutput]:
    return task_output_repo.get_by_taskid(taskid)


@app.delete("/output/{taskid}", tags=["output"], name="delete")
def delete_task_output(taskid: str) -> list[TaskOutput]:
    return task_output_repo.delete(taskid)


@app.get("/output/video/preview/{name}", tags=["output"], name="get_video_preview")
def get_video_preview(name: str, random: bool = True):
    preview = get_video_frame(os.path.join(TASK_OUTPUT_PATH, name), random_number=random)
    return Response(content=preview, media_type="image/jpeg")
