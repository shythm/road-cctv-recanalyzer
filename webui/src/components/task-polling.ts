import { useState, useEffect } from "react";

import { TaskItem, TaskState } from "../models";

const useTaskPolling = (
  handleUpdate: () => Promise<TaskItem[]>,
  interval: number = 2000
) => {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [, setTrigger] = useState<number>(0);

  const polling = tasks.some(
    (task) =>
      task.state === TaskState.PENDING || task.state === TaskState.STARTED
  );

  useEffect(() => {
    const fetchTaskItems = async () => {
      const tasks = await handleUpdate();
      setTasks(tasks);
    };
    fetchTaskItems();

    // polling every interval if there are PENDING or STARTED tasks
    if (polling) {
      const intervalId = setInterval(fetchTaskItems, interval);
      return () => clearInterval(intervalId);
    }
  }, [handleUpdate, polling, interval]);

  const pollTasks = () => setTrigger((prev) => prev + 1);

  return { tasks, pollTasks };
};

export default useTaskPolling;
