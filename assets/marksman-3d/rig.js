/* SharpWR original art rig. Geometry, materials and animation are authored here.
 * No gameplay, damage, cooldown or collision decisions are made by this module. */
(function(scope){
'use strict';
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v)),smooth=v=>{v=clamp(v);return v*v*(3-2*v);};
const pulse=(u,a,b)=>u<a?smooth(u/a):u>b?1-smooth((u-b)/(1-b)):1;
function createRig(T,profile,options={}){
 const root=new T.Group();root.name='SharpWR_'+profile.id;root.userData={champion:profile.name,artBrief:profile.art_brief,originalArt:true};
 const joints={},rest={},secondary=[],sockets={},details=[],geometryCache=new Map();let serial=0;
 const palette=profile.palette,materials={},low=!!options.lowPoly;
 const seg=low?8:20,rows=low?5:14;
 for(const [name,color]of Object.entries(palette))materials[name]=new T.MeshStandardMaterial({color,metalness:name==='metal'?.72:name==='light'?.22:.08,roughness:name==='skin'?.66:name==='metal'?.32:.57,emissive:name==='energy'?color:'#000000',emissiveIntensity:name==='energy'?1.35:0});
 materials.dark=new T.MeshStandardMaterial({color:'#10171f',roughness:.7});materials.eye=new T.MeshStandardMaterial({color:palette.energy,emissive:palette.energy,emissiveIntensity:.35,roughness:.2});materials.white=new T.MeshStandardMaterial({color:'#f7f1e7',roughness:.6});materials.glass=new T.MeshStandardMaterial({color:palette.energy,transparent:true,opacity:.5,metalness:.25,roughness:.2});
 const mat=(name)=>materials[name]||materials.cloth;
 function bone(name,parent,x=0,y=0,z=0){const b=new T.Bone();b.name=name;b.position.set(x,y,z);parent.add(b);joints[name]=b;return b;}
 function mesh(g,m,parent=root,x=0,y=0,z=0){if(g.parameters&&!['ExtrudeGeometry','TubeGeometry','LatheGeometry'].includes(g.type)){const key=g.type+JSON.stringify(g.parameters);if(geometryCache.has(key)){g.dispose();g=geometryCache.get(key);}else geometryCache.set(key,g);}const o=new T.Mesh(g,typeof m==='string'?mat(m):m);o.name='part_'+serial++;o.position.set(x,y,z);o.castShadow=true;o.receiveShadow=true;parent.add(o);return o;}
 function ellipsoid(parent,m,r,x,y,z,sx=1,sy=1,sz=1){const o=mesh(new T.SphereGeometry(1,seg,rows),m,parent,x,y,z);o.scale.set(sx*r,sy*r,sz*r);return o;}
 function capsule(parent,m,r,length,x=0,y=0,z=0){return mesh(new T.CapsuleGeometry(r,Math.max(.01,length-2*r),low?3:6,low?7:14),m,parent,x,y,z);}
 function rounded(parent,m,w,h,d,x=0,y=0,z=0,bevel=.035){const s=new T.Shape(),r=Math.min(bevel,w/3,h/3);s.moveTo(-w/2+r,-h/2);s.lineTo(w/2-r,-h/2);s.quadraticCurveTo(w/2,-h/2,w/2,-h/2+r);s.lineTo(w/2,h/2-r);s.quadraticCurveTo(w/2,h/2,w/2-r,h/2);s.lineTo(-w/2+r,h/2);s.quadraticCurveTo(-w/2,h/2,-w/2,h/2-r);s.lineTo(-w/2,-h/2+r);s.quadraticCurveTo(-w/2,-h/2,-w/2+r,-h/2);const g=new T.ExtrudeGeometry(s,{depth:d,bevelEnabled:true,bevelThickness:r/2,bevelSize:r/2,bevelSegments:low?1:3,steps:1,curveSegments:low?3:5});g.translate(0,0,-d/2);return mesh(g,m,parent,x,y,z);}
 function tube(parent,m,points,r=.025){const curve=new T.CatmullRomCurve3(points.map(v=>new T.Vector3(...v)));return mesh(new T.TubeGeometry(curve,Math.max(6,points.length*(low?2:5)),r,low?4:8,false),m,parent);}
 function taper(parent,m,r1,r2,length,x=0,y=0,z=0){return mesh(new T.CylinderGeometry(r1,r2,length,low?8:16,1),m,parent,x,y,z);}
 function ring(parent,m,r,thick=.025,x=0,y=0,z=0){return mesh(new T.TorusGeometry(r,thick,low?4:8,low?14:36),m,parent,x,y,z);}
 function blade(parent,m,points,depth=.05){const s=new T.Shape();points.forEach(([x,y],i)=>i?s.lineTo(x,y):s.moveTo(x,y));s.closePath();const g=new T.ExtrudeGeometry(s,{depth,bevelEnabled:true,bevelThickness:.012,bevelSize:.015,bevelSegments:low?1:2,curveSegments:low?3:6});g.translate(0,0,-depth/2);return mesh(g,m,parent);}
 function attachSocket(name,parent,x=0,y=0,z=0){const o=new T.Object3D();o.name='socket_'+name;o.position.set(x,y,z);parent.add(o);sockets[name]=o;return o;}
 function ribbon(name,parent,m,width,length,spread=0){const chain=bone(name,parent,0,0,0),segments=[];let prev=chain;
  for(let i=0;i<5;i++){const b=bone(name+'_'+i,prev,0,i===0?0:-length/5,0);const o=rounded(b,m,width*(1-i*.11),length/5+.018,.035,spread*i/5,-length/10,-.015,.016);segments.push(b);prev=b;}
  secondary.push({name,chain:segments,kind:'cloth',strength:.08});return chain;
 }
 function hairStrand(parent,points,width,color='light'){return tube(parent,color,points,width);}
 function gun(parent,kind,side=1){const weapon=new T.Group();weapon.name='weapon_'+kind+'_'+side;parent.add(weapon);weapon.rotation.x=Math.PI/2;
  const big=['cannon','relic_cannon','launcher','rifle','electric_rifle','crossbow'].includes(kind),length=kind==='relic_cannon'?1.75:kind==='rifle'?1.4:kind==='cannon'?1.15:kind==='launcher'?1.55:.53;
  if(['bow','crossblade','spear','axes','feathers','spirit_orbs','gauntlet','void_cannons','crossbows'].includes(kind))return weapon;
  rounded(weapon,'secondary',big?.24:.12,big?.28:.18,big?.56:.2,0,0,.18);rounded(weapon,'metal',big?.21:.13,big?.15:.11,length,0,.055,length*.48);
  const barrel=taper(weapon,'metal',big?.075:.04,big?.09:.045,length*.75,0,.055,length*.62);barrel.rotation.x=Math.PI/2;
  const aperture=ring(weapon,'dark',big?.075:.036,.025,0,.055,length*.99);attachSocket(side===1?'muzzle':'off_muzzle',weapon,0,.055,length);
  rounded(weapon,'dark',.105,.22,.15,0,-.16,.14);const guard=ring(weapon,'metal',.085,.017,0,-.12,.21);guard.scale.set(1,.7,1);
  for(let i=0;i<3;i++)rounded(weapon,'metal',big?.26:.13,.025,.045,0,.065,length*.4+i*.12);
  if(kind==='rifle'){rounded(weapon,'cloth',.18,.19,.38,0,.02,-.26);const scope=taper(weapon,'dark',.054,.054,.34,0,.24,.43);scope.rotation.x=Math.PI/2;ellipsoid(weapon,'glass',.054,0,.24,.61,1,1,.25);rounded(weapon,'metal',.065,.1,.06,0,.17,.43);}
  if(kind==='electric_rifle'){for(let i=0;i<3;i++)rounded(weapon,'energy',.12,.02,.2,0,.17,.34+i*.22);const coil=ring(weapon,'energy',.14,.02,0,.06,.77);}
  if(kind==='relic_cannon'){rounded(weapon,'light',.52,.45,1.5,0,.02,.53,.07);rounded(weapon,'dark',.3,.23,1.55,0,.04,.55);for(const s of [-1,1])rounded(weapon,'metal',.055,.35,1.3,s*.25,.02,.55);for(let i=0;i<4;i++)rounded(weapon,'energy',.31,.035,.055,0,.25,.16+i*.26);ring(weapon,'energy',.19,.035,0,.02,1.34);}
  if(kind==='cannon'){const can=taper(weapon,'secondary',.21,.28,.9,0,.08,.54);can.rotation.x=Math.PI/2;for(const z of [.16,.9])ring(weapon,'metal',.23,.04,0,.08,z);ellipsoid(weapon,'dark',.19,0,.08,1.03,1,1,.1);for(let i=0;i<6;i++)rounded(weapon,'metal',.05,.3,.055,Math.sin(i*Math.PI/3)*.24,.08+Math.cos(i*Math.PI/3)*.24,.7);}
  if(kind==='launcher'){const shark=ellipsoid(weapon,'secondary',.22,0,.08,.92,1,1,2.8);const fin=blade(weapon,'light',[[-.04,0],[.02,.28],[.12,0]],.12);fin.position.set(0,.25,.92);for(const s of [-1,1]){ellipsoid(weapon,'white',.075,s*.19,.15,1.23,1,.55,.75);ellipsoid(weapon,'dark',.033,s*.23,.16,1.26);for(let i=0;i<4;i++){const tooth=mesh(new T.ConeGeometry(.028,.09,6),'light',weapon,s*.07,-.08,1.3+i*.04);tooth.rotation.x=Math.PI;}}}
  if(kind==='crossbow'){const arc=tube(weapon,'metal',[[-.45,0,.55],[-.28,.08,.7],[0,.1,.77],[.28,.08,.7],[.45,0,.55]],.045);tube(weapon,'dark',[[-.45,0,.55],[0,.015,.3],[.45,0,.55]],.012);rounded(weapon,'energy',.045,.04,.6,0,.11,.4);}
  return weapon;
 }
 function ornateWeapon(parent,kind,side=1){
  if(!['bow','crossblade','spear','axes','feathers','spirit_orbs','gauntlet','void_cannons','crossbows'].includes(kind))return gun(parent,kind,side);
  const w=new T.Group();w.name='weapon_'+kind+'_'+side;parent.add(w);w.rotation.x=Math.PI/2;attachSocket(side===1?'muzzle':'off_muzzle',w,0,0,.4);
  if(kind==='bow'){
   tube(w,'metal',[[0,-.92,.15],[-.13,-.63,.22],[-.25,-.35,.07],[-.16,0,0],[-.25,.35,.07],[-.13,.63,.22],[0,.92,.15]],.048);
   tube(w,'energy',[[0,-.92,.15],[.08,0,.05],[0,.92,.15]],.011);for(const s of [-1,1]){const b=blade(w,'light',[[-.03,0],[-.22,.28],[-.04,.53],[.03,.25]],.055);b.position.set(-.1,s*.39,.1);b.scale.y=s;ellipsoid(w,'energy',.07,-.12,s*.35,.08,1,2,.8);}
  }else if(kind==='spear'){
   const shaft=taper(w,'dark',.035,.035,1.75,0,0,0);const point=blade(w,'light',[[-.11,0],[0,.46],[.11,0],[0,.1]],.07);point.position.y=.87;for(let i=0;i<4;i++)ring(w,'metal',.045,.02,0,-.37+i*.15,0).rotation.x=Math.PI/2;
  }else if(kind==='crossblade'){
   for(let i=0;i<4;i++){const b=blade(w,'metal',[[0,0],[-.13,.17],[-.08,.67],[.16,.42],[.11,.16]],.075);b.rotation.z=i*Math.PI/2;}ring(w,'dark',.15,.045);ellipsoid(w,'energy',.13,0,0,.065,1,1,.4);
  }else if(kind==='axes'){
   taper(w,'dark',.04,.04,.8,0,-.06,0);const edge=blade(w,'metal',[[-.08,-.1],[-.37,-.05],[-.56,.12],[-.53,.45],[-.35,.62],[-.08,.34],[.05,.25]],.09);edge.position.y=.1;tube(w,'light',[[-.56,.22,.055],[-.48,.49,.055],[-.32,.69,.055]],.028);ring(w,'metal',.07,.025,0,-.4,0).rotation.x=Math.PI/2;
  }else if(kind==='feathers'){
   for(let j=0;j<3;j++){const f=blade(w,j===1?'light':'secondary',[[0,0],[-.095,.2],[-.04,.57],[.06,.34],[.075,.18]],.035);f.rotation.z=(j-1)*.24;f.position.x=(j-1)*.065;}
  }else if(kind==='gauntlet'){
   rounded(w,'metal',.25,.33,.24,0,0,0,.065);ring(w,'light',.105,.025,0,0,.15);ellipsoid(w,'energy',.11,0,0,.17,1,1,.35);for(let i=0;i<3;i++)rounded(w,'light',.037,.12,.04,-.09+i*.09,-.13,.13);
  }else if(kind==='crossbows'){
   rounded(w,'metal',.13,.12,.4,0,0,.14);tube(w,'metal',[[-.28,0,.3],[0,.03,.43],[.28,0,.3]],.035);tube(w,'secondary',[[-.28,0,.3],[0,0,.1],[.28,0,.3]],.012);
  }else if(kind==='void_cannons'){
   ellipsoid(w,'secondary',.18,0,.02,.22,1,1,2.3);for(const s of [-1,1]){const plate=blade(w,'cloth',[[0,0],[s*.15,.05],[s*.25,.45],[0,.22]],.1);plate.rotation.x=Math.PI/2;plate.position.z=.15;}ellipsoid(w,'energy',.07,0,.03,.59);
  }else if(kind==='spirit_orbs'){
   for(let i=0;i<8;i++){const a=i*Math.PI/4;ellipsoid(w,'metal',.075,Math.sin(a)*.3,Math.cos(a)*.3,0);ellipsoid(w,'energy',.034,Math.sin(a)*.3,Math.cos(a)*.3,.065);}
  }
  return w;
 }
 function face(head,creature=false){
  const r=profile.rig==='yordle'?.29:.22;
  if(profile.headgear==='mask'){
   const mask=ellipsoid(head,'light',r,.035,0,.04,.86,1.16,.89);for(const s of [-1,1]){ellipsoid(head,'dark',.049,s*.084,.038,.23,1.12,.44,.3);ellipsoid(head,'energy',.018,s*.087,.036,.246,1,.5,.5);}tube(head,'metal',[[-.15,.1,.19],[-.1,.19,.17],[.02,.22,.14]],.017);rounded(head,'metal',.07,.035,.02,.045,-.13,.235);return;
  }
  ellipsoid(head,'skin',r,0,0,0,.83,1.12,.82);
  for(const side of [-1,1])ellipsoid(head,'skin',.075,side*.105,-.065,.10,.83,.86,.54);
  if(profile.rig==='yordle'){head.scale.setScalar(1.1);}
  for(const s of [-1,1]){
   ellipsoid(head,'skin',.067,s*r*.81,-.015,-.025,.43,1,.65);
   ellipsoid(head,'white',.045,s*.079,.037,profile.rig==='yordle'?.237:.176,1.05,.52,.37);ellipsoid(head,'eye',.023,s*.079,.038,profile.rig==='yordle'?.254:.193,.75,1,.35);ellipsoid(head,'dark',.011,s*.077,.039,profile.rig==='yordle'?.264:.203,.7,1,.35);
   tube(head,'dark',[[s*.037,.099,.179],[s*.09,.107,.169],[s*.132,.087,.141]],.011);
  }
  ellipsoid(head,'skin',.042,0,-.011,profile.rig==='yordle'?.245:.187,.67,1.12,.91);tube(head,'secondary',[[-.047,-.087,.173],[0,-.092,.19],[.047,-.087,.173]],.008);
  if(profile.headgear==='eyepatch'){ellipsoid(head,'dark',.058,-.079,.038,.21,1,.75,.25);tube(head,'dark',[[-.2,.08,.06],[0,.047,.21],[.2,.02,.04]],.013);}
  if(['goggles','visor','pilot'].includes(profile.headgear)){for(const s of [-1,1]){ring(head,'metal',.066,.018,s*.085,.077,.201).scale.y=.7;ellipsoid(head,profile.headgear==='goggles'&&profile.theme==='silver'?'secondary':'glass',.064,s*.085,.077,.208,1,.7,.15);}tube(head,'dark',[[-.22,.08,0],[0,.083,.202],[.22,.08,0]],.011);}
  if(profile.headgear==='moustache'||profile.headgear==='pilot'){for(const s of [-1,1]){const hair=ellipsoid(head,'dark',.061,s*.045,-.067,.2,1.5,.37,.4);hair.rotation.z=s*.24;}}
  if(['ears','rat'].includes(profile.headgear)){for(const s of [-1,1]){const ear=ellipsoid(head,'skin',profile.headgear==='rat'?.18:.19,s*.27,.17,-.025,.67,1.45,.21);ear.rotation.z=-s*.4;ellipsoid(head,'secondary',.11,s*.29,.19,.022,.65,1.3,.15);}}
  if(['crown','horns','tiara'].includes(profile.headgear)){
   const band=ring(head,'metal',.217,.017,0,.125,0);band.rotation.x=Math.PI/2;
   for(let i=-2;i<=2;i++){const spike=blade(head,'metal',[[-.025,0],[0,.13+(2-Math.abs(i))*.035],[.025,0]],.03);spike.position.set(i*.065,.145,.17-Math.abs(i)*.018);}ellipsoid(head,'energy',.045,0,.13,.22,1,1,.4);
  }
  if(profile.headgear==='hood'){
   const hood=ellipsoid(head,'cloth',.26,0,.10,-.065,1.14,1.22,.96);
   // Open face is formed by a crescent frame rather than a solid sphere in front.
   hood.scale.z*=.70;
   tube(head,'light',[[-.22,-.08,.05],[-.23,.16,.10],[-.16,.31,.11],[0,.37,.08],[.16,.31,.11],[.23,.16,.10],[.22,-.08,.05]],.039);
  }
  if(profile.headgear==='hat'||profile.headgear==='pirate'){
   const brim=mesh(new T.CylinderGeometry(.42,.42,.055,32),'cloth',head,0,.22,0);brim.scale.set(1,1,profile.headgear==='pirate'?.58:.9);
   const crown=taper(head,'secondary',profile.headgear==='hat'?.23:.28,.27,profile.headgear==='hat'?.36:.23,0,profile.headgear==='hat'?.42:.35,0);rounded(head,'metal',.13,.065,.035,0,.31,.25);const plume=tube(head,'light',[[.2,.33,-.02],[.3,.56,-.08],[.38,.6,-.19]],.043);}
 }
 function hairstyle(head,chest){
  if(profile.hair==='none')return;
  const color=['Ashe','Ezreal','Tristana','Varus'].includes(profile.name)?'light':profile.name==='Jinx'||profile.name==='Zeri'?'energy':profile.name==='Miss Fortune'||profile.name==='Xayah'?'secondary':'dark';
  ellipsoid(head,color,.232,0,.13,-.035,.95,.63,.91);
  for(let i=0;i<7;i++){const x=(i-3)*.046,points=[[x,.2,-.11],[x*.92,.27,.025],[x*.88,.18,.17],[x*.82+.02,.08+Math.abs(i-3)*.018,.184]];hairStrand(head,points,.033,color);}
  if(['long','locks','braids','tied'].includes(profile.hair)){
   const count=profile.hair==='braids'?2:profile.hair==='tied'?1:profile.hair==='locks'?8:6;
   for(let i=0;i<count;i++){const x=count===1?0:count===2?(i?1:-1)*.17:(i-(count-1)/2)*.058;const chain=bone('hair_'+i,head,x,.1,-.14);const length=profile.hair==='braids'?1.75:profile.name==='Senna'?1.27:.72;
    let prior=chain;const bones=[];
    for(let j=0;j<5;j++){const b=bone('hair_'+i+'_'+j,prior,0,j===0?0:-length/5,0);hairStrand(b,[[0,.03,0],[.013,-length/10,-.03],[0,-length/5,-.01]],profile.hair==='braids'?.058:.035,color);if(profile.hair==='braids'){ring(b,'metal',.063,.012,0,-length/7,0).rotation.x=Math.PI/2;}bones.push(b);prior=b;}
    secondary.push({name:'hair_'+i,chain:bones,kind:'hair',strength:profile.hair==='braids'?.09:.06});
   }
  }
  if(profile.hair==='crest'){for(let i=0;i<5;i++){const tuft=ellipsoid(head,color,.1,0,.28+i*.025,-.15+i*.065,.6,1.9,.75);tuft.rotation.x=-.2;}}
 }
 function humanoid(){
  const small=profile.rig==='yordle',bodyScale=profile.body==='broad'?1.24:profile.body==='slender'?.86:1.;
  const hip=bone('hips',root,0,small?.87:1.23,0),spine=bone('spine',hip,0,.21,0),chest=bone('chest',spine,0,small?.28:.36,0),neck=bone('neck',chest,0,.19,0),head=bone('head',neck,0,small?.25:.23,0);
  const rings=[new T.Vector2(.2,0),new T.Vector2(.21,.11),new T.Vector2(.18,.24),new T.Vector2(.25,.43),new T.Vector2(.31,.58),new T.Vector2(.19,.69)];
  const torso=mesh(new T.LatheGeometry(rings,low?12:28),'cloth',hip,0,0,0);torso.scale.set(bodyScale,small?.78:1,.64);ellipsoid(hip,'secondary',.24,0,-.015,0,bodyScale,.7,.69);
  const breast=ellipsoid(chest,'cloth',.25,0,-.105,.025,bodyScale,1.1,.69);
  for(const side of [-1,1]){const panel=ellipsoid(chest,'secondary',.155,side*.12*bodyScale,-.1,.112,.92,.91,.43);panel.rotation.z=side*.12;}
  tube(chest,'metal',[[-.22,.06,.08],[-.16,.0,.17],[0,-.02,.205],[.16,.0,.17],[.22,.06,.08]],.013);
  const belt=ring(hip,'dark',.216,.035,0,.045,0);belt.rotation.x=Math.PI/2;belt.scale.y=.68;tube(chest,'metal',[[-.18,-.22,.22],[0,-.25,.26],[.18,-.22,.22]],.018);
  rounded(hip,'metal',.12,.11,.045,0,.055,.185);for(const s of [-1,1])rounded(hip,'dark',.11,.23,.13,s*.255,.06,0,.025);
  const l=small?.35:.53,shin=small?.32:.49,armLength=small?.32:.36;
  for(const [sign,side]of [[-1,'L'],[1,'R']]){
   const thigh=bone('thigh_'+side,hip,sign*(small?.14:.16),-.07,0),knee=bone('shin_'+side,thigh,0,-l,0),foot=bone('foot_'+side,knee,0,-shin,0);
   ellipsoid(thigh,'cloth',small?.14:.125,0,-l*.44,0,1.0,l/(small?.27:.25),.9);ellipsoid(knee,'dark',.10,0,-shin*.44,0,.82,shin/.19,.89);ellipsoid(knee,'metal',.10,0,-.025,.026,.96,.78,.54);ellipsoid(foot,'dark',.105,0,-.015,.09,.88,.8,1.8);ellipsoid(knee,'secondary',.105,0,-shin*.67,.015,.91,1.65,.8);ring(knee,'metal',.106,.018,0,-shin*.49,0).rotation.x=Math.PI/2;
   const shoulder=bone('arm_'+side,chest,sign*(small?.29:.31)*bodyScale,.045,0),elbow=bone('forearm_'+side,shoulder,0,-armLength,0),hand=bone('hand_'+side,elbow,0,-armLength*.87,0);
   ellipsoid(shoulder,profile.name==='Draven'?'skin':'secondary',.14,0,-.035,0,1,.9,1);capsule(shoulder,profile.name==='Draven'?'skin':'cloth',.087,armLength,0,-armLength*.49,0);capsule(elbow,'skin',.075,armLength*.86,0,-armLength*.43,0);ellipsoid(elbow,'metal',.081,0,-armLength*.67,.012,.85,1.3,.79);ellipsoid(hand,'skin',.069,0,-.032,0,.78,1.12,.66);
   for(let finger=0;finger<3;finger++)capsule(hand,'skin',.018,.073,(-1+finger)*.032,-.091,.018);
   attachSocket('hand_'+side,hand,0,-.06,.06);attachSocket('foot_'+side,foot,0,0,.07);
   shoulder.rotation.z=sign*.1;
  }
  face(head);hairstyle(head,chest);attachSocket('head',head,0,.2,.15);attachSocket('chest',chest,0,0,.25);attachSocket('root',hip,0,0,0);
  const weapon=profile.weapon;
  if(weapon==='bow'){ornateWeapon(joints.hand_L,'bow');attachSocket('muzzle',joints.hand_L,0,-.05,.14);}
  else if(weapon==='void_cannons')for(const side of ['L','R']){const pod=ornateWeapon(joints['arm_'+side],weapon,side==='R'?1:-1);pod.position.set(side==='L'?-.1:.1,.2,-.05);pod.rotation.x=0;}
  else if(['pistols','axes','crossbows','feathers'].includes(weapon)){for(const side of ['L','R'])ornateWeapon(joints['hand_'+side],weapon==='pistols'?'pistol':weapon,side==='R'?1:-1);}
  else if(weapon==='blade_pistol'){gun(joints.hand_R,'pistol');const w=ornateWeapon(joints.hand_L,'spear',-1);w.scale.set(.7,.65,.7);}
  else ornateWeapon(joints.hand_R,weapon);
  if(weapon==='launcher'){const minigun=gun(chest,'rifle',-1);minigun.position.set(-.3,-.15,-.3);minigun.rotation.set(.2,0,-.3);for(let i=0;i<5;i++){const g=taper(minigun,'metal',.035,.035,.7,Math.sin(i*1.26)*.12,Math.cos(i*1.26)*.12,.6);g.rotation.x=Math.PI/2;}}
  if(['Vayne','Xayah','Ashe','Senna','Lucian','Jhin','Samira','Yunara','Kalista'].includes(profile.name)){
   const coat=bone('cape',chest,0,.11,-.17);ribbon('cape_center',coat,profile.name==='Senna'||profile.name==='Jhin'?'light':profile.name==='Vayne'?'secondary':'cloth',profile.name==='Xayah'?.62:.4,profile.name==='Yunara'?1.25:.95);
   for(const s of [-1,1]){const tail=ribbon('coat_'+s,hip,profile.name==='Senna'||profile.name==='Jhin'?'light':'secondary',.22,.75,s*.045);tail.position.set(s*.2,.07,-.055);tail.rotation.z=-s*.08;}
  }
  if(['Ashe','Xayah','Senna','Kalista'].includes(profile.name)){for(const side of [-1,1]){const mantle=ellipsoid(chest,profile.name==='Ashe'?'light':'secondary',.22,side*.19,.04,-.075,1.2,.53,.88);mantle.rotation.z=side*.3;}}
  if(['Caitlyn','Miss Fortune','Sivir'].includes(profile.name)){for(const side of [-1,1]){const skirt=ribbon('skirt_'+side,hip,'cloth',.32,.48,side*.035);skirt.position.set(side*.20,.06,.015);skirt.rotation.z=side*.14;}tube(chest,'metal',[[-.15,.01,.17],[-.10,-.24,.22],[.03,-.46,.17]],.017);}
  if(['Ezreal','Lucian','Zeri'].includes(profile.name)){tube(chest,'dark',[[-.19,.05,.14],[-.10,-.16,.21],[.13,-.39,.15]],.035);for(const side of [-1,1]){const lapel=blade(chest,'secondary',[[0,0],[side*.11,-.12],[side*.05,-.28],[-side*.025,-.14]],.025);lapel.position.set(side*.14,.03,.18);}}
  if(profile.name==='Xayah'){for(let i=0;i<9;i++){const f=blade(chest,i%2?'secondary':'light',[[0,0],[-.05,-.3],[.015,-.63],[.075,-.2]],.025);f.position.set((i-4)*.065,.1,-.19);f.rotation.z=(i-4)*.09;}}
  if(profile.name==='Ezreal'||profile.name==='Samira'){const scarf=ribbon('scarf',chest,'secondary',.13,.63);scarf.position.set(-.16,.14,-.09);ring(neck,'secondary',.14,.05,0,-.01,0).rotation.x=Math.PI/2;}
  if(profile.name==='Draven'){for(let i=0;i<14;i++)ellipsoid(chest,'light',.06,Math.cos(i*.45)*.33,.05,Math.sin(i*.45)*.13,1,1.5,1);}
  if(profile.name==='Twitch'){
   const muzzle=ellipsoid(head,'skin',.13,0,-.03,.2,.7,.7,1.65);ellipsoid(head,'dark',.045,0,-.02,.39);for(const s of [-1,1])for(let i=0;i<3;i++)tube(head,'light',[[s*.04,-.03,.3],[s*.2,-.025+i*.023,.31],[s*.32,-.03+i*.04,.28]],.005);
   const chain=bone('tail',hip,0,-.03,-.16);let prev=chain;const bs=[];for(let i=0;i<7;i++){const b=bone('tail_'+i,prev,0,i?-.018:0,i?-.16:0);capsule(b,'skin',.035-i*.003,.18,0,0,-.07).rotation.x=Math.PI/2;bs.push(b);prev=b;}secondary.push({name:'tail',chain:bs,kind:'tail',strength:.1});
  }
  if(profile.name==='Yunara'){
   for(let i=0;i<3;i++){const skirt=ribbon('robe_'+i,hip,i===1?'light':'secondary',.28,1.01);skirt.position.set((i-1)*.23,-.02,.1);}
   const halo=ring(chest,'metal',.53,.021,0,.25,-.27);details.push({object:halo,kind:'halo'});for(let i=0;i<6;i++){const a=i*Math.PI/3,o=ellipsoid(root,'energy',.072,Math.sin(a)*.71,1.3+Math.cos(a)*.24,Math.cos(a)*.6);details.push({object:o,kind:'orb',angle:a});}
  }
  if(profile.name==='Zeri'){rounded(chest,'metal',.25,.35,.13,0,-.06,-.19);for(const s of [-1,1])ellipsoid(head,'energy',.18,s*.24,.14,-.08,1,.85,1);}
  if(profile.name==='Jhin'){ellipsoid(joints.arm_R,'metal',.24,.025,.07,0,1,.72,1);for(let i=0;i<4;i++)rounded(chest,'metal',.11,.021,.023,0,-.02-i*.06,.23);}
  if(profile.name==='Kalista'){for(const s of [-1,1]){const spike=blade(joints['arm_'+(s<0?'L':'R')],'light',[[-.025,0],[0,.32],[.06,0]],.055);spike.position.set(s*.07,.04,-.09);}}
  if(profile.body==='tall')root.scale.setScalar(1.08);else if(small)root.scale.setScalar(.96);
  if(profile.locomotion==='hunched'){spine.rotation.x=.35;head.rotation.x=-.2;}
 }
 function creature(dragon=false){
  const hip=bone('hips',root,0,.63,0),spine=bone('spine',hip,0,.06,.12),chest=bone('chest',spine,0,.03,.28),neck=bone('neck',chest,0,.08,.34),head=bone('head',neck,0,.09,.24);
  ellipsoid(hip,'secondary',.48,0,.03,-.08,dragon?.7:1.05,.8,1.45);ellipsoid(chest,'cloth',.35,0,.01,.04,1,.83,1.2);
  ellipsoid(head,'skin',dragon?.3:.33,0,0,.02,dragon?1.15:1.06,1,1.1);const jaw=bone('jaw',head,0,-.11,.21);ellipsoid(jaw,'skin',.22,0,-.03,.11,1.3,.53,1.1);ellipsoid(head,'dark',.23,0,-.05,.25,1,.59,.22);for(const s of [-1,1]){ellipsoid(head,'light',.085,s*.215,.09,.18,1,.85,.35);ellipsoid(head,'eye',.044,s*.237,.094,.208,.75,1,.5);ellipsoid(head,'dark',.018,s*.243,.09,.223,.6,1,.4);ellipsoid(head,'dark',.031,s*.14,.013,.345);const horn=tube(head,'metal',[[s*.19,.18,-.01],[s*.24,.37,-.12],[s*.18,.49,-.18]],.04);}
  for(let i=-2;i<=2;i++){const tooth=mesh(new T.ConeGeometry(.025,.075,8),'light',head,i*.072,-.055,.37);tooth.rotation.x=Math.PI;}
  const legpairs=dragon?2:3;
  for(let pair=0;pair<legpairs;pair++)for(const [s,side]of [[-1,'L'],[1,'R']]){const name=pair===0?'front':pair===1?'rear':'middle',thigh=bone(name+'_'+side,hip,s*.28,-.05,.29-pair*.48),knee=bone(name+'_knee_'+side,thigh,s*.1,-.19,.045),foot=bone(name+'_foot_'+side,knee,0,-.28,.09);capsule(thigh,'cloth',.095,.28,s*.04,-.13,0);capsule(knee,'skin',.07,.31,0,-.13,0);ellipsoid(foot,'skin',.094,0,-.03,.035,1.4,.63,1.6);for(let c=-1;c<=1;c++)ellipsoid(foot,'light',.033,c*.06,-.025,.145,.6,.6,1.8);}
  const tail=bone('tail',hip,0,.08,-.48),chain=[];let prev=tail;for(let i=0;i<7;i++){const b=bone('tail_'+i,prev,0,0,i?-.2:0);const part=taper(b,i===6?'light':'secondary',.1-i*.011,.112-i*.012,.23,0,0,-.09);part.rotation.x=Math.PI/2;chain.push(b);prev=b;}secondary.push({name:'tail',chain,kind:'tail',strength:.09});
  if(dragon){
   for(const[s,side]of[[-1,'L'],[1,'R']]){const wing=bone('wing_'+side,chest,s*.22,.13,-.06);const points=[[0,0],[s*.23,.52],[s*.79,.74],[s*1.03,.22],[s*.61,.1],[s*.2,-.05]];const membrane=blade(wing,'secondary',points,.025);membrane.material=new T.MeshStandardMaterial({color:palette.secondary,roughness:.7,side:T.DoubleSide});for(const end of [[s*.23,.52],[s*.79,.74],[s*1.03,.22],[s*.61,.1]])tube(wing,'metal',[[0,0,0],[end[0]*.55,end[1]*.6,0],[...end,0]],.021);wing.rotation.y=s*.55;}
   for(let i=0;i<5;i++)mesh(new T.ConeGeometry(.06,.14,8),'metal',hip,0,.4,-.35+i*.18);
  }else{
   for(let i=0;i<4;i++){const plate=ellipsoid(hip,'metal',.34,0,.13,-.3+i*.16,1.2,.43,.5);plate.rotation.x=-.2;}
   for(const s of [-1,1])for(let i=0;i<3;i++)ellipsoid(hip,'energy',.08,s*.32,.14,-.2+i*.18,1,.6,.8);
  }
  attachSocket('muzzle',head,0,-.015,.42);attachSocket('head',head,0,.3,.1);attachSocket('chest',chest,0,.2,.1);attachSocket('root',hip);root.scale.setScalar(dragon?1.06:1.08);
 }
 function vehicle(){
  const hip=bone('hips',root,0,.8,0),spine=bone('spine',hip,0,.24,-.12),chest=bone('chest',spine,0,.14,0),neck=bone('neck',chest,0,.1,0),head=bone('head',neck,0,.16,0);
  ellipsoid(chest,'cloth',.19,0,-.12,0,1,1.3,.7);
  for(const [side,sign]of [['L',-1],['R',1]]){const arm=bone('arm_'+side,chest,sign*.17,0,0),fore=bone('forearm_'+side,arm,0,-.2,0),hand=bone('hand_'+side,fore,0,-.16,0);capsule(arm,'cloth',.06,.2,0,-.10,0);capsule(fore,'skin',.049,.16,0,-.08,0);ellipsoid(hand,'skin',.055,0,0,0);arm.rotation.x=-1.2;fore.rotation.x=-.3;attachSocket('hand_'+side,hand);}
  const hull=ellipsoid(hip,'secondary',.49,0,0,.05,1.35,.7,2);rounded(hip,'metal',.88,.055,1.2,0,.23,-.15,.07);
  const glass=ellipsoid(hip,'glass',.36,0,.27,-.1,1.1,.65,1.1);glass.material=new T.MeshStandardMaterial({color:palette.energy,transparent:true,opacity:.27,roughness:.1,side:T.DoubleSide});
  face(head);ellipsoid(head,'cloth',.23,0,.12,-.06,1,.75,.8);for(const s of [-1,1]){const wing=rounded(hip,'cloth',1.1,.07,.62,s*.67,-.025,-.05,.06);wing.rotation.z=-s*.07;rounded(hip,'metal',.92,.025,.045,s*.67,.017,-.05);const fin=blade(hip,'secondary',[[0,0],[.14,.3],[.5,.35],[.6,0]],.06);fin.position.set(s*.17,.03,-.8);fin.rotation.y=s*.15;const exhaust=taper(hip,'metal',.085,.09,.26,s*.23,-.06,-.78);exhaust.rotation.x=Math.PI/2;ring(hip,'energy',.073,.018,s*.23,-.06,-.94);}
  rounded(hip,'dark',.2,.14,.85,0,-.17,.61);for(const s of [-1,1]){const barrel=taper(hip,'metal',.035,.04,.7,s*.23,-.15,.74);barrel.rotation.x=Math.PI/2;attachSocket(s<0?'off_muzzle':'muzzle',hip,s*.23,-.15,1.1);}
  const rotor=bone('rotor',hip,0,0,1.035);for(let i=0;i<3;i++){const b=rounded(rotor,'metal',.055,.47,.027,0,.2,0,.014);b.rotation.z=i*Math.PI*2/3;}ellipsoid(rotor,'metal',.09,0,0,.04,1,1,.65);
  attachSocket('head',head,0,.23,.1);attachSocket('chest',chest,0,.2,.1);attachSocket('root',hip);
 }
 if(profile.rig==='dragon'||profile.rig==='creature')creature(profile.rig==='dragon');else if(profile.rig==='vehicle')vehicle();else humanoid();
 // A deforming scarf membrane proves the export contains a genuine skin, not
 // only separate rigid props. Its upper seam follows chest, lower hem hips.
 if(profile.rig==='human'){
  root.updateMatrixWorld(true);const h=joints.hips,c=joints.chest,skeleton=new T.Skeleton([h,c]),rows=8,cols=8,positions=[],skinI=[],skinW=[],indices=[];
  for(let row=0;row<=rows;row++)for(let col=0;col<=cols;col++){const u=col/cols-.5,v=row/rows,y=1.13+v*.55;positions.push(u*.43,y,-.175-.02*Math.sin(u*Math.PI));skinI.push(0,1,0,0);skinW.push(1-v,v,0,0);}
  for(let r=0;r<rows;r++)for(let c0=0;c0<cols;c0++){const a=r*(cols+1)+c0,b=a+cols+1;indices.push(a,a+1,b,a+1,b+1,b);}
  const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.Float32BufferAttribute(positions,3));geometry.setAttribute('skinIndex',new T.Uint16BufferAttribute(skinI,4));geometry.setAttribute('skinWeight',new T.Float32BufferAttribute(skinW,4));geometry.setIndex(indices);geometry.computeVertexNormals();const skin=new T.SkinnedMesh(geometry,mat('cloth'));skin.name='deforming_back_panel';skin.castShadow=true;skin.receiveShadow=true;root.add(skin);skin.bind(skeleton);skeleton.calculateInverses();
 }
 root.updateMatrixWorld(true);for(const[name,b]of Object.entries(joints))rest[name]={p:b.position.clone(),r:b.rotation.clone()};
 return {root,joints,rest,secondary,sockets,details,profile,materials,helpers:{mesh,ring,tube},metrics(){let meshes=0,vertices=0,triangles=0;root.traverse(o=>{if(o.isMesh){meshes++;vertices+=o.geometry.attributes.position.count;triangles+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3;}});return{meshes,vertices,triangles,joints:Object.keys(joints).length};}};
}
function animateRig(rig,state={}){
 const {joints:j,rest,profile:p}=rig,t=state.time||0,speed=clamp(state.speed||0,0,2),walking=speed>.015;
 for(const[name,b]of Object.entries(j)){b.position.copy(rest[name].p);b.rotation.copy(rest[name].r);}
 const add=(n,x=0,y=0,z=0)=>{if(j[n]){j[n].rotation.x+=x;j[n].rotation.y+=y;j[n].rotation.z+=z;}};
 const set=(n,x=0,y=0,z=0)=>{if(j[n])j[n].rotation.set(x,y,z);};
 const phase=state.gaitPhase??t*(p.locomotion==='hop'?8:6.6),stride=Math.min(.34,speed*.24),breath=Math.sin(t*2.05)*.008;
 if(j.chest){j.chest.scale.set(1,1+breath,1+breath*.35);}if(j.hips)j.hips.position.y+=breath*.3;
 if(p.rig==='human'||p.rig==='yordle'){
  if(['rifle','electric_rifle','relic_cannon','cannon','launcher'].includes(p.weapon)){set('arm_R',-1.17,0,.13);set('forearm_R',-.23,0,.04);set('arm_L',-1.04,.2,-.13);set('forearm_L',-.45,-.2,0);}
  else {add('arm_L',-.06,0,-.05);add('arm_R',-.1,0,.045);add('forearm_L',-.2);add('forearm_R',-.2);}
  if(walking){
   for(const[s,side]of[[-1,'L'],[1,'R']]){
    const c=phase+(s<0?Math.PI:0),sine=Math.sin(c),lift=Math.max(0,sine)*.1*speed,forward=Math.cos(c)*stride;
    const length=p.rig==='yordle'?.67:1.02,l1=p.rig==='yordle'?.35:.53,l2=length-l1,d=Math.min(length-.001,Math.sqrt((length-lift)**2+forward**2));
    const knee=Math.PI-Math.acos(clamp((l1*l1+l2*l2-d*d)/(2*l1*l2),-1,1)),hip=Math.atan2(forward,length-lift)-Math.acos(clamp((l1*l1+d*d-l2*l2)/(2*l1*d),-1,1));
    set('thigh_'+side,hip);set('shin_'+side,knee);set('foot_'+side,-hip-knee);
    if(!['rifle','electric_rifle','relic_cannon','cannon','launcher','bow'].includes(p.weapon))add('arm_'+side,-Math.sin(c)*.25*speed);
   }
   add('hips',0,Math.sin(phase)*.04*speed,Math.cos(phase)*.014*speed);add('spine',0,-Math.sin(phase)*.035*speed);
   j.hips.position.y-=Math.abs(Math.sin(phase))*.025*speed;
   if(p.locomotion==='hop'){j.hips.position.y+=Math.max(0,Math.sin(phase))*.17;add('thigh_L',-.22);add('thigh_R',-.22);}
   if(p.locomotion==='agile')add('spine',.09*speed);if(p.locomotion==='heavy')add('spine',.05*speed);
   if(p.locomotion==='float'){j.hips.position.y+=.11+Math.sin(t*3)*.035;set('thigh_L',-.17);set('thigh_R',-.14);set('shin_L',.35);set('shin_R',.25);}
  }else {add('head',Math.sin(t*1.3)*.015,Math.sin(t*.7)*.015);add('forearm_L',Math.sin(t*1.8)*.008);}
 }else if(p.rig==='dragon'||p.rig==='creature'){
  for(const [index,name]of ['front','rear','middle'].entries())for(const[s,side]of[[-1,'L'],[1,'R']]){const a=phase+(s<0?Math.PI:0)+index*Math.PI;add(name+'_'+side,Math.sin(a)*.42*speed);add(name+'_knee_'+side,Math.max(0,Math.cos(a))*.4*speed);add(name+'_foot_'+side,-Math.sin(a)*.2*speed);}
  j.hips.position.y+=Math.sin(phase*2)*.021*speed;add('head',Math.sin(t*1.7)*.025,Math.sin(t*.8)*.025);
  for(const[s,side]of[[-1,'L'],[1,'R']])add('wing_'+side,Math.sin(t*1.5)*.035,s*Math.sin(t*1.9)*.05,s*Math.sin(t*1.5)*.015);
 }else if(p.rig==='vehicle'){
  j.hips.position.y+=Math.sin(t*2.4)*.06;add('hips',Math.sin(t*2)*.02,0,Math.sin(t*1.3)*.025);add('head',0,Math.sin(t*.9)*.045);if(j.rotor)j.rotor.rotation.z=t*34;
 }
 const action=state.action||'Idle',slot=action==='AA'?'attack':action==='P'?'passive':action;
 const spec=p.skills[slot]||p[slot],u=clamp(state.progress||0),weight=state.weight??(spec?pulse(u,.25,.68):0),pose=spec?.pose;
 if(spec&&weight>0){
  const w=weight,release=smooth((u-.25)/.2),follow=smooth((u-.5)/.5),osc=Math.sin(t*23)*.04;
  const blend=(n,x,y=0,z=0)=>{if(j[n]){j[n].rotation.x=j[n].rotation.x*(1-w)+x*w;j[n].rotation.y=j[n].rotation.y*(1-w)+y*w;j[n].rotation.z=j[n].rotation.z*(1-w)+z*w;}};
  // Every pose includes balance through hips/spine/head, not only weapon arms.
  add('hips',0,-.06*w,0);add('spine',-.045*w,.065*w,0);add('head',.02*w,-.04*w,0);
  if(pose==='bow'||pose==='bow_charge'||pose==='bow_high'){
   blend('arm_L',-1.52-(pose==='bow_high'?.3:0),.12,-.18);blend('forearm_L',-.05);blend('arm_R',-1.2,-.55,.4);blend('forearm_R',-.83-release*.14,-.65,0);add('chest',0,-.15*w);add('head',0,.17*w);
   if(release>.8)blend('forearm_R',-.65+follow*.25,-.2,0);
  }else if(['rifle','heavy_rifle','kneel','kneel_channel','cannon','crossbow','crossbow_channel'].includes(pose)){
   blend('arm_R',-1.38,0,.12);blend('forearm_R',-.2);blend('arm_L',-1.12,.32,-.13);blend('forearm_L',-.53,-.35);add('chest',-.055*w,0,0);
   if(release>.5){add('spine',osc*w);add('arm_R',Math.sin(t*29)*.025*w);}
   if(pose.startsWith('kneel')){j.hips.position.y-=.23*w;blend('thigh_L',-.65);blend('shin_L',1.04);blend('thigh_R',-.98);blend('shin_R',1.3);blend('foot_L',-.39);blend('foot_R',-.32);}
  }else if(['pistol','gauntlet','cast','point'].includes(pose)){
   blend('arm_R',-1.54,.04,.06);blend('forearm_R',-.04);blend('arm_L',-.28,0,-.15);add('chest',0,-.12*w);add('spine',(release>.5?.045:-.02)*w);if(release>.5)blend('forearm_R',-.13-follow*.2);
  }else if(['dual_cast','dual_channel','spread','two_hand','heavy_two_hand'].includes(pose)){
   for(const[s,side]of[[-1,'L'],[1,'R']]){blend('arm_'+side,-1.45+(pose==='spread'?.18:0),-s*.1,s*(pose==='spread'?.65:.18));blend('forearm_'+side,pose==='two_hand'?-.33:-.06);}
   if(pose.includes('channel')){add('spine',osc*w);add('arm_L',Math.sin(t*35)*.026*w);add('arm_R',-Math.sin(t*35)*.026*w);}
   if(pose==='heavy_two_hand'){blend('arm_L',-1.22,.3,-.1);blend('forearm_L',-.55,-.27);add('spine',-.09*w);}
  }else if(['throw','spear_throw','dual_throw','throw_heavy','disc_throw','axe','brandish','rocket','rocket_heavy','switch'].includes(pose)){
   const swing=-.55-(1-release)*1.75+follow*.5;blend('arm_R',swing,-.2+release*.35,.16);blend('forearm_R',-.7*(1-release));blend('arm_L',pose==='dual_throw'?swing:-.3,.1,-.22);if(pose==='dual_throw')blend('forearm_L',-.7*(1-release));
   add('hips',0,(-.25+release*.45)*w);add('chest',0,(-.25+release*.3)*w);add('spine',(.1-release*.14)*w);
   if(pose==='rocket'||pose==='rocket_heavy'){blend('arm_R',-1.42);blend('forearm_R',-.18);blend('arm_L',-1.15,.3,-.13);blend('forearm_L',-.5,-.3);}
  }else if(['buff','passive','orbit','rally','summon','summon_wide','ascend','guard','dash_guard'].includes(pose)){
   const wide=['summon_wide','ascend','rally','orbit'].includes(pose);for(const[s,side]of[[-1,'L'],[1,'R']]){blend('arm_'+side,wide?-.8:-1.02,s*.12,s*(wide?.95:.36));blend('forearm_'+side,wide?-.4:-.9);}
   add('head',-.1*w);if(pose==='ascend'){j.hips.position.y+=.37*w;blend('thigh_L',-.1);blend('thigh_R',-.15);blend('shin_L',.28);blend('shin_R',.25);}
  }else if(['pull','place','bomb','artillery'].includes(pose)){
   blend('arm_R',pose==='place'?-.65:-1.4,.12,.16);blend('forearm_R',-.35-release*.65);blend('arm_L',pose==='pull'?-1.15:-.45,-.1,-.22);add('spine',pose==='place'?.38*w:-.07*w);if(pose==='place'){blend('thigh_L',-.23);blend('shin_L',.45);j.hips.position.y-=.12*w;}
  }else if(['spin','spin_channel','dash_slash'].includes(pose)){
   add('hips',0,u*Math.PI*2*(pose==='spin_channel'?2:1)*w);for(const[s,side]of[[-1,'L'],[1,'R']]){blend('arm_'+side,-.6,0,s*1.05);blend('forearm_'+side,-.12);}add('spine',.08*w);blend('thigh_L',-.15);blend('thigh_R',.16);
  }else if(['dash','recoil_dash','blink','glide','slide','sprint','fade','roll','jump','leap_fan'].includes(pose)){
   const lean=pose==='recoil_dash'?-.23:.28;add('spine',lean*w);blend('arm_R',-.65,0,.35);blend('arm_L',-.4,0,-.28);blend('thigh_L',-.6);blend('shin_L',.9);blend('thigh_R',.4);blend('shin_R',.5);
   if(pose==='roll')add('hips',u*Math.PI*2*w,0,0);
   if(pose==='jump'||pose==='leap_fan'){j.hips.position.y+=Math.sin(u*Math.PI)*.65*w;blend('thigh_R',-.5);blend('shin_R',1.0);if(pose==='leap_fan'){blend('arm_L',-.8,0,-1.1);blend('arm_R',-.8,0,1.1);}}
  }else if(['breath','spit','spit_low','sneeze','call'].includes(pose)){
   add('neck',(-.12+release*.22)*w);add('head',pose==='call'?-.4*w:pose==='spit_low'?.25*w:-.08*w);add('jaw',(.2+release*.3)*w);add('spine',Math.sin(u*Math.PI*2)*.06*w);if(pose==='sneeze'){add('head',Math.sin(u*Math.PI*2)*.22*w);j.hips.position.z-=Math.sin(u*Math.PI)*.1*w;}
  }else if(pose==='fly'){
   j.hips.position.y+=.45*w;for(const[s,side]of[[-1,'L'],[1,'R']]){add('wing_'+side,0,-s*.25,s*Math.sin(t*12)*.55*w);add('front_'+side,-.2*w);add('rear_'+side,.25*w);}add('spine',-.12*w);
  }else if(pose==='barrage')add('hips',Math.sin(t*22)*.012*w,0,0);
  if(p.rig==='creature'&&pose==='artillery'){add('neck',-.35*w);add('head',-.27*w);add('jaw',.5*w);add('spine',-.12*w);}
  if(p.rig==='vehicle'){add('hips',pose==='dash'?.18*w:pose==='bomb'?-.1*w:0,0,pose==='dash'?.13*w:0);add('head',-.05*w);}
 }
 for(const item of rig.secondary){item.chain.forEach((b,index)=>{const lag=t*3.6-index*.64,amount=item.strength*(.25+speed*.8+weight*.65),axis=item.kind==='tail'?'y':'x';b.rotation[axis]+=Math.sin(lag)*amount;b.rotation.z+=Math.sin(lag*.65)*amount*.35;});}
 for(const d of rig.details){if(d.kind==='orb'){const a=d.angle+t*.65;d.object.position.set(Math.sin(a)*.72,1.3+Math.cos(a)*.14,Math.cos(a)*.65);}else if(d.kind==='halo')d.object.rotation.z=t*.15;}
 rig.root.updateMatrixWorld(true);return {action,pose,weight,release:spec?.anticipation||.28};
}
function animationClips(T,rig){
 const clips=[],names=['Idle','Walk','AA','P','Q','W','E','R'];
 for(const name of names){const spec=name==='AA'?rig.profile.attack:name==='P'?rig.profile.passive:rig.profile.skills[name],duration=name==='Idle'?3:name==='Walk'?1.2:spec.study_duration;
  const tracks=[],times=[],poses={};for(const joint of Object.keys(rig.joints))poses[joint]={rotation:[],position:[]};const count=Math.ceil(duration*30);
  for(let frame=0;frame<=count;frame++){const t=frame/count*duration;times.push(t);animateRig(rig,{time:t,action:name,progress:t/duration,speed:name==='Walk'?1:0,gaitPhase:t/duration*Math.PI*2});for(const [joint,b]of Object.entries(rig.joints)){poses[joint].rotation.push(...b.quaternion.toArray());poses[joint].position.push(...b.position.toArray());}}
  if(name==='Idle'||name==='Walk'){for(const values of Object.values(poses)){values.rotation.splice(-4,4,...values.rotation.slice(0,4));values.position.splice(-3,3,...values.position.slice(0,3));}}
  for(const [joint,values]of Object.entries(poses)){if(values.rotation.some((v,i)=>Math.abs(v-values.rotation[i%4])>1e-7))tracks.push(new T.QuaternionKeyframeTrack(joint+'.quaternion',times,values.rotation));if(values.position.some((v,i)=>Math.abs(v-values.position[i%3])>1e-7))tracks.push(new T.VectorKeyframeTrack(joint+'.position',times,values.position));}
  const clip=new T.AnimationClip(name,duration,tracks);clip.userData={timing:'authored visual study; not a game timing measurement'};clips.push(clip);
 }
 animateRig(rig,{time:0});return clips;
}
const API={createRig,animateRig,animationClips,clamp,smooth,pulse};
if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanRig=API;
})(typeof globalThis!=='undefined'?globalThis:this);
