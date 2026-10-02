// Presentation only: all time, position, damage and resources come from D.
(async()=>{
 if(D.champion!=='Ezreal')return;
 const stage=document.createElement('div');stage.id='stage3d';stage.innerHTML='<div class="scene-label"><b>ARCANE TRAINING GROUNDS</b><span>EZREAL · REPLAY V2</span></div><div class="scene-status">Loading 3D arena…</div><div class="scene-bottom">Drag to orbit · scroll to zoom <label><input id="range3d" type="checkbox" checked> AA range</label><label><input id="path3d" type="checkbox"> Movement trail</label></div>';
 canvas.before(stage);
 const tools=document.createElement('div');tools.className='replay-tools';tools.innerHTML='<div class="camera-modes"><button data-camera="duel" class="active">Duel</button><button data-camera="tactical">Tactical</button><button data-camera="follow">Follow</button><button id="cameraReset">Reset camera</button></div><div><button id="focusView">Focus view</button><button id="loopReplay" aria-pressed="false">Loop OFF</button></div>';stage.before(tools);
 let cameraMode='duel';tools.querySelectorAll('[data-camera]').forEach(button=>button.onclick=()=>{cameraMode=button.dataset.camera;tools.querySelectorAll('[data-camera]').forEach(b=>b.classList.toggle('active',b===button));});
 $('focusView').onclick=()=>{const on=document.querySelector('.wrap').classList.toggle('cinema');$('focusView').textContent=on?'Exit focus':'Focus view';};
 $('loopReplay').onclick=()=>{window.replayLoop=!window.replayLoop;$('loopReplay').textContent=window.replayLoop?'Loop ON':'Loop OFF';$('loopReplay').setAttribute('aria-pressed',String(window.replayLoop));};

 try{
 const THREE=await import('https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js');
 const scene=new THREE.Scene();scene.background=new THREE.Color('#101f29');scene.fog=new THREE.Fog('#101f29',23,55);
 let renderer,software=false;
 try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;}
 catch(error){const {SVGRenderer}=await import('https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/renderers/SVGRenderer.js');renderer=new SVGRenderer();renderer.setQuality('high');renderer.setPrecision(2);software=true;}
 stage.prepend(renderer.domElement);
 const Material=software?class extends THREE.MeshLambertMaterial{constructor(options={}){const {roughness,metalness,...rest}=options;super(rest);}}:THREE.MeshStandardMaterial;
 const camera=new THREE.PerspectiveCamera(38,1,.1,100);let yaw=.9,pitch=.78,zoom=18;const focus=new THREE.Vector3(-2,0,0);let previousFrame='',lastDraw=-1;
 $('cameraReset').onclick=()=>{yaw=.9;pitch=.78;zoom=18;cameraMode='duel';tools.querySelectorAll('[data-camera]').forEach(b=>b.classList.toggle('active',b.dataset.camera==='duel'));};
 scene.add(new THREE.HemisphereLight(0xb9e8ff,0x263528,2.3));const sun=new THREE.DirectionalLight(0xffe0a3,3.8);sun.position.set(-5,15,8);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-16,right:16,top:16,bottom:-16});sun.shadow.bias=-.001;scene.add(sun);
 const mats={stone:new Material({color:0x52655b,roughness:.9}),edge:new Material({color:0x233e37,roughness:1}),blue:new Material({color:0x307c9a,metalness:.35,roughness:.5}),cloth:new Material({color:0x343448,roughness:.8}),skin:new Material({color:0xdca77b,roughness:.7}),gold:new Material({color:0xcba356,metalness:.6,roughness:.35}),hair:new Material({color:0xe6bd69,roughness:.7}),dark:new Material({color:0x212e38,roughness:.7}),target:new Material({color:0x9c5255,roughness:.7})};
 const glow=c=>new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:.9,depthWrite:false});const cyan=glow(0x62efff),gold=glow(0xffd26b),violet=glow(0xb6a2ff);
 function mesh(g,m,x=0,y=0,z=0,parent=scene){const a=new THREE.Mesh(g,m);a.position.set(x,y,z);a.castShadow=true;a.receiveShadow=true;parent.add(a);return a;}
 function box(w,h,d,m,x,y,z,parent){return mesh(new THREE.BoxGeometry(w,h,d),m,x,y,z,parent);}function ball(r,m,x,y,z,parent){return mesh(new THREE.SphereGeometry(r,16,12),m,x,y,z,parent);}
 function ring(r,m,parent=scene){const a=mesh(new THREE.TorusGeometry(r,.025,8,80),m,0,.05,0,parent);a.rotation.x=Math.PI/2;return a;}
 const base=mesh(new THREE.CylinderGeometry(17,17,1,72),mats.edge,0,-.6,0);base.renderOrder=-20;
 for(let x=-12;x<=12;x+=1.65)for(let z=-10;z<=10;z+=1.65){if(x*x+z*z>220)continue;const color=new THREE.Color(0x52655b).multiplyScalar(.88+.12*Math.sin(x*31+z*13));const m=mats.stone.clone();m.color=color;box(1.59,.15,1.59,m,x,-.05,z).renderOrder=-10;}
 const rim=ring(14,new THREE.MeshBasicMaterial({color:0x78957b}));
 for(let j=0;j<24;j++){const a=j*Math.PI/12,r=14.3,x=Math.cos(a)*r,z=Math.sin(a)*r;box(1.3,.5,1.2,mats.edge,x,.13,z);if(j%3===0){box(.5,1.6,.5,mats.dark,x,.9,z);const crystal=mesh(new THREE.OctahedronGeometry(.35),cyan,x,1.95,z);const light=new THREE.PointLight(0x50d9eb,2,5);light.position.copy(crystal.position);scene.add(light);}else{mesh(new THREE.ConeGeometry(.8,2.5,7),new Material({color:0x254b3a}),x,1.6,z);}}
 const rune=ring(2.5,new THREE.MeshBasicMaterial({color:0x77927c,transparent:true,opacity:.25}));ring(3.2,new THREE.MeshBasicMaterial({color:0x77927c,transparent:true,opacity:.15}));
 function character(enemy=false){
 const root=new THREE.Group();scene.add(root);const rig=new THREE.Group();root.add(rig);
 // Articulated silhouette: jacket, shoulder pads, strapped boots and arcane gauntlet.
 mesh(new THREE.CylinderGeometry(.29,.23,.72,8),enemy?mats.target:mats.blue,0,1.26,0,rig);
 box(.43,.12,.43,mats.gold,0,.87,0,rig);box(.13,.6,.46,mats.cloth,0,1.24,0,rig);
 const head=ball(.235,mats.skin,0,1.9,0,rig);head.scale.set(.86,1.1,.9);
 const neck=mesh(new THREE.CylinderGeometry(.09,.1,.16,8),mats.skin,0,1.69,0,rig);
 if(!enemy){
  mesh(new THREE.SphereGeometry(.25,12,8,0,Math.PI*2,0,Math.PI*.55),mats.hair,0,2.01,0,rig);
  for(let i=0;i<5;i++){const tuft=mesh(new THREE.ConeGeometry(.075,.22,5),mats.hair,-.17+i*.08,2.13,.04,rig);tuft.rotation.z=-.4+i*.15;}
  box(.38,.085,.1,mats.dark,0,2.0,.19,rig);for(const sign of [-1,1])ball(.05,mats.gold,sign*.11,2.0,.25,rig);
  const scarf=box(.15,.57,.08,mats.cloth,-.2,1.23,-.27,rig);scarf.rotation.z=-.15;
  box(.58,.13,.48,mats.gold,0,1.59,0,rig);
 }else{
  box(.85,.25,.6,mats.gold,0,1.61,0,rig);
  for(const sign of [-1,1]){const horn=mesh(new THREE.ConeGeometry(.1,.45,8),mats.gold,sign*.25,2.17,0,rig);horn.rotation.z=-sign*.6;}
  box(.45,.27,.45,mats.dark,0,1.08,0,rig);
 }
 const limbs=[],knees=[];for(const sign of [-1,1]){const leg=new THREE.Group();leg.position.set(sign*.16,.85,0);rig.add(leg);mesh(new THREE.CylinderGeometry(.115,.09,.36,8),mats.cloth,0,-.17,0,leg);const knee=new THREE.Group();knee.position.y=-.36;leg.add(knee);mesh(new THREE.CylinderGeometry(.09,.115,.32,8),mats.dark,0,-.16,0,knee);box(.25,.17,.38,mats.dark,0,-.38,.075,knee);box(.23,.07,.27,mats.gold,0,-.16,.02,knee);limbs.push(leg);knees.push(knee);}
 const arms=[],elbows=[];for(const sign of [-1,1]){const arm=new THREE.Group();arm.position.set(sign*.36,1.59,0);rig.add(arm);ball(.14,enemy?mats.gold:mats.blue,0,0,0,arm);mesh(new THREE.CylinderGeometry(.095,.08,.29,8),enemy?mats.target:mats.blue,0,-.17,0,arm);const elbow=new THREE.Group();elbow.position.y=-.33;arm.add(elbow);mesh(new THREE.CylinderGeometry(.09,.085,.27,8),mats.skin,0,-.12,0,elbow);if(sign===1&&!enemy){box(.23,.29,.27,mats.gold,0,-.16,0,elbow);ball(.085,cyan,0,-.14,.16,elbow);}else ball(.085,mats.skin,0,-.29,0,elbow);arms.push(arm);elbows.push(elbow);}
 const selection=ring(.52,new THREE.MeshBasicMaterial({color:enemy?0xf3977d:0x60e6e5,transparent:true,opacity:.65}),root);
 return{root,rig,limbs,knees,arms,elbows,selection};
 }
 const hero=character(),target=character(true);target.root.rotation.y=-Math.PI/2;
 const range=ring(5.75,new THREE.MeshBasicMaterial({color:0x75d3db,transparent:true,opacity:.22}));
 const overlay=document.createElement('div');overlay.className='unit-hud';stage.append(overlay);
 const floating=document.createElement('div');floating.className='floating-hits';stage.append(floating);
 const stacksHud=document.createElement('div');stacksHud.className='replay-stacks';stage.after(stacksHud);
 const skillHud=document.createElement('div');skillHud.className='skill-hud';skillHud.innerHTML=['Q','W','E','R'].map(s=>'<div data-slot="'+s+'"><b>'+s+'</b><span>READY</span></div>').join('');stage.append(skillHud);
 const fx=new THREE.Group();scene.add(fx);
 const shared={line:new THREE.CylinderGeometry(1,1,1,8),orb:new THREE.SphereGeometry(1,software?8:14,software?6:10),ring:new THREE.TorusGeometry(1,.035,6,software?40:64)};
 const pool=[];let poolIndex=0;function clearFX(){poolIndex=0;pool.forEach(o=>o.visible=false);}
 function effect(geometry,material){let o=pool[poolIndex++];if(!o){o=new THREE.Mesh(geometry,material);pool.push(o);fx.add(o);}o.geometry=geometry;o.material=material;o.visible=true;o.position.set(0,0,0);o.scale.set(1,1,1);o.quaternion.identity();return o;}
 function line(a,b,m,width=.025){const delta=b.clone().sub(a),o=effect(shared.line,m);o.position.copy(a).add(b).multiplyScalar(.5);o.scale.set(width,delta.length(),width);if(delta.lengthSq()>0)o.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize());return o;}
 function effectRing(r,m){const o=effect(shared.ring,m);o.scale.setScalar(r);o.rotation.x=Math.PI/2;return o;}
 function effectOrb(r,m,v){const o=effect(shared.orb,m);o.scale.setScalar(r);o.position.copy(v);return o;}
 const heroHud=document.createElement('div');heroHud.className='unit-hud hero-hud';stage.append(heroHud);
 const actionBanner=document.createElement('div');actionBanner.className='action-banner';stage.append(actionBanner);
 const legend=document.createElement('div');legend.className='effect-legend';legend.innerHTML='<span>● AA / Q</span><span>● W mark</span><span>● E blink</span><span>● R wave</span>';stage.after(legend);
 const impacts=D.events.filter(e=>e.phase==='impact'),commands=D.attacks.filter(e=>e.kind!=='attack_launch'),wCommands=commands.filter(e=>e.action==='W'&&e.kind==='cast');
 function recorded(list,t){return ReplayState.lastAt(list,t,selected>=0?D.events[selected].order:Infinity);}
 function at(t){const p=pos(t),angle=Math.asin(Math.sin((p.kite_arc||0)/Math.max(1,p.attack_range||550)*3))/3;return new THREE.Vector3(-p.distance/100*Math.cos(angle),0,p.distance/100*Math.sin(angle));}
 function project(v){const q=v.clone().project(camera);return{x:(q.x*.5+.5)*stage.clientWidth,y:(-.5*q.y+.5)*stage.clientHeight};}
 let dragging=false,px=0,py=0;renderer.domElement.onpointerdown=e=>{dragging=true;px=e.clientX;py=e.clientY;renderer.domElement.setPointerCapture(e.pointerId);};renderer.domElement.onpointerup=()=>dragging=false;renderer.domElement.onpointermove=e=>{if(dragging){cameraMode='free';tools.querySelectorAll('[data-camera]').forEach(b=>b.classList.remove('active'));yaw-=(e.clientX-px)*.008;pitch=Math.max(.35,Math.min(1.3,pitch+(e.clientY-py)*.006));px=e.clientX;py=e.clientY;}};renderer.domElement.onwheel=e=>{e.preventDefault();cameraMode='free';zoom=Math.max(12,Math.min(36,zoom+e.deltaY*.01));};
 const flights=D.visual_flights||[];const status=stage.querySelector('.scene-status');status.textContent='LIVE ENGINE TRACE';status.classList.add('ready');canvas.style.display='none';
 window.render3d=t=>{
 const w=stage.clientWidth,h=stage.clientHeight,signature=[t,selected,w,h,yaw,pitch,zoom,cameraMode,$('range3d').checked,$('path3d').checked].join('|');
 if(signature===previousFrame)return;
 if(software&&playing&&lastDraw>=0&&Math.abs(t-lastDraw)<1/24)return;
 previousFrame=signature;lastDraw=t;
 if(stage.dataset.size!==w+'x'+h){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();stage.dataset.size=w+'x'+h;}
 const p=pos(t),v=at(t);hero.root.position.copy(v);hero.root.rotation.y=Math.atan2(-v.x,-v.z);range.position.copy(v);range.scale.setScalar((p.attack_range||550)/575);range.visible=$('range3d').checked;
 let viewYaw=yaw,viewPitch=pitch,viewZoom=zoom;
 if(cameraMode==='duel'){focus.copy(v).multiplyScalar(.5);viewZoom=Math.max(16,Math.min(32,p.distance/100*1.5+9));}
 else if(cameraMode==='tactical'){focus.copy(v).multiplyScalar(.5);viewYaw=.12;viewPitch=1.15;viewZoom=Math.max(17,p.distance/100*1.6+9);}
 else if(cameraMode==='follow'){focus.copy(v).multiplyScalar(.65);viewZoom=Math.max(14,p.distance/100*1.4+8);}
 camera.position.set(focus.x+Math.sin(viewYaw)*Math.cos(viewPitch)*viewZoom,Math.sin(viewPitch)*viewZoom,focus.z+Math.cos(viewYaw)*Math.cos(viewPitch)*viewZoom);camera.lookAt(focus);camera.updateMatrixWorld();
 const a=at(Math.max(0,t-.03)),b=at(Math.min(D.duration,t+.03)),moving=a.distanceTo(b)>.004,gait=(p.kite_arc||0)/18+p.distance/22;
 hero.limbs.forEach((l,i)=>l.rotation.x=moving?Math.sin(gait+i*Math.PI)*.5:0);hero.knees.forEach((k,i)=>k.rotation.x=moving?Math.max(0,-Math.sin(gait+i*Math.PI))*.6:0);hero.rig.position.y=moving?Math.abs(Math.sin(gait))*.035:0;
 const command=recorded(commands,t),age=command?t-command.time:99,activeEnd=command?(command.windup_end??command.cast_end??command.time):t;
 const posing=command&&(t<=activeEnd||age<.12),action=command?.action;
 hero.arms.forEach((arm,i)=>{arm.rotation.x=moving?Math.sin(gait+i*Math.PI)*.22:0;arm.rotation.z=0;});hero.elbows.forEach(elbow=>elbow.rotation.x=-.15);hero.rig.rotation.z=0;
 if(posing){const u=Math.min(1,age/Math.max(.05,activeEnd-command.time));hero.arms[1].rotation.x=-1.45;hero.elbows[1].rotation.x=-.2;
  if(action==='W'){hero.elbows[1].rotation.x=-.8+u*.6;hero.arms[1].rotation.z=-.2;}
  else hero.arms[1].rotation.z=0;
  if(action==='R'){hero.arms[0].rotation.x=-1.4;hero.elbows[0].rotation.x=-.35;hero.elbows[1].rotation.x=-.65;hero.rig.rotation.z=-.1;}
  if(action==='E'){hero.arms[0].rotation.z=.4;hero.arms[1].rotation.z=-.4;}
 }else hero.arms.forEach(arm=>arm.rotation.z=0);
 actionBanner.textContent=posing?(action==='AA'?'BASIC ATTACK · WINDUP':action+' · CASTING'):(moving?'REPOSITIONING':'READY');actionBanner.dataset.action=posing?action:'move';
 clearFX();
 for(const f of flights){if(t<f.launch||t>f.impact||f.impact<=f.launch)continue;const u=(t-f.launch)/(f.impact-f.launch),o=at(f.launch).add(new THREE.Vector3(0,1.25,0)),end=new THREE.Vector3(0,1.1,0),head=o.clone().lerp(end,u),trail=o.clone().lerp(end,Math.max(0,u-.2));const material=f.action==='W'?gold:f.action==='R'?violet:cyan;if(f.action==='R'){const direction=end.clone().sub(o).normalize(),side=new THREE.Vector3(-direction.z,0,direction.x).multiplyScalar(1.45);for(let j=0;j<12;j++){const sa=-1+2*j/12,sb=-1+2*(j+1)/12,pa=head.clone().addScaledVector(side,sa).addScaledVector(direction,-.32*sa*sa),pb=head.clone().addScaledVector(side,sb).addScaledVector(direction,-.32*sb*sb);line(pa,pb,gold,.09);line(pa.clone().add(new THREE.Vector3(0,.35,0)),pb.clone().add(new THREE.Vector3(0,.35,0)),cyan,.04);}}else{line(trail,head,material,f.action==='AA'?.035:.08);effectOrb(f.action==='W'?.18:f.action==='Q'?.12:.065,material,head);if(f.action==='Q'){for(let j=1;j<=3;j++){const mote=o.clone().lerp(end,Math.max(0,u-j*.045));effectOrb(.055,cyan,mote);}}}}
 const latestHit=recorded(impacts,t);
 if(ReplayState.markActive(wCommands,impacts,t,selected>=0?D.events[selected].order:Infinity)){const mark=effectRing(.58+.04*Math.sin(t*7),gold);mark.position.y=1.1;mark.rotation.x=0;mark.rotation.y=t*2;}
 for(const e of D.events){if(!ReplayState.visible(e,t,selected>=0?D.events[selected].order:Infinity))continue;const dt=t-e.time;if(e.phase!=='impact'||dt<0||dt>.38)continue;const hit=effectRing(.3+dt*2,e.action.startsWith('W')?gold:cyan);hit.position.y=.12;}
 for(const e of D.attacks){const dt=t-e.time;if(e.action!=='E'||e.kind!=='cast'||dt<0||dt>.55)continue;for(const sample of [Math.max(0,e.time-.001),Math.min(D.duration,e.cast_end||e.time+.05)]){const portal=effectRing(.55+dt*.9,violet);portal.position.copy(at(sample));portal.position.y=.18;portal.rotation.y=dt*4;line(portal.position.clone(),portal.position.clone().add(new THREE.Vector3(0,1.8*(1-dt/.55),0)),cyan,.025);}}
 if($('path3d').checked){for(let j=1;j<=16;j++){const ta=Math.max(0,t-1.6+j*.1),tb=Math.max(0,t-1.6+(j-1)*.1),a=at(ta),b=at(tb);a.y=b.y=.08;if(a.distanceTo(b)>.002)line(a,b,violet,.012);}}
 for(const e of impacts){if(!ReplayState.visible(e,t,selected>=0?D.events[selected].order:Infinity))continue;const dt=t-e.time;if(e.action!=='W detonation'||dt<0||dt>.45)continue;for(let j=0;j<8;j++){const angle=j*Math.PI/4,rad=.2+dt*2.6;effectOrb(.04,gold,new THREE.Vector3(Math.cos(angle)*rad,1.1+Math.sin(dt*5)*.2,Math.sin(angle)*rad));}}
 const resource=[...D.events].reverse().find(e=>ReplayState.visible(e,t,selected>=0?D.events[selected].order:Infinity)&&(e.mana_after!==undefined||e.mana!==undefined)),mana=resource?.mana_after??resource?.mana;
 const heroQ=project(v.clone().add(new THREE.Vector3(0,2.6,0)));heroHud.style.left=heroQ.x+'px';heroHud.style.top=heroQ.y+'px';heroHud.innerHTML='<b>EZREAL</b><span>'+(mana===null||mana===undefined?'Mana —':Math.floor(mana)+' MANA')+'</span>';
 const hp=latestHit?.hp_after??D.max_hp,q=project(new THREE.Vector3(0,2.7,0));overlay.style.left=q.x+'px';overlay.style.top=q.y+'px';overlay.innerHTML='<b>'+String(D.target).split(' • ').pop().replace(/[<>&]/g,'')+'</b><div><i style="width:'+Math.max(0,hp/D.max_hp*100)+'%"></i></div><span>'+Math.ceil(hp).toLocaleString()+' HP</span>';target.rig.rotation.z=hp<=0?-.9:0;target.rig.position.y=hp<=0?-.4:0;
 floating.replaceChildren();D.events.filter(e=>e.phase==='impact'&&ReplayState.visible(e,t,selected>=0?D.events[selected].order:Infinity)&&t>=e.time&&t-e.time<.8&&e.damage>0).slice(-4).forEach((e,i)=>{const d=document.createElement('div'),q=project(new THREE.Vector3(0,2.8+(t-e.time)*1.4+i*.2,0));d.style.cssText='left:'+q.x+'px;top:'+q.y+'px;opacity:'+(1-(t-e.time)/.8);d.textContent=e.action+' · '+Math.round(e.damage);d.dataset.type=e.damage_components?.some(c=>c.damage_type==='magic')?'magic':'physical';floating.append(d);});
 const cd=[...D.events].reverse().find(e=>ReplayState.visible(e,t,selected>=0?D.events[selected].order:Infinity)&&e.cooldowns);skillHud.querySelectorAll('[data-slot]').forEach(el=>{const s=el.dataset.slot,remaining=Math.max(0,(cd?.cooldowns?.[s]||0)-(t-(cd?.time||0)));el.classList.toggle('cooling',remaining>0);el.classList.toggle('casting',command?.action===s&&age<.4);el.querySelector('span').textContent=remaining>0?remaining.toFixed(1)+'s':'READY';});
 const snapshot=latestHit?.after||{};stacksHud.textContent='STACKS · '+Object.entries(snapshot.items||{}).filter(([k,v])=>typeof v==='number'&&v>0).map(([k,v])=>k.replaceAll('_',' ')+' '+v.toFixed(1)).join(' · ')+(Object.values(snapshot.items||{}).some(v=>typeof v==='number'&&v>0)?' · ':'')+'Rising Spell Force '+(snapshot.stacks?.rising_spell_force||0);
 renderer.render(scene,camera);
 };
 renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();canvas.style.display='block';stage.style.display='none';window.render3d=null;});
 }catch(err){stage.remove();tools.remove();console.warn('3D replay unavailable; showing recorded 2D replay.',err);}
})();
