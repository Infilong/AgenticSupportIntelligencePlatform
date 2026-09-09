import type { components } from '../../api/schema';

export type Run = components['schemas']['RunDetail'];
export type MessagePage = components['schemas']['MessagePage'];
export type Created = components['schemas']['MessageCreated'];
export type Handoff = components['schemas']['HandoffExport'];
export type Citation = components['schemas']['CitedPassage'];

export const stateLabel = (state: string) => ({
  not_processed: 'Not processed', queued: 'Queued', running: 'Processing', waiting_for_input: 'Waiting for development response',
  awaiting_review: 'Needs review', completed: 'Completed', rejected: 'Rejected',
  failed: 'Processing failed', cancelled: 'Cancelled',
}[state] ?? state);

export const outcomeLabel = (outcome: string | null) => ({
  grounded_draft: 'Response draft', policy_review_required: 'Policy exception review',
  conflicting_evidence: 'Conflicting evidence', clarification_needed: 'Clarification needed',
  insufficient_evidence: 'No supporting knowledge', approved_response: 'Approved response', rejected_response: 'Response rejected',
}[outcome ?? ''] ?? 'Next step');

export const active = (state: string) => ['queued', 'running', 'waiting_for_input', 'awaiting_review'].includes(state);
export const languageLabel = (language: string) => ({ en: 'English', ja: '日本語', zh: '中文' }[language] ?? language);
export const duration = (ms: number | null | undefined) => ms == null ? 'Not recorded' : `${(ms / 1000).toFixed(2)} s`;
