import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../../api/client';

/** Poll one domain resource without overlapping requests or retaining a previous route's data. */
export function useResource<T>(path: string, interval = 0) {
  const [value, setValue] = useState<{ path: string; data: T } | null>(null);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision(x => x + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    setError('');
    async function fetchNext() {
      try {
        const data = await api<T>(path, { signal: controller.signal });
        if (!controller.signal.aborted) { setValue({ path, data }); setError(''); }
      } catch (err) {
        if (!controller.signal.aborted) {
          if (err instanceof ApiError && [401, 403, 404].includes(err.status)) setValue(null);
          setError((err as Error).message);
        }
      } finally {
        if (interval && !controller.signal.aborted) timer = setTimeout(fetchNext, interval);
      }
    }
    void fetchNext();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [path, interval, revision]);
  return { data: value?.path === path ? value.data : null, error, refresh };
}
