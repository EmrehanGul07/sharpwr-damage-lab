import { readFileSync } from 'node:fs';
import { describe,it,expect } from 'vitest';
import { arenaBuild } from '../src/arena-build';
import { ArenaRunes } from '../src/arena-runes';
import type { Database } from '../src/data';
const db=JSON.parse(readFileSync(new URL('../../app-data/database.json',import.meta.url),'utf8')) as Database;
describe('live arena loadout',()=>{
 it('fresh rounds reset item procs; saved champion only; equipment changes damage',()=>{
  const storage=new Map<string,string>();
  Object.assign(globalThis,{localStorage:{getItem:(key:string)=>storage.get(key)||null}});
  storage.set('sharpwr.build',JSON.stringify({champion:'Ezreal',level:15,items:["Guinsoo's Rageblade",'Statikk Shiv'],runes:true}));
  const factory=arenaBuild(db),a=factory('Ezreal',15)!,b=factory('Ezreal',15)!;
  expect(factory('Jinx',15)).toBeNull();
  expect(a.stats.attack_damage).toBeGreaterThan(db.champions.find(c=>c.name==='Ezreal')!.levels['15'].attack_damage);
  const s={time:1,hero:[0,0,0],target:[4,0,0],dummy:{max:2000,hp:2000,armor:0,mr:0,aaReduction:0},duel:{hitVictim:{kind:'champion'}}};
  const h={attack:true,slot:'AA',raw:{physical:a.stats.attack_damage}};
  const initial=a.resolve(s,h);expect(b.resolve(s,h)).toEqual(initial);
  for(let i=2;i<6;i++){s.time=i;a.resolve(s,h);}
  expect(a.attackSpeed()).toBeGreaterThan(b.attackSpeed());
 });
 it('Empowerment fires on three hits, respects four-second gaps and amplifies later hits',()=>{
  const r=new ArenaRunes(15,'Empowerment',[]);
  expect(r.apply(0,true,1,0,0,1).physical).toBe(0);
  expect(r.apply(5,true,1,0,0,1).physical).toBe(0);
  expect(r.apply(6,true,1,0,0,1).physical).toBe(0);
  expect(r.apply(7,true,1,0,0,1).physical).toBe(165);
  expect(r.apply(8,true,1,0,0,1).multiplier).toBe(1.08);
 });
});
