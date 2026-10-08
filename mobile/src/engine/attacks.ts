/** Stateful port of sharpwr.aa_engine.combat_hits. Damage only: timing belongs to the fight scheduler. */
import type { Database, StatKey } from "../data";
import { buildProblems, type BuildInput } from "./build";
export interface Target {
  health: number;
  armor: number;
  magicResist: number;
  bonusHealth?: number;
  attackReduction?: number;
}
export interface AttackState {
  health: number;
  time: number;
  distance?: number;
  bonusAd?: number;
  bonusAs?: number;
  crit?: number;
  attackPhysical?: number;
  criticalPhysical?: number;
  nonbasicPhysical?: number;
  skillOnHit?: boolean;
  spellCastTimes?: number[];
  ultimateCastTime?: number;
  movementDistance?: number;
  attackId?: number;
  launch?: boolean;
  maxMana?: number;
  primaryExternalDamage?: number;
  onHitHealthMultiplier?: number;
}
export interface AttackHit {
  damage: number;
  attackSpeed: number;
  crit: number;
  armor: number;
  magicResist: number;
  physical: number;
  magic: number;
  trueDamage: number;
  physicalDamage: number;
  magicDamage: number;
  notes: string[];
  stacks: Record<string, number>;
  energizedReserved?: boolean;
}
export interface AttackOptions {
  energized?: boolean;
  spellblade?: boolean;
  itemProcs?: boolean;
  initialFlurry?: boolean;
  activeReady?: boolean;
}
export const resistanceMultiplier = (x: number) =>
  x >= 0 ? 100 / (100 + x) : 2 - 100 / (100 - x);
export const effectiveResistance = (
  value: number,
  pct = 0,
  flat = 0,
  cap = 1,
) =>
  value < 0
    ? value
    : Math.max(
        0,
        value * (1 - Math.min(cap, Math.max(0, pct))) - Math.max(0, flat),
      );
const growth = (level: number) => (level - 1) * (0.7025 + 0.0175 * (level - 1));
export class AttackKernel {
  private total: (key: StatKey) => number;
  private has: (name: string) => boolean;
  private baseAd: number;
  private ad: number;
  private mana: number;
  private baseAs: number;
  private ratio: number;
  private naturalBonusAs: number;
  private rage = 0;
  private dancer = 0;
  private light = 0;
  private dark = 0;
  private rageHits = 0;
  private kraken = 0;
  private terminusHits = 0;
  private yuntalCrit: number;
  private yuntalUntil = -1;
  private yuntalCd = 0;
  private spellReady = 0;
  private spellPending: boolean;
  private duskReady = 0;
  private galeReady = 0;
  private fiend = 0;
  private fiendUntil = 8;
  private lastUlt: number | undefined;
  private charge: number;
  private path = 0;
  private launches = new Set<number>();
  private attacks = new Set<number>();
  private pending = new Set<number>();
  private count = 0;
  private lastTime = -1;
  constructor(
    private db: Database,
    private input: BuildInput,
    private target: Target,
    private options: AttackOptions = {},
  ) {
    const problems = buildProblems(db, input.items, input.boots);
    if (problems.length) throw Error(problems.join(" "));
    const champion = db.champions.find((c) => c.name === input.champion);
    if (!champion?.aa) throw Error("Unknown champion");
    if (
      !Number.isInteger(input.level) ||
      input.level < 1 ||
      input.level > 15 ||
      !Number.isFinite(target.health) ||
      target.health <= 0
    )
      throw Error("Invalid fight input");
    for (const n of [
      target.armor,
      target.magicResist,
      target.bonusHealth ?? 0,
      target.attackReduction ?? 0,
    ])
      if (!Number.isFinite(n)) throw Error("Invalid target");
    const records = input.items.map(
      (name) => db.items.find((i) => i.name === name)!,
    );
    if (input.boots)
      records.push(db.boots.find((i) => i.name === input.boots)!);
    this.total = (key) =>
      records.reduce((sum, item) => sum + item.stats[key], 0);
    this.has = (name) => input.items.includes(name);
    const aa = champion.aa,
      u = growth(input.level);
    this.baseAd = aa.base_ad;
    this.baseAs = aa.base_as;
    this.ratio = aa.as_ratio;
    this.naturalBonusAs = aa.base_bonus_as + aa.as_growth * u;
    this.mana =
      (champion.levels[String(input.level)].mana ?? 0) + this.total("mana");
    this.ad =
      this.baseAd +
      aa.ad_growth * u +
      (input.champion === "Senna" ? (input.mist ?? 0) * 1.25 : 0) +
      this.total("ad") +
      (this.has("Manamune") || this.has("Muramana") ? 0.02 * this.mana : 0);
    this.yuntalCrit = Math.min(
      0.25,
      Math.max(0, input.yuntalStacks ?? 0) * 0.002,
    );
    this.charge = options.energized ? 100 : 0;
    this.spellPending = !!options.spellblade;
    if (options.initialFlurry && this.has("Yun Tal Wildarrows")) {
      this.yuntalUntil = 6;
      this.yuntalCd = 25;
    }
  }
  hit(state: AttackState): AttackHit {
    for (const value of [
      state.time,
      state.health,
      state.bonusAd ?? 0,
      state.bonusAs ?? 0,
    ])
      if (!Number.isFinite(value)) throw Error("Non-finite attack state");
    if (state.time < this.lastTime || state.time < 0 || state.health < 0)
      throw Error("Invalid event order");
    this.lastTime = state.time;
    const proc = this.options.itemProcs !== false,
      has = this.has,
      total = this.total,
      t = state.time,
      skill = !!state.skillOnHit,
      notes: string[] = [];
    const energized = ["Stormrazor", "Rapid Firecannon", "Statikk Shiv"].filter(
      has,
    );
    if (energized.length && proc) {
      const travelled = Math.max(
        this.path,
        state.movementDistance ?? this.path,
      );
      this.charge = Math.min(
        100,
        this.charge + ((travelled - this.path) * 26) / 700,
      );
      this.path = travelled;
    }
    if (state.launch) {
      if (state.attackId === undefined)
        throw Error("Launch requires attack ID");
      if (!this.launches.has(state.attackId)) {
        this.launches.add(state.attackId);
        if (energized.length && proc && this.charge >= 100 - 1e-9) {
          this.pending.add(state.attackId);
          this.charge = 0;
        }
      }
      return {
        damage: 0,
        attackSpeed: 0,
        crit: 0,
        armor: 0,
        magicResist: 0,
        physical: 0,
        magic: 0,
        trueDamage: 0,
        physicalDamage: 0,
        magicDamage: 0,
        notes,
        stacks: { energized_charge: this.charge },
        energizedReserved: this.pending.has(state.attackId),
      };
    }
    this.count++;
    const ad = this.ad + (state.bonusAd ?? 0);
    for (const cast of state.spellCastTimes ?? [])
      if (cast >= this.spellReady) this.spellPending = true;
    if (
      state.ultimateCastTime !== undefined &&
      state.ultimateCastTime !== this.lastUlt
    ) {
      this.lastUlt = state.ultimateCastTime;
      this.fiendUntil = state.ultimateCastTime + 8;
      if (has("Fiendhunter Bolts") && proc) this.fiend = 3;
    }
    const dyn =
      (has("Guinsoo's Rageblade") && proc ? 0.08 * this.rage : 0) +
      (has("Phantom Dancer") && proc ? 0.06 * this.dancer : 0) +
      (has("Yun Tal Wildarrows") && proc && t < this.yuntalUntil ? 0.35 : 0);
    let speed = Math.min(
      3,
      this.baseAs +
        this.ratio *
          (this.naturalBonusAs + total("as") + dyn + (state.bonusAs ?? 0)),
    );
    const baseCrit = Math.min(
      1,
      total("crit") +
        (this.input.champion === "Senna"
          ? Math.floor((this.input.mist ?? 0) / 20) * 0.1
          : 0) +
        (has("Yun Tal Wildarrows") && proc ? this.yuntalCrit : 0),
    );
    const crit = state.crit ?? baseCrit,
      cd =
        (has("Infinity Edge") ? 2.3 : 2) *
        (this.input.champion === "Senna" ? 0.9 : 1);
    let armor = effectiveResistance(
      this.target.armor,
      total("pctpen") + (has("Terminus") && proc ? 0.1 * this.dark : 0),
      total("flatpen"),
      has("Terminus") && proc ? 0.4 : 1,
    );
    let physical = state.attackPhysical ?? ad * (1 + crit * (cd - 1)),
      onp = 0,
      onm = 0,
      trueDamage = 0;
    if (this.fiend && t <= this.fiendUntil && !skill) {
      speed = Math.min(3, speed + this.ratio * 0.5);
      physical = (state.criticalPhysical ?? ad * cd) * 0.8;
      trueDamage = ad * 0.15 * crit;
      notes.push("Opening Barrage");
    }
    if (has("Hexoptics C44") && !skill) {
      const d = state.distance ?? 550,
        factor =
          1 + Math.min(10, Math.max(0, Math.floor((d - 50) / 50))) * 0.01,
        secondary = state.nonbasicPhysical ?? 0;
      physical = (physical - secondary) * factor + secondary;
      notes.push(`C44 ${Math.round((factor - 1) * 100)}% basic only`);
    }
    if (
      has("Galeforce") &&
      this.options.activeReady &&
      !skill &&
      !state.spellCastTimes &&
      t >= this.galeReady
    ) {
      onp +=
        40 + (85 * (this.input.level - 1)) / 14 + 0.35 * (ad - this.baseAd);
      this.galeReady = t + 60;
      notes.push("Cloudburst");
    }
    const botrk =
      this.db.champions.find((c) => c.name === this.input.champion)
        ?.attack_type === "Melee"
        ? 0.085
        : 0.06;
    if (has("Blade of the Ruined King"))
      onp += Math.max(15, botrk * state.health);
    if (has("Terminus") && proc) onm += 30;
    if (has("Wit's End")) onm += 40;
    if (has("Nashor's Tooth")) onm += 15 + 0.2 * total("ap");
    if (has("Recurve Bow")) onp += 15;
    if (has("Muramana") && !skill) onp += 0.015 * (state.maxMana ?? this.mana);
    let phantom = false;
    if (has("Guinsoo's Rageblade") && proc) {
      onm += 30;
      if (this.rage >= 3) {
        this.rageHits++;
        if (this.rageHits >= 3) {
          phantom = true;
          this.rageHits = 0;
        }
      }
    }
    let primaryMagic = onm;
    const primaryMr = effectiveResistance(
      this.target.magicResist,
      total("pctmpen") + (has("Terminus") && proc ? 0.1 * this.dark : 0),
      total("flatmpen"),
      has("Terminus") && proc ? 0.4 : 1,
    );
    const terminus = () => {
      this.terminusHits++;
      if (this.terminusHits % 2) this.light = Math.min(3, this.light + 1);
      else this.dark = Math.min(3, this.dark + 1);
    };
    if (has("Terminus") && proc) {
      terminus();
      armor = effectiveResistance(
        this.target.armor,
        Math.min(0.4, total("pctpen") + 0.1 * this.dark),
        total("flatpen"),
      );
    }
    const kraken = () => {
      this.kraken++;
      if (this.kraken >= 3) {
        onp +=
          (120 + (48 * (this.input.level - 1)) / 14) *
          (1 +
            0.75 *
              Math.max(
                0,
                Math.min(
                  1,
                  (this.target.health - state.health) / this.target.health,
                ),
              ));
        this.kraken -= 3;
        notes.push(phantom ? "Kraken (Phantom)" : "Kraken");
      }
    };
    if (has("Kraken Slayer") && proc) kraken();
    const primaryPhysical = onp;
    const amp =
      (has("Lord Dominik's Regards")
        ? 1 +
          Math.min(
            0.12,
            (Math.max(0, this.target.bonusHealth ?? 0) / 125) * 0.01,
          )
        : 1) *
      (this.input.boots === "Immortal Treads" ? 1.05 : 1) *
      (!skill ? 1 - (this.target.attackReduction ?? 0) : 1);
    if (phantom) {
      onm += 30;
      if (has("Blade of the Ruined King")) {
        const primary =
          ((physical + primaryPhysical) * resistanceMultiplier(armor) +
            primaryMagic * resistanceMultiplier(primaryMr) +
            trueDamage) *
          amp *
          (state.onHitHealthMultiplier ?? 1);
        onp += Math.max(
          15,
          botrk *
            Math.max(
              0,
              state.health - primary - (state.primaryExternalDamage ?? 0),
            ),
        );
      }
      if (has("Terminus") && proc) onm += 30;
      if (has("Wit's End")) onm += 40;
      if (has("Nashor's Tooth")) onm += 15 + 0.2 * total("ap");
      if (has("Recurve Bow")) onp += 15;
      if (has("Terminus") && proc) terminus();
      if (has("Kraken Slayer") && proc) kraken();
      notes.push("Phantom Hit");
    }
    if (energized.length && proc) {
      const id = state.attackId,
        fresh = id === undefined || !this.attacks.has(id),
        reserved = id !== undefined && this.pending.has(id),
        fires =
          reserved ||
          (this.charge >= 100 - 1e-9 &&
            (skill || (fresh && (id === undefined || !this.launches.has(id)))));
      if (fires) {
        for (const name of energized) {
          onm +=
            name === "Stormrazor" ? 120 : name === "Rapid Firecannon" ? 80 : 60;
          notes.push(
            name === "Stormrazor"
              ? "Storm Energized"
              : name === "Rapid Firecannon"
                ? "RFC Energized"
                : "Shiv Energized",
          );
        }
        if (reserved) this.pending.delete(id!);
        else this.charge = 0;
      }
      if (!skill && fresh) {
        if (!fires)
          this.charge = Math.min(
            100,
            this.charge + (has("Statikk Shiv") ? 14 : 9),
          );
        if (id !== undefined) this.attacks.add(id);
      }
    }
    if (has("Kircheis Shard") && this.options.energized && this.count === 1) {
      onm += 40;
      notes.push("Jolt");
    }
    if (this.spellPending && t >= this.spellReady) {
      const choices: Array<[number, number, string]> = [];
      if (has("Essence Reaver") && proc)
        choices.push([
          1.35,
          1.35 * this.baseAd + Math.min(80, 0.8 * baseCrit * 100),
          "ER",
        ]);
      if (has("Trinity Force") && proc)
        choices.push([2, 2 * this.baseAd, "Trinity"]);
      if (has("Iceborn Gauntlet") && proc)
        choices.push([1, this.baseAd + 0.25 * total("armor"), "Iceborn"]);
      if (has("Sheen")) choices.push([1, this.baseAd, "Sheen"]);
      choices.sort((a, b) => b[0] - a[0] || b[1] - a[1]);
      if (choices.length) {
        onp += choices[0][1];
        notes.push(choices[0][2]);
        this.spellReady = t + 1.5;
        this.spellPending = false;
      }
    }
    if (
      has("Duskblade of Draktharr") &&
      proc &&
      !skill &&
      t >= this.duskReady
    ) {
      onp += 60 + (100 * (this.input.level - 1)) / 14;
      notes.push("Nightstalker");
      this.duskReady = t + 10;
    }
    physical += onp;
    const giant = has("Lord Dominik's Regards")
      ? 1 +
        Math.min(0.12, (Math.max(0, this.target.bonusHealth ?? 0) / 125) * 0.01)
      : 1;
    physical *= giant;
    onm *= giant;
    primaryMagic *= giant;
    trueDamage *= giant;
    const mr = effectiveResistance(
      this.target.magicResist,
      total("pctmpen") + (has("Terminus") && proc ? 0.1 * this.dark : 0),
      total("flatmpen"),
      has("Terminus") && proc ? 0.4 : 1,
    );
    const magicDamage =
        has("Terminus") && proc
          ? primaryMagic * resistanceMultiplier(primaryMr) +
            (onm - primaryMagic) * resistanceMultiplier(mr)
          : onm * resistanceMultiplier(mr),
      physicalDamage = physical * resistanceMultiplier(armor);
    const damage =
      (physicalDamage + magicDamage + trueDamage) *
      (this.input.boots === "Immortal Treads" ? 1.05 : 1) *
      (!skill ? 1 - (this.target.attackReduction ?? 0) : 1);
    if (
      has("Phantom Dancer") &&
      proc &&
      (!skill || this.input.champion === "Ezreal")
    )
      this.dancer = Math.min(5, this.dancer + 1);
    if (has("Guinsoo's Rageblade") && proc)
      this.rage = Math.min(4, this.rage + 1);
    if (has("Yun Tal Wildarrows") && proc && !skill) {
      this.yuntalCrit = Math.min(0.25, this.yuntalCrit + 0.002);
      if (this.yuntalCd <= t) {
        this.yuntalUntil = t + 6;
        this.yuntalCd = t + 25;
        notes.push("Flurry");
      } else this.yuntalCd = Math.max(t, this.yuntalCd - (1 + crit));
    }
    if (this.fiend && t <= this.fiendUntil && !skill) this.fiend--;
    return {
      damage,
      attackSpeed: speed,
      crit,
      armor,
      magicResist: mr,
      physical,
      magic: onm,
      trueDamage,
      physicalDamage,
      magicDamage,
      notes,
      stacks: {
        rage: this.rage,
        phantom_dancer: this.dancer,
        light: this.light,
        dark: this.dark,
        kraken: this.kraken,
        yuntal_crit: this.yuntalCrit,
        energized_charge: this.charge,
      },
    };
  }
}
