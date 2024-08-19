import { useState, useEffect } from "react";

import { TaskItem, TaskState } from "../models";
import { transTaskItem, transTaskOutput } from "../models/util";
import {
  taskTrackingReadAll,
  taskTrackingStart,
  taskTrackingStop,
  taskTrackingDelete,
  outputRead,
} from "../client";

import TaskItemView from "../components/task-item-view";

function TrackPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [trigFetchTaskItems, setTrigFetchTaskItems] = useState(0);

  const [targetname, setTargetName] = useState("");
  const [confidence, setConfidence] = useState(0.6);

  // Check if there are any PENDING or STARTED tasks
  const polling = tasks.some(
    (task) =>
      task.state === TaskState.PENDING || task.state === TaskState.STARTED
  );

  useEffect(() => {
    const fetchTaskItems = async () => {
      const tasks = await taskTrackingReadAll();
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
    if (targetname && confidence) {
      await taskTrackingStart({
        query: {
          targetname: targetname,
          confidence: confidence.toString(),
        },
      });
      window.alert("차량 추적 작업이 제출되었습니다.");
      setTrigFetchTaskItems((prev) => prev + 1);
    }
  };

  const handleTaskOutputFetch = async (id: string) => {
    const output = await outputRead({
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
      await taskTrackingStop({
        path: {
          taskid: id,
        },
      });
      setTrigFetchTaskItems((prev) => prev + 1);
    }
  };

  const handleTaskDelete = async (id: string) => {
    if (window.confirm("정말로 작업을 삭제하시겠습니까?")) {
      await taskTrackingDelete({
        path: {
          taskid: id,
        },
      });
      setTrigFetchTaskItems((prev) => prev + 1);
    }
  };

  return (
    <section>
      <h2 className="titlebox mb-4">CCTV 영상 차량 추적하기</h2>
      <p className="descbox my-4">
        녹화된 CCTV 영상 파일을 선택한 후 YOLOv8 + DeepSORT 기반 차량 추적을
        진행할 수 있습니다.
      </p>
      <div className="my-4 grid grid-cols-1 gap-2 md:grid-cols-2 md:gap-8">
        <div>
          <div className="text-lg font-medium mb-2">
            CCTV 영상 녹화본 파일 이름
          </div>
          <div>
            <input
              type="text"
              className="inputbox"
              value={targetname}
              onChange={(e) => setTargetName(e.target.value)}
            />
          </div>
        </div>
        <div>
          <div className="text-lg font-medium mb-2">신뢰도 임계값</div>
          <div>
            <input
              type="number"
              className="inputbox"
              min={0.0}
              max={1.0}
              step={0.01}
              value={confidence}
              onChange={(e) => setConfidence(Number(e.target.value))}
            />
          </div>
        </div>
      </div>
      <div className="text-right">
        <button className="btn-base btn-dark" onClick={() => handleTaskStart()}>
          추적 시작하기
        </button>
      </div>
      <p className="descbox my-4">
        영상 차량 추적 작업 목록 및 결과는 아래에서 확인할 수 있습니다.
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

export default TrackPage;
