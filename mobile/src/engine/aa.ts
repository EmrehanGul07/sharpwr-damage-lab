import type { Database } from "../data";
import type { BuildInput } from "./build";
import { AttackKernel, type Target } from "./attacks";
/** Python's decimal rounding uses the exact binary float and ties to even. */
export function pythonRound(value: number, digits: number): number {
  if (!Number.isFinite(value) || value === 0) return value;
  const buffer = new DataView(new ArrayBuffer(8));
  buffer.setFloat64(0, Math.abs(value));
  const bits = buffer.getBigUint64(0),
    exponent = Number((bits >> 52n) & 2047n);
  const mantissa = (bits & ((1n << 52n) - 1n)) + (exponent ? 1n << 52n : 0n);
  const shift = (exponent || 1) - 1023 - 52;
  const scale = 10n ** BigInt(digits);
  const numerator = mantissa * scale * (shift > 0 ? 1n << BigInt(shift) : 1n);
  const denominator = shift < 0 ? 1n << BigInt(-shift) : 1n;
  let rounded = numerator / denominator;
  const remainder = numerator % denominator;
  if (
    remainder * 2n > denominator ||
    (remainder * 2n === denominator && rounded % 2n !== 0n)
  )
    rounded++;
  return (Math.sign(value) * Number(rounded)) / Number(scale);
}
/** Python sim_build's AA-only benchmark: duration includes the final attack cycle. No champion abilities/runes. */
export function simulateAa(db: Database, build: BuildInput, target: Target) {
  const kernel = new AttackKernel(db, { ...build, runes: false }, target, {
    energized: true,
  });
  let health = target.health,
    time = 0,
    damage = 0,
    attacks = 0;
  while (health > 0 && attacks < 500) {
    const hit = kernel.hit({ health, time });
    health -= hit.damage;
    if (
      build.items.includes("The Collector") &&
      health > 0 &&
      health <= target.health * 0.05
    )
      health = 0;
    // sim_build calculates DPS from rounded per-hit log damage.
    damage += pythonRound(hit.damage, 1);
    attacks++;
    time += 1 / hit.attackSpeed;
  }
  return {
    ttk: health <= 0 ? pythonRound(time, 3) : null,
    dps: pythonRound(damage / time, 1),
    attacks,
    damage,
    health: Math.max(0, health),
  };
}
