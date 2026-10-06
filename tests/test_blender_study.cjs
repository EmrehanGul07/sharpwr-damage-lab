'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
(async()=>{
 const T=await import('three'),{GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js'),{clone}=await import('three/addons/utils/SkeletonUtils.js');
 const Avatar=require('../assets/marksman-3d/baked-avatar.js'),bytes=fs.readFileSync(path.join(__dirname,'../static/marksman-3d/ezreal/character.glb'));
 const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
 assert.deepEqual(new Set(gltf.animations.map(c=>c.name)),new Set(['Idle','Walk','AA','P','Q','W','E','R']));
 const profile={...JSON.parse(fs.readFileSync(path.join(__dirname,'../data/marksman-art-direction.json'))).champions.Ezreal,name:'Ezreal'},avatar=Avatar.createAvatar(T,gltf,clone,profile);
 assert.ok(avatar.sockets.muzzle,'gauntlet socket');let skinned=0;
 avatar.root.traverse(o=>{if(o.isSkinnedMesh){skinned++;const weights=o.geometry.attributes.skinWeight;for(let i=0;i<weights.count;i++)assert.ok(Math.abs(weights.getX(i)+weights.getY(i)+weights.getZ(i)+weights.getW(i)-1)<1e-5,'normalized skin weights');}});
 assert.ok(skinned>0&&skinned<=24,'one skinned mesh: draw calls bounded by material batches');
 const snapshot=()=>{avatar.root.updateMatrixWorld(true);return avatar.root.getObjectByName('handL').matrixWorld.elements.slice();};let poses=0;
 for(const action of gltf.animations.map(c=>c.name))for(const progress of [0,.15,.3,.5,.75,1]){avatar.animate({action,progress,time:progress*1.2});const a=snapshot();assert.ok(a.every(Number.isFinite));avatar.animate({action:'R',progress:.8,time:9});avatar.animate({action,progress,time:progress*1.2});assert.deepEqual(snapshot(),a,'seek must restore the same pose');poses++;}
 avatar.animate({action:'Idle',time:0});const idle=avatar.root.getObjectByName('handL').getWorldPosition(new T.Vector3());avatar.animate({action:'Q',progress:.55});const cast=avatar.root.getObjectByName('handL').getWorldPosition(new T.Vector3());assert.ok(cast.z>idle.z+.25,'Q extends gauntlet forwards');
 const muzzle=avatar.sockets.muzzle.getWorldPosition(new T.Vector3());assert.ok(muzzle.distanceTo(cast)<.35,'effect socket follows gauntlet');
 avatar.animate({action:'Idle',time:0});const rest=avatar.root.getObjectByName('footL').getWorldPosition(new T.Vector3()).y;let contact=9;
 for(let i=0;i<60;i++){avatar.animate({action:'Walk',time:i/60*1.2,loopDuration:1.2});const heights=['footL','footR'].map(n=>avatar.root.getObjectByName(n).getWorldPosition(new T.Vector3()).y);contact=Math.min(contact,...heights);assert.ok(Math.min(...heights)>rest*.6,'feet stay above floor');}
 assert.ok(contact<rest+.02,'the run cycle plants its feet');
 console.log('PASS: Blender study / 8 baked clips / '+skinned+' skin batches / '+poses+' deterministic poses');
})().catch(e=>{console.error(e);process.exit(1);});
