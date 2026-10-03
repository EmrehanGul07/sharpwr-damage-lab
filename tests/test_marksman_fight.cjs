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
  assert.equal(state.showTarget,false);slots.add(state.action);enemySlots.add(state.opponent.action);frames++;
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
