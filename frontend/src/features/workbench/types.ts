import type { components } from '../../api/schema';

export type Run = components['schemas']['RunDetail'];
export type MessagePage = components['schemas']['MessagePage'];
export type Created = components['schemas']['MessageCreated'];
export type Handoff = components['schemas']['HandoffExport'];
export type Citation = components['schemas']['CitedPassage'];

export const stateLabel = (state: string) => ({
  queued: 'Queued', processing: 'Processing', waiting_development: 'Waiting for development response',
  draft: 'Draft ready', clarification: 'Clarification needed', insufficient_evidence: 'No supporting knowledge',
  failed: 'Processing failed', cancelled: 'Cancelled',
}[state] ?? state);

export const active = (state: string) => ['queued', 'processing', 'waiting_development'].includes(state);
export const languageLabel = (language: string) => ({ en: 'English', ja: '日本語', zh: '中文' }[language] ?? language);
export const duration = (ms: number | null | undefined) => ms == null ? 'Not recorded' : `${(ms / 1000).toFixed(2)} s`;
