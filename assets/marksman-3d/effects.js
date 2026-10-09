/* Deterministic, seek-safe presentation effects. No random state or damage logic. */
(function(scope){'use strict';
const STYLE={
 focus:['aura',.7,1,'frost'],fan:['fan',1.0,7,'frost'],hawk:['bird',1.4,1,'frost'],ice_arrow:['arrow',1.7,1,'frost'],
 pierce:['pierce',1.2,1,'hextech'],trap:['trap',.8,1,'hextech'],net:['net',1.1,1,'hextech'],sniper:['sniper',1.3,1,'hextech'],
 bomb:['bomb',1.1,1,'hextech'],fire_path:['path',1.1,1,'ember'],gatling:['barrage',.85,7,'powder'],rocket:['rocket',1.2,1,'hextech'],
 axe_orbit:['orbit_axe',.9,2,'steel'],rush:['speed',.9,1,'blood'],axe_pair:['axe',1.0,2,'steel'],axe_return:['boomerang',1.7,2,'blood'],
 mystic_arrow:['arcane_arrow',1,1,'arcane'],flux:['flux',1,1,'arcane'],blink:['blink',1,1,'arcane'],crescent:['crescent',1.8,1,'arcane'],
 grenade:['grenade',.8,1,'rose'],flourish:['beam',1.3,1,'rose'],lotus:['lotus',.9,1,'rose'],curtain:['sniper',1.5,1,'rose'],
 switch:['weapon_shift',.7,1,'chaos'],zap:['lightning_beam',1.1,1,'chaos'],chompers:['chompers',1,3,'chaos'],mega_rocket:['rocket',2,1,'chaos'],
 missile_swarm:['swarm',1,6,'void'],void_lance:['lance',1.45,1,'void'],supercharge:['speed',1.1,1,'void'],void_dash:['dash_shield',1.1,1,'void'],
 spear:['spear',1.3,1,'spectral'],sentinel:['ghost',1,1,'spectral'],rend:['rend',1,7,'spectral'],oath:['summon',1.4,1,'spectral'],
 spit:['acid',1,1,'acid'],bio_barrage:['mouth_aura',.8,1,'acid'],ooze:['ooze',1.2,1,'acid'],artillery:['artillery',1.5,1,'acid'],
 light_beam:['beam',1.3,1,'light'],star:['star',1.1,1,'light'],light_dash:['dash',1,1,'light'],culling:['barrage',1.2,10,'light'],
 ricochet:['ricochet',1,2,'powder'],strut:['speed',.8,1,'powder'],rain:['rain',1.5,10,'powder'],bullet_cone:['cone_barrage',1.8,12,'powder'],
 flair:['slash_bullet',1,1,'steel'],blade_whirl:['blade_ring',1.1,2,'steel'],wild_rush:['dash_slash',1.1,1,'steel'],inferno:['radial_barrage',1.55,12,'blood'],
 dark_beam:['dark_beam',1.3,1,'mist'],root:['root',1.1,1,'mist'],mist:['mist',1.2,1,'mist'],dawning:['wide_beam',1.9,1,'mist'],
 boomerang:['boomerang',1.2,1,'sand'],ricochet_blade:['weapon_aura',.9,1,'sand'],spell_shield:['shield',1.15,1,'sand'],hunt:['rally',1.15,1,'sand'],
 fire_breath:['flame',1.15,1,'ember'],sneeze:['sneeze',1.3,1,'ember'],wing_flight:['flight',1,1,'ember'],mother_flame:['dragon_shadow',2,1,'ember'],
 rapid:['weapon_aura',.8,1,'powder'],rocket_jump:['jump',1.25,1,'powder'],charge:['charge',1,1,'powder'],buster:['cannon_ball',1.55,1,'powder'],
 ambush:['stealth',1,1,'toxic'],cask:['cask',1.2,1,'toxic'],contaminate:['poison_burst',1.2,6,'toxic'],spray:['weapon_aura',1.1,1,'toxic'],
 charged_arrow:['charged_arrow',1.45,1,'corruption'],blight:['aura',.8,1,'corruption'],arrow_rain:['arrow_rain',1.5,8,'corruption'],corruption:['chains',1.5,1,'corruption'],
 tumble:['roll_trail',.85,1,'silver'],silver_rings:['rings',1,3,'silver'],condemn:['heavy_bolt',1.2,1,'silver'],final_hour:['aura',1.15,1,'silver'],
 feather_pair:['feather',1,2,'feather'],plumage:['feather_orbit',1,5,'feather'],recall:['recall_feathers',1.35,7,'feather'],feather_fan:['feather_fan',1.6,9,'feather'],
 cultivate:['beads',1,8,'spirit'],spirit_arc:['spirit_arc',1.3,1,'spirit'],kanmei:['glide',1.15,1,'spirit'],transcend:['ascend',1.7,1,'spirit'],
 // Empowered basic attacks while an instant buff is up (art direction: empowered_attack).
 spray_bolt:['pierce',1.5,1,'toxic'],focus_flurry:['fan',.55,4,'frost'],spinning_axe:['axe',1.1,1,'blood'],plumage_shot:['feather',1,2,'feather'],bio_spit:['acid',1.35,1,'acid'],ricochet_shot:['disc',.9,1,'sand'],
 spark:['spark_bolt',1,5,'electric'],laser:['lightning_beam',1.35,1,'electric'],surge:['rail',1.2,1,'electric'],lightning:['lightning_storm',1.7,8,'electric']
};
// Base-skin color direction, with separate spell colors instead of one model-wide tint.
const SPELL_COLORS={
 Ashe:['#68c9ff','#70bfff','#9bddff','#63bcff','#84ddff'],Caitlyn:['#e8c790','#efcf91','#b99768','#76dce9','#f5c49a'],Corki:['#ffbd56','#ff9541','#ef6a2b','#ffd577','#ff9c40'],Draven:['#d9dbe4','#ded8c5','#e6965f','#dbd9d1','#e19c58'],Ezreal:['#ffd95a','#71e6ff','#ffd948','#ffe56c','#ffc33e'],Jhin:['#eab4d6','#b473d2','#da96d5','#a84bcf','#f4b97d'],Jinx:['#f2b3df','#ebc77c','#67d1ff','#ec9869','#ff8e42'],"Kai'Sa":['#b46aff','#cf83ff','#ca8eff','#a473ec','#cba0ff'],Kalista:['#69d8d2','#67ddda','#8acacb','#61ddd8','#7cdfdb'],"Kog'Maw":['#b7e954','#a0dc49','#a5df66','#90d94c','#a7e845'],Lucian:['#f6e9b8','#ffe39b','#98d8ff','#dceaff','#ffe6aa'],"Miss Fortune":['#ffbe68','#ffc073','#eda071','#ffa950','#ffc280'],Samira:['#f6cf7b','#dedbe8','#dde3ef','#eaae88','#efc49a'],Senna:['#73dcd1','#a9f0df','#70d3cf','#73d5ce','#ffeeaf'],Sivir:['#c9cf8a','#f0d789','#d6eab5','#ffe28d','#9fdcd5'],Smolder:['#ffae42','#ff9e36','#ffd46c','#ffac58','#ff8535'],Tristana:['#ffbf70','#ffd184','#ffb65c','#edb678','#ffc568'],Twitch:['#8fde58','#81c762','#91dc4a','#a4e961','#a2d97a'],Varus:['#b47aff','#b482ef','#b673eb','#af83d7','#b476eb'],Vayne:['#b8caff','#b7caff','#eef5ff','#d1d9ff','#aaa5f7'],Xayah:['#d587e9','#edb5fa','#d67cdb','#e897f4','#e9a1ed'],Yunara:['#a295ff','#aea5ff','#a8e4ea','#b9a0ff','#d09fff'],Zeri:['#d0f77c','#defa8b','#dcf57c','#b5ee83','#cef885']};
// Basic attack visual per weapon, and the impact family each projectile kind ends in.
const WEAPON_AA={bow:'arrow',rifle:'pierce',pistols:'barrage',axes:'axe',spear:'spear',cannon:'cannon_ball',maw:'acid',breath:'flame',aircraft:'barrage',relic_cannon:'dark_beam',void_cannons:'swarm',crossbows:'heavy_bolt',crossblade:'disc',feathers:'feather',spirit_orbs:'spirit_arc',electric_rifle:'spark_bolt',launcher:'pierce',blade_pistol:'barrage',crossbow:'heavy_bolt'};
const IMPACTS={explosion:['rocket','bomb','grenade','cannon_ball','artillery','charge','dragon_shadow','flame','sneeze'],splash:['acid','ooze','cask','poison_burst'],sparks:['pierce','barrage','slash_bullet','heavy_bolt','spark_bolt','arrow','charged_arrow','spear','axe','disc','boomerang','feather','fan','swarm','cone_barrage','radial_barrage','arcane_arrow','lance','dark_beam','beam','wide_beam','sniper']};
function impactKind(profile,action,empowered){const slot=action.startsWith('AA')?'AA':action[0],effect=slot==='AA'?(empowered||WEAPON_AA[profile.weapon]||'arcane_arrow'):profile.skills?.[slot]?.effect,style=STYLE[effect]||[effect,1,1,profile.theme];if(style[3]==='frost')return'shards';for(const[k,list]of Object.entries(IMPACTS))if(list.includes(style[0]))return k;return'burst';}
function effectColor(profile,slot){return SPELL_COLORS[profile.name]?.[{P:0,Q:1,W:2,E:3,R:4,AA:1}[slot]]||profile.palette.energy;}
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)),hash=(i)=>{const x=Math.sin(i*127.1+311.7)*43758.5453;return x-Math.floor(x);};
function createEffects(T,scene,{software=false,budget=1400}={}){
 const group=new T.Group();group.name='Deterministic_Visual_Effects';scene.add(group);const pool=[],materials=new Map();let used=0,particleCount=0;
 const geometries={sphere:new T.SphereGeometry(1,12,8),cone:new T.ConeGeometry(1,1,8),line:new T.CylinderGeometry(1,1,1,8),ring:new T.TorusGeometry(1,.032,6,48),gem:new T.OctahedronGeometry(1),box:new T.BoxGeometry(1,1,1)};
 function flatShape(points,depth=.035){const shape=new T.Shape();points.forEach(([x,y],i)=>i?shape.lineTo(x,y):shape.moveTo(x,y));shape.closePath();const g=new T.ExtrudeGeometry(shape,{depth,bevelEnabled:false,steps:1});g.translate(0,0,-depth/2);return g;}
 const crescent=[];for(let i=0;i<=24;i++){const x=-1.35+i*2.7/24;crescent.push([x,-x*x*.24]);}for(let i=24;i>=0;i--){const x=-1.35+i*2.7/24;crescent.push([x,-x*x*.24-.12-.28*(1-(x/1.35)**2)]);}
 geometries.crescent=flatShape(crescent,.055);geometries.axe=flatShape([[-.04,-.65],[.05,-.65],[.05,.08],[.18,.2],[.46,.25],[.51,.6],[.3,.79],[.03,.46],[-.18,.28],[-.28,.43],[-.43,.7],[-.55,.47],[-.37,.1],[-.04,.06]],.065);geometries.feather=flatShape([[0,-.22],[-.11,.0],[-.19,.28],[-.12,.6],[0,.91],[.12,.57],[.17,.22],[.07,-.03]],.025);
 const buffer=new T.BufferGeometry(),attribute=(name,count,size)=>{const value=new T.Float32BufferAttribute(Array(count).fill(0),size);buffer.setAttribute(name,value);return value.array;};
 // Allocate through Three.js so typed arrays belong to the renderer's realm (mobile replay iframe).
 const positions=attribute('position',budget*3,3),colors=attribute('color',budget*3,3),sizes=attribute('pSize',budget,1),alphas=attribute('pAlpha',budget,1);
 const shader=new T.ShaderMaterial({transparent:true,depthWrite:false,blending:T.AdditiveBlending,vertexColors:true,uniforms:{pixelScale:{value:420}},vertexShader:'attribute float pSize; attribute float pAlpha; varying vec3 vColor; varying float vAlpha; uniform float pixelScale; void main(){vColor=color;vAlpha=pAlpha;vec4 p=modelViewMatrix*vec4(position,1.0);gl_Position=projectionMatrix*p;gl_PointSize=clamp(pSize*pixelScale/max(1.,-p.z),1.,70.);}',fragmentShader:'varying vec3 vColor;varying float vAlpha;void main(){vec2 p=gl_PointCoord*2.-1.;float d=length(p);float core=exp(-d*d*8.);float halo=max(0.,1.-d)*.25;float alpha=(core+halo)*vAlpha;if(alpha<.01)discard;gl_FragColor=vec4(vColor,alpha);}'});
 const particles=new T.Points(buffer,shader);particles.frustumCulled=false;group.add(particles);particles.visible=!software;
 function material(color,opacity=.85){opacity=clamp(opacity);const key=new T.Color(color).getHexString()+':'+Math.round(opacity*20);if(!materials.has(key))materials.set(key,new T.MeshBasicMaterial({color,transparent:true,opacity:Math.round(opacity*20)/20,depthWrite:false,blending:T.AdditiveBlending,side:T.DoubleSide}));return materials.get(key);}
 function object(kind,color,opacity=.85){let o=pool[used++];if(!o){o=new T.Mesh();pool.push(o);group.add(o);}o.geometry=geometries[kind];o.material=material(color,opacity);o.visible=true;o.position.set(0,0,0);o.scale.set(1,1,1);o.quaternion.identity();return o;}
 function sphere(v,r,color,alpha=.8){const o=object('sphere',color,alpha);o.position.copy(v);o.scale.setScalar(r);return o;}
 function segment(a,b,width,color,alpha=.8){const d=b.clone().sub(a),o=object('line',color,alpha);o.position.copy(a).add(b).multiplyScalar(.5);o.scale.set(width,d.length(),width);if(d.lengthSq()>0)o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());return o;}
 function ring(v,r,color,alpha=.8,normal=new T.Vector3(0,1,0)){const o=object('ring',color,alpha);o.position.copy(v);o.scale.setScalar(r);o.quaternion.setFromUnitVectors(new T.Vector3(0,0,1),normal);return o;}
 function projectile(v,direction,r,color,kind='arrow'){const o=object(kind==='ball'?'sphere':kind==='disc'?'ring':kind==='gem'?'gem':kind==='axe'?'axe':kind==='feather'?'feather':'cone',color,.94);o.position.copy(v);o.scale.set(r,r*(kind==='ball'?1:4.5),r);o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),direction);return o;}
 function emit(v,count,color,seed,age,{radius=.5,speed=1,lifetime=.75,gravity=.8,size=.08,up=.5}={}){
  if(age<0||age>lifetime)return;const c=new T.Color(color),a=1-age/lifetime;
  if(software){for(let i=0;i<Math.min(count,6);i++){const angle=hash(seed+i)*Math.PI*2,point=v.clone().add(new T.Vector3(Math.cos(angle)*age*speed,up*age-gravity*age*age*.5,Math.sin(angle)*age*speed));sphere(point,size*.45,c,a);}return;}
  for(let i=0;i<count&&particleCount<budget;i++){const k=particleCount++,angle=hash(seed+i)*Math.PI*2,r=hash(seed+i+61)*radius,sp=(.3+hash(seed+i+94))*speed;positions[k*3]=v.x+Math.cos(angle)*(r+age*sp);positions[k*3+1]=v.y+hash(seed+i+42)*.12+up*age-gravity*age*age*.5;positions[k*3+2]=v.z+Math.sin(angle)*(r+age*sp);colors[k*3]=c.r;colors[k*3+1]=c.g;colors[k*3+2]=c.b;sizes[k]=size*(.7+hash(seed+i+17))*(.3+a*.7);alphas[k]=a;}
 }
 function begin(){used=0;particleCount=0;pool.forEach(o=>o.visible=false);}
 function finish(){buffer.setDrawRange(0,particleCount);for(const key of ['position','color','pSize','pAlpha'])buffer.attributes[key].needsUpdate=true;}
 function beam(a,b,width,color,age){segment(a,b,width,color,.65);segment(a,b,width*.33,'#efffff',.85);const n=b.clone().sub(a).normalize();ring(a,width*2,color,.6,n);ring(b,width*2.6,color,.5,n);emit(b,20,color,41,age,{speed:1.8,up:1,gravity:1.5,size:.1});}
 function ribbon(points,width,color,alpha=.8){for(let i=1;i<points.length;i++)segment(points[i-1],points[i],width*(.3+.7*i/points.length),color,alpha*i/points.length);}
 function drawArcane(slot,spec,frame){
  const u=clamp(frame.progress??0),source=frame.source||new T.Vector3(-2,1.2,0),target=frame.target||new T.Vector3(2,1.2,0),hero=frame.hero||source.clone().setY(0),dir=target.clone().sub(frame.projectile||source).normalize(),side=new T.Vector3(-dir.z,0,dir.x).normalize(),release=frame.release??(slot==='AA'?.23:slot==='R'?.55:.35),impactAt=frame.impactAt??(slot==='AA'?.57:slot==='R'?.92:.80),travel=clamp((u-release)/(impactAt-release)),v=frame.projectile?.clone()||source.clone().lerp(target,travel),color=slot==='AA'?'#f5d879':slot==='Q'?'#45d8ff':slot==='W'?'#ffe474':'#ffce55',gold='#fff2b7';
  if(u<release){const charge=clamp(u/release);if(slot!=='AA'){ring(source,.11+charge*(slot==='R'?.38:.15),color,.5,dir);ring(source,.06+charge*.13,gold,.7,dir);for(let i=0;i<(slot==='R'?12:5);i++){const a=i*Math.PI*2/(slot==='R'?12:5)+u*8;const p=source.clone().addScaledVector(side,Math.cos(a)*(.42-charge*.26)).add(new T.Vector3(0,Math.sin(a)*(.42-charge*.26),0));sphere(p,.024,color,.6);}}else sphere(source,.045,color,.65);return;}
  if(u<impactAt){
   if(slot==='AA'){projectile(v,dir,.033,color,'ball');segment(v.clone().addScaledVector(dir,-.19),v,.012,gold,.9);segment(v.clone().addScaledVector(dir,-.34),v,.016,color,.3);}
   else if(slot==='Q'){const arrow=projectile(v,dir,.13,'#d7fbff');arrow.scale.set(.095,.48,.095);const core=v.clone().addScaledVector(dir,-.17);sphere(core,.085,color,.6);for(let i=0;i<13;i++){const distance=.085+i*.067,p=v.clone().addScaledVector(dir,-distance);const a=frame.age*15+i*.57;const left=p.clone().addScaledVector(side,Math.sin(a)*.043);left.y+=Math.cos(a)*.043;sphere(left,.042*(1-i/15),color,.75-i*.04);}segment(v.clone().addScaledVector(dir,-.8),v,.025,color,.42);ring(v.clone().addScaledVector(dir,-.25),.115,color,.7,dir);}
   else if(slot==='W'){ring(v,.28,color,.85,dir);ring(v,.21,gold,.75,dir);for(let i=0;i<6;i++){const a=i*Math.PI/3+u*7,p=v.clone().addScaledVector(side,Math.cos(a)*.26);p.y+=Math.sin(a)*.26;projectile(p,dir,.035,gold,'gem');}segment(v.clone().addScaledVector(dir,-.22),v,.035,color,.5);}
   else{const up=new T.Vector3(0,1,0),normal=side.clone().cross(up).normalize(),wave=object('crescent',color,.83);wave.position.copy(v);wave.quaternion.setFromRotationMatrix(new T.Matrix4().makeBasis(side,dir,side.clone().cross(dir).normalize()));wave.scale.set(1.45,1.5,1);for(let i=0;i<23;i++){const x=i/22*2-1,p=v.clone().addScaledVector(side,x*1.8).addScaledVector(dir,-x*x*.43);segment(p.clone().addScaledVector(dir,-.55),p,.032,color,.65);sphere(p,.055,gold,.8);}}
  }else{const age=(u-impactAt)*(spec.study_duration||1),fade=1-clamp(age/.32);if(fade>0){const r=slot==='AA'?.11:slot==='Q'?.34:slot==='W'?.48:.95;ring(target,r+(1-fade)*.30,color,fade*.8,dir);if(slot==='W'){ring(target,.4,color,.6,dir);ring(target,.23,gold,.65,dir);}else{for(let i=0;i<(slot==='AA'?5:slot==='R'?22:12);i++){const a=i*Math.PI*2/(slot==='AA'?5:slot==='R'?22:12),end=target.clone().addScaledVector(side,Math.cos(a)*r*(1-fade+.2));end.y+=Math.sin(a)*r*(1-fade+.2);segment(target,end,slot==='AA'?.008:.014,color,fade*.75);}emit(target,slot==='AA'?9:slot==='R'?64:30,color,73,age,{radius:.045,speed:slot==='AA'?.4:1.4,up:.4,gravity:0,lifetime:.32,size:slot==='AA'?.04:.075});}}
  }
 }
 function draw(profile,slot,frame={}){
  const spec=slot==='AA'?profile.attack:slot==='P'?profile.passive:profile.skills[slot];if(!spec)return;
  const effect=slot==='AA'?frame.empowered||WEAPON_AA[profile.weapon]||'arcane_arrow':slot==='P'?'passive':spec.effect;
  if(profile.name==='Ezreal'&&slot==='E'){
   const u=frame.progress||0,release=frame.release??.35,start=frame.start||frame.hero,end=frame.end||frame.hero,source=frame.source,target=frame.target;
   if(start&&end&&u<release+.12){for(const p of[start,end]){const v=p.clone().setY(.09);ring(v,.45,'#ffe576',.7);ring(v,.28,'#fff0ad',.7);emit(v.clone().setY(.6),18,'#ffe576',frame.seed||1,Math.max(0,u-release)*2,{radius:.24,speed:.5,up:.7,gravity:0,lifetime:.3,size:.055});}}
   if(source&&target&&u>=release&&u<(frame.impactAt??.74)){const dir=target.clone().sub(frame.projectile||source).normalize(),v=frame.projectile?.clone()||source.clone().lerp(target,clamp((u-release)/((frame.impactAt??.74)-release)));projectile(v,dir,.075,'#fff0a7','ball');segment(v.clone().addScaledVector(dir,-.32),v,.025,'#ffcf52',.8);}return;
  }
  if(profile.name==='Jinx'&&['AA','W','R'].includes(slot)){
   const u=frame.progress||0,release=frame.release??.35,impactAt=frame.impactAt??.74,source=frame.source,target=frame.target;if(!source||!target)return;const dir=target.clone().sub(frame.projectile||source).normalize(),v=frame.projectile?.clone()||source.clone().lerp(target,clamp((u-release)/(impactAt-release))),rocket=slot==='R'||frame.empowered==='rocket',color=slot==='W'?'#67d1ff':rocket?'#ff9655':'#ffe2a4';
   if(u<release){sphere(source,.06+(u/release)*.05,color,.6);return;}if(u>=impactAt)return;
   if(rocket){const scale=slot==='R'?1.65:.7,body=projectile(v,dir,.12*scale,'#dce0d6');body.scale.set(.11*scale,.45*scale,.11*scale);sphere(v.clone().addScaledVector(dir,-.28*scale),.11*scale,color,.8);const side=new T.Vector3(-dir.z,0,dir.x).normalize();for(const sign of[-1,1])segment(v.clone().addScaledVector(dir,-.17*scale),v.clone().addScaledVector(dir,-.30*scale).addScaledVector(side,sign*.18*scale),.035*scale,'#df5176',.85);for(let i=1;i<9;i++)sphere(v.clone().addScaledVector(dir,-i*.085*scale),.065*scale*(1-i/10),i%2?color:'#ffcb82',.55*(1-i/10));}
   else if(slot==='W'){projectile(v,dir,.065,'#c6f7ff');segment(v.clone().addScaledVector(dir,-.55),v,.033,color,.7);ring(v,.11,color,.8,dir);}
   else{sphere(v,.028,color);segment(v.clone().addScaledVector(dir,-.25),v,.013,color,.9);}return;
  }
  // Ezreal's basic bolt and Mystic Shot deliberately have separate silhouettes and rhythms.
  if(profile.name==='Ezreal'&&['AA','Q','W','R'].includes(slot)){
   drawArcane(slot,spec,frame);return;
  }
  const style=STYLE[effect]||[effect,1,1,profile.theme],kind=style[0],scale=style[1],count=style[2],u=clamp(frame.progress??0),age=frame.age??u*(spec.study_duration||1),active=frame.active??true,source=frame.source||new T.Vector3(-3,1.5,0),target=frame.target||new T.Vector3(0,1.2,0),hero=frame.hero||source.clone().setY(0),color=effectColor(profile,frame.colorSlot||slot),accent=['W','E','R'].includes(slot)&&profile.name==='Ezreal'?'#fff0a6':profile.palette.metal;
  const direction=target.clone().sub(frame.projectile||source).normalize(),side=new T.Vector3(-direction.z,0,direction.x),ground=target.clone().setY(.06),release=frame.release??.35,impactAt=frame.impactAt??.74,travel=clamp((u-release)/Math.max(.01,impactAt-release)),impact=frame.impact??u>=impactAt,origin=source.clone(),head=origin.clone().lerp(target,travel),fade=1-clamp((u-impactAt)/(1-impactAt)),seed=(frame.seed||1)*83;
  const trails=(v,dir,c,n=7,r=.065)=>{for(let i=1;i<=n;i++)sphere(v.clone().addScaledVector(dir,-i*.09),r*(1-i/(n+1)),c,(1-i/(n+1))*.8);};
  // Anticipation: socket charge tracks the articulated hand or muzzle.
  if(u<release&&active&&!['trap','lotus','chompers','charge','passive'].includes(kind)){const charge=clamp(u/Math.max(.01,release));ring(source,.06+charge*.13,color,.6,direction);emit(source,8,color,seed,charge*.4,{radius:.16,speed:-.24,lifetime:.5,up:0,gravity:0,size:.065});}
  if(kind==='passive'){
   const center=hero.clone().setY(profile.rig==='creature'||profile.rig==='dragon'?.7:1.2);ring(hero.clone().setY(.045),.63,color,.34);for(let i=0;i<7;i++){const a=age*1.8+i*Math.PI*2/7,v=center.clone().add(new T.Vector3(Math.sin(a)*.65,Math.sin(a*1.7)*.15,Math.cos(a)*.65));projectile(v,new T.Vector3(0,1,0),.045,color,'gem');}emit(center,24,color,seed,age%1.2,{radius:.4,speed:.1,lifetime:1.3,up:.4,gravity:0,size:.045});return;
  }
  const buffs=['aura','mouth_aura','weapon_aura','weapon_shift','rings','beads','feather_orbit','orbit_axe','rally','ascend','shield','dash_shield','stealth','mist','speed','glide','rail','flight','roll_trail'];
  if(buffs.includes(kind)){
   const center=hero.clone().setY(profile.rig==='dragon'||profile.rig==='creature'?.6:1.12);
   if(kind==='shield'||kind==='dash_shield'){sphere(center,.72*scale,color,.12);for(let i=0;i<3;i++)ring(center,.72*scale,color,.35,new T.Vector3(i===0?1:0,i===1?1:0,i===2?1:0));}
   else if(['beads','feather_orbit','orbit_axe','rings'].includes(kind)){for(let i=0;i<count;i++){const a=age*2+i*Math.PI*2/count,v=center.clone().add(new T.Vector3(Math.sin(a)*.72,Math.cos(a*.7)*.13,Math.cos(a)*.72));const o=projectile(v,new T.Vector3(Math.cos(a),0,-Math.sin(a)),kind==='beads'?.07:.095,color,kind==='beads'?'ball':kind==='rings'?'disc':'arrow');if(kind==='orbit_axe'){o.geometry=geometries.axe;o.scale.setScalar(.38);o.rotateY(age*7);}}}
   else if(kind==='ascend'){ring(hero.clone().setY(.08),1.0,color,.7);for(let i=0;i<4;i++)ring(center.clone().add(new T.Vector3(0,i*.21,0)),.65-i*.07,color,.5);for(let i=0;i<6;i++){const a=i*Math.PI/3;segment(hero.clone().add(new T.Vector3(Math.cos(a)*.65,0,Math.sin(a)*.65)),hero.clone().add(new T.Vector3(Math.cos(a)*.65,2.5,Math.sin(a)*.65)),.012,color,.3);}}
   else if(kind==='stealth'||kind==='mist'){for(let i=0;i<5;i++){const v=center.clone().add(new T.Vector3(Math.sin(age+i)*.4,-.5,Math.cos(age+i)*.4));sphere(v,.25+u*.2,color,.08);}ring(hero.clone().setY(.05),.63,color,.22);}
   else if(['speed','glide','rail','flight','roll_trail'].includes(kind)){for(const sign of [-1,1]){const points=[];for(let i=0;i<9;i++)points.push(hero.clone().addScaledVector(side,sign*.24).addScaledVector(direction,-.16-i*.13).add(new T.Vector3(0,.08+(kind==='flight'?.7:0),0)));ribbon(points,.023,color,.55);}emit(hero.clone().setY(.1),24,color,seed,age%.65,{radius:.25,speed:.3,up:.25,gravity:.5,lifetime:.7});}
   else {ring(center,.52,color,.4);ring(hero.clone().setY(.05),.6,color,.28);emit(center,18,color,seed,age%.7,{radius:.28,speed:.1,up:.45,gravity:0,lifetime:.8});}
   return;
  }
  if(kind==='blink'||kind==='dash'||kind==='dash_slash'||kind==='jump'){
   const start=frame.start||hero.clone().addScaledVector(direction,-1.4),end=frame.end||hero;
   for(const v of [start,end]){const c=v.clone().setY(1);ring(c,.72,color,.6,direction);ring(c,.42,accent,.5,direction);emit(c,22,color,seed,age%.8,{radius:.35,speed:.85,up:1,lifetime:.85});}
   if(kind==='dash_slash')ring(end.clone().setY(1),.83,accent,.7,new T.Vector3(0,1,0));if(kind==='jump')ring(end.clone().setY(.05),.35+u*.7,color,.6);return;
  }
  if(['beam','dark_beam','wide_beam','lightning_beam','sniper'].includes(kind)&&u>=release){
   if(kind==='lightning_beam'){const points=[];for(let i=0;i<13;i++){const v=source.clone().lerp(target,i/12);v.addScaledVector(side,(hash(seed+i)-.5)*.18*(i>0&&i<12));v.y+=(hash(seed+i+53)-.5)*.12;points.push(v);}ribbon(points,.033*scale,color,.9);}
   else beam(source,target,kind==='wide_beam'?.21:kind==='dark_beam'?.08:.038,color,age*.5);
   if(kind==='sniper'){ring(target,.35,accent,.8,direction);for(const a of [0,Math.PI/2]){const offset=new T.Vector3(Math.cos(a)*.45,Math.sin(a)*.45,0);segment(target.clone().sub(offset),target.clone().add(offset),.012,accent,.8);}}
   return;
  }
  if(['trap','lotus','chompers','charge','cask','ooze','rain','arrow_rain','artillery','dragon_shadow'].includes(kind)){
   ring(ground,kind==='charge'?.35:.62*scale,color,.45);
   if(kind==='trap'||kind==='chompers'){for(let i=0;i<count;i++){if(frame.trapSpent?.includes(i))continue;const v=frame.traps?.[i]?new T.Vector3(...frame.traps[i]).setY(.06):ground.clone().addScaledVector(side,(i-(count-1)/2)*.5);ring(v,.2,accent,.9);for(let tooth=0;tooth<8;tooth++){const a=tooth*Math.PI/4,pos=v.clone().add(new T.Vector3(Math.sin(a)*.16,.08,Math.cos(a)*.16));projectile(pos,new T.Vector3(0,1,0),.035,accent);}sphere(v.clone().setY(.13),.1,color,.45);}}
   else if(kind==='lotus'){for(let i=0;i<6;i++){const a=i*Math.PI/3,o=projectile(ground.clone().add(new T.Vector3(Math.sin(a)*.18,.07,Math.cos(a)*.18)),new T.Vector3(Math.sin(a),.3,Math.cos(a)),.12,color,'gem');}ring(ground,.32,accent,.7);}
   else if(kind==='charge'){sphere(target,.18,accent,.8);for(let i=0;i<4;i++)ring(target,.25+i*.08,color,.5);}
   else if(kind==='ooze'||kind==='cask'){for(let i=0;i<6;i++){const v=ground.clone().add(new T.Vector3(Math.sin(i*2)*.4,0,Math.cos(i*2)*.4));sphere(v,.25,color,.2);ring(v,.22,color,.3);}emit(ground,28,color,seed,age%.8,{radius:.6,speed:.1,up:.25,gravity:0,lifetime:1});}
   else if(kind==='rain'||kind==='arrow_rain'||kind==='artillery'){for(let i=0;i<count;i++){const phase=(u*2+i*.113)%1,a=hash(seed+i)*Math.PI*2,r=hash(seed+i+42)*.7,v=ground.clone().add(new T.Vector3(Math.cos(a)*r,2.5*(1-phase),Math.sin(a)*r));projectile(v,new T.Vector3(0,-1,0),kind==='artillery'?.15:.045,color,kind==='artillery'?'ball':'arrow');if(phase>.8)emit(v.clone().setY(.08),5,color,seed+i,(phase-.8)*2,{radius:.06,speed:.7,up:.6,lifetime:.5});}}
   else if(kind==='dragon_shadow'){for(let i=0;i<12;i++){const v=target.clone().add(new T.Vector3((i-6)*.13,.5,.1));projectile(v,direction,.22,color);emit(v,5,color,seed+i,age%.9,{radius:.1,speed:1.2,up:.6,lifetime:1});}const shadow=object('gem',profile.palette.cloth,.28);shadow.position.copy(ground).add(new T.Vector3(0,2.5,0));shadow.scale.set(2.5,.11,1.2);}
   return;
  }
  if(kind==='path'){
   for(let i=0;i<10;i++){const v=hero.clone().addScaledVector(direction,-i*.22).setY(.08);sphere(v,.18,color,.15);emit(v,6,color,seed+i,age%.8,{radius:.12,speed:.24,up:1.1,gravity:0,lifetime:.9,size:.09});}return;
  }
  if(kind==='lightning_storm'){
   const center=hero.clone().setY(.12);ring(center,.4+u*1.4,color,.65);for(let i=0;i<8;i++){const a=i*Math.PI/4,endpoint=center.clone().add(new T.Vector3(Math.sin(a)*(1+u*.8),0,Math.cos(a)*(1+u*.8))),points=[];for(let k=0;k<8;k++){const v=center.clone().lerp(endpoint,k/7);v.y+=(hash(seed+i*11+k)-.5)*.17;points.push(v);}ribbon(points,.016,color,.8);}emit(center,44,color,seed,age%.9,{radius:.45,speed:1,up:1,lifetime:1});return;
  }
  if(kind==='root'||kind==='chains'||kind==='rend'||kind==='poison_burst'){
   for(let i=0;i<(kind==='chains'?4:count);i++){const a=i*Math.PI*2/Math.max(4,count)+age*.7,points=[];for(let k=0;k<=10;k++){const f=k/10,v=target.clone().add(new T.Vector3(Math.cos(a+f*3)*(.38+f*.3),f*1.1-.65,Math.sin(a+f*3)*(.38+f*.3)));points.push(v);}ribbon(points,.023,color,.75);}
   emit(target,36,color,seed,age%.7,{radius:.28,speed:.85,up:1,lifetime:.8});return;
  }
  if(kind==='bird'||kind==='ghost'||kind==='summon'){
   const v=frame.projectile?.clone()||source.clone().lerp(target,travel),o=object('gem',color,.55);o.position.copy(v);o.scale.set(.22,.3,.15);for(const s of [-1,1]){const wing=object('cone',color,.65);wing.position.copy(v).add(new T.Vector3(s*.24,Math.sin(age*9)*.04,0));wing.scale.set(.25,.05,.25);wing.rotation.z=s*Math.sin(age*9)*.4;}trails(v,direction,color);return;
  }
  if(kind==='blade_ring'||kind==='radial_barrage'){
   ring(hero.clone().setY(1.1),.85*scale,color,.7);for(let i=0;i<count;i++){const a=age*8+i*Math.PI*2/count,v=hero.clone().add(new T.Vector3(Math.sin(a)*.85,1.15,Math.cos(a)*.85));projectile(v,new T.Vector3(Math.cos(a),0,-Math.sin(a)),.07,accent);}return;
  }
  if(u>=release){
   const spread=['fan','feather_fan','cone_barrage','swarm','spark_bolt','barrage'].includes(kind),returning=['boomerang','recall_feathers'].includes(kind),n=Math.min(count,14);
   for(let i=0;i<n;i++){
    const offset=(i-(n-1)/2),end=target.clone().addScaledVector(side,spread?offset*.35:kind==='recall_feathers'?offset*.28:0),start=origin.clone();
    let f=travel;if(returning)f=u<.64?clamp((u-release)/(.64-release)):1-clamp((u-.64)/.36);if(kind==='recall_feathers'){start.copy(end);end.copy(origin);f=travel;}
    if(kind==='swarm'){start.addScaledVector(side,offset*.065);start.y+=.2;}
    const v=frame.projectile?.clone()||start.clone().lerp(end,f),dir=end.clone().sub(start).normalize();// Released projectiles stay on the frozen firing line; no ballistic offset.
    // A fading particle trail along the path already flown, so every projectile reads as travelling.
    for(let k=1;k<=6;k++){const pf=f-k*.035;if(pf<=0||pf>1)break;emit(start.clone().lerp(end,pf),2,color,seed+i*31+k,k*.06,{radius:.035,speed:.12,up:.08,gravity:0,lifetime:.45,size:.075*scale});}
    if(kind==='crescent'){const wave=object('crescent',color,.66);wave.position.copy(v);wave.quaternion.setFromRotationMatrix(new T.Matrix4().makeBasis(side.clone().normalize(),dir,side.clone().cross(dir).normalize()));wave.scale.set(1.18,1.18,1);for(let j=0;j<16;j++){const x=j/15*2-1,tip=v.clone().addScaledVector(side,x*1.25).addScaledVector(dir,-x*x*.35);sphere(tip,.075,color);if(j>0)segment(tip,v.clone().addScaledVector(side,(x-2/15)*1.25).addScaledVector(dir,-((x-2/15)**2)*.35),.04,accent);}}
    else if(kind==='net'){for(let j=-2;j<=2;j++){segment(v.clone().addScaledVector(side,j*.08).add(new T.Vector3(0,-.2,0)),v.clone().addScaledVector(side,j*.08).add(new T.Vector3(0,.2,0)),.012,color);segment(v.clone().addScaledVector(side,-.2).add(new T.Vector3(0,j*.08,0)),v.clone().addScaledVector(side,.2).add(new T.Vector3(0,j*.08,0)),.012,color);}}
    else if(kind==='flame'||kind==='sneeze'){for(let j=0;j<8;j++){const f0=Math.max(0,f-j*.028),tip=start.clone().lerp(end,f0);sphere(tip,(.1+j*.012)*scale,j%2?color:accent,.28);emit(tip,3,color,seed+j,age%.5,{radius:.07,speed:.4,up:.2,lifetime:.5,gravity:0});}}
    else if(kind==='rocket'){const o=projectile(v,dir,.12*scale,accent);o.scale.set(.11*scale,.55*scale,.11*scale);sphere(v.clone().addScaledVector(dir,-.32),.13*scale,color,.6);trails(v,dir,color,9,.09);}
    else if(kind==='star'){for(let j=0;j<4;j++){const a=j*Math.PI/2,ray=v.clone().add(new T.Vector3(0,Math.sin(a)*.2,Math.cos(a)*.2));segment(v,ray,.023,color);}trails(v,dir,color);}
    else if(kind==='axe'||effect==='axe_return'){const o=projectile(v,dir,.30*scale,accent,'axe');o.scale.setScalar(.45*scale);o.rotateZ(age*17+i);trails(v,dir,color,5,.05);}
    else if(kind==='feather'||kind==='feather_fan'||kind==='recall_feathers'){const o=projectile(v,dir,.16*scale,color,'feather');o.scale.setScalar(.36*scale);trails(v,dir,color,6,.035);}
    else if(kind==='bomb'||kind==='grenade'){const bomb=v.clone();sphere(bomb,.11*scale,accent,.9);ring(bomb,.12*scale,color,.6,dir);emit(bomb,8,color,seed+i,age%.45,{radius:.05,speed:.25,up:0,gravity:0,lifetime:.5,size:.05});}
    else if(kind==='disc'||kind==='boomerang'){const o=projectile(v,dir,.16*scale,color,'disc');o.rotateX(age*13);for(let j=0;j<4;j++){const a=age*12+j*Math.PI/2,blade=v.clone().add(new T.Vector3(0,Math.sin(a)*.19,Math.cos(a)*.19));segment(v,blade,.04,accent);}}
    else if(kind==='flux'){ring(v,.24,color,.9,dir);ring(v,.15,accent,.9,dir);sphere(v,.04,'#ffffff');}
    else {projectile(v,dir,(kind==='acid'||kind==='cannon_ball'?.105:.06)*scale,color,kind==='acid'||kind==='cannon_ball'?'ball':kind==='spirit_arc'?'gem':'arrow');trails(v,dir,color,kind==='charged_arrow'?10:6,.065*scale);}
   }
  }
  if(impact&&fade>0){ring(target,.12+(1-fade)*.6*scale,color,fade,new T.Vector3(1,0,0));emit(target,kind==='rocket'?70:kind==='cannon_ball'?45:22,color,seed,(1-fade)*.8,{radius:.13,speed:1.2*scale,lifetime:.85,up:1,gravity:1.4,size:.09});}
 }
 // Hit effects by what struck: ordnance explodes, acid and venom splash, frost shatters, bullets and blades throw sparks.
 function impact(profile,action,age,point,seed=1,hit={}){if(age<0||age>.9)return;if(hit.mark){ring(point,.24+age*.12,'#ffe474',(1-age/.9)*.65,new T.Vector3(1,0,0));return;}if(hit.detonation){const f=1-age/.9;ring(point,.24+age*1.4,'#ffe474',f,new T.Vector3(1,0,0));emit(point,36,'#fff2b7',seed*67,age,{radius:.12,speed:2.2,up:.7,gravity:0,lifetime:.6,size:.075});return;}const slot=action.startsWith('AA')?'AA':action[0],kind=impactKind(profile,action,hit.empowered),c=effectColor(profile,hit.colorSlot||slot),big=slot==='R'?1.6:slot==='AA'?.7:1,f=1-age/.9,ground=point.clone().setY(.06);
  if(kind==='explosion'){sphere(point,(.12+age*.9)*big,c,f*.5);sphere(point,(.05+age*.4)*big,'#fff1c2',f*.8);ring(ground,(.2+age*1.6)*big,c,f*.55);emit(point,Math.round(44*big),c,seed*67,age,{radius:.12,speed:2.1*big,up:1.4,gravity:2.2,lifetime:.9,size:.11});emit(point,14,'#7d746a',seed*31,age,{radius:.2,speed:.45,up:.9,gravity:-.3,lifetime:.9,size:.17});}
  else if(kind==='splash'){ring(ground,(.15+age*.9)*big,c,f*.5);for(let i=0;i<8;i++){const a=i*Math.PI/4+seed,d=(.1+age*.8)*big,y=Math.max(.05,point.y+age*1.2-age*age*4);sphere(new T.Vector3(point.x+Math.cos(a)*d,y,point.z+Math.sin(a)*d),.05*big*f+.01,c,f*.8);}emit(point,26,c,seed*67,age,{radius:.1,speed:1.2,up:1.6,gravity:3.5,lifetime:.8,size:.09});}
  else if(kind==='shards'){ring(point,.1+age,c,f*.7,new T.Vector3(1,0,0));for(let i=0;i<9;i++){const a=i*Math.PI*2/9+seed*.7,dir=new T.Vector3(Math.cos(a),Math.sin(a)*.8+.3,Math.sin(a*1.3)).normalize();projectile(point.clone().addScaledVector(dir,.08+age*.9*big),dir,.035*big,'#e8fbff','cone');}emit(point,22,c,seed*67,age,{radius:.08,speed:1.3,up:.8,gravity:1.5,lifetime:.7,size:.07});}
  else if(kind==='sparks'){ring(point,.08+age*.7*big,c,f*.7,new T.Vector3(1,0,0));for(let i=0;i<10;i++){const a=hash(seed+i)*Math.PI*2,e=hash(seed+i+9)*.8+.2,dir=new T.Vector3(Math.cos(a),e,Math.sin(a)).normalize();segment(point.clone().addScaledVector(dir,age*1.6*big),point.clone().addScaledVector(dir,age*1.6*big+.12*f),.012,i%2?c:'#fff6d8',f*.9);}emit(point,Math.round(16*big),c,seed*67,age,{radius:.05,speed:1.6,up:.9,gravity:2,lifetime:.6,size:.07});}
  else{ring(point,.1+age*1.1,c,f*.65,new T.Vector3(1,0,0));emit(point,slot==='R'?40:16,c,seed*67,age,{radius:.1,speed:1.3,up:1,gravity:1.8,lifetime:.7,size:.09});}
 }
 function mark(point,remaining,time){const pulse=.85+Math.sin(time*7)*.08;ring(point,.36*pulse,'#ffe474',Math.min(1,remaining)*.75,new T.Vector3(1,0,0));ring(point,.22,'#fff2b7',Math.min(1,remaining)*.5,new T.Vector3(1,0,0));}
 function dispose(){scene.remove(group);for(const g of Object.values(geometries))g.dispose();for(const m of materials.values())m.dispose();shader.dispose();buffer.dispose();}
 return {group,begin,finish,draw,impact,mark,dispose,metrics:()=>({meshPool:pool.length,liveMeshes:used,particles:particleCount,budget})};
}
// Original lightweight combat sounds. Audio starts only after a gameplay gesture.
function createCombatAudio({Context=globalThis.AudioContext||globalThis.webkitAudioContext}={}){
 let ctx=null,master=null,enabled=true,closed=false;const seen=new WeakSet();
 function unlock(){if(closed||!enabled||!Context)return;try{if(!ctx){ctx=new Context();master=ctx.createGain();master.gain.value=.22;master.connect(ctx.destination);}void ctx.resume()?.catch(()=>{});}catch{}}
 function cue(name,slot,kind,enemy=false,weapon=null){if(!ctx||ctx.state!=='running'||!enabled||closed)return;const t=ctx.currentTime,rocket=name==='Jinx'&&(slot==='R'||kind==='rocket'||weapon==='rocket'),arcane=name==='Ezreal',detonation=kind==='detonation',hit=kind!=='launch',duration=rocket?.28:detonation?.22:hit?.10:.14,base=rocket?90:arcane?(slot==='W'?720:slot==='Q'?450:slot==='R'?180:320):slot==='W'?190:240;
  try{for(let i=0;i<2;i++){const osc=ctx.createOscillator(),gain=ctx.createGain();osc.type=rocket?'sawtooth':arcane?'sine':'triangle';osc.frequency.setValueAtTime(base*(i?1.51:1)*(hit?1.3:1),t);osc.frequency.exponentialRampToValueAtTime(Math.max(30,base*(hit?.3:1.8)),t+duration);gain.gain.setValueAtTime(.0001,t);gain.gain.exponentialRampToValueAtTime((enemy?.35:.6)/(i+1),t+.006);gain.gain.exponentialRampToValueAtTime(.0001,t+duration);osc.connect(gain);gain.connect(master);osc.start(t);osc.stop(t+duration+.01);osc.onended=()=>{osc.disconnect();gain.disconnect();};}}catch{}
 }
 function update(actors){for(const {state,enemy=false} of actors){for(const e of state.events||[])if(state.time>=e.launch&&!seen.has(e)){seen.add(e);if(state.time-e.launch<.15)cue(state.profile.name,e.slot,'launch',enemy,e.empowered);}for(const h of state.log||[])if(!seen.has(h)){seen.add(h);if(state.time-h.t<.15&&(h.dealt>0||h.text==='mark applied'))cue(state.profile.name,h.slot,h.slot.includes('detonation')?'detonation':h.text==='mark applied'?'mark':h.slot==='AA'&&state.combat?.weapon==='rockets'?'rocket':'hit',enemy);}}}
 return{unlock,update,setEnabled(value){enabled=!!value;if(master)master.gain.value=enabled?.22:0;if(enabled)unlock();},dispose(){closed=true;if(ctx)void ctx.close()?.catch(()=>{});ctx=null;},cue};
}
const API={STYLE,SPELL_COLORS,WEAPON_AA,IMPACTS,impactKind,effectColor,createEffects,createCombatAudio,hash};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanEffects=API;
})(typeof globalThis!=='undefined'?globalThis:this);
