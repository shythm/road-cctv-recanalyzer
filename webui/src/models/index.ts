export type CCTVStream = {
  name: string;
  coordx: number;
  coordy: number;
};

export enum TaskState {
  UNKNOWN = -1,
  PENDING = 0,
  STARTED = 1,
  CANCELED = 2,
  FINISHED = 3,
  FAILED = 4,
}

export type TaskItem = {
  id: string;
  name: string;
  params: {
    [key: string]: string;
  };
  state: TaskState;
  reason: string;
  progress: number;
  createdat: Date;
};

export type TaskOutput = {
  name: string;
  type: string;
  desc: string;
  taskid: string;
  metadata: {
    [key: string]: string;
  };
  createdat: Date;
};
