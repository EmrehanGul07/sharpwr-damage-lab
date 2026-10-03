/* Blender-authored GLB animation adapter. Root movement remains owned by replay. */
(function(scope){'use strict';
function createAvatar(T,template,cloneSkeleton,profile){
 const root=cloneSkeleton(template.scene),mixer=new T.AnimationMixer(root),actions=new Map();
 root.traverse(o=>{if(o.isMesh){o.geometry=o.geometry.clone();o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();o.castShadow=true;o.receiveShadow=true;}});
 for(const clip of template.animations){const a=mixer.clipAction(clip);a.setLoop(T.LoopOnce,1);a.clampWhenFinished=true;actions.set(clip.name,a);}
 const socket=root.getObjectByName('socket_muzzle');let current=null;
 function animate(state={}){const name=actions.has(state.action)?state.action:'Idle',action=actions.get(name);if(current!==action){mixer.stopAllAction();action.reset().play();current=action;}let u=['Idle','Walk'].includes(name)?((state.time||0)/(state.loopDuration||(name==='Walk'?1.2:3)))%1:Math.max(0,Math.min(1,state.progress||0));if(u<0)u+=1;action.time=u*action.getClip().duration;mixer.update(0);root.updateMatrixWorld(true);return{action:name,weight:1};}
 function metrics(){let meshes=0,vertices=0,triangles=0;root.traverse(o=>{if(o.isMesh){meshes++;vertices+=o.geometry.attributes.position.count;triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3;}});return{meshes,vertices,triangles,joints:17,study:true};}
 animate({action:'Idle',time:0});return{root,profile,study:true,sockets:{muzzle:socket},animate,metrics};
}
const API={createAvatar};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanBakedAvatar=API;
})(typeof globalThis!=='undefined'?globalThis:this);
