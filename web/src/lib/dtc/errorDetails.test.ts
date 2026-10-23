import { describe, expect, it } from 'vitest';
import { detailTexts, mapDetails } from './errorDetails';
import { ah64Model, f14Model, f16Model } from './fixtures';

describe('mapDetails', () => {
  it('ties library messages to the point they mention', () => {
    const [a, b] = mapDetails(['waypoints[1]: lat 95 outside [-90, 90]', 'lines[1].points[0]: lon is required'], f16Model());
    expect(a).toMatchObject({ pointId: 'b', ref: { type: 'waypoints' } });
    expect(b).toMatchObject({ pointId: 'l1', ref: { type: 'line', index: 1 } });
  });

  it('understands routes and the contract validator slash paths', () => {
    expect(mapDetails(['routes[1].points[1]: bad'], f14Model())[0]).toMatchObject({ pointId: 'r2', ref: { type: 'route', index: 1 } });
    expect(mapDetails(['waypoints/0/lat: 95 is greater than the maximum of 90'], f16Model())[0]?.pointId).toBe('a');
  });

  it('finds the AH-64 group of a flat waypoint index', () => {
    expect(mapDetails(['waypoints[3]: x'], ah64Model())[0]).toMatchObject({ pointId: 't3', ref: { type: 'ah64', mission: 2, kind: 'TGT' } });
  });

  it('keeps messages that mention no point and survives odd input', () => {
    const msg = 'F-16C_50 allows at most 25 steerpoints; got 26';
    expect(mapDetails([msg], f16Model())).toEqual([{ message: msg }]);
    expect(mapDetails(['waypoints[99]: nope'], f16Model())[0]?.pointId).toBeUndefined();
    expect(mapDetails(undefined, f16Model())).toEqual([]);
  });

  it('flattens FastAPI style objects and single values', () => {
    expect(detailTexts([{ loc: ['body', 'model'], msg: 'field required' }, 'plain'])).toEqual(['body.model: field required', 'plain']);
    expect(detailTexts('one')).toEqual(['one']);
  });
});
