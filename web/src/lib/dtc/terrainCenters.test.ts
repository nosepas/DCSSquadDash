import { describe, expect, it } from 'vitest';
import { TERRAIN_VIEWS, viewForTerrain, WORLD_VIEW } from './terrainCenters';

const IDS = ['Caucasus', 'Syria', 'Nevada', 'PersianGulf', 'MarianaIslands', 'Sinai', 'Falklands', 'Normandy', 'TheChannel', 'GermanyCW', 'Kola'];

describe('terrain views', () => {
  it('has a sane default centre for each of the 11 maps', () => {
    expect(Object.keys(TERRAIN_VIEWS).sort()).toEqual([...IDS].sort());
    for (const v of Object.values(TERRAIN_VIEWS)) {
      expect(Math.abs(v.lat)).toBeLessThanOrEqual(90);
      expect(Math.abs(v.lon)).toBeLessThanOrEqual(180);
      expect(v.zoom).toBeGreaterThanOrEqual(3);
    }
  });

  it('puts well-known maps in the right hemisphere and falls back to the world', () => {
    expect(viewForTerrain('Falklands').lat).toBeLessThan(0);
    expect(viewForTerrain('Nevada').lon).toBeLessThan(0);
    expect(viewForTerrain('Syria').lon).toBeGreaterThan(30);
    expect(viewForTerrain('Atlantis')).toBe(WORLD_VIEW);
    expect(viewForTerrain(null)).toBe(WORLD_VIEW);
  });
});
