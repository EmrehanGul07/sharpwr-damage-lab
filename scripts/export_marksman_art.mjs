/** Export original geometry + eight authored animation clips for all champions. */
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(import.meta.url);
const threePath=process.env.SHARPWR_THREE_ROOT||path.join(root,'node_modules/three');
const THREE=await import(pathToFileURL(path.join(threePath,'build/three.module.js')).href);
const {GLTFExporter}=await import(pathToFileURL(path.join(threePath,'examples/jsm/exporters/GLTFExporter.js')).href);
const {GLTFLoader}=await import(pathToFileURL(path.join(threePath,'examples/jsm/loaders/GLTFLoader.js')).href);
const Rig=require('../assets/marksman-3d/rig.js');
const direction=JSON.parse(fs.readFileSync(path.join(root,'data/marksman-art-direction.json'),'utf8'));
globalThis.FileReader=class {readAsArrayBuffer(blob){blob.arrayBuffer().then(v=>{this.result=v;this.onloadend?.();});}readAsDataURL(blob){blob.arrayBuffer().then(v=>{this.result='data:'+blob.type+';base64,'+Buffer.from(v).toString('base64');this.onloadend?.();});}};
const out=path.join(root,'assets/marksman-3d/models');fs.mkdirSync(out,{recursive:true});
const index={schema:1,version:direction.version,format:'glTF 2.0 binary',license:'Original SharpWR procedural geometry and animation; champion identities belong to Riot Games. No extracted game asset used.',timing:direction.timing_policy,champions:{}};
for(const[name,p]of Object.entries(direction.champions)){
 const rig=Rig.createRig(THREE,{...p,name}),clips=Rig.animationClips(THREE,rig);rig.root.userData.animationTiming=direction.timing_policy;
 const binary=await new GLTFExporter().parseAsync(rig.root,{binary:true,animations:clips,onlyVisible:true});
 const loaded=await new GLTFLoader().parseAsync(binary,'');
 if(loaded.animations.length!==8)throw Error(name+': missing animation clips');
 const filename=p.id+'.glb';fs.writeFileSync(path.join(out,filename),Buffer.from(binary));
 index.champions[name]={file:filename,bytes:binary.byteLength,...rig.metrics(),rig:p.rig,weapon:p.weapon,clips:loaded.animations.map(c=>({name:c.name,duration:c.duration,tracks:c.tracks.length})),skills:Object.fromEntries(Object.entries(p.skills).map(([s,v])=>[s,{pose:v.pose,effect:v.effect}]))};
 console.log(name,Math.round(binary.byteLength/1024)+' KiB',rig.metrics().joints+' joints');
}
fs.writeFileSync(path.join(root,'data/marksman-3d-assets.json'),JSON.stringify(index,null,2)+'\n');
console.log('Exported and reimported all 23 GLBs / 184 clips.');

const packed=spawnSync(process.env.PYTHON||"python3",[path.join(root,"scripts/package_marksman_art.py")],{encoding:"utf8"});if(packed.status!==0)throw Error(packed.stderr||"Asset packaging failed");console.log(packed.stdout.trim());
