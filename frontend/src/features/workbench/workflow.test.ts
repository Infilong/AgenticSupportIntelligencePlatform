import { expect, test } from 'vitest';
import { nodeState } from './workflow';
import type { Run } from './types';

function run(state: string, steps: object[] = [], extra = {}) { return { state, steps, ...extra } as Run; }
test('latest chronological record wins even when a new job restarts its attempt counter', () => {
  const result = nodeState(run('awaiting_review', [
    { node: 'human_review', status: 'failed', job_attempt: 3 },
    { node: 'human_review', status: 'waiting', job_attempt: 1 },
  ]), 'human_review');
  expect(result.label).toBe('Paused'); expect(result.records).toHaveLength(2);
});
test.each(['failed', 'cancelled', 'rejected', 'completed'])('terminal %s does not show an orphaned start as running', state => {
  expect(nodeState(run(state, [{ node: 'retrieve_evidence', status: 'started' }]), 'retrieve_evidence').label).toBe('Unfinished record');
  expect(nodeState(run(state, [{ node: 'development_generation', status: 'waiting' }]), 'development_generation').label).toBe('Paused before stop');
});
test('only known branches are skipped; failures and unknown execution are not successful', () => {
  expect(nodeState(run('completed', [], { outcome: 'clarification_needed' }), 'retrieve_evidence').label).toBe('Skipped by outcome');
  expect(nodeState(run('completed', [], { outcome: 'insufficient_evidence' }), 'human_review').label).toBe('Skipped by outcome');
  expect(nodeState(run('failed'), 'human_review').label).toBe('Not reached');
  expect(nodeState(run('queued'), 'human_review').label).toBe('Pending');
  expect(nodeState(run('failed', [{ node: 'human_review', status: 'uncertain' }]), 'human_review').label).toBe('Outcome uncertain');
});
