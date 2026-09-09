import { useState } from 'react';

export function CopyResponse({ response }: { response: string }) {
  const [status, setStatus] = useState<'idle' | 'copying' | 'copied' | 'failed'>('idle');
  async function copy() {
    if (status === 'copying') return;
    setStatus('copying');
    try {
      await navigator.clipboard.writeText(response);
      setStatus('copied');
    } catch {
      setStatus('failed');
    }
  }
  return <div className="copy-response">
    <button type="button" onClick={copy} disabled={status === 'copying'}>
      {status === 'copying' ? 'Copying…' : 'Copy approved response'}
    </button>
    <p role="status" className="muted">
      {status === 'copied' ? 'Approved response copied.' : status === 'failed'
        ? 'Could not copy. Select the response text above and copy it manually, or try again.' : ''}
    </p>
  </div>;
}
