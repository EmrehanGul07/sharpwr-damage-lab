/* Blender-authored GLB animation adapter. Root movement remains owned by replay. */
(function(scope){'use strict';
function createAvatar(T,template,cloneSkeleton,profile,{software=false}={}){
 const asset=cloneSkeleton(template.scene),root=new T.Group();root.name="SharpWR_world";root.add(asset);const mixer=new T.AnimationMixer(asset),actions=new Map();
 root.traverse(o=>{if(o.isMesh){o.geometry=o.geometry.clone();o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();o.castShadow=true;o.receiveShadow=true;}});
 // Three treats the track name "root" as the mixer object; bind the actual exported bone explicitly.
 const boneRoot=asset.getObjectByName("root");
 for(const original of template.animations){const clip=original.clone();if(boneRoot)for(const track of clip.tracks)if(track.name.startsWith("root."))track.name=boneRoot.uuid+track.name.slice(4);const a=mixer.clipAction(clip);a.setLoop(T.LoopOnce,1);a.clampWhenFinished=true;actions.set(clip.name,a);}
 const proxies=[];if(software){const skins=[];root.traverse(o=>{if(o.isSkinnedMesh)skins.push(o);});for(const skin of skins){const geometry=skin.geometry.clone();geometry.deleteAttribute('skinIndex');geometry.deleteAttribute('skinWeight');const material=new T.MeshLambertMaterial({color:skin.material.color,side:T.FrontSide});const mesh=new T.Mesh(geometry,material);mesh.name=skin.name+'_CPU';mesh.matrixAutoUpdate=false;skin.parent.add(mesh);skin.visible=false;proxies.push({skin,mesh,bind:skin.geometry.attributes.position.array.slice()});}}
 const bones=asset.getObjectsByProperty('isBone',true),snapshot=()=>bones.map(b=>({p:b.position.clone(),q:b.quaternion.clone(),s:b.scale.clone()}));let live=null,transition=null;
 const socket=root.getObjectByName('socket_muzzle');let current=null;
 function animate(state={}){const name=actions.has(state.action)?state.action:'Idle',action=actions.get(name);if(current!==action){mixer.stopAllAction();action.reset().play();current=action;}let u=name==='Walk'&&Number.isFinite(state.gaitPhase)?(state.gaitPhase/(Math.PI*2))%1:['Idle','Walk'].includes(name)?((state.time||0)/(state.loopDuration||(name==='Walk'?1.2:3)))%1:Math.max(0,Math.min(1,state.progress||0));if(u<0)u+=1;action.time=u*action.getClip().duration;mixer.update(0);
 if(state.live){const t=state.time||0,progress=state.progress||0,reset=!live||t<live.time||t-live.time>.25,changed=live&&(name!==live.name||!['Idle','Walk'].includes(name)&&progress<live.progress-.1);
  if(reset)transition=null;else if(changed)transition={from:live.pose,start:t,duration:['Idle','Walk'].includes(name)?.12:Math.max(.015,Math.min(.07,Number.isFinite(state.blendSeconds)?state.blendSeconds:.07))};
  if(transition){const u=Math.max(0,Math.min(1,(t-transition.start)/transition.duration)),alpha=u*u*(3-2*u);bones.forEach((b,i)=>{const from=transition.from[i];b.position.lerpVectors(from.p,b.position,alpha);b.quaternion.slerpQuaternions(from.q,b.quaternion,alpha);b.scale.lerpVectors(from.s,b.scale,alpha);});if(u>=1)transition=null;}
  live={name,time:t,progress,pose:snapshot()};
 }
 root.updateMatrixWorld(true);for(const {skin,mesh,bind}of proxies){skin.skeleton.update();const position=mesh.geometry.attributes.position,v=new T.Vector3();for(let i=0;i<position.count;i++){v.fromArray(bind,i*3);skin.applyBoneTransform(i,v);position.setXYZ(i,v.x,v.y,v.z);}position.needsUpdate=true;mesh.geometry.computeVertexNormals();mesh.matrix.copy(skin.matrix);mesh.updateMatrixWorld(true);}
 return{action:name,weight:1};}
 function metrics(){let meshes=0,vertices=0,triangles=0;root.traverse(o=>{if(o.isMesh){meshes++;vertices+=o.geometry.attributes.position.count;triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3;}});return{meshes,vertices,triangles,joints:root.getObjectsByProperty('isBone',true).length,study:true};}
 animate({action:'Idle',time:0});return{root,profile,study:true,sockets:{muzzle:socket},animate,metrics};
}
const API={createAvatar};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanBakedAvatar=API;
})(typeof globalThis!=='undefined'?globalThis:this);
