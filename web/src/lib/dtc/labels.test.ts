import { describe, expect, it } from 'vitest';
import { labelCandidates, labelsVisible, LABEL_MIN_ZOOM } from './labels';

const box = { south: 0, west: 0, north: 10, east: 10 };
const at = (n: number, lat = 5, lon = 5) => ({ n, lat, lon });

describe('airfield labels', () => {
  it('only shows names from the threshold zoom', () => {
    expect(labelsVisible(LABEL_MIN_ZOOM - 1)).toBe(false);
    expect(labelsVisible(LABEL_MIN_ZOOM)).toBe(true);
  });

  it('gives no labels when zoomed out', () => {
    expect(labelCandidates([at(1)], box, LABEL_MIN_ZOOM - 1)).toEqual([]);
  });

  it('keeps only places inside the view', () => {
    const items = [at(1), at(2, 20, 5), at(3, 5, -1), at(4, 10, 10)];
    expect(labelCandidates(items, box, 9).map((i) => i.n)).toEqual([1, 4]);
  });

  it('caps the number of labels', () => {
    const items = Array.from({ length: 300 }, (_, i) => at(i));
    expect(labelCandidates(items, box, 9)).toHaveLength(60);
    expect(labelCandidates(items, box, 9, 5)).toHaveLength(5);
  });
});
