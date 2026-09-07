import {describe,expect,it} from 'vitest';
import {WalkDestination,turnWalkHeading,easeWalkHeading} from '../lib/twin-walk-navigation';

describe('simple house navigation',()=>{
  it('rejects invalid/remote targets, slows near destination and finishes without overshoot',()=>{
    const trip=new WalkDestination();
    expect(trip.start({x:0,z:0},{x:NaN,z:1})).toBe(false);
    expect(trip.start({x:0,z:0},{x:50,z:1})).toBe(false);
    expect(trip.start({x:0,z:0},{x:0,z:2})).toBe(true);
    expect(trip.step({x:0,z:1.5},16)?.precision).toBe(true);
    expect(trip.step({x:0,z:1.9},16)).toBeNull();
    expect(trip.status).toBe('arrived');
  });
  it.each([30,60,144,240])('stops at a wall without endless walking at %i FPS',fps=>{
    const trip=new WalkDestination();trip.start({x:0,z:0},{x:3,z:0});
    for(let i=0;i<fps*2;i++)trip.step({x:0,z:0},1000/fps);
    expect(trip.status).toBe('blocked');expect(trip.target).toBeNull();
  });
  it('manual cancellation forgets old targets',()=>{
    const trip=new WalkDestination();trip.start({x:0,z:0},{x:3,z:0});trip.cancel();
    expect(trip.step({x:0,z:0},16)).toBeNull();expect(trip.status).toBe('idle');
  });
  it('turns at the same speed at every refresh rate and takes the short turn across north',()=>{
    for(const fps of [30,60,144,240]){
      let yaw=0;for(let i=0;i<fps;i++)yaw=turnWalkHeading(yaw,1,1000/fps);
      expect(yaw).toBeCloseTo(-1.15,6);
    }
    expect(easeWalkHeading(Math.PI-0.1,-Math.PI+0.1,16)).toBeGreaterThan(Math.PI-0.1);
  });
});
