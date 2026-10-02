// Presentation only: all time, position, damage and resources come from D.
(async()=>{
 if(D.champion!=='Ezreal')return;
 const stage=document.createElement('div');stage.id='stage3d';stage.innerHTML='<div class="scene-label"><b>ARCANE TRAINING GROUNDS</b><span>EZREAL · 3D COMBAT REPLAY</span></div><div class="scene-status">Loading 3D arena…</div><div class="scene-bottom">Drag to orbit · scroll to zoom <label><input id="range3d" type="checkbox" checked> Range</label></div>';
 canvas.before(stage);
 try{
 const THREE=await import('https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js');
 const scene=new THREE.Scene();scene.background=new THREE.Color('#101f29');scene.fog=new THREE.Fog('#101f29',23,55);
 let renderer,software=false;
 try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;}
 catch(error){const {SVGRenderer}=await import('https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/renderers/SVGRenderer.js');renderer=new SVGRenderer();renderer.setQuality('high');renderer.setPrecision(2);software=true;}
 stage.prepend(renderer.domElement);
 const Material=software?class extends THREE.MeshLambertMaterial{constructor(options){const {roughness,metalness,...rest}=options;super(rest);}}:THREE.MeshStandardMaterial;
 const camera=new THREE.PerspectiveCamera(38,1,.1,100);let yaw=.9,pitch=.78,zoom=22;const focus=new THREE.Vector3(-2,0,0);
 scene.add(new THREE.HemisphereLight(0xb9e8ff,0x263528,2.3));const sun=new THREE.DirectionalLight(0xffe0a3,3.8);sun.position.set(-5,15,8);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-16,right:16,top:16,bottom:-16});sun.shadow.bias=-.001;scene.add(sun);
 const mats={stone:new Material({color:0x52655b,roughness:.9}),edge:new Material({color:0x233e37,roughness:1}),blue:new Material({color:0x307c9a,metalness:.35,roughness:.5}),cloth:new Material({color:0x343448,roughness:.8}),skin:new Material({color:0xdca77b,roughness:.7}),gold:new Material({color:0xcba356,metalness:.6,roughness:.35}),hair:new Material({color:0xe6bd69,roughness:.7}),dark:new Material({color:0x212e38,roughness:.7}),target:new Material({color:0x9c5255,roughness:.7})};
 const glow=c=>new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:.9,depthWrite:false});const cyan=glow(0x62efff),gold=glow(0xffd26b),violet=glow(0xb6a2ff);
 function mesh(g,m,x=0,y=0,z=0,parent=scene){const a=new THREE.Mesh(g,m);a.position.set(x,y,z);a.castShadow=true;a.receiveShadow=true;parent.add(a);return a;}
 function box(w,h,d,m,x,y,z,parent){return mesh(new THREE.BoxGeometry(w,h,d),m,x,y,z,parent);}function ball(r,m,x,y,z,parent){return mesh(new THREE.SphereGeometry(r,16,12),m,x,y,z,parent);}
 function ring(r,m,parent=scene){const a=mesh(new THREE.TorusGeometry(r,.025,8,80),m,0,.05,0,parent);a.rotation.x=Math.PI/2;return a;}
 mesh(new THREE.CylinderGeometry(17,17,1,72),mats.edge,0,-.6,0);
 for(let x=-12;x<=12;x+=1.65)for(let z=-10;z<=10;z+=1.65){if(x*x+z*z>220)continue;const color=new THREE.Color(0x52655b).multiplyScalar(.88+.12*Math.sin(x*31+z*13));const m=mats.stone.clone();m.color=color;box(1.59,.15,1.59,m,x,-.05,z);}
 const rim=ring(14,new THREE.MeshBasicMaterial({color:0x78957b}));
 for(let j=0;j<24;j++){const a=j*Math.PI/12,r=14.3,x=Math.cos(a)*r,z=Math.sin(a)*r;box(1.3,.5,1.2,mats.edge,x,.13,z);if(j%3===0){box(.5,1.6,.5,mats.dark,x,.9,z);const crystal=mesh(new THREE.OctahedronGeometry(.35),cyan,x,1.95,z);const light=new THREE.PointLight(0x50d9eb,2,5);light.position.copy(crystal.position);scene.add(light);}else{mesh(new THREE.ConeGeometry(.8,2.5,7),new Material({color:0x254b3a}),x,1.6,z);}}
 const rune=ring(2.5,new THREE.MeshBasicMaterial({color:0x77927c,transparent:true,opacity:.25}));ring(3.2,new THREE.MeshBasicMaterial({color:0x77927c,transparent:true,opacity:.15}));
 function character(enemy=false){const root=new THREE.Group();scene.add(root);const rig=new THREE.Group();root.add(rig);const torso=box(.65,.78,.42,enemy?mats.target:mats.blue,0,1.25,0,rig);const head=ball(.25,mats.skin,0,1.96,0,rig);if(!enemy){const hair=mesh(new THREE.SphereGeometry(.27,12,8,0,Math.PI*2,0,Math.PI*.6),mats.hair,0,2.06,0,rig);box(.13,.36,.39,mats.gold,.4,1.55,0,rig);box(.52,.11,.46,mats.gold,0,.88,0,rig);box(.35,.14,.12,mats.dark,0,1.99,.23,rig);ball(.13,cyan,.52,1.42,.25,rig);}else{box(.95,.28,.57,mats.gold,0,1.67,0,rig);for(const sign of [-1,1]){const horn=mesh(new THREE.ConeGeometry(.1,.48,8),mats.gold,sign*.28,2.18,0,rig);horn.rotation.z=-sign*.5;}}
 const limbs=[];for(const sign of [-1,1]){const leg=new THREE.Group();leg.position.set(sign*.18,.84,0);rig.add(leg);box(.23,.66,.24,mats.dark,0,-.3,0,leg);box(.26,.17,.4,mats.dark,0,-.68,.07,leg);limbs.push(leg);}const arm=new THREE.Group();arm.position.set(.43,1.6,0);rig.add(arm);box(.19,.55,.2,enemy?mats.target:mats.blue,0,-.25,0,arm);box(.23,.25,.25,mats.gold,0,-.5,0,arm);box(.18,.6,.19,enemy?mats.target:mats.blue,-.83,-.27,0,arm);
 const selection=ring(.56,new THREE.MeshBasicMaterial({color:enemy?0xf3977d:0x60e6e5,transparent:true,opacity:.65}),root);return{root,rig,limbs,arm,selection};}
 const hero=character(),target=character(true);target.root.rotation.y=-Math.PI/2;
 const range=ring(5.75,new THREE.MeshBasicMaterial({color:0x75d3db,transparent:true,opacity:.22}));
 const overlay=document.createElement('div');overlay.className='unit-hud';stage.append(overlay);
 const floating=document.createElement('div');floating.className='floating-hits';stage.append(floating);
 const stacksHud=document.createElement('div');stacksHud.className='replay-stacks';stage.after(stacksHud);
 const skillHud=document.createElement('div');skillHud.className='skill-hud';skillHud.innerHTML=['Q','W','E','R'].map(s=>'<div data-slot="'+s+'"><b>'+s+'</b><span>READY</span></div>').join('');stage.append(skillHud);
 const fx=new THREE.Group();scene.add(fx);const owned=[];function clearFX(){while(fx.children.length)fx.remove(fx.children[0]);for(const g of owned)g.dispose();owned.length=0;}function line(a,b,m,width=.025){const delta=b.clone().sub(a),g=new THREE.CylinderGeometry(width,width,delta.length(),8);owned.push(g);const o=new THREE.Mesh(g,m);o.position.copy(a).add(b).multiplyScalar(.5);o.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize());fx.add(o);return o;}
 function at(t){const p=pos(t),angle=Math.asin(Math.sin((p.kite_arc||0)/Math.max(1,p.attack_range||550)*3))/3;return new THREE.Vector3(-p.distance/100*Math.cos(angle),0,p.distance/100*Math.sin(angle));}
 function project(v){const q=v.clone().project(camera);return{x:(q.x*.5+.5)*stage.clientWidth,y:(-.5*q.y+.5)*stage.clientHeight};}
 let dragging=false,px=0,py=0;renderer.domElement.onpointerdown=e=>{dragging=true;px=e.clientX;py=e.clientY;renderer.domElement.setPointerCapture(e.pointerId);};renderer.domElement.onpointerup=()=>dragging=false;renderer.domElement.onpointermove=e=>{if(dragging){yaw-=(e.clientX-px)*.008;pitch=Math.max(.35,Math.min(1.3,pitch+(e.clientY-py)*.006));px=e.clientX;py=e.clientY;}};renderer.domElement.onwheel=e=>{e.preventDefault();zoom=Math.max(12,Math.min(36,zoom+e.deltaY*.01));};
 const flights=D.visual_flights||[];const status=stage.querySelector('.scene-status');status.textContent='LIVE ENGINE TRACE';status.classList.add('ready');canvas.style.display='none';
 window.render3d=t=>{
 const w=stage.clientWidth,h=stage.clientHeight;if(stage.dataset.size!==w+'x'+h){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();stage.dataset.size=w+'x'+h;}
 camera.position.set(focus.x+Math.sin(yaw)*Math.cos(pitch)*zoom,Math.sin(pitch)*zoom,Math.cos(yaw)*Math.cos(pitch)*zoom);camera.lookAt(focus);
 const p=pos(t),v=at(t);hero.root.position.copy(v);hero.root.rotation.y=Math.atan2(-v.x,-v.z);range.position.copy(v);range.scale.setScalar((p.attack_range||550)/575);range.visible=$('range3d').checked;
 const a=at(Math.max(0,t-.03)),b=at(Math.min(D.duration,t+.03)),moving=a.distanceTo(b)>.004;const gait=(p.kite_arc||0)/18+p.distance/22;hero.limbs.forEach((l,i)=>l.rotation.x=moving?Math.sin(gait+i*Math.PI)*.5:0);hero.rig.position.y=moving?Math.abs(Math.sin(gait))*.035:0;
 const command=[...D.attacks].reverse().find(e=>e.time<=t&&e.kind!=='attack_launch');const age=command?t-command.time:99;hero.arm.rotation.x=age<.32?-1.2*Math.sin(Math.min(1,age/.12)*Math.PI*.5):-.1;
 clearFX();
 for(const f of flights){if(t<f.launch||t>f.impact||f.impact<=f.launch)continue;const u=(t-f.launch)/(f.impact-f.launch),o=at(f.launch).add(new THREE.Vector3(0,1.25,0)),end=new THREE.Vector3(0,1.1,0),head=o.clone().lerp(end,u),trail=o.clone().lerp(end,Math.max(0,u-.2));const material=f.action==='W'?gold:f.action==='R'?violet:cyan;if(f.action==='R'){const direction=end.clone().sub(o).normalize(),side=new THREE.Vector3(-direction.z,0,direction.x).multiplyScalar(1.45);line(head.clone().sub(side),head.clone().add(side),gold,.12);line(head.clone().sub(side).add(new THREE.Vector3(0,.45,0)),head.clone().add(side).add(new THREE.Vector3(0,.45,0)),cyan,.055);}else{line(trail,head,material,f.action==='AA'?.035:.08);const orb=ball(f.action==='W'?.16:.1,material,head.x,head.y,head.z,fx);owned.push(orb.geometry);}}
 const latestHit=[...D.events].reverse().find(e=>e.phase==='impact'&&e.time<=t);
 const wCast=[...D.attacks].reverse().find(e=>e.kind==='cast'&&e.action==='W'&&e.impact_time<=t);
 const detonated=wCast&&D.events.some(e=>e.time>=wCast.impact_time&&e.time<=t&&e.phase==='impact'&&e.action==='W detonation');
 if(wCast&&!detonated&&t-wCast.impact_time<4){const mark=ring(.65,gold,fx);owned.push(mark.geometry);mark.position.y=1.1;mark.rotation.x=0;mark.rotation.y=t*2;}
 for(const e of D.events){const dt=t-e.time;if(e.phase!=='impact'||dt<0||dt>.38)continue;const hit=ring(.3+dt*2,e.action.startsWith('W')?gold:cyan,fx);owned.push(hit.geometry);hit.position.y=.12;}
 for(const e of D.attacks){const dt=t-e.time;if(e.action!=='E'||e.kind!=='cast'||dt<0||dt>.55)continue;for(const sample of [Math.max(0,e.time-.001),Math.min(D.duration,e.cast_end||e.time+.05)]){const portal=ring(.55+dt*.9,violet,fx);owned.push(portal.geometry);portal.position.copy(at(sample));portal.position.y=.18;portal.rotation.y=dt*4;line(portal.position.clone(),portal.position.clone().add(new THREE.Vector3(0,1.8*(1-dt/.55),0)),cyan,.025);}}
 const hp=latestHit?.hp_after??D.max_hp,q=project(new THREE.Vector3(0,2.7,0));overlay.style.left=q.x+'px';overlay.style.top=q.y+'px';overlay.innerHTML='<b>'+String(D.target).split(' • ').pop().replace(/[<>&]/g,'')+'</b><div><i style="width:'+Math.max(0,hp/D.max_hp*100)+'%"></i></div><span>'+Math.ceil(hp).toLocaleString()+' HP</span>';target.rig.rotation.z=hp<=0?-.9:0;target.rig.position.y=hp<=0?-.4:0;
 floating.replaceChildren();D.events.filter(e=>e.phase==='impact'&&t>=e.time&&t-e.time<.8&&e.damage>0).slice(-4).forEach((e,i)=>{const d=document.createElement('div'),q=project(new THREE.Vector3(0,2.8+(t-e.time)*1.4+i*.2,0));d.style.cssText='left:'+q.x+'px;top:'+q.y+'px;opacity:'+(1-(t-e.time)/.8);d.textContent=Math.round(e.damage);floating.append(d);});
 const cd=[...D.events].reverse().find(e=>e.time<=t&&e.cooldowns);skillHud.querySelectorAll('[data-slot]').forEach(el=>{const s=el.dataset.slot,remaining=Math.max(0,(cd?.cooldowns?.[s]||0)-(t-(cd?.time||0)));el.classList.toggle('cooling',remaining>0);el.classList.toggle('casting',command?.action===s&&age<.4);el.querySelector('span').textContent=remaining>0?remaining.toFixed(1)+'s':'READY';});
 const snapshot=latestHit?.after||{};stacksHud.textContent='Recorded stacks · '+Object.entries(snapshot.items||{}).filter(([k,v])=>typeof v==='number'&&v>0).map(([k,v])=>k.replaceAll('_',' ')+' '+v.toFixed(1)).join(' · ')+' · Rising Spell Force '+(snapshot.stacks?.rising_spell_force||0);
 renderer.render(scene,camera);
 };
 renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();canvas.style.display='block';stage.style.display='none';window.render3d=null;});
 }catch(err){stage.remove();console.warn('3D replay unavailable; showing recorded 2D replay.',err);}
})();
