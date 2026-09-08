import { useEffect, useState } from "react";
import { errorMessage } from "../api";
import type { Page, Trace } from "../work/api";
import type { RecordsApi, RecordDetail, RecordSummary } from "./api";

export function useRecords(api: RecordsApi, search: string, status: string, offset: number, revision: number) {
  const [page, setPage] = useState<Page<RecordSummary> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let current = true; let timer: ReturnType<typeof setTimeout>;
    setPage(null); setError("");
    async function load() {
      try {
        const result = await api.list(search, status, offset);
        if (!current) return;
        setPage(result); setError("");
        timer = setTimeout(load, 5000);
      } catch (error) { if (current) setError(errorMessage(error)); }
    }
    void load();
    return () => { current = false; clearTimeout(timer); };
  }, [api, search, status, offset, revision]);
  return { page, error };
}

export function useRecordDetail(api: RecordsApi, id: string, revision: number, runId = "") {
  const [record, setRecord] = useState<RecordDetail | null>(null);
  const [trace, setTrace] = useState<Trace | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let current = true; let timer: ReturnType<typeof setTimeout>;
    setRecord(null); setTrace(null); setError("");
    async function load() {
      try {
        const detail = await api.detail(id);
        const result = await api.trace(runId || detail.latest_run_id);
        if (!current) return;
        setRecord(detail); setTrace(result); setError("");
        timer = setTimeout(load, 3000);
      } catch (error) { if (current) setError(errorMessage(error)); }
    }
    void load();
    return () => { current = false; clearTimeout(timer); };
  }, [api, id, revision, runId]);
  return { record, trace, error };
}
