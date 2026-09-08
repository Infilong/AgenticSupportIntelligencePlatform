import type { components } from '../../api/schema';

export type DocumentPage = components['schemas']['DocumentPage'];
export type DocumentDetail = components['schemas']['DocumentDetail'];
export type UploadResult = components['schemas']['UploadResult'];
export type SourcePreview = components['schemas']['SourcePreview'];
export type RetrievalResult = components['schemas']['RetrievalResult'];

export function documentState(document: DocumentDetail['document']) {
  if (document.withdrawn) return 'Withdrawn';
  if (document.job_status === 'queued' || document.job_status === 'running') return 'Indexing';
  if (document.job_status === 'failed') return document.active_version_id ? 'Replacement failed' : 'Indexing failed';
  if (document.active_version_id) return 'Ready';
  return document.job_status === 'cancelled' ? 'Cancelled' : 'Not indexed';
}
