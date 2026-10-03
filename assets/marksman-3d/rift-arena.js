/* Original lane environment. Shared materials/geometries and bounded foliage budgets. */
(function(scope){'use strict';
function createArena(T,scene,{software=false,quality='high'}={}){
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
const API={createArena};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanArena=API;
})(typeof globalThis!=='undefined'?globalThis:this);
