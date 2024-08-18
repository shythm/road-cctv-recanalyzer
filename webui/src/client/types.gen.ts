// This file is auto-generated by @hey-api/openapi-ts

export type CCTVStream = {
    name: string;
    coordx: number;
    coordy: number;
};

export type HTTPValidationError = {
    detail?: Array<ValidationError>;
};

export type TaskItem = {
    id: string;
    name: string;
    params: {
        [key: string]: (string);
    };
    state: TaskState | number;
    reason: string;
    progress: number;
    createdat?: string;
};

export type TaskOutput = {
    name: string;
    type: string;
    desc: string;
    taskid: string;
    metadata: {
        [key: string]: (string);
    };
    createdat?: string;
};

export type TaskState = -1 | 0 | 1 | 2 | 3 | 4;

export type ValidationError = {
    loc: Array<(string | number)>;
    msg: string;
    type: string;
};

export type StreamReadAllResponse = Array<CCTVStream>;

export type StreamReadAllError = unknown;

export type StreamCreateData = {
    query: {
        cctvname: string;
        coordx: number;
        coordy: number;
    };
};

export type StreamCreateResponse = CCTVStream;

export type StreamCreateError = HTTPValidationError;

export type StreamDeleteData = {
    path: {
        cctvname: string;
    };
};

export type StreamDeleteResponse = CCTVStream;

export type StreamDeleteError = HTTPValidationError;

export type TaskRecordReadAllResponse = Array<TaskItem>;

export type TaskRecordReadAllError = unknown;

export type TaskRecordStartData = {
    query: {
        /**
         * CCTV 이름
         */
        cctv: string;
        /**
         * 녹화 종료 시간
         */
        endat: string;
        /**
         * 녹화 시작 시간
         */
        startat: string;
    };
};

export type TaskRecordStartResponse = TaskItem;

export type TaskRecordStartError = HTTPValidationError;

export type TaskRecordStopData = {
    path: {
        taskid: string;
    };
};

export type TaskRecordStopResponse = unknown;

export type TaskRecordStopError = HTTPValidationError;

export type TaskRecordDeleteData = {
    path: {
        taskid: string;
    };
};

export type TaskRecordDeleteResponse = unknown;

export type TaskRecordDeleteError = HTTPValidationError;

export type TaskTrackingReadAllResponse = Array<TaskItem>;

export type TaskTrackingReadAllError = unknown;

export type TaskTrackingStartData = {
    query: {
        /**
         * 신뢰도 임계값
         */
        confidence?: string | null;
        /**
         * 분석할 CCTV 영상
         */
        targetname: string;
    };
};

export type TaskTrackingStartResponse = TaskItem;

export type TaskTrackingStartError = HTTPValidationError;

export type TaskTrackingStopData = {
    path: {
        taskid: string;
    };
};

export type TaskTrackingStopResponse = unknown;

export type TaskTrackingStopError = HTTPValidationError;

export type TaskTrackingDeleteData = {
    path: {
        taskid: string;
    };
};

export type TaskTrackingDeleteResponse = unknown;

export type TaskTrackingDeleteError = HTTPValidationError;

export type OutputReadAllResponse = Array<TaskOutput>;

export type OutputReadAllError = unknown;

export type OutputReadData = {
    path: {
        taskid: string;
    };
};

export type OutputReadResponse = Array<TaskOutput>;

export type OutputReadError = HTTPValidationError;

export type OutputDeleteData = {
    path: {
        taskid: string;
    };
};

export type OutputDeleteResponse = Array<TaskOutput>;

export type OutputDeleteError = HTTPValidationError;