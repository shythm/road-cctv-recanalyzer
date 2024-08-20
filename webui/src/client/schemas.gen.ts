// This file is auto-generated by @hey-api/openapi-ts

export const $CCTVStream = {
    properties: {
        name: {
            type: 'string',
            title: 'Name'
        },
        coordx: {
            type: 'number',
            title: 'Coordx'
        },
        coordy: {
            type: 'number',
            title: 'Coordy'
        }
    },
    type: 'object',
    required: ['name', 'coordx', 'coordy'],
    title: 'CCTVStream'
} as const;

export const $HTTPValidationError = {
    properties: {
        detail: {
            items: {
                '$ref': '#/components/schemas/ValidationError'
            },
            type: 'array',
            title: 'Detail'
        }
    },
    type: 'object',
    title: 'HTTPValidationError'
} as const;

export const $TaskItem = {
    properties: {
        id: {
            type: 'string',
            title: 'Id'
        },
        name: {
            type: 'string',
            title: 'Name'
        },
        params: {
            additionalProperties: {
                type: 'string'
            },
            type: 'object',
            title: 'Params'
        },
        state: {
            anyOf: [
                {
                    '$ref': '#/components/schemas/TaskState'
                },
                {
                    type: 'integer'
                }
            ],
            title: 'State'
        },
        reason: {
            type: 'string',
            title: 'Reason'
        },
        progress: {
            type: 'number',
            title: 'Progress'
        },
        createdat: {
            type: 'string',
            format: 'date-time',
            title: 'Createdat'
        }
    },
    type: 'object',
    required: ['id', 'name', 'params', 'state', 'reason', 'progress'],
    title: 'TaskItem'
} as const;

export const $TaskOutput = {
    properties: {
        name: {
            type: 'string',
            title: 'Name'
        },
        type: {
            type: 'string',
            title: 'Type'
        },
        desc: {
            type: 'string',
            title: 'Desc'
        },
        taskid: {
            type: 'string',
            title: 'Taskid'
        },
        metadata: {
            additionalProperties: {
                type: 'string'
            },
            type: 'object',
            title: 'Metadata'
        },
        createdat: {
            type: 'string',
            format: 'date-time',
            title: 'Createdat'
        }
    },
    type: 'object',
    required: ['name', 'type', 'desc', 'taskid', 'metadata'],
    title: 'TaskOutput'
} as const;

export const $TaskState = {
    type: 'integer',
    enum: [-1, 0, 1, 2, 3, 4],
    title: 'TaskState'
} as const;

export const $ValidationError = {
    properties: {
        loc: {
            items: {
                anyOf: [
                    {
                        type: 'string'
                    },
                    {
                        type: 'integer'
                    }
                ]
            },
            type: 'array',
            title: 'Location'
        },
        msg: {
            type: 'string',
            title: 'Message'
        },
        type: {
            type: 'string',
            title: 'Error Type'
        }
    },
    type: 'object',
    required: ['loc', 'msg', 'type'],
    title: 'ValidationError'
} as const;