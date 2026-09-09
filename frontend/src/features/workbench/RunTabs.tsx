import type { KeyboardEvent } from 'react';

export const runTabs = ['Response', 'Workflow', 'Sources', 'History'] as const;
export type RunTab = typeof runTabs[number];

export function RunTabs({ selected, onSelect }: { selected: RunTab; onSelect: (tab: RunTab) => void }) {
  function move(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const next = event.key === 'ArrowRight' ? (index + 1) % 4 : event.key === 'ArrowLeft' ? (index + 3) % 4 : event.key === 'Home' ? 0 : event.key === 'End' ? 3 : null;
    if (next === null) return;
    event.preventDefault(); onSelect(runTabs[next]);
    document.getElementById(`run-tab-${runTabs[next]}`)?.focus();
  }
  return <div className="run-tabs" role="tablist" aria-label="Message details">{runTabs.map((tab, index) => <button key={tab} id={`run-tab-${tab}`} role="tab"
    aria-selected={selected === tab} aria-controls={`run-panel-${tab}`} tabIndex={selected === tab ? 0 : -1}
    onClick={() => onSelect(tab)} onKeyDown={event => move(event, index)}>{tab}</button>)}</div>;
}
