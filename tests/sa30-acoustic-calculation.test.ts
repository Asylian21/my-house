import { describe, expect, it } from 'vitest';
import { ACOUSTIC_WALL_SPECS } from '../lib/acoustic-walls';
import { massAirMassResonanceHz, separatedMasonryScenarioDb, SA30_ACOUSTIC_CALCULATION } from '../lib/archive/sa30-acoustic-calculation';

describe('Archived SA30 preliminary acoustic calculation', () => {
  it('counts one room-side plaster per leaf and keeps the 100 mm cavity', () => {
    expect(SA30_ACOUSTIC_CALCULATION.masonryMassKgM2).toBe(73);
    expect(SA30_ACOUSTIC_CALCULATION.plasterMassKgM2).toBe(27);
    expect(SA30_ACOUSTIC_CALCULATION.leafMassKgM2).toBe(100);
    expect(SA30_ACOUSTIC_CALCULATION.totalMassKgM2).toBe(200);
    expect(SA30_ACOUSTIC_CALCULATION.finishedLayers.map(layer=>layer.thicknessMm)).toEqual([15,100,100,100,15]);
    expect(SA30_ACOUSTIC_CALCULATION.finishedTotalMm).toBe(330);
    expect(SA30_ACOUSTIC_CALCULATION.resonanceHz).toBeCloseTo(23.839, 2);
    expect(SA30_ACOUSTIC_CALCULATION.cavityMm).toBe(100);
    expect(SA30_ACOUSTIC_CALCULATION).not.toHaveProperty('estimatedRwDb');
    expect(SA30_ACOUSTIC_CALCULATION).not.toHaveProperty('declaredRwDb');
    expect(ACOUSTIC_WALL_SPECS.some(wall=>String(wall.assembly.code)==='SA30')).toBe(false);
    expect(SA30_ACOUSTIC_CALCULATION.status).toBe('ARCHIVED_SUPERSEDED_20260916');
  });

  it('reproduces the masonry mass relation and declares the separation and flanking assumptions', () => {
    // Published example: a 480 kg/m² pair has a 57.1 dB equivalent mass rating.
    expect(separatedMasonryScenarioDb(240,240,50).equivalentMassDb).toBeCloseTo(57.0748,3);
    expect(SA30_ACOUSTIC_CALCULATION.scenario.equivalentMassDb).toBeCloseTo(46.42884,4);
    expect(SA30_ACOUSTIC_CALCULATION.scenario.separationBonusDb).toBe(12);
    expect(SA30_ACOUSTIC_CALCULATION.scenario.flankingCorrectionDb).toBe(0);
    expect(SA30_ACOUSTIC_CALCULATION.scenario.apparentRatingDb).toBeCloseTo(58.42884,4);
    expect(SA30_ACOUSTIC_CALCULATION.ratingLabel).toContain('R′w,model ≈ 58 dB');
    expect(separatedMasonryScenarioDb(100,120,100)).toEqual(separatedMasonryScenarioDb(120,100,100));
  });

  it('does not extend the masonry scenario to underweight leaves or unqualified gaps', () => {
    for(const masses of [[73,100,100],[100,92.5,100],[100,100,30],[NaN,100,100],[100,Infinity,100],[100,100,Infinity]]) {
      expect(()=>separatedMasonryScenarioDb(masses[0],masses[1],masses[2])).toThrow(RangeError);
    }
  });

  it('is symmetric and lowers resonance when leaf mass or cavity depth increases', () => {
    const baseline=massAirMassResonanceHz(73,100,0.1);
    expect(massAirMassResonanceHz(100,73,0.1)).toBe(baseline);
    expect(massAirMassResonanceHz(146,200,0.1)).toBeCloseTo(baseline/Math.sqrt(2),8);
    expect(massAirMassResonanceHz(73,100,0.2)).toBeCloseTo(baseline/Math.sqrt(2),8);
  });

  it('rejects missing or nonphysical inputs instead of reporting a misleading number', () => {
    for (const value of [0,-1,NaN,Infinity]) {
      expect(()=>massAirMassResonanceHz(value,73,0.1)).toThrow(RangeError);
      expect(()=>massAirMassResonanceHz(73,value,0.1)).toThrow(RangeError);
      expect(()=>massAirMassResonanceHz(73,73,value)).toThrow(RangeError);
    }
  });
});
