import { useCallback, useState } from 'react';
import { loadLayerPrefs, saveLayerPrefs, type LayerPrefs } from '../../../lib/dtc/layerPrefs';

/** Which reference layers are on; remembered per viewer in localStorage. */
export function useLayerPrefs() {
  const [prefs, setPrefs] = useState<LayerPrefs>(loadLayerPrefs);
  const toggle = useCallback((key: keyof LayerPrefs) => {
    setPrefs((p) => {
      const next = { ...p, [key]: !p[key] };
      saveLayerPrefs(next);
      return next;
    });
  }, []);
  return { prefs, toggle };
}
