import { describe, expect, it } from 'vitest';
import { calculateH200Acoustics, H200_ACOUSTIC_CALCULATION } from '../lib/h200-acoustic-calculation';
import { OFFICE_ACOUSTIC_ASSEMBLY } from '../lib/acoustic-walls';
import report from '../lib/h200-research.json';
import junction from '../lib/h200-junction.json';
import { INTERIOR_WALLS } from '../lib/twin-interior';

describe('H200 single-board revision', () => {
  it('reproduces the independent 45 mm lining calculation without claiming a measured rating', () => {
    const result = H200_ACOUSTIC_CALCULATION;
    expect(result.baseMassKgM2).toBe(127);
    expect(result.liningMassKgM2).toBe(17.5);
    expect(result.resonanceHz).toBeCloseTo(64.074946743, 8);
    expect(result.improvementDb).toBeCloseTo(20.766234922, 8);
    expect(result.estimatedRwDb).toBeCloseTo(55.766234922, 8);
    expect(result.evidence).toBe('PRELIMINARY_MODEL_NOT_MEASURED');
    expect(OFFICE_ACOUSTIC_ASSEMBLY.estimatedRwDb).toBe(56);
    expect(OFFICE_ACOUSTIC_ASSEMBLY.layers.reduce((sum, layer) => sum + layer.thicknessMm, 0)).toBe(187.5);
    expect(report.sections.find(s => s.id === 'vypocet')!.equations!.at(-1)).toContain('55,76623');
  });

  it('compares the same model with R2 and checks sensitivity without treating it as an uncertainty bound', () => {
    const old = calculateH200Acoustics(2);
    expect(old.resonanceHz).toBeCloseTo(47.972995778, 8);
    expect(old.calculationResonanceHz).toBe(50);
    expect(old.estimatedRwDb - H200_ACOUSTIC_CALCULATION.estimatedRwDb).toBeCloseTo(2.154364991, 8);
    const light = calculateH200Acoustics(1, 1300);
    expect(light.resonanceHz).toBeGreaterThan(H200_ACOUSTIC_CALCULATION.resonanceHz);
    expect(light.estimatedRwDb).toBeCloseTo(55.70, 2);
  });

  it('keeps the documented joints on the real single-board edge and leaves the door support intact', () => {
    const wall = INTERIOR_WALLS.find(w => w.id === 'IW-STUDY-NORTH')!.rectMm;
    const nib = INTERIOR_WALLS.find(w => w.id === 'C-OFFICE-NORTH-JAMB')!.rectMm;
    expect(junction.joints.J1.y0).toBe(wall.y0);
    expect(junction.joints.J1.y1 - junction.joints.J1.y0).toBe(12.5);
    expect(junction.joints.J1.x1 - junction.joints.J1.x0).toBe(5);
    expect(junction.joints.J2.y1).toBe(wall.y0);
    expect(junction.joints.J2.y1 - junction.joints.J2.y0).toBe(5);
    expect(junction.joints.J2.y0 - nib.y0).toBe(37.5);
  });
});
