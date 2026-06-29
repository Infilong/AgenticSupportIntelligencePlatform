import { ReactNode } from "react";

export type PrimitiveTone = "neutral" | "good" | "warn" | "bad";

export function Badge({ tone = "neutral", children }: { tone?: PrimitiveTone; children: ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function Metric({ label, value }: { label: string; value: string | number }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="empty"><strong>{title}</strong><span>{detail}</span></div>;
}
