import { useCallback, useState } from 'react';

/** Which radio inputs hold unparsable text right now; the download is held back while any does. */
export function useInvalidInputs() {
  const [ids, setIds] = useState<readonly string[]>([]);
  const report = useCallback((id: string, invalid: boolean) => {
    setIds((cur) => {
      if (invalid) return cur.includes(id) ? cur : [...cur, id];
      return cur.includes(id) ? cur.filter((x) => x !== id) : cur;
    });
  }, []);
  return { count: ids.length, report };
}
