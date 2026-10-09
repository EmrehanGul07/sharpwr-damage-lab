'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),T=require(require.resolve('three',{paths:[__dirname,require('node:path').join(__dirname,'../mobile')]}));
const A=require('../assets/marksman-3d/rift-arena.js'),P=require('../assets/marksman-3d/practice.js'),D=require('../assets/marksman-3d/duel.js'),F=require('../assets/marksman-3d/fight.js');
const C=JSON.parse(fs.readFileSync('app-data/practice.json')).champions,profile=name=>({...C[name],name}),N=A.navigation;
assert(N.passable([0,0,0]));assert(N.passable([0,0,6]));assert(!N.passable([8,0,6]));assert(!N.passable([-9.5,0,0]));
for(const raw of [[99,0,99],[-9.5,0,0],[-3.1,0,4.8],[8,0,6]])assert(N.passable(N.project(raw)),'projection ends on walkable terrain');
const from=[-10.8,0,0],to=[-8,0,0];assert(N.trace(from,to,'dash')[0]<-10.4,'dash stops at physical tower');assert.deepEqual(N.trace(from,to,'blink'),to,'blink crosses a tower if landing is legal');
assert(N.trace([0,0,0],[0,0,9])[2]<7.4,'walking cannot leave river');
assert(N.passable(N.trace([0,0,0],[6,0,7],'blink')),'blink has a legal endpoint');
for(const name of ['Ezreal','Lucian','Tristana','Vayne']){
 const s=P.create(profile(name),{movements:F.MOVEMENT,arena:N});s.hero=from.slice();s.destination=from.slice();s.target=[-6,0,0];
 const slot=Object.keys(F.MOVEMENT[name])[0],ind=P.aim(s,slot,to);assert(N.passable(ind.endpoint));assert(Math.hypot(ind.endpoint[0]-s.hero[0],ind.endpoint[2]-s.hero[2])<=ind.range+.05);
 assert(P.cast(s,slot,to));const endpoint=s.events.at(-1).landing.slice();for(let i=0;i<240;i++)P.step(s,1/120);assert(N.passable(s.hero));assert(Math.hypot(s.hero[0]-endpoint[0],s.hero[2]-endpoint[2])<.01,'cast lands where indicator showed');
}
for(const software of[false,true])for(const quality of['low','high']){const scene=new T.Scene(),a=A.createArena(T,scene,{terrain:'dragon-lane',software,quality});a.animate(3);assert.equal(a.root.name,'SharpWR_Dragon_Lane');assert(a.metrics().arenaMeshes<650);a.root.traverse(o=>assert(o.position.toArray().every(Number.isFinite)));a.dispose();assert.equal(scene.children.length,0);}
for(const difficulty of['easy','medium','hard','impossible']){const d=D.create(profile('Ezreal'),profile('Jinx'),{arena:N,movements:F.MOVEMENT,difficulty});for(let i=0;i<3600&&!d.finished;i++){D.step(d,1/120);assert(N.passable(d.player.hero));assert(N.passable(d.enemy.hero));}}
console.log('PASS dragon lane: shared terrain, river/tower collisions, blink/dash indicators and endpoints, renderer budgets, four bot modes');
