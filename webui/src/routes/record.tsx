import { useState, useEffect } from "react";

import { CCTVStream, TaskItem, TaskState } from "../models";
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

function RecordPage() {
  const [cctvstreams, setCCTVStreams] = useState<CCTVStream[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [trigFetchTaskItems, setTrigFetchTaskItems] = useState(0);

  const [selected, setSelected] = useState<string>("");
  const [startat, setStartAt] = useState<string>("");
  const [endat, setEndAt] = useState<string>("");

  useEffect(() => {
    // Fetch CCTVStreams at the beginning
    streamReadAll().then((streams) => {
      if (streams.data) {
        setCCTVStreams(streams.data.map(transCCTVStream));
      }
    });
  }, []);

  // Check if there are any PENDING or STARTED tasks
  const polling = tasks.some(
    (task) =>
      task.state === TaskState.PENDING || task.state === TaskState.STARTED
  );

  useEffect(() => {
    const fetchTaskItems = async () => {
      const tasks = await taskRecordReadAll();
      if (tasks.data) {
        setTasks(tasks.data.map(transTaskItem));
      }
    };
    fetchTaskItems();

    // Polling every 2 seconds if there are any PENDING or STARTED tasks
    if (polling) {
      const interval = setInterval(fetchTaskItems, 2000);
      return () => clearInterval(interval);
    }
  }, [polling, trigFetchTaskItems]);

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
      setTrigFetchTaskItems((prev) => prev + 1);
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
      setTrigFetchTaskItems((prev) => prev + 1);
    }
  };

  const handleTaskDelete = async (id: string) => {
    if (window.confirm("정말로 작업을 삭제하시겠습니까?")) {
      await taskRecordDelete({
        path: {
          taskid: id,
        },
      });
      setTrigFetchTaskItems((prev) => prev + 1);
    }
  };

  return (
    <section>
      <h2 className="titlebox mb-4">CCTV 녹화하기</h2>
      <p className="descbox my-4">
        녹화를 원하시는 CCTV를 선택한 후 녹화 시작 시간 및 종료 시간을 입력하여
        녹화를 진행할 수 있습니다.
      </p>
      <div className="text-lg font-medium my-4">CCTV 선택</div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        {cctvstreams.map((cctv) => (
          <div className="flex items-center" key={cctv.name}>
            <input
              id={cctv.name}
              type="radio"
              checked={selected === cctv.name}
              name={cctv.name}
              onChange={() => setSelected(cctv.name)}
            />
            <label
              htmlFor={cctv.name}
              className="ml-2 cursor-pointer hover:underline"
            >
              {cctv.name}
            </label>
          </div>
        ))}
      </div>
      <div className="my-4 grid grid-cols-1 gap-2 md:grid-cols-2 md:gap-8">
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
