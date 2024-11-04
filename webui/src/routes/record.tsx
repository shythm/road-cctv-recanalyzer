import { useState, useEffect, useCallback } from "react";

import { CCTVStream } from "../models";
import {
  transCCTVStream,
  transTaskItem,
  transTaskOutput,
} from "../models/util";
import {
  streamReadAll,
  taskRecordReadAll,
  taskRecordStart,
  taskRecordStop,
  taskRecordDelete,
  outputReadByTaskid,
} from "../client";

import TaskItemView from "../components/task-item-view";
import useTaskPolling from "../components/task-polling";
import { Autocomplete } from "@mui/material";

function RecordPage() {
  const [cctvstreams, setCCTVStreams] = useState<CCTVStream[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [startat, setStartAt] = useState<string>("");
  const [endat, setEndAt] = useState<string>("");

  const readTasks = useCallback(async () => {
    const tasks = await taskRecordReadAll();
    if (tasks.data) {
      return tasks.data.map(transTaskItem);
    } else {
      return [];
    }
  }, []);
  const { tasks, pollTasks } = useTaskPolling(readTasks);

  useEffect(() => {
    // Fetch CCTVStreams at the beginning
    streamReadAll().then((streams) => {
      if (streams.data) {
        setCCTVStreams(streams.data.map(transCCTVStream));
      }
    });
  }, []);

  const handleTaskStart = async () => {
    if (selected && startat && endat) {
      await taskRecordStart({
        query: {
          cctv: selected,
          startat,
          endat,
        },
      });
      window.alert(`${selected} 녹화 작업이 제출되었습니다.`);
      pollTasks();
    }
  };

  const handleTaskOutputFetch = async (id: string) => {
    const output = await outputReadByTaskid({
      path: {
        taskid: id,
      },
    });
    if (output.data) {
      return output.data.map(transTaskOutput);
    } else {
      return [];
    }
  };

  const handleTaskCancel = async (id: string) => {
    if (window.confirm("정말로 작업을 취소하시겠습니까?")) {
      await taskRecordStop({
        path: {
          taskid: id,
        },
      });
      pollTasks();
    }
  };

  const handleTaskDelete = async (id: string) => {
    if (window.confirm("정말로 작업을 삭제하시겠습니까?")) {
      await taskRecordDelete({
        path: {
          taskid: id,
        },
      });
      pollTasks();
    }
  };

  return (
    <section>
      <h2 className="titlebox mb-4">CCTV 녹화하기</h2>
      <p className="descbox my-4">
        녹화를 원하시는 CCTV를 선택한 후 녹화 시작 시간 및 종료 시간을 입력하여
        녹화를 진행할 수 있습니다.
      </p>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        <div>
          <div className="text-lg font-medium mb-2">CCTV 선택</div>
          <Autocomplete
            options={cctvstreams}
            getOptionLabel={(option) => option.name}
            renderInput={(params) => (
              <div ref={params.InputProps.ref}>
                <input
                  type="text"
                  {...params.inputProps}
                  className="inputbox"
                  placeholder="CCTV 선택"
                />
              </div>
            )}
            onChange={(_, newValue) => {
              if (newValue) {
                setSelected(newValue.name);
              }
            }}
          />
        </div>
        <div>
          <div className="text-lg font-medium mb-2">녹화 시작 시간</div>
          <div>
            <input
              type="datetime-local"
              className="inputbox"
              value={startat}
              onChange={(e) => setStartAt(e.target.value)}
            />
          </div>
        </div>
        <div>
          <div className="text-lg font-medium mb-2">녹화 종료 시간</div>
          <div>
            <input
              type="datetime-local"
              className="inputbox"
              value={endat}
              onChange={(e) => setEndAt(e.target.value)}
            />
          </div>
        </div>
      </div>
      <div className="text-right">
        <button className="btn-base btn-dark" onClick={() => handleTaskStart()}>
          녹화 시작하기
        </button>
      </div>
      <p className="descbox my-4">
        녹화 작업 목록은 아래에서 확인할 수 있습니다.
      </p>
      <TaskItemView
        tasks={tasks}
        onTaskOutputFetch={async (id) => await handleTaskOutputFetch(id)}
        onTaskCancel={async (id) => await handleTaskCancel(id)}
        onTaskDelete={async (id) => await handleTaskDelete(id)}
        outputDownloadLinkGenerator={(output) => {
          return `/static/${output.name}`;
        }}
      />
    </section>
  );
}

export default RecordPage;
