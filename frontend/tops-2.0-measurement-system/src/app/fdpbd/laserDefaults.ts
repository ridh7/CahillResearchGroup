// Instrument-specific leaking-correction constants for the FD-PBD UI.
// Edit these values here when the optics/electronics calibration changes —
// they are intentionally not editable from the UI.

export type LaserOption = 'TOPS 1' | 'TOPS 2';

export type LeakingDefaults = {
  amplitude_corrected_0: string;
  amplitude_corrected_1: string;
  amplitude_corrected_2: string;
  amplitude_corrected_3: string;
  delay_0: string;
  delay_1: string;
  delay_2: string;
};

export const TOPS1_DEFAULTS: LeakingDefaults = {
  amplitude_corrected_0: '9.61e-1',
  amplitude_corrected_1: '9.06e-4',
  amplitude_corrected_2: '-5.66e-6',
  amplitude_corrected_3: '9.6e-9',
  delay_0: '8.96e-3',
  delay_1: '-1.17e-5',
  delay_2: '2.81e-11',
};

export const TOPS2_DEFAULTS: LeakingDefaults = {
  amplitude_corrected_0: '1',
  amplitude_corrected_1: '1.50e-4',
  amplitude_corrected_2: '1.18e-6',
  amplitude_corrected_3: '-6.08e-9',
  delay_0: '5.08e-3',
  delay_1: '-1.10e-5',
  delay_2: '7.33e-12',
};

// Path shown in the UI tooltip so users know where to edit these values.
export const LASER_DEFAULTS_PATH =
  'frontend/tops-2.0-measurement-system/src/app/fdpbd/laserDefaults.ts';
