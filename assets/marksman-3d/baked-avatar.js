/* Blender-authored GLB animation adapter. Root movement remains owned by replay. */
(function(scope){'use strict';
function createAvatar(T,template,cloneSkeleton,profile,{software=false}={}){
 const root=cloneSkeleton(template.scene),mixer=new T.AnimationMixer(root),actions=new Map();
 root.traverse(o=>{if(o.isMesh){o.geometry=o.geometry.clone();o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();o.castShadow=true;o.receiveShadow=true;}});
 for(const clip of template.animations){const a=mixer.clipAction(clip);a.setLoop(T.LoopOnce,1);a.clampWhenFinished=true;actions.set(clip.name,a);}
 const proxies=[];if(software){const skins=[];root.traverse(o=>{if(o.isSkinnedMesh)skins.push(o);});for(const skin of skins){const geometry=skin.geometry.clone();geometry.deleteAttribute('skinIndex');geometry.deleteAttribute('skinWeight');const material=new T.MeshLambertMaterial({color:skin.material.color,side:T.FrontSide});const mesh=new T.Mesh(geometry,material);mesh.name=skin.name+'_CPU';mesh.matrixAutoUpdate=false;skin.parent.add(mesh);skin.visible=false;proxies.push({skin,mesh,bind:skin.geometry.attributes.position.array.slice()});}}
 const socket=root.getObjectByName('socket_muzzle');let current=null;
 function animate(state={}){const name=actions.has(state.action)?state.action:'Idle',action=actions.get(name);if(current!==action){mixer.stopAllAction();action.reset().play();current=action;}let u=['Idle','Walk'].includes(name)?((state.time||0)/(state.loopDuration||(name==='Walk'?1.2:3)))%1:Math.max(0,Math.min(1,state.progress||0));if(u<0)u+=1;action.time=u*action.getClip().duration;mixer.update(0);root.updateMatrixWorld(true);for(const {skin,mesh,bind}of proxies){skin.skeleton.update();const position=mesh.geometry.attributes.position,v=new T.Vector3();for(let i=0;i<position.count;i++){v.fromArray(bind,i*3);skin.applyBoneTransform(i,v);position.setXYZ(i,v.x,v.y,v.z);}position.needsUpdate=true;mesh.geometry.computeVertexNormals();mesh.matrix.copy(skin.matrix);mesh.updateMatrixWorld(true);}
 return{action:name,weight:1};}
 function metrics(){let meshes=0,vertices=0,triangles=0;root.traverse(o=>{if(o.isMesh){meshes++;vertices+=o.geometry.attributes.position.count;triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3;}});return{meshes,vertices,triangles,joints:root.getObjectsByProperty('isBone',true).length,study:true};}
 animate({action:'Idle',time:0});return{root,profile,study:true,sockets:{muzzle:socket},animate,metrics};
}
const API={createAvatar};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanBakedAvatar=API;
})(typeof globalThis!=='undefined'?globalThis:this);
