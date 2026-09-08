import { useEffect, useRef, useState } from "react";
import { errorMessage } from "../api";
import type { TaskRun, Trace, WorkApi } from "./api";

export const activeRun = (status: string) => ["queued", "running", "stopping"].includes(status);

export function useRunTrace(api: WorkApi, id: string, revision: number, onSettled: () => void) {
  const [trace, setTrace] = useState<Trace | null>(null);
  const [taskInfo, setTaskInfo] = useState<TaskRun | null>(null);
  const [error, setError] = useState("");
  const previousStatus = useRef("");
  const callback = useRef(onSettled); callback.current = onSettled;
  useEffect(() => {
    let current = true; let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const [result, task] = await Promise.all([api.trace(id), api.taskRun(id)]);
        if (!current) return;
        setTrace(result); setTaskInfo(task); setError("");
        const changed = previousStatus.current !== result.run.status;
        previousStatus.current = result.run.status;
        if (activeRun(result.run.status)) timer = setTimeout(refresh, 1000);
        if (changed) callback.current();
      } catch (error) {
        if (current) { setError(errorMessage(error)); timer = setTimeout(refresh, 3000); }
      }
    }
    void refresh();
    return () => { current = false; clearTimeout(timer); };
  }, [api, id, revision]);
  return { trace, taskId: taskInfo?.task_id ?? null, taskInfo, error };
}
