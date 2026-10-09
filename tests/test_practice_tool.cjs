'use strict';
// Practice Tool engine (assets/marksman-3d/practice.js with sharpwr/practice_data.py numbers): every
// champion casts every skill on the dummy; numbers, timing and buffs follow the exported data.
const assert=require('node:assert/strict'),fs=require('node:fs'),{execFileSync}=require('node:child_process');
const Practice=require('../assets/marksman-3d/practice.js'),Fight=require('../assets/marksman-3d/fight.js'),Tool=require('../assets/marksman-3d/practice-tool.js');
const catalogue=JSON.parse(fs.readFileSync('app-data/practice.json'));
const run=(s,seconds)=>{const end=s.time+seconds;while(s.time<end-1e-9)Practice.step(s,Math.min(1/60,end-s.time));};
const finite=v=>Array.isArray(v)?v.every(finite):typeof v==='number'?Number.isFinite(v):true;
let casts=0,numbers=0;
for(const[name,p]of Object.entries(catalogue.champions)){
 const profile={...p,name},s=Practice.create(profile,{movements:Fight.MOVEMENT});
 Practice.setDummy(s,{hp:99999,armor:0,mr:0});s.noCooldowns=true;
 // Basic attack: the level's attack speed sets the rhythm; AD lands as physical damage.
 Practice.holdAttack(s,true);run(s,4);Practice.holdAttack(s,false);run(s,1.5);
 const attacks=s.log.filter(l=>l.slot==='AA'),interval=1/Practice.stats(s).as;
 assert(attacks.length>=Math.floor(4/interval)-1,name+' keeps attacking while held');
 for(const a of attacks)assert.ok(Math.abs(a.dealt-p.practice.attack.damage.physical[14])<1e-9,name+' AA = AD at level 15 vs 0 armor');
 for(let i=1;i<attacks.length;i++)assert.ok(attacks[i].t-attacks[i-1].t>=interval-1/60-1e-9,name+' attacks no faster than attack speed');
 // Every skill, cast at the dummy from attack range.
 for(const slot of['Q','W','E','R','P']){s.hero=[s.target[0]-4,0,s.target[2]];s.destination=s.hero.slice();s.log.length=0;s.buffs.length=0;
  assert(Practice.cast(s,slot),name+' '+slot+' casts');casts++;
  let buffAS=0;for(let i=0;i<240;i++){Practice.step(s,1/60);const f=Practice.frame(s);assert(finite(f.hero)&&finite(f.target)&&f.effects.every(e=>Number.isFinite(e.progress)),name+' '+slot+' frame stays finite');buffAS=Math.max(buffAS,...s.buffs.filter(b=>b.slot===slot).map(b=>b.as));}
  const S=p.practice.slots[slot],hit=s.log.find(l=>l.slot===slot&&l.dealt);
  if(slot!=='P'&&S.mode==='hit'&&hit){numbers++;const expected=Object.values(S.damage).reduce((v,rows)=>v+rows[(slot==='R'?3:4)-1][14],0);assert.ok(Math.abs(hit.dealt-expected)<1e-6,name+' '+slot+' number = engine raw damage at 0 resistances');}
  if(slot!=='P'&&S.mode!=='hit')assert(!hit,name+' '+slot+' shows no number unless the engine resolves it');
  if(slot!=='P'&&S.buff)assert.equal(buffAS,S.buff.as?S.buff.as[(S.buff.by==='R'?3:4)-1]:0,name+' '+slot+' attack speed buff');
 }
}
// Tristana Q: attack speed from the engine's Rapid Fire while it lasts.
{const p={...catalogue.champions.Tristana,name:'Tristana'},s=Practice.create(p,{movements:Fight.MOVEMENT}),base=Practice.stats(s).as;assert(Practice.cast(s,'Q'));const buffed=Practice.stats(s).as;assert.ok(Math.abs(buffed-base-p.practice.as_ratio*p.practice.slots.Q.buff.as[3])<1e-9);run(s,p.practice.slots.Q.buff.duration[3]+.1);assert.equal(Practice.stats(s).as,base);}
// Joystick input during an attack windup does not cancel it: the attack fires, then the hero moves
// the way the joystick points; a skill pressed during a cast waits for it.
{const p={...catalogue.champions.Ezreal,name:'Ezreal'},s=Practice.create(p,{movements:Fight.MOVEMENT});const start=s.hero.slice();assert(Practice.cast(s,'AA'));const launch=s.events[0].launch;
 while(s.time<launch-1/60){Practice.move(s,[s.hero[0]-1.5,0,s.hero[2]+1]);Practice.step(s,1/60);assert.deepEqual(s.hero,start,'the hero stands still during the windup');}
 for(let i=0;i<12;i++){Practice.move(s,[s.hero[0]-1.5,0,s.hero[2]+1]);Practice.step(s,1/60);}assert(s.hero[0]<start[0]-.1&&s.hero[2]>start[2]+.05,'then it moves the way the joystick points');
 run(s,1);assert.equal(s.log.filter(l=>l.slot==='AA').length,1,'the attack still lands');
 assert(Practice.cast(s,'R'));run(s,.6);assert(!Practice.cast(s,'Q'),'R is still casting');run(s,1.5);assert(s.events.some(e=>e.slot==='Q'),'buffered Q casts after R');}
// Ezreal W marks the dummy; the next other hit detonates it.
{const p={...catalogue.champions.Ezreal,name:'Ezreal'},s=Practice.create(p,{movements:Fight.MOVEMENT});Practice.setDummy(s,{hp:9999,armor:0,mr:0});Practice.cast(s,'W');run(s,1.2);assert.equal(s.dummy.mark.slot,'W');Practice.cast(s,'AA');run(s,1.5);assert.deepEqual(s.log.filter(l=>l.dealt).map(l=>l.slot),['AA','W detonation']);}
// The dummy heals after a pause and keeps the last combo.
{const p={...catalogue.champions.Jinx,name:'Jinx'},s=Practice.create(p,{movements:Fight.MOVEMENT});Practice.cast(s,'AA');run(s,1);assert(s.dummy.hp<s.dummy.max);run(s,6);assert.equal(s.dummy.hp,s.dummy.max);assert.equal(s.lastCombo.count,1);}
// Notes export.
{const text=Tool.notesMarkdown({champions:{Vayne:{tested:true,General:'Roll is shorter',R:'Stealth lasts longer'}}},catalogue,new Date('2026-10-06'));assert.match(text,/## Vayne \(tested\)/);assert.match(text,/\*\*R · Final Hour:\*\* Stealth lasts longer/);}
// The committed export matches the engine.
const fresh=execFileSync('python3',['-c','import sys;sys.path.insert(0,".");from marksman_art import practice_catalogue;from sharpwr.practice_data import render_practice_json;sys.stdout.write(render_practice_json(practice_catalogue(icon_files=True)))'],{maxBuffer:1<<26}).toString();
assert.equal(fresh,fs.readFileSync('app-data/practice.json','utf8'),'Run: python scripts/export_app_data.py');
// Human controls never issue an implicit move from an out-of-range attack.
{const s=Practice.create({...catalogue.champions.Ezreal,name:'Ezreal'},{movements:Fight.MOVEMENT,autoApproach:false});s.target=[15,0,0];const start=s.hero.slice();Practice.holdAttack(s,true);assert.equal(Practice.cast(s,'AA'),false);for(let i=0;i<180;i++)Practice.step(s,1/120);assert.deepEqual(s.hero,start);assert.deepEqual(s.destination,start);Practice.holdAttack(s,false);}
// Gait follows travelled distance, remains frozen at rest, and resumes without clock jumps.
{const s=Practice.create({...catalogue.champions.Ezreal,name:'Ezreal'});s.time=30;Practice.move(s,[s.hero[0]+1,0,0]);const before=s.hero.slice();Practice.step(s,1/60);const d=Math.hypot(s.hero[0]-before[0],s.hero[2]-before[2]);assert(Math.abs(s.gaitPhase-d/2.76*Math.PI*2)<1e-8);const phase=s.gaitPhase;Practice.move(s,s.hero.slice());Practice.step(s,.5);assert.equal(s.gaitPhase,phase);Practice.move(s,[s.hero[0]+1,0,0]);Practice.step(s,1/60);assert(s.gaitPhase>phase&&s.gaitPhase-phase<.2);}
console.log(`PASS: practice tool / ${Object.keys(catalogue.champions).length} champions / ${casts} casts / ${numbers} engine damage numbers / attack rhythm / buffs / attack not cancelled by movement / input buffer / mark detonation / dummy reset / notes export`);
