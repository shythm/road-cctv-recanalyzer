import { useState, useEffect } from "react";

import {
  streamReadAll,
  taskRecordReadAll,
  taskRecordStart,
  CCTVStream,
  TaskItem,
} from "../client";

function RecordPage() {
  const [cctvstreams, setCCTVStreams] = useState<CCTVStream[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);

  const [selected, setSelected] = useState<string>("");
  const [startat, setStartAt] = useState<string>("");
  const [endat, setEndAt] = useState<string>("");

  useEffect(() => {
    streamReadAll().then((streams) => {
      if (streams.data) {
        setCCTVStreams(streams.data);
      }
    });
  }, []);

  useEffect(() => {
    const polling = setInterval(() => {
      taskRecordReadAll().then((tasks) => {
        if (tasks.data) {
          setTasks(tasks.data);
        }
      });
    }, 2000);

    return () => {
      clearInterval(polling);
    };
  }, []);

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
        <button
          className="btn-normal"
          onClick={() => {
            if (selected && startat && endat) {
              taskRecordStart({
                query: {
                  cctv: selected,
                  startat,
                  endat,
                },
              }).then(() => {
                window.alert(`${selected} 녹화 작업이 시작되었습니다.`);
              });
            }
          }}
        >
          녹화 시작하기
        </button>
      </div>
      <p className="descbox my-4">
        녹화 작업 목록은 아래에서 확인할 수 있습니다.
      </p>
      <div>
        {tasks.map((task) => (
          <div key={task.id} className="mb-8">
            <div className="font-medium">{task.id}</div>
            <div>작업 제출 날짜: {task.createdat}</div>
            <div>입력: {JSON.stringify(task.params)}</div>
            <div>
              상태: {task.state} / {task.reason}
            </div>
            <div>진행률: {task.progress}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default RecordPage;
