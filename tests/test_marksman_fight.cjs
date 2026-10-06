'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const Fight=require('../assets/marksman-3d/fight.js');
const profiles=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../data/marksman-art-direction.json'))).champions;
assert.equal(Fight.DURATION,20);
let frames=0;
for(const name of Object.keys(profiles)){
 const slots=new Set(),enemySlots=new Set();
 for(let tick=0;tick<=1200;tick++){
  const time=tick/60,state=Fight.frame(profiles,name,'Jinx',time);
  assert.deepEqual(state,Fight.frame(profiles,name,'Jinx',time),'seek must be deterministic');
  for(const actor of[state,state.opponent]){assert.ok(actor.progress>=0&&actor.progress<=1);assert.ok(Number.isFinite(actor.speed));}
  assert.ok([...state.hero,...state.target].every(Number.isFinite));
  assert.ok(Math.hypot(state.hero[0]-state.target[0],state.hero[2]-state.target[2])>3,'models stay separated');
  assert.equal(state.showTarget,false);slots.add(state.action);enemySlots.add(state.opponent.action);for(const e of state.effects)if(e.persistent)slots.add(e.slot);for(const e of state.opponent.effects)if(e.persistent)enemySlots.add(e.slot);frames++;
 }
 for(const slot of['Walk','AA','P','Q','W','E','R']){assert.ok(slots.has(slot),name+' shows '+slot);assert.ok(enemySlots.has(slot),'opponent shows '+slot);}
 const hidden=Fight.frame(profiles,name,'Ashe',13.7,{particles:false});
 assert.deepEqual(hidden.effects,[]);assert.deepEqual(hidden.opponent.effects,[]);assert.deepEqual(hidden.impacts,[]);assert.deepEqual(hidden.opponent.impacts,[]);
 assert.equal(Fight.frame(profiles,name,'Ashe',-3).time,0);assert.equal(Fight.frame(profiles,name,'Ashe',23).time,20);
}
assert.throws(()=>Fight.frame(profiles,'Missing','Jinx',1));assert.throws(()=>Fight.frame(profiles,'Ezreal','Jinx',NaN));
const html=fs.readFileSync(require('node:path').join(__dirname,'../assets/marksman-3d/studio.html'),'utf8');
assert.ok(html.includes('__FIGHT_SCRIPT__'));assert.ok(html.includes('id="fight"'));assert.ok(html.includes('MarksmanFight.frame'));
for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)){const code=match[1];if(!code.trim()||code.includes('__')||code.trim().startsWith('{'))continue;new Function(code);}
console.log('PASS: 23 matchups / '+frames+' deterministic fight frames / complete AA-P-Q-W-E-R exchanges');

for(const [name,moves]of Object.entries(Fight.MOVEMENT))for(const [slot,move]of Object.entries(moves)){
 const event=Fight.SCHEDULE.find(e=>e[1]===slot),start=event[0],duration=slot==='AA'?profiles[name].attack.study_duration:profiles[name].skills[slot].study_duration;
 const begin=Fight.worldPosition(profiles,name,start,1),land=Fight.worldPosition(profiles,name,start+duration*.68,1);
 assert.ok(Math.hypot(land[0]-begin[0],land[2]-begin[2])>move.distance*.85,name+' '+slot+' must move the model');
 const end=start+duration+2.1,near=Fight.worldPosition(profiles,name,end-1e-5,1),after=Fight.worldPosition(profiles,name,end+1e-5,1);assert.ok(Math.hypot(...near.map((v,i)=>v-after[i]))<.001,'continuous recovery '+name);
}
const e=profiles.Ezreal.skills.E.study_duration;
const before=Fight.worldPosition(profiles,'Ezreal',7.8+e*.37,1),after=Fight.worldPosition(profiles,'Ezreal',7.8+e*.39,1);
assert.ok(Math.hypot(...before.map((v,i)=>v-after[i]))>1.5,'blink must teleport at release');
const grounded=Fight.worldPosition(profiles,'Ashe',5.0,1),firing=Fight.worldPosition(profiles,'Ashe',5.3,1);
assert.deepEqual(grounded,firing,'planted casts must not slide');
assert.notDeepEqual(Fight.worldPosition(profiles,'Ashe',2.3,1),Fight.worldPosition(profiles,'Ashe',2.6,1),'an instant buff (Ashe Q) never plants the hero');
console.log('PASS: 9 champion movement profiles / physical displacement / blink release / grounded casting');
