import { loadBuild, buildInput } from './build-state';
import { buildStats, buildProblems } from './engine/build';
import { AttackKernel, effectiveResistance, resistanceMultiplier, type Target } from './engine/attacks';
import type { Database } from './data';
import { ArenaRunes } from './arena-runes';

/** A fresh proc scheduler per round; the saved Build Lab remains the source of truth. */
export function arenaBuild(db: Database) {
  return (champion: string, level: number) => {
    const saved = loadBuild(localStorage, db);
    if (saved.champion !== champion) return null;
    const input = { ...buildInput(saved), level };
    if (buildProblems(db, input.items, input.boots).length) return null;
    const stats = buildStats(db, input);
    const target: Target = { health: 2000, armor: 0, magicResist: 0 };
    const kernel = new AttackKernel(db, input, target);
    const championData=db.champions.find(c=>c.name===champion)!;
    const page=championData.rune_page;
    const runes=new ArenaRunes(level,input.runes&&page?page.keystone:'',input.runes&&page?[...page.primary,page.secondary]:[]);
    function runeDamage(s: any,h: any,raw: Record<string,number>) {
      if(h.secondary||s.duel?.hitVictim?.kind!=='champion')return raw;
      const p=runes.apply(s.time,!!h.attack,s.dummy.hp/s.dummy.max,stats.attack_damage-championData.levels[String(level)].attack_damage,stats.ability_power,resistanceMultiplier(effectiveResistance(s.dummy.armor,stats.armor_pen_pct,stats.armor_pen_flat)));
      if(p.phaseRush)for(const slot of ['Q','W','E'])s.deadlines[slot]=s.time+Math.max(0,(s.deadlines[slot]||0)-s.time)*.8;
      for(const kind of Object.keys(raw))raw[kind]*=p.multiplier;
      raw.physical=(raw.physical||0)+p.physical;
      if(p.firstStrike)raw.true=(raw.true||0)+Object.values(raw).reduce((a,b)=>a+b,0)*.07;
      return raw;
    }
    const spells: number[] = [];
    let path = 0, previous: number[] | null = null, procAs = 0;
    return {
      label: [...input.items, input.boots, input.runes ? 'default rune stats' : null].filter(Boolean).join(' · ') || 'Empty build',
      stats,
      mitigate(d: {armor:number;mr:number;aaReduction:number},kind:string,value:number,attack:boolean) {
        const multiplier=kind==='physical'?resistanceMultiplier(effectiveResistance(d.armor,stats.armor_pen_pct,stats.armor_pen_flat)):kind==='magic'?resistanceMultiplier(effectiveResistance(d.mr,stats.magic_pen_pct,stats.magic_pen_flat)):1;
        return value*multiplier*(attack?1-d.aaReduction:1);
      },
      bonusAs(time: number) { return runes.bonusAs(time); },
      bonusAd(time: number) { return runes.bonusAd(time); },
      cast(slot: string, time: number) { if (slot !== 'AA' && slot !== 'P') spells.push(time); while (spells.length > 20) spells.shift(); },
      step(hero: number[]) { if (previous) path += Math.hypot(hero[0]-previous[0], hero[2]-previous[2])*100; previous = hero.slice(); },
      attackSpeed() { return procAs || stats.attack_speed; },
      resolve(s: any, h: any) {
        const d = s.dummy;
        target.health = d.max; target.armor = d.armor; target.magicResist = d.mr; target.attackReduction = d.aaReduction;
        if (!h.secondary && (h.attack || champion === 'Ezreal' && h.slot === 'Q')) {
          const hit = kernel.hit({ time: s.time, health: d.hp, movementDistance: path,
            attackPhysical: (h.raw?.physical || 0)*(h.attack?1+stats.crit_chance*(stats.crit_damage-1):1), nonbasicPhysical: h.attack?0:h.raw?.physical || 0,
            distance: Math.hypot(s.hero[0]-s.target[0],s.hero[2]-s.target[2])*100,
            bonusAd: Math.max(0, stats.attack_damage - db.champions.find(c=>c.name===champion)!.levels[String(level)].attack_damage),
            bonusAs: input.runes ? championData.rune_stats?.[String(level)]?.bonus_as || 0 : 0,
            spellCastTimes: spells, maxMana: stats.mana ?? undefined, skillOnHit: !h.attack });
          procAs = champion==='Jhin'?stats.attack_speed:Math.min(stats.attack_speed_cap,hit.attackSpeed);
          return runeDamage(s,h,{ physical: hit.physicalDamage, magic: hit.magicDamage + (h.raw?.magic || 0)*resistanceMultiplier(effectiveResistance(d.mr, stats.magic_pen_pct, stats.magic_pen_flat)), true: hit.trueDamage+(h.raw?.true||0) });
        }
        return runeDamage(s,h,Object.fromEntries(Object.entries(h.raw || {}).map(([kind, value]) => [kind, Number(value) * (kind === 'physical' ? resistanceMultiplier(effectiveResistance(d.armor, stats.armor_pen_pct, stats.armor_pen_flat)) : kind === 'magic' ? resistanceMultiplier(effectiveResistance(d.mr, stats.magic_pen_pct, stats.magic_pen_flat)) : 1)])));
      },
    };
  };
}
