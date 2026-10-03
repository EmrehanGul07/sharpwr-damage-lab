'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const T=require(process.env.SHARPWR_THREE_ROOT||'three');
const Rig=require('../assets/marksman-3d/rig.js'),FX=require('../assets/marksman-3d/effects.js');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/marksman-art-direction.json'))),manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/marksman-3d-assets.json')));
assert.equal(Object.keys(data.champions).length,23);assert.equal(Object.keys(manifest.champions).length,23);
let poses=0,effects=0;const signature=new Set();
const snapshot=rig=>JSON.stringify(Object.values(rig.joints).map(b=>[...b.position.toArray(),...b.quaternion.toArray()]));
for(const[name,p]of Object.entries(data.champions)){
 assert.deepEqual(Object.keys(p.skills),['Q','W','E','R']);
 const rig=Rig.createRig(T,{...p,name}),clips=Rig.animationClips(T,rig);
 assert.deepEqual(clips.map(c=>c.name),['Idle','Walk','AA','P','Q','W','E','R']);
 for(const clip of clips){assert.ok(clip.tracks.length>0,name+' '+clip.name);for(const track of clip.tracks){assert.ok([...track.values].every(Number.isFinite));if(['Idle','Walk'].includes(clip.name)){const size=track.getValueSize();assert.deepEqual([...track.values.slice(0,size)],[...track.values.slice(-size)]);}}}
 signature.add(JSON.stringify([p.weapon,p.rig,p.hair,p.headgear,rig.metrics()]));
 for(const action of clips.map(c=>c.name))for(const progress of [0,.08,.25,.45,.7,.9,1]){
  const state={action,progress,time:progress*2.7,speed:action==='Walk'?1:0};Rig.animateRig(rig,state);const before=snapshot(rig);
  rig.root.traverse(o=>{assert.ok([...o.matrixWorld.elements].every(Number.isFinite),name+' '+action);});
  Rig.animateRig(rig,{action:'R',progress:.87,time:42});Rig.animateRig(rig,state);assert.equal(snapshot(rig),before,'seek must be stateless');poses++;
 }
 const scene=new T.Scene(),fx=FX.createEffects(T,scene,{budget:600});
 for(const slot of ['AA','P','Q','W','E','R'])for(const progress of [0,.1,.35,.55,.74,1]){
  const state={progress,age:progress*1.2,source:new T.Vector3(-3,1.2,0),target:new T.Vector3(0,1.2,0),hero:new T.Vector3(-3,0,0),seed:13};
  fx.begin();fx.draw(p,slot,state);fx.finish();
  scene.traverse(o=>{if(o.visible&&o.isMesh){assert.ok([...o.position.toArray(),...o.scale.toArray(),...o.quaternion.toArray()].every(Number.isFinite));assert.ok(o.material.opacity>=0&&o.material.opacity<=1);}});
  assert.ok(fx.metrics().particles<=600);effects++;
 }
 fx.dispose();
 const asset=manifest.champions[name],file=fs.readFileSync(path.join(__dirname,'../assets/marksman-3d/models',asset.file));
 assert.equal(file.readUInt32LE(0),0x46546c67);assert.equal(file.readUInt32LE(4),2);assert.equal(file.length,asset.bytes);
 assert.equal(asset.clips.length,8);assert.ok(asset.joints>=10);
}
assert.equal(signature.size,23,'all champions need a distinct authored model');
console.log('PASS: 23 unique rigs / 184 clips / '+poses+' deterministic poses / '+effects+' finite effect frames');
