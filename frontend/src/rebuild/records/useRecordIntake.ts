import { useEffect, useRef, useState } from "react";
import { errorMessage } from "../api";
import type { Agent, WorkApi } from "../work/api";
import type { RecordsApi, RecordSubmission } from "./api";

export function useRecordIntake(api: RecordsApi, actions: WorkApi, onCreated: (id: string) => void) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [offset, setOffset] = useState(0); const [more, setMore] = useState(false);
  const [agent, setAgent] = useState(""); const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0); const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const alive = useRef(true);
  const submission = useRef<{ serialized: string; key: string } | null>(null);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  useEffect(() => {
    let active = true; setLoading(true); setError(""); setAgent(""); setAgents([]);
    actions.agents(offset).then(page => {
      if (!active) return;
      const available = page.items.filter(item => item.active && !item.archived_at);
      setAgents(available); setAgent(available[0]?.id ?? ""); setMore(page.has_next);
    }).catch(error => { if (active) setError(errorMessage(error)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [actions, offset, revision]);
  async function submit(format: "text" | "json", raw: string, reference: string, language: "en" | "ja" | "zh" | "") {
    if (busy || !agent) return;
    setError("");
    let content: string | object = raw;
    try {
      if (!raw.trim()) throw new Error("Enter data to process.");
      if (format === "json") {
        try { content = JSON.parse(raw); } catch { throw new Error("Enter valid JSON, using an object or array."); }
        if (!content || typeof content !== "object" || Object.keys(content).length === 0)
          throw new Error("JSON must be a nonempty object or array.");
      }
      const body: RecordSubmission = { agent_id: agent, language: language || null,
        input: { format, content, source: "admin", source_reference: reference.trim() || null } };
      const serialized = JSON.stringify(body);
      if (submission.current?.serialized !== serialized) submission.current = { serialized, key: crypto.randomUUID() };
      setBusy(true);
      const record = await api.create(body, submission.current.key);
      if (alive.current) onCreated(record.id);
    } catch (error) { if (alive.current) setError(errorMessage(error)); }
    finally { if (alive.current) setBusy(false); }
  }
  return { agents, agent, setAgent, offset, setOffset, more, loading, error, busy, submit,
    reload: () => setRevision(value => value + 1) };
}
