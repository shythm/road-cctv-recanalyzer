import { useState } from "react";
import {
  AttachFile as AttachFileIcon,
  ContentCopy as ContentCopyIcon,
  ArrowDropDown as ArrowDropDownIcon,
  ArrowDropUp as ArrowDropUpIcon,
} from "@mui/icons-material";

import { TaskItem, TaskState, TaskOutput } from "../models";

export default function TaskItemView(props: {
  tasks: TaskItem[];
  onTaskCancel: (id: string) => void;
  onTaskDelete: (id: string) => void;
  onTaskOutputFetch: (id: string) => Promise<TaskOutput[]>;
  outputDownloadLinkGenerator: (output: TaskOutput) => string;
}) {
  const {
    tasks,
    onTaskCancel,
    onTaskDelete,
    onTaskOutputFetch,
    outputDownloadLinkGenerator,
  } = props;
  const [outputStorage, setOutputStorage] = useState<{
    [key: string]: TaskOutput[];
  }>({});

  const handleTaskOutputFetch = async (id: string) => {
    if (id in outputStorage) {
      const storage = { ...outputStorage };
      delete storage[id];
      setOutputStorage(storage);
    } else {
      const output = await onTaskOutputFetch(id);
      setOutputStorage({
        ...outputStorage,
        [id]: output,
      });
    }
  };

  const handleCopyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      window.alert(`'${text}'가 클립보드에 복사되었습니다.`);
    } catch (e) {
      window.alert("클립보드 복사에 실패했습니다." + e);
    }
  };

  return (
    <div className="flex flex-col-reverse">
      {tasks.map((task) => {
        const taskOutput = outputStorage[task.id] || null;

        return (
          <div key={task.id} className="w-full border rounded mb-4 p-4">
            <div className="mb-2 flex justify-between">
              <div className="font-medium">ID: {task.id}</div>
              <div>{task.createdat.toLocaleString()}</div>
            </div>
            <div className="flex flex-wrap gap-3 mb-2">
              {Object.entries(task.params).map(([key, value]) => (
                <div key={key} className="text-sm font-medium">
                  <span className="bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded-l">
                    {key}
                  </span>
                  <span className="bg-gray-100 text-gray-800 px-2.5 py-0.5 rounded-r">
                    {value}
                  </span>
                </div>
              ))}
            </div>
            <div className="text-gray-800 mb-2">
              <span className="font-medium mr-2">{TaskState[task.state]}:</span>
              {task.reason}
            </div>
            {task.state === TaskState.STARTED && (
              <div className="flex space-x-4 mb-2">
                <div className="self-center w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-gray-500 h-2.5 rounded-full"
                    style={{ width: `${Math.min(task.progress, 1.0) * 100}%` }}
                  />
                </div>
                <div>{Math.round(task.progress * 100)}%</div>
              </div>
            )}
            <div className="space-x-2">
              {task.state === TaskState.PENDING ||
              task.state === TaskState.STARTED ? (
                <button
                  className="btn-base-small btn-danger"
                  onClick={(e) => {
                    e.preventDefault();
                    onTaskCancel(task.id);
                  }}
                >
                  취소
                </button>
              ) : (
                <>
                  <button
                    className="btn-base-small btn-dark"
                    onClick={(e) => {
                      e.preventDefault();
                      handleTaskOutputFetch(task.id);
                    }}
                  >
                    결과 파일 {taskOutput ? "숨기기" : "보기"}
                    <span className="-mr-1">
                      {taskOutput ? (
                        <ArrowDropUpIcon fontSize="small" />
                      ) : (
                        <ArrowDropDownIcon fontSize="small" />
                      )}
                    </span>
                  </button>
                  <button
                    className="btn-base-small btn-danger"
                    onClick={(e) => {
                      e.preventDefault();
                      onTaskDelete(task.id);
                    }}
                  >
                    삭제
                  </button>
                </>
              )}
            </div>
            {taskOutput &&
              taskOutput.map((output) => (
                <div
                  key={output.name}
                  className="flex items-center space-x-2 mt-4 p-3 rounded border bg-gray-50"
                >
                  <AttachFileIcon className="self-start" />
                  <div>
                    <div className="flex space-x-4">
                      <a
                        href={outputDownloadLinkGenerator(output)}
                        className="font-medium hover:underline"
                      >
                        {output.name}
                      </a>
                      <button
                        className="flex items-center text-sm hover:underline"
                        onClick={() => handleCopyToClipboard(output.name)}
                      >
                        <ContentCopyIcon fontSize="small" />
                        <span className="ml-1">파일명 복사</span>
                      </button>
                    </div>
                    <div className="text-gray-800 text-sm">
                      {output.type} ⋅ {output.desc}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        );
      })}
    </div>
  );
}
