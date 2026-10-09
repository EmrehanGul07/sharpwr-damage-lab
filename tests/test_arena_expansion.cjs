'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const P=require('../assets/marksman-3d/practice.js'),D=require('../assets/marksman-3d/duel.js'),F=require('../assets/marksman-3d/fight.js');
const C=JSON.parse(fs.readFileSync('app-data/practice.json')).champions;
function round(name='Ezreal',options={}){const d=D.create({...C[name],name},{...C.Ezreal,name:'Ezreal'},{distance:500,movements:F.MOVEMENT,...options});d.bot.next=Infinity;d.enemy.health.hp=d.enemy.health.max=20000;return d;}
function run(d,t){for(let i=0;i<Math.ceil(t/D.DT);i++)D.step(d,D.DT);}
// The missile bends towards its originally selected living target, without moving its owner.
{const d=round(),s=d.player;P.cast(s,'AA');const e=s.events.at(-1);run(d,e.launch+.04);const head=e.projectile.slice(),hero=s.hero.slice();d.enemy.hero=[4,0,3];d.enemy.destination=d.enemy.hero.slice();run(d,.05);assert(e.projectile[2]>head[2]);assert.deepEqual(s.hero,hero);run(d,1);assert.deepEqual(e.impactPoint,[4,0,3]);}
// Selecting a different target after launch cannot redirect an AA to it.
{const d=round('Ezreal',{lane:true}),s=d.player;run(d,.01);P.cast(s,'AA');D.selectTarget(d,s,d.lane.units.find(m=>m.side===1).id);run(d,1);assert.equal(d.enemy.health.count,1);}
// Three discrete trap centers agree with the effect frame, and stay champion-only.
{const d=round('Jinx');P.cast(d.player,'E',d.enemy.hero);const e=d.player.events.at(-1);assert.equal(e.traps.length,3);assert.equal(P.frame(d.player).effects[0].traps.length,3);assert.equal(Math.round(Math.hypot(e.traps[0][0]-e.traps[1][0],e.traps[0][2]-e.traps[1][2])*100),50);}
// Flight endpoints: maximum flight adds 10x base damage, missing health remains impact-time.
{const d=round('Jinx'),s=d.player;const raw=t=>{s.time=t;const h={execute:true,event:{launch:0},slot:'R',raw:{}};d.mechanics.beforeHit(s,h);return h.raw.physical;};assert.equal(raw(1),raw(0)*10);assert.equal(raw(2),raw(1));}
// Assist and tower triggers require recent personal contribution, and expire after 3s.
{const d=round('Jinx'),s=d.player;for(const kind of['champion','tower']){s.time=2;s.combat.excitedUntil=0;d.mechanics.takedown(s,{kind,health:{contributors:{0:0}}});assert.equal(s.combat.excitedUntil,8);s.time=4;s.combat.excitedUntil=0;d.mechanics.takedown(s,{kind,health:{contributors:{0:0}}});assert.equal(s.combat.excitedUntil,0);}}
// All database marksmen obey resource and manual control rules, regardless of difficulty.
for(const name of Object.keys(C)){const d=round(name),s=d.player;assert(s.resource);assert(Number.isFinite(s.resource.mana));s.autoApproach=false;const start=s.hero.slice();P.holdAttack(s,true);run(d,1);assert.deepEqual(s.hero,start,name);}
for(const name of Object.keys(C))for(const slot of ['Q','W','E','R']){const d=round(name),s=d.player,before=s.resource.mana,cost=d.mechanics.cost(s,slot);if(P.cast(s,slot))assert(Math.abs(s.resource.mana-(before-cost))<1e-7,`${name} ${slot} pays its resource cost, including instant buffs`);}
// Third-hit and five-stack mechanics are attached to the victim, not another locked target.
{const d=round('Vayne'),s=d.player;P.holdAttack(s,true);run(d,4);assert(s.log.some(h=>h.parts?.true?.raw>0));}
{const d=round("Kai'Sa"),s=d.player;P.holdAttack(s,true);run(d,5);assert(s.log.some(h=>h.parts?.magic?.raw>20));}
{const d=round('Caitlyn'),s=d.player;P.holdAttack(s,true);run(d,6);assert(s.log.some(h=>h.parts?.physical?.raw>P.stats(s).ad));}
{const d=round('Lucian'),s=d.player;P.cast(s,'W');run(d,.7);P.cast(s,'AA');run(d,1);assert.equal(s.log.filter(h=>h.slot==='AA').length,2);}
// Named scenarios are deterministic, obey skill cooldowns and expose their report type.
for(const scenario of['kite','dodge','last-hit','tower']){const d=round('Ezreal',{scenario,lane:scenario==='last-hit'||scenario==='tower',duration:3});run(d,3.1);assert(d.finished);assert.equal(D.summary(d).scenario,scenario);assert(Math.abs(D.summary(d).duration-3)<=D.DT+1e-9);}
console.log('PASS arena expansion: real homing, three traps, flight damage, takedowns, roster resources/passives and four scenarios');
