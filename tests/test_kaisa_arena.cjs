'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const P=require('../assets/marksman-3d/practice.js'),D=require('../assets/marksman-3d/duel.js'),F=require('../assets/marksman-3d/fight.js'),M=require('../assets/marksman-3d/duel-mechanics.js');
const C=JSON.parse(fs.readFileSync('app-data/practice.json')).champions;
function round(lane=false){const d=D.create({...C["Kai'Sa"],name:"Kai'Sa"},{...C.Ezreal,name:'Ezreal'},{movements:F.MOVEMENT,distance:500,lane,duration:120});d.bot.next=Infinity;d.player.autoApproach=false;d.player.resource.hpRegen=0;return d;}
function run(d,t){for(let i=0;i<Math.ceil(t/D.DT);i++)D.step(d,D.DT);}
// An invalid R is side-effect free, including dead/expired/minion marks.
{const d=round(true),s=d.player,start=s.hero.slice(),mana=s.resource.mana;assert(!P.cast(s,'R'));assert.equal(s.resource.mana,mana);assert.deepEqual(s.hero,start);assert.equal(s.deadlines.R,undefined);d.enemy.health.plasma=1;d.enemy.health.plasmaUntil=-1;assert(!P.cast(s,'R'));run(d,.01);const m=d.lane.units.find(m=>m.side===1);m.health.plasma=2;m.health.plasmaUntil=10;D.selectTarget(d,s,m.id);assert(!P.cast(s,'R'));assert.equal(s.health.shield,undefined);}
// Actual AA applies the mark; R uses the target-centered landing region and total AD scaling.
{const d=round(),s=d.player;assert(P.cast(s,'AA'));run(d,1);assert(d.enemy.health.plasma>0);const target=d.enemy.hero.slice();assert(P.cast(s,'R',[10,0,5]));const e=s.events.at(-1);assert(Math.hypot(e.landing[0]-target[0],e.landing[2]-target[2])<=4.000001);assert.equal(s.health.shield,150+1.6*P.stats(s).ad);assert(D.frame(d).playerHealth.shield>0);const hp=s.health.hp;assert.equal(M.absorb(s.health,100,s.time),0);assert.equal(s.health.hp,hp);const left=s.health.shield;assert.equal(M.absorb(s.health,left+37,s.time),37);assert.equal(s.health.shield,0);}
// Every rank uses total AD (not bonus AD) and the full AP coefficient.
{for(let rank=1;rank<=3;rank++){const d=round(),s=d.player;s.ranks.R=rank;s.loadout={stats:{attack_damage:200,ability_power:70,attack_speed:1},attackSpeed(){return 1;},cast(){}};d.enemy.health.plasma=1;d.enemy.health.plasmaUntil=4;assert(P.cast(s,'R'));assert.equal(s.health.shield,[100,125,150][rank-1]+[.8,1.2,1.6][rank-1]*200+70);}}
// Opposing AA absorbs armor-mitigated damage, without reducing HP until the shield is exhausted.
{const d=round(),s=d.player;s.health.shield=1000;s.health.shieldUntil=2;const hp=s.health.hp;assert(P.cast(d.enemy,'AA'));run(d,1);assert(s.health.shield<1000);assert.equal(s.health.hp,hp);assert(d.enemy.training.damage>0);run(d,1.1);assert.equal(D.frame(d).playerHealth.shield,0);assert.equal(M.absorb(s.health,50,s.time),50);}
// Tower shots use the same absorption path as champion skills/attacks.
{const d=round(true),s=d.player;run(d,.01);s.health.shield=1000;s.health.shieldUntil=2;const hp=s.health.hp;d.lane.shots.push({target:'player',damage:100,start:d.time,arrive:d.time+.02,done:false,tower:true});run(d,.05);assert(s.health.shield<1000);assert.equal(s.health.hp,hp);}
console.log('PASS KaiSa arena: marked champion R eligibility, landing region, shield scaling/expiry and champion/tower absorption');
