/* Original lane environment. Shared materials/geometries and bounded foliage budgets. */
(function(scope){'use strict';
function createLegacyArena(T,scene,{software=false,quality='high'}={}){
 const root=new T.Group();root.name='SharpWR_Rift_Lane';scene.add(root);const geometries=new Map(),materials=new Map(),water=[],lights=[];
 const hash=n=>{const v=Math.sin(n*127.1+19.7)*43758.54;return v-Math.floor(v);};
 function mat(color,roughness=.9){const key=color+roughness;if(!materials.has(key))materials.set(key,new T.MeshStandardMaterial({color,roughness,metalness:roughness<.6?.35:0}));return materials.get(key);}
 function geom(kind){if(!geometries.has(kind))geometries.set(kind,kind==='plane'?new T.PlaneGeometry(1,1,software?24:1,software?20:1):kind==='rock'?new T.IcosahedronGeometry(1,0):kind==='leaf'?new T.IcosahedronGeometry(1,1):kind==='cone'?new T.ConeGeometry(1,1,7):kind==='trunk'?new T.CylinderGeometry(.75,1,1,7):kind==='ring'?new T.TorusGeometry(1,.025,5,36):new T.BoxGeometry(1,1,1));return geometries.get(kind);}
 function mesh(kind,color,pos,scale,rough=.9){const m=new T.Mesh(geom(kind),mat(color,rough));m.position.set(...pos);m.scale.set(...scale);m.castShadow=!software&&kind!=='plane';if(software&&kind==='plane')m.renderOrder=color==='#274d36'?-10:-8;m.receiveShadow=true;root.add(m);return m;}
 mesh('plane','#274d36',[0,-.09,0],[26,20,1]).rotation.x=-Math.PI/2;
 if(!software)mesh('box','#183f31',[0,-.25,0],[26,.3,20]);
 // Worn central lane: broken edges, warm stone, patches of grass between slabs.
 const tiles=[],limit=software?12:22;for(let x=-limit;x<=limit;x++)for(let z=-3;z<=3;z++){const seed=(x+50)*31+z+4,a=x*.58,b=z*.57;if(Math.abs(a)>11.8)continue;tiles.push({x:a,z:b,h:hash(seed),seed});}
 const tileGeo=new T.BoxGeometry(.54,.08,.53);geometries.set('tiles',tileGeo);const tileMat=mat('#838677');
 if(!software){const batch=new T.InstancedMesh(tileGeo,tileMat,tiles.length),dummy=new T.Object3D();for(const [i,v]of tiles.entries()){dummy.position.set(v.x,-.04+v.h*.009,v.z);dummy.rotation.y=(v.h-.5)*.06;dummy.scale.set(1,.7+v.h*.3,1);dummy.updateMatrix();batch.setMatrixAt(i,dummy.matrix);batch.setColorAt(i,new T.Color(v.h>.8?'#a09e83':v.h<.18?'#60745f':'#828574'));}batch.receiveShadow=true;root.add(batch);}else for(const v of tiles){const m=new T.Mesh(tileGeo,mat(v.h>.8?'#92917a':v.h<.18?'#667761':'#7b8274'));m.position.set(v.x,-.04,v.z);m.renderOrder=-9;root.add(m);}
 for(let i=0;i<(software?34:74);i++){const x=(hash(i+10)*2-1)*11.7,sign=i%2?1:-1,z=sign*(2.05+hash(i+75)*.65),size=.15+hash(i+99)*.35;mesh('rock',i%3?'#617062':'#82917b',[x,.02,z],[size,.10+size*.35,size*.8]).rotation.y=i;}
 // Brush clusters and layered broad-leaf trees frame, rather than obscure, the playable lane.
 for(let i=0;i<(software?20:46);i++){const x=(hash(i+200)*2-1)*11,z=(i%2?1:-1)*(2.8+hash(i+310)*1.25),s=.3+hash(i+460)*.4;const m=mesh('leaf',i%3?'#326946':'#477b44',[x,s*.35,z],[s,s*.55,s*.75]);m.rotation.y=i;}
 for(let i=0;i<(software?10:24);i++){const x=(hash(i+501)*2-1)*11.8,z=(i%2?1:-1)*(4.8+hash(i+651)*2.8),h=1.6+hash(i+71)*1.3;mesh('trunk','#65513a',[x,h*.35,z],[.15,h*.7,.15]);for(let k=0;k<3;k++)mesh('leaf',k===0?'#254c37':k===1?'#346749':'#4a8050',[x+(hash(i+k+89)-.5)*.4,h*(.66+k*.12),z],[.8-k*.08,.68,.85-k*.06]);}
 // A quiet river outside the lane, with explicit ripples in both render paths.
 const river=mesh('plane','#225d69',[0,-.045,6.5],[24,2.6,1],.35);river.rotation.x=-Math.PI/2;
 for(let i=0;i<12;i++){const m=mesh('plane','#5d9e9d',[(hash(i+811)*2-1)*11,-.038,5.7+hash(i+88)*1.6],[.5+hash(i+12),.028,1],.4);m.rotation.x=-Math.PI/2;water.push({mesh:m,x:m.position.x});}
 for(const [x,color]of[[-8.2,'#56d4ff'],[8.2,'#e17a73']]){mesh('trunk','#586971',[x,.24,0],[.65,.5,.65]);mesh('trunk','#75858a',[x,1.05,0],[.36,1.5,.36]);for(let i=0;i<4;i++){const a=i*Math.PI/2;mesh('rock','#8a958e',[x+Math.cos(a)*.45,1.85,Math.sin(a)*.45],[.18,.42,.18]);}const c=mesh('rock',color,[x,2.16,0],[.25,.56,.25],.3);c.material=mat(color,.3);c.material.emissive=new T.Color(color);c.material.emissiveIntensity=.45;const ring=mesh('ring','#b8a374',[x,.07,0],[.9,.9,.9],.4);ring.rotation.x=-Math.PI/2;if(!software){const l=new T.PointLight(color,2.3,5);l.position.set(x,2,0);root.add(l);lights.push(l);}}
 for(let i=0;i<8;i++){const x=(i-3.5)*2.4,z=i%2?3.2:-3.2;mesh('trunk','#62726c',[x,.2,z],[.15,.4,.15]);const g=mesh('rock','#8bc5b1',[x,.48,z],[.09,.15,.09],.3);g.material.emissive=new T.Color('#73cdb8');g.material.emissiveIntensity=.35;}
 function animate(time){for(const w of water)w.mesh.position.x=w.x+Math.sin(time*.22+w.x)*.12;}
 function dispose(){scene.remove(root);for(const g of geometries.values())g.dispose();for(const m of materials.values())m.dispose();}
 return{root,animate,dispose,metrics:()=>({arenaMeshes:root.children.filter(o=>o.isMesh).length,arenaInstances:software?0:tiles.length})};
}
// Dragon-lane layout is shared by the renderer and the movement solver. World units = 100 game units.
const LANE={bounds:[11.5,8],zones:[[-11.5,11.5,-2.35,2.35],[-9.8,9.8,-3.55,-1.8],[-8.8,-4.6,1.8,3.8],[4.6,8.8,1.8,3.8],[-3.8,1.2,1.8,7.6],[-7,-1.8,5.8,8]],
 brush:[[-6.7,-2.85,3.7,1.15],[5.8,-2.85,3.7,1.15],[-6.7,3.05,3.4,1.25],[6.7,3.05,3.4,1.25]],obstacles:[[-9.5,0,.75],[9.5,0,.75],[-3.1,4.8,.65]]};
for(let i=0;i<10;i++){const a=.48+i*.26;LANE.obstacles.push([-5+Math.cos(a)*2.25,7+Math.sin(a)*2.25,.42]);}
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[2]-b[2]);
function passable(p,margin=.28){return LANE.zones.some(([l,r,b,t])=>p[0]>=l+margin&&p[0]<=r-margin&&p[2]>=b+margin&&p[2]<=t-margin)&&!LANE.obstacles.some(([x,z,r])=>Math.hypot(p[0]-x,p[2]-z)<r+margin);}
function projectPoint(p){if(passable(p))return[p[0],0,p[2]];let best=null,score=Infinity;
 for(const [l,r,b,t]of LANE.zones){let q=[Math.max(l+.29,Math.min(r-.29,p[0])),0,Math.max(b+.29,Math.min(t-.29,p[2]))];
  for(const[x,z,rad]of LANE.obstacles){const dx=q[0]-x,dz=q[2]-z,d=Math.hypot(dx,dz);if(d<rad+.29){q=[x+(dx||1)/(d||1)*(rad+.3),0,z+dz/(d||1)*(rad+.3)];}}
  if(passable(q)&&distance(q,p)<score){best=q;score=distance(q,p);}}
 return best||[0,0,0];}
function trace(from,to,kind='walk'){if(kind==='blink'||kind==='jump'){const length=distance(from,to),steps=Math.max(1,Math.ceil(length/.04));for(let i=steps;i>=0;i--){const u=i/steps,p=[from[0]+(to[0]-from[0])*u,0,from[2]+(to[2]-from[2])*u];if(passable(p))return p;}return from.slice();}const length=distance(from,to),steps=Math.max(1,Math.ceil(length/.06));let out=from.slice();
 for(let i=1;i<=steps;i++){const u=i/steps,p=[from[0]+(to[0]-from[0])*u,0,from[2]+(to[2]-from[2])*u];if(passable(p)){out=p;continue;}
  if(kind!=='walk')break;const x=[p[0],0,out[2]],z=[out[0],0,p[2]];if(passable(x))out=x;else if(passable(z))out=z;else break;}
 out[1]=0;return out;}
const navigation={passable,project:projectPoint,trace,layout:LANE};
function createDragonArena(T,scene,{software=false,quality='high'}={}){
 const root=new T.Group();root.name='SharpWR_Dragon_Lane';scene.add(root);const geos=new Map(),mats=new Map(),textures=[],water=[],crystals=[];
 const hash=n=>{const x=Math.sin(n*127.1+81.2)*43758.5453;return x-Math.floor(x);};
 function material(color,roughness=.95){const key=color+roughness;if(!mats.has(key))mats.set(key,new T.MeshStandardMaterial({color,roughness,metalness:roughness<.55?.25:0}));return mats.get(key);}
 function geometry(kind){if(!geos.has(kind))geos.set(kind,kind==='plane'?new T.PlaneGeometry(1,1):kind==='slab'?(()=>{const shape=new T.Shape();shape.moveTo(-.5,-.28);for(const[x,y]of[[-.3,-.5],[.4,-.46],[.5,.15],[.32,.5],[-.47,.4]])shape.lineTo(x,y);shape.closePath();const g=new T.ExtrudeGeometry(shape,{depth:.045,bevelEnabled:true,bevelThickness:.004,bevelSize:.008,bevelSegments:1,steps:1});g.rotateX(Math.PI/2);return g;})():kind==='rock'?new T.DodecahedronGeometry(1,0):kind==='leaf'?new T.IcosahedronGeometry(1,1):kind==='cylinder'?new T.CylinderGeometry(1,1,1,12):kind==='cone'?new T.ConeGeometry(1,1,8):kind==='ring'?new T.TorusGeometry(1,.018,4,48):new T.BoxGeometry(1,1,1));return geos.get(kind);}
 function mesh(kind,color,x,y,z,sx,sy,sz,rough=.95){const m=new T.Mesh(geometry(kind),material(color,rough));m.position.set(x,y,z);m.scale.set(sx,sy,sz);m.castShadow=!software&&quality!=='low'&&kind!=='plane';m.receiveShadow=true;root.add(m);return m;}
 function flat(color,x,z,w,h,y=-.075){const m=mesh('plane',color,x,y,z,w,h,1);m.rotation.x=-Math.PI/2;m.renderOrder=y<-.09?-10:-9;return m;}
 // Fine diffuse detail prevents large terrain surfaces from reading as flat colour cards.
 function noiseTexture(base,seed,grass=false){if(software||typeof document==='undefined')return null;const canvas=document.createElement('canvas');canvas.width=canvas.height=256;const ctx=canvas.getContext('2d');if(!ctx)return null;ctx.fillStyle=base;ctx.fillRect(0,0,256,256);
  for(let i=0;i<3400;i++){const x=hash(i+seed)*256,y=hash(i+seed+7)*256,v=hash(i+seed+31);ctx.fillStyle=v>.5?'rgba(195,206,129,.12)':'rgba(16,40,24,.15)';ctx.fillRect(x,y,1+v*3,1+v*2);}
  for(let i=0;i<130;i++){const x=hash(i+seed+60)*256,y=hash(i+seed+80)*256;ctx.strokeStyle=grass?'rgba(154,177,91,.18)':'rgba(49,67,42,.17)';ctx.lineWidth=grass?1:.6;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+3,y-(grass?7:2));ctx.lineTo(x+5,y-4);ctx.stroke();}
  const tex=new T.CanvasTexture(canvas);tex.wrapS=tex.wrapT=T.RepeatWrapping;tex.repeat.set(5,4);tex.colorSpace=T.SRGBColorSpace;textures.push(tex);return tex;}
 const turf=noiseTexture('#c1c5b1',340,true),stone=noiseTexture('#d3d1bd',690);if(turf)for(const color of['#304c31','#476b3a','#63764b'])material(color).map=turf;if(stone){stone.repeat.set(1,1);material('#ffffff').map=stone;}
 // Hand-authored palette: blue-green river, sage grass, warm limestone, cool slate cliffs.
 flat('#304c31',0,0,29,22,-.12);flat('#476b3a',0,0,24,8,-.105);flat('#63764b',0,0,23.1,4.85,-.085);
 for(const[x,z,w,h]of LANE.brush)flat('#253e28',x,z,w+.3,h+.25,-.078);
 // The river meets the lane, then opens into the dragon-pit basin.
 const riverShape=new T.Shape();const banks=[[-3.8,1.7],[-2.8,2.1],[-1.7,2.25],[.35,2.1],[1,3],[.8,4.8],[1.1,6.8],[-1.1,8.3],[-6.5,8.5],[-7.1,6],[-3.9,5.8],[-3.5,4.3]];riverShape.moveTo(banks[0][0],-banks[0][1]);for(const[x,z]of banks.slice(1))riverShape.lineTo(x,-z);riverShape.closePath();const riverGeo=new T.ShapeGeometry(riverShape);riverGeo.rotateX(-Math.PI/2);geos.set('river-bank',riverGeo);const river=new T.Mesh(riverGeo,material('#427d78',.5));river.position.y=-.062;root.add(river);
 const waterDetail=noiseTexture('#91afa0',1034);if(waterDetail){waterDetail.repeat.set(.15,.15);river.material.map=waterDetail;}
 for(let i=0;i<banks.length;i++){const[x,z]=banks[i];mesh('rock','#7d8a64',x,.015,z,.27,.07,.25);}
 for(let i=0;i<14;i++){const m=flat('#79b8a5',-3+hash(i+2)*3.7,2.9+hash(i+5)*4.6,.3+hash(i+4)*.55,.022,-.047);m.rotation.z=.1;water.push({m,x:m.position.x});}
 // Lane paving: offset, irregular slabs and a lighter central worn footpath.
 const tileRows=[];for(let x=-22;x<=22;x++)for(let z=-4;z<=4;z++){const seed=(x+25)*19+z+5,px=x*.5+(z%2)*.23,pz=z*.46;if(Math.abs(px)>11.2||hash(seed+203)<(Math.abs(z)>2?.48:.12))continue;tileRows.push({p:[px+(hash(seed+63)-.5)*.09,-.027,pz+(hash(seed+37)-.5)*.08],s:[.44+hash(seed+22)*.045,1,.39+hash(seed+18)*.04],r:[0,hash(seed+9)*.55,0],color:Math.abs(z)<2?(hash(seed)>.5?'#979981':'#848c72'):hash(seed)>.45?'#828e6e':'#6b7d58'});}
 function batch(kind,rows){if(software){for(const row of rows){const m=mesh(kind,row.color,...row.p,...row.s);if(row.r)m.rotation.set(...row.r);if(kind==='slab')m.renderOrder=-9;}return;}
  const geo=geometry(kind),mat=material('#ffffff'),b=new T.InstancedMesh(geo,mat,rows.length),dummy=new T.Object3D();for(const[i,row]of rows.entries()){dummy.position.set(...row.p);dummy.scale.set(...row.s);dummy.rotation.set(...(row.r||[0,0,0]));dummy.updateMatrix();b.setMatrixAt(i,dummy.matrix);b.setColorAt(i,new T.Color(row.color));}b.receiveShadow=true;b.castShadow=quality==='high'&&kind!=='slab';root.add(b);}
 batch('slab',software?tileRows.filter((_,i)=>i%2===0):tileRows);
 // Low stone shoulders and continuous cliff boundaries follow the same walkable rectangles.
 const rockRows=[];for(let i=0;i<62;i++){const x=-12.6+i*.41,z=-4.0-(hash(i+9)*.38);rockRows.push({p:[x,.23,z],s:[.42,.38+hash(i)*.32,.47],r:[.1,hash(i)*Math.PI,.08],color:i%3?'#596a59':'#758271'});}
 for(let i=0;i<47;i++){const x=-12.5+i*.54;if(x>-4.1&&x<1.6)continue;rockRows.push({p:[x,.3,4.23],s:[.6,.62+hash(i+7)*.38,.63],r:[.08,hash(i+5)*Math.PI,.03],color:i%3?'#556857':'#718575'});}
 for(const[x,z,r]of LANE.obstacles.slice(2))rockRows.push({p:[x,.5,z],s:[r*1.1,.8,r*1.15],r:[0,hash(x+z)*3,0],color:'#627769'});
 batch('rock',rockRows);
 // Tall lane brush, clustered grass blades: readable silhouettes and dark centres.
 const blades=[],smallGrass=[];for(const[x,z,w,h]of LANE.brush){for(let i=0;i<(software?12:quality==='low'?42:85);i++){const px=x+(hash(i+x*17)-.5)*w,pz=z+(hash(i+z*11)-.5)*h,height=.45+hash(i+13)*.35;blades.push({p:[px,height*.46,pz],s:[.09,height,.07],r:[(hash(i)-.5)*.15,hash(i+3)*6,.15],color:i%4?'#668a3d':'#92a453'});}}
 batch('cone',blades);
 for(let i=0;i<(software?30:120);i++){const x=(hash(i+802)*2-1)*11.5,z=(i%2?1:-1)*(2.08+hash(i+408)*.45);smallGrass.push({p:[x,.12,z],s:[.07,.24,.065],color:'#638849'});}batch('cone',smallGrass);
 // Jungle canopy stays beyond the playable walls so actors remain visible.
 const treeLeaves=[],trunks=[];for(let i=0;i<(software?10:quality==='low'?15:25);i++){const x=-12.8+hash(i+110)*25.6,z=i%2?-5.6-hash(i+140)*2.9:5.3+hash(i+150)*3.2;if(x>-4.6&&x<1.8&&z>0)continue;const h=1.65+hash(i+900)*1.0;
  trunks.push({p:[x,h*.35,z],s:[.14,h*.7,.14],color:'#5e6244'});for(let k=0;k<3;k++)treeLeaves.push({p:[x+(hash(i+k)-.5)*.45,h*(.65+k*.2),z],s:[.86-k*.12,.63,.83-k*.1],color:['#244b37','#346746','#53804b'][k]});}
 batch('cylinder',trunks);batch('leaf',treeLeaves);
 // Two outer tower platforms: decorative only, with physical footprints.
 for(const[x,z]of LANE.obstacles.slice(0,2)){const color=x<0?'#69c9dd':'#e79081';mesh('cylinder','#758276',x,-.035,z,1.3,.10,1.3);mesh('cylinder','#53665f',x,.18,z,.76,.35,.76);mesh('cylinder','#8a9687',x,.55,z,.53,.72,.53);mesh('cylinder','#b0b5a0',x,1.15,z,.35,.65,.35);
  for(let k=0;k<4;k++){const a=k*Math.PI/2;mesh('box','#7c9084',x+Math.cos(a)*.34,1.56,z+Math.sin(a)*.34,.16,.46,.16);}
  const c=mesh('rock',color,x,1.83,z,.22,.43,.22,.4);c.material.emissive=new T.Color(color);c.material.emissiveIntensity=.65;crystals.push(c);
  const ring=mesh('ring','#b4a775',x,.032,z,1.2,1.2,1.2,.4);ring.rotation.x=-Math.PI/2;}
 // A dragon emblem in the pit floor, no live dragon or artificial damage source.
 const emblem=mesh('ring','#699484',-5,-.041,7,1.14,1.14,1.14);emblem.rotation.x=-Math.PI/2;for(let i=0;i<3;i++){const m=flat('#8aa791',-5+(i-1)*.32,7,.16,.6,-.038);m.rotation.z=(i-1)*.35;}
 function animate(t){for(const w of water)w.m.position.x=w.x+Math.sin(t*.2+w.x)*.065;for(const c of crystals)c.material.emissiveIntensity=.6+Math.sin(t*1.5)*.08;}
 function dispose(){scene.remove(root);geos.forEach(g=>g.dispose());mats.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());}
 return{root,animate,dispose,metrics:()=>({arenaMeshes:root.children.filter(o=>o.isMesh).length,arenaInstances:software?0:tileRows.length+rockRows.length+blades.length+smallGrass.length+treeLeaves.length+trunks.length,terrain:'dragon-lane'})};
}

function createArena(T,scene,options={}){return options.terrain==='dragon-lane'?createDragonArena(T,scene,options):createLegacyArena(T,scene,options);}
const API={createArena,navigation};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanArena=API;
})(typeof globalThis!=='undefined'?globalThis:this);
