'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const Duel=require('../assets/marksman-3d/duel.js'),Bot=require('../assets/marksman-3d/duel-bot.js'),Practice=require('../assets/marksman-3d/practice.js'),Fight=require('../assets/marksman-3d/fight.js');
const catalogue=JSON.parse(fs.readFileSync('app-data/practice.json')).champions;
const profile=name=>({...catalogue[name],name});
const create=(difficulty='medium',extra={})=>Duel.create(profile('Ezreal'),profile('Jinx'),{difficulty,movements:Fight.MOVEMENT,...extra});
function run(d,seconds,dt=1/60){for(let i=0;i<Math.round(seconds/dt);i++)Duel.step(d,dt);}
// All difficulty knobs belong to the decision policy. A mode never edits a profile or combat stat.
const original=JSON.stringify(catalogue),stats=[];
for(const difficulty of Object.keys(Bot.MODES)){const d=create(difficulty);stats.push({combat:Practice.stats(d.enemy),health:d.enemy.health,ranks:d.enemy.ranks,skills:d.enemy.profile.practice.slots});
 Duel.step(d,Bot.MODES[difficulty].reaction-.01);assert.equal(d.enemy.events.length,0,'cannot react before observation latency');}
for(const row of stats)assert.deepEqual(row,stats[0]);assert.equal(JSON.stringify(catalogue),original);
// The controller receives only delayed public observations: a future enemy position is invisible.
{const b=Bot.create('hard');const v=(time,x)=>({time,enemy:{position:[x,0,0]}});Bot.observe(b,v(0,1));Bot.observe(b,v(.1,9));assert.equal(Bot.visible(b,.15).enemy.position[0],1);assert.equal(Bot.visible(b,.25).enemy.position[0],9);}
// Seeded runs are reproducible and independent of render frame rate.
{const a=create('hard',{seed:42}),b=create('hard',{seed:42});run(a,12,1/60);run(b,12,1/30);assert.deepEqual(Duel.frame(a),Duel.frame(b));assert.deepEqual(a.bot.decision,b.bot.decision);}
// Incoming skillshots do not home: leave the firing line before they arrive and they miss.
{const d=create('easy',{distance:900});d.bot.next=1e9;assert(Practice.cast(d.player,'Q'));Practice.move(d.enemy,[d.enemy.hero[0],0,3]);run(d,1);assert.equal(d.enemy.health.hp,d.enemy.health.max);assert.equal(d.player.log.filter(x=>x.dealt).length,0);}
// A shot aimed away can intersect a moving target later; collision is decided during flight.
{const d=create('easy',{distance:500});d.bot.next=1e9;d.enemy.hero[2]=1.2;d.enemy.destination=[d.enemy.hero[0],0,-1.2];d.player.target=d.enemy.hero.slice();assert(Practice.cast(d.player,'Q',[d.enemy.hero[0],0,0]));run(d,1);assert(d.enemy.health.hp<d.enemy.health.max);assert(d.player.log.some(x=>x.slot==='Q'&&x.dealt));}
// Basic attacks remain targeted, respect windup and hit a moving target.
{const d=create('easy',{distance:500});d.bot.next=1e9;assert(Practice.cast(d.player,'AA'));Practice.move(d.enemy,[d.enemy.hero[0],0,3]);run(d,1);assert(d.enemy.health.hp<d.enemy.health.max);assert.equal(d.player.log.filter(x=>x.slot==='AA').length,1);}
// Damage travels in both directions, death freezes the round, no dummy healing or respawn occurs.
{const d=create('impossible');run(d,80);assert(d.player.health.hp<d.player.health.max);assert(d.finished);assert.equal(d.result,'defeat');const end=JSON.stringify(Duel.frame(d));run(d,10);assert.equal(JSON.stringify(Duel.frame(d)),end);assert(!Practice.cast(d.player,'Q'));}
// Hard and Impossible evade a visible line telegraph using a real movement command.
for(const difficulty of['hard','impossible']){const d=create(difficulty,{distance:900,seed:7});Practice.cast(d.player,'Q');run(d,.25);assert.equal(d.bot.decision.reason,'dodge');assert(d.enemy.destination[2]!==0);}
// Full roster: valid stats, finite frames and normal cast cooldowns in all four modes.
let rounds=0;
for(const name of Object.keys(catalogue))for(const difficulty of Object.keys(Bot.MODES)){
 const d=Duel.create(profile('Ezreal'),profile(name),{difficulty,movements:Fight.MOVEMENT,duration:12,seed:4});run(d,13);assert(d.finished,name);assert(['defeat','timeout'].includes(d.result),name);
 const f=Duel.frame(d);assert(f.hero.every(Number.isFinite)&&f.target.every(Number.isFinite),name);
 const attacks=d.enemy.log.filter(x=>x.slot==='AA'&&x.dealt);for(let i=1;i<attacks.length;i++)assert(attacks[i].t>attacks[i-1].t,name+' legal attack cadence');rounds++;
}
assert.throws(()=>create('cheater'));assert.throws(()=>create('hard',{level:16}));assert.throws(()=>Duel.step(create(),-1));
console.log(`PASS duel AI: ${rounds} roster/mode rounds, stat parity, delayed observation, reproducibility, moving collision, homing AA, death, dodge`);
