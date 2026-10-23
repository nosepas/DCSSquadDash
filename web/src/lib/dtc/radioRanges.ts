/** Documented band limits in MHz: plausibility hints only (NOT verified in the game), they never block anything. */
export type Band = 'UHF' | 'VHF' | 'FM' | 'HF';

export const BAND_RANGES: Record<Band, readonly [number, number]> = {
  UHF: [225, 399.975],
  VHF: [108, 174],
  FM: [30, 87.975],
  HF: [2, 29.999],
};

const F16 = 'F-16C_50';
const AH64 = 'AH-64D_BLK_II';

/** Band of a radio: F-16 COMM1/COMM2, AH-64 FM1/FM2/UHF/VHF/HF(_RX/_TX). Unknown = no check. */
export function bandOf(aircraft: string, radioId: string): Band | null {
  if (aircraft === F16) return radioId === 'COMM1' ? 'UHF' : radioId === 'COMM2' ? 'VHF' : null;
  if (aircraft !== AH64) return null;
  if (radioId === 'FM1' || radioId === 'FM2') return 'FM';
  if (radioId === 'UHF' || radioId === 'VHF') return radioId;
  return radioId.startsWith('HF') ? 'HF' : null;
}

export function isOutOfRange(aircraft: string, radioId: string, mhz: number): boolean {
  const band = bandOf(aircraft, radioId);
  if (!band) return false;
  const [lo, hi] = BAND_RANGES[band];
  return mhz < lo || mhz > hi;
}

/** The F-16 sample only has whole-MHz channels: fractional values are not confirmed to work in DCS. */
export const isUnconfirmedFraction = (aircraft: string, mhz: number): boolean => aircraft === F16 && !Number.isInteger(mhz);
