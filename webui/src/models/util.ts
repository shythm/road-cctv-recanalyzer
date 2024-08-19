import { CCTVStream, TaskItem, TaskState, TaskOutput } from ".";
import {
  CCTVStream as CCTVStreamDTO,
  TaskItem as TaskItemDTO,
  TaskOutput as TaskOutputDTO,
} from "../client";

export const transCCTVStream = (dto: CCTVStreamDTO): CCTVStream => {
  return {
    name: dto.name,
    coordx: dto.coordx,
    coordy: dto.coordy,
  };
};

export const transTaskItem = (dto: TaskItemDTO): TaskItem => {
  let taskState = TaskState.UNKNOWN;
  switch (dto.state) {
    case 0:
      taskState = TaskState.PENDING;
      break;
    case 1:
      taskState = TaskState.STARTED;
      break;
    case 2:
      taskState = TaskState.CANCELED;
      break;
    case 3:
      taskState = TaskState.FINISHED;
      break;
    case 4:
      taskState = TaskState.FAILED;
      break;
  }

  return {
    id: dto.id,
    name: dto.name,
    params: dto.params,
    state: taskState,
    reason: dto.reason,
    progress: dto.progress,
    createdat: new Date(dto.createdat!),
  };
};

export const transTaskOutput = (dto: TaskOutputDTO): TaskOutput => {
  return {
    name: dto.name,
    type: dto.type,
    desc: dto.desc,
    taskid: dto.taskid,
    metadata: dto.metadata,
    createdat: new Date(dto.createdat!),
  };
};
