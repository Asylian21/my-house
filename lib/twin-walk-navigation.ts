/** Deliberate, short walks for a house tour, with no continuous autorun. */
export const EASY_WALK = Object.freeze({
  turnRadiansPerSecond: 1.15,
  arrivalM: 0.16,
  slowDownM: 0.7,
  maxDestinationM: 10,
  stalledSeconds: 0.65,
  maxTripSeconds: 20,
});

export type WalkTurn = 'left' | 'right';
export type WalkTravelStatus = 'idle' | 'walking' | 'arrived' | 'blocked';
type Point = { readonly x: number; readonly z: number };

export function turnWalkHeading(yaw: number, direction: number, deltaMs: number) {
  const seconds = Math.max(0, Math.min(50, Number.isFinite(deltaMs) ? deltaMs : 0)) / 1000;
  // Right-handed Y-up world: screen-right turns towards -X when looking +Z.
  return yaw - Math.sign(direction) * EASY_WALK.turnRadiansPerSecond * seconds;
}

export function easeWalkHeading(current: number, target: number, deltaMs: number) {
  const difference = Math.atan2(Math.sin(target-current), Math.cos(target-current));
  return current + difference * (1-Math.exp(-Math.max(0, Math.min(50, deltaMs))/180));
}

export class WalkDestination {
  target: Point | null = null;
  status: WalkTravelStatus = 'idle';
  private elapsedS = 0;
  private stalledS = 0;
  private last: Point | null = null;

  start(position: Point, target: Point) {
    this.cancel();
    const distance = Math.hypot(target.x-position.x, target.z-position.z);
    if (!Number.isFinite(distance) || distance > EASY_WALK.maxDestinationM || distance < EASY_WALK.arrivalM) return false;
    // Babylon vectors expose x/z as prototype accessors, not enumerable fields.
    this.target = {x:target.x,z:target.z};
    this.last = {x:position.x,z:position.z};
    this.status = 'walking';
    return true;
  }

  cancel(status: WalkTravelStatus = 'idle') {
    this.target = null;
    this.status = status;
    this.elapsedS = 0;
    this.stalledS = 0;
    this.last = null;
  }

  step(position: Point, deltaMs: number) {
    if (!this.target) return null;
    const seconds = Math.max(0, Math.min(50, deltaMs))/1000;
    this.elapsedS += seconds;
    const distance = Math.hypot(this.target.x-position.x, this.target.z-position.z);
    if (!Number.isFinite(distance)) { this.cancel('blocked'); return null; }
    if (distance <= EASY_WALK.arrivalM) { this.cancel('arrived'); return null; }
    const travelled = this.last ? Math.hypot(position.x-this.last.x, position.z-this.last.z) : 0;
    this.last = {x:position.x,z:position.z};
    // Ignore initial acceleration / camera alignment. Measure speed, not per-frame pixels.
    this.stalledS = this.elapsedS > 0.8 && travelled < seconds*0.06 ? this.stalledS+seconds : 0;
    if (this.stalledS > EASY_WALK.stalledSeconds || this.elapsedS > EASY_WALK.maxTripSeconds) {
      this.cancel('blocked'); return null;
    }
    return {heading:{x:(this.target.x-position.x)/distance,z:(this.target.z-position.z)/distance}, precision:distance<EASY_WALK.slowDownM};
  }
}
