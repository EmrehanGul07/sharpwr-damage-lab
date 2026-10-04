"""Original Blender skinned roster. No extracted Riot assets. Run in Blender 4.5 LTS.
Distinct silhouettes, material batches, weapon-aware clips and secondary bone motion.
"""
import bpy, math, json, hashlib, zipfile, shutil, sys
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/marksman-3d/production';OUT.mkdir(parents=True,exist_ok=True)
CAT=json.loads((ROOT/'data/marksman-art-direction.json').read_text())['champions']
SIGN=hashlib.sha256(Path(__file__).read_bytes()+(ROOT/'data/marksman-art-direction.json').read_bytes()).hexdigest()
SELECT=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(CAT)
FEMALE={'Ashe','Caitlyn','Jinx',"Kai'Sa",'Kalista','Miss Fortune','Samira','Senna','Sivir','Vayne','Xayah','Yunara','Zeri'}
HAIR={'Ashe':'#e0e4e1','Caitlyn':'#28202f','Draven':'#23171a','Jinx':'#32b7d5',"Kai'Sa":'#25162f','Kalista':'#113e46','Lucian':'#19191d','Miss Fortune':'#a43d27','Samira':'#231d24','Senna':'#252a29','Sivir':'#352129','Twitch':'#776d56','Varus':'#d4d4da','Vayne':'#261c32','Xayah':'#a24672','Yunara':'#2a3336','Zeri':'#87c839','Tristana':'#d3e0ea'}
def rgb(h):
 def linear(v):return v/12.92 if v<=.04045 else((v+.055)/1.055)**2.4
 return tuple(linear(int(h[i:i+2],16)/255)for i in(1,3,5))
def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
def clean():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for col in [bpy.data.meshes,bpy.data.curves,bpy.data.armatures,bpy.data.materials,bpy.data.actions]:
  for d in list(col):
   if d.users==0:col.remove(d)
def build(name,p):
 clean();parts=[];M={}
 palette={**p['palette'],'hair':HAIR.get(name,p['palette']['light']),'white':'#dbe7e5','dark':'#151c24','iris':p['palette']['energy'],'leather':'#332e35'}
 if name=='Corki':palette.update(cloth='#66804c',secondary='#a96a39',light='#e9dfb1',metal='#ac8861')
 for key,h in palette.items():
  m=bpy.data.materials.new(name+' / '+key);m.diffuse_color=(*rgb(h),1);m.use_nodes=True;node=m.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=m.diffuse_color;node.inputs['Roughness'].default_value=.3 if key=='metal' else .62;node.inputs['Metallic'].default_value=.72 if key=='metal' else 0
  if key in ['energy','iris']:node.inputs['Emission Color'].default_value=m.diffuse_color;node.inputs['Emission Strength'].default_value=.8 if key=='energy' else .1
  M[key]=m
 def ell(label,loc,scale,mat='cloth',bone='chest',seg=16,rings=10):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc);o=bpy.context.object;o.name=label;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(M[mat]);o.select_set(False)
  for f in o.data.polygons:f.use_smooth=True
  parts.append((o,bone));return o
 def bar(label,a,b,r,mat='metal',bone='R_hand'):
  a,b=Vector(a),Vector(b);o=ell(label,(a+b)*.5,(r,r,(b-a).length*.5+r*.3),mat,bone);o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(b-a);return o
 def box(label,loc,scale,mat='metal',bone='R_hand',bevel=.025):
  bpy.ops.mesh.primitive_cube_add(size=2,location=loc);o=bpy.context.object;o.name=label;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(M[mat]);mod=o.modifiers.new('Crafted edges','BEVEL');mod.width=bevel;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False);parts.append((o,bone));return o
 def curve(label,points,r,mat='light',bone='chest',taper=False):
  c=bpy.data.curves.new(label,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=1;s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
  for i,(v,co)in enumerate(zip(s.bezier_points,points)):v.co=co;v.handle_left_type='AUTO';v.handle_right_type='AUTO';v.radius=(1-i/max(1,len(points)-1))*.9+.08 if taper else 1
  o=bpy.data.objects.new(label,c);bpy.context.collection.objects.link(o);o.data.materials.append(M[mat]);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.select_set(False);parts.append((o,bone));return o
 def patch(label,verts,faces,mat='cloth',bone='cape'):
  mesh=bpy.data.meshes.new(label);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(label,mesh);bpy.context.collection.objects.link(o);o.data.materials.append(M[mat]);sol=o.modifiers.new('Fabric thickness','SOLIDIFY');sol.thickness=.018;bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=sol.name);bev=o.modifiers.new('Hem bevel','BEVEL');bev.width=.012;bev.segments=2;bpy.ops.object.modifier_apply(modifier=bev.name);o.select_set(False);parts.append((o,bone));return o
 defs={'hips':((0,0,1.12),(0,0,1.32),None),'spine':((0,0,1.32),(0,0,1.59),'hips'),'chest':((0,0,1.59),(0,0,1.80),'spine'),'neck':((0,0,1.80),(0,0,1.95),'chest'),'head':((0,0,1.95),(0,0,2.23),'neck'),'cape':((0,.08,1.73),(0,.16,1.1),'chest'),'hair':((0,.06,2.15),(0,.14,1.70),'head')}
 for s,side in[(-1,'L'),(1,'R')]:
  defs[side+'_arm']=((s*.32,0,1.73),(s*.37,0,1.40),'chest');defs[side+'_forearm']=((s*.37,0,1.40),(s*.40,0,1.12),side+'_arm');defs[side+'_hand']=((s*.40,0,1.12),(s*.40,-.018,1.02),side+'_forearm');defs[side+'_thigh']=((s*.12,0,1.13),(s*.145,-.01,.66),'hips');defs[side+'_shin']=((s*.145,-.01,.66),(s*.145,0,.20),side+'_thigh');defs[side+'_foot']=((s*.145,0,.20),(s*.145,-.15,.10),side+'_shin')
 muzzle=(.4,-.14,1.2);muzzle_bone='R_hand';human=p['rig'] in ['human','yordle']
 if human:
  female=name in FEMALE;wide=.27 if p['body']=='broad' else .20 if female else .235
  body=[ell('Upper torso',(0,0,1.55),(wide,.13,.30),'cloth',None),ell('Waist',(0,.004,1.29),(.155 if female else wide*.8,.115,.23),'cloth',None),ell('Pelvis',(0,0,1.12),(.22 if female else .205,.13,.18),'secondary',None),ell('Neck',(0,0,1.87),(.065,.065,.11),'skin',None)]
  for s,side in [(-1,'L'),(1,'R')]:
   body +=[bar('Shoulder',(s*.16,0,1.73),(s*.32,0,1.73),.09 if female else .12,'cloth',None),bar('Upper arm',(s*.32,0,1.73),(s*.37,0,1.40),.066 if female else .083,'cloth',None),bar('Forearm',(s*.37,0,1.4),(s*.40,0,1.12),.053 if female else .065,'skin',None),bar('Thigh',(s*.12,0,1.13),(s*.145,-.01,.66),.085 if female else .101,'secondary',None),bar('Calf',(s*.145,-.01,.66),(s*.145,0,.20),.067,'secondary',None)]
   ell('Palm',(s*.4,-.01,1.08),(.052,.038,.07),'skin',side+'_hand')
   for f in range(4):bar('Finger',(s*.40+(f-1.5)*.015,-.011,1.04),(s*.40+(f-1.5)*.015,-.027,1.005),.009,'skin',side+'_hand')
   ell('Fitted boot',(s*.145,.008,.28),(.082,.075,.19),'leather',side+'_shin');ell('Boot toe',(s*.145,-.075,.105),(.09,.15,.072),'leather',side+'_foot');box('Boot clasp',(s*.145,-.074,.31),(.025,.012,.025),'metal',side+'_shin',.005)
  parts[:]=[(o,b)for o,b in parts if o not in body];bpy.ops.object.select_all(action='DESELECT')
  for o in body:o.select_set(True)
  bpy.context.view_layer.objects.active=body[0];bpy.ops.object.join();skin=bpy.context.object;skin.name='Continuous tailored skin'
  mod=skin.modifiers.new('Continuous joints','REMESH');mod.mode='VOXEL';mod.voxel_size=.027;mod.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=mod.name);mod=skin.modifiers.new('Relaxed surface','SMOOTH');mod.factor=.55;mod.iterations=3;bpy.ops.object.modifier_apply(modifier=mod.name);skin.data.materials.clear()
  for k in ['cloth','secondary','skin','light','leather']:skin.data.materials.append(M[k])
  for f in skin.data.polygons:
   c=skin.matrix_world@f.center;index=2 if c.z>1.81 or(abs(c.x)>.285 and c.z<1.43) else 1 if c.z<1.20 else 0
   if name in ['Jinx','Sivir','Varus','Draven','Samira','Miss Fortune']and abs(c.x)>.275:index=2
   if name in ['Jinx','Sivir']and abs(c.x)<.28 and 1.18<c.z<1.43:index=2
   if name=='Jinx'and c.z<1.10:index=2 if c.z>.66 else 4
   if name=='Varus'and abs(c.x)<.28 and c.z>1.40:index=2
   if name=='Yunara'and abs(c.x)<.28:index=3 if c.z>1.17 else 0
   if name in ['Ashe','Caitlyn']and c.z<1.05:index=2 if c.z>.70 else 4
   f.material_index=index;f.use_smooth=True
  parts.append((skin,None));skin.select_set(False)
  face=ell('Shaped face',(0,-.012,2.075),(.133 if female else .147,.116,.20),'skin','head',24,16)
  for v in face.data.vertices:v.co.x*=.73+.27*min(1,max(0,(v.co.z/.20+.8)/.75))
  ell('Nose',(0,-.132,2.063),(.021,.032,.034),'skin','head');curve('Mouth',[(-.027,-.121,2.007),(0,-.124,2.003),(.027,-.121,2.007)],.0035,'secondary','head')
  for s in[-1,1]:
   ell('Ear',(s*.139,.003,2.062),(.025,.018,.044),'skin','head');ell('Eye',(s*.05,-.118,2.101),(.029,.014,.014),'white','head');ell('Iris',(s*.05,-.131,2.101),(.012,.005,.011),'iris','head');ell('Pupil',(s*.05,-.136,2.101),(.005,.002,.007),'dark','head');curve('Brow',[(s*.021,-.118,2.136),(s*.052,-.124,2.142),(s*.082,-.11,2.131)],.0055,'hair','head')
  if p['hair']!='none':
   ell('Sculpted hair cap',(0,.018,2.208),(.146,.121,.105),'hair','head')
   for i in range(8):
    x=(i-3.5)*.032;curve('Parted fringe',[(x,.08,2.22),(x-.018,-.02,2.29),(x-.03,-.106,2.235),(x-.028,-.13,2.16+abs(i-3.5)*.009)],.018,'hair','head',True)
   if p['hair'] in ['long','locks','braids']:
    for i in range(7):
     x=(i-3)*.04;z=1.38 if p['hair']=='braids' else 1.66;curve('Flowing hair',[(x,.10,2.19),(x,.135,2.0),(x+.03,.16,1.79),(x+.05,.14,z)],.035 if p['hair']!='braids' else .025,'hair','hair',True)
   if p['hair']=='tied':ell('Ponytail knot',(0,.13,2.16),(.075,.08,.07),'hair','head');curve('Ponytail',[(0,.13,2.19),(.06,.24,2.15),(.07,.24,1.88)],.053,'hair','hair',True)
   if p['hair']=='crest':curve('Raised crest',[(0,.075,2.18),(0,0,2.39),(.02,-.10,2.35)],.053,'hair','head',True)
  # Tailored panels and weighted secondary cloth differ by champion's design.
  coat=name in ['Ashe','Caitlyn','Jhin','Lucian','Miss Fortune','Senna','Vayne','Xayah','Yunara','Kalista']
  for s in[-1,1]:
   if name not in ['Jinx','Varus',"Kai'Sa",'Sivir']:patch('Shoulder panel',[(s*.12,-.13,1.77),(s*.27,-.07,1.76),(s*.24,-.13,1.51),(s*.16,-.15,1.56)],[(0,1,2,3)],'secondary','chest')
   curve('Tailored piping',[(s*.19,-.115,1.74),(s*.20,-.12,1.5),(s*.17,-.10,1.26)],.007,'metal','spine')
   ell('Armored cuff',(s*.38,0,1.25),(.067,.066,.08),'metal',('L' if s<0 else 'R')+'_forearm')
   if coat:patch('Split coat tail',[(s*.055,.08,1.30),(s*.22,.07,1.30),(s*.29,.16,.80),(s*.08,.21,.76)],[(0,1,2,3)],'cloth','cape')
  curve('Waist belt',[(-.22,-.07,1.22),(-.11,-.14,1.22),(0,-.15,1.22),(.11,-.14,1.22),(.22,-.07,1.22)],.017,'leather','hips');box('Belt emblem',(0,-.167,1.22),(.034,.013,.03),'metal','hips',.008)
  if name in ['Ashe','Vayne','Xayah','Senna','Yunara']:
   patch('Weighted cape',[(-.23,.05,1.76),(.23,.05,1.76),(.36,.23,.70),(0,.28,.56),(-.36,.23,.70)],[(0,1,2,3,4)],'secondary','cape')
  if name in ['Ashe','Caitlyn','Yunara']:
   for side in[-1,1]:patch('Tailored skirt',[(side*.01,-.135,1.22),(side*.22,-.09,1.22),(side*.31,-.105,.82),(side*.01,-.19,.76)],[(0,1,2,3)],'cloth','hips')
  if name in ['Samira','Miss Fortune']:
   curve('Red scarf',[(-.09,-.08,1.85),(0,-.09,1.86),(.09,-.08,1.85)],.029,'secondary','neck');patch('Scarf streamer',[(.08,.06,1.83),(.17,.16,1.77),(.29,.25,1.42),(.13,.13,1.64)],[(0,1,2,3)],'secondary','cape')
  if name=='Zeri':
   box('Zaun power pack',(0,.18,1.52),(.13,.085,.18),'secondary','chest');curve('Electric cable',[(.13,.16,1.65),(.25,.03,1.55),(.38,.0,1.24)],.01,'energy','chest')
  if name=='Jinx':
   for s in[-1,1]:curve('Long blue braid',[(s*.10,.1,2.20),(s*.16,.18,1.8),(s*.22,.15,1.3),(s*.28,.12,.57)],.027,'hair','hair',True)
   for i in range(3):curve('Cloud tattoo',[(.38,-.058,1.37+i*.07),(.41,-.064,1.40+i*.07),(.39,-.061,1.44+i*.07)],.007,'light','R_forearm')
  if name=='Kalista':
   for x in[-.18,.05,.17]:bar('Embedded spectral spear',(x,.075,1.43),(x+.12,.08,1.87),.014,'energy','chest')
  if name=="Kai'Sa":
   for s,side in[(-1,'L'),(1,'R')]:
    defs[side+'_pod']=((s*.2,.03,1.75),(s*.35,-.03,2.15),'chest');ell('Void carapace',(s*.29,.06,1.91),(.16,.15,.31),'secondary',side+'_pod');ell('Void aperture',(s*.34,-.055,2.08),(.06,.025,.075),'energy',side+'_pod');curve('Carapace ridge',[(s*.18,.03,1.75),(s*.39,.03,1.96),(s*.29,-.08,2.28)],.028,'metal',side+'_pod',True)
  if name=='Draven':
   for s in[-1,1]:ell('Broad shoulder armor',(s*.30,0,1.76),(.16,.14,.10),'metal','chest');curve('Moustache',[(0,-.14,2.037),(s*.075,-.13,2.027),(s*.09,-.117,2.06)],.01,'hair','head',True)
  if name=='Jhin':ell('Ivory theatrical mask',(0,-.083,2.078),(.137,.064,.175),'light','head');curve('Mask gold flourish',[(.08,-.14,2.20),(.095,-.15,2.10),(.035,-.152,1.99)],.012,'metal','head');ell('Mask eye',(-.052,-.155,2.11),(.022,.009,.012),'dark','head')
  if name=='Samira':box('Eyepatch',(-.05,-.137,2.1),(.035,.015,.023),'dark','head',.009);curve('Patch strap',[(-.12,-.06,2.12),(0,-.125,2.14),(.14,.03,2.1)],.006,'dark','head')
  gear=p['headgear']
  if gear in ['hat','pirate']:
   brim=ell('Hat brim',(0,0,2.27),(.25,.19,.027),'cloth','head');ell('Hat crown',(0,.02,2.38),(.15,.12,.13 if gear=='hat' else .07),'secondary','head');curve('Hat band',[(-.12,-.085,2.34),(0,-.12,2.34),(.12,-.085,2.34)],.012,'metal','head')
  if gear=='hood':
   ell('Hood back',(0,.085,2.12),(.18,.125,.25),'cloth','head');curve('Hood opening',[(-.15,-.025,2.0),(-.16,-.07,2.18),(0,-.08,2.35),(.16,-.07,2.18),(.15,-.025,2.0)],.026,'metal','head')
  if gear in ['crown','tiara','horns']:
   curve('Circlet',[(-.13,-.03,2.23),(0,-.14,2.24),(.13,-.03,2.23)],.012,'metal','head')
   for s in[-1,1]:bar('Crown point',(s*.10,-.06,2.23),(s*.15,-.02,2.41),.022,'metal','head')
   ell('Circlet jewel',(0,-.148,2.245),(.019,.012,.023),'energy','head')
  if gear in ['goggles','visor']:
   for s in[-1,1]:ell('Eye armor',(s*.052,-.139,2.106),(.038,.018,.027),'metal','head');ell('Lens',(s*.052,-.154,2.106),(.028,.007,.017),'energy','head')
  if gear in ['ears','rat']:
   for s in[-1,1]:patch('Pointed ear',[(s*.12,-.01,2.09),(s*.36,.01,2.24),(s*.28,.04,2.08)],[(0,1,2)],'skin','head')
  if name=='Twitch':
   ell('Rat muzzle',(0,-.155,2.055),(.083,.11,.071),'skin','head');ell('Nose tip',(0,-.26,2.062),(.03,.021,.023),'dark','head');defs['tail']=((0,.075,1.13),(0,.5,.65),'hips');curve('Rat tail',[(0,.09,1.13),(0,.3,.75),(.12,.55,.35),(.36,.72,.16)],.025,'skin','tail',True)
  # Weapon structures are authored in the resting hand coordinates and deform with it.
  weapon_start=len(parts);w=p['weapon']
  def gun(side,length=.72,heavy=False):
   x=side*.4;bone=('L' if side<0 else 'R')+'_hand';r=.085 if heavy else .045
   box('Weapon receiver',(x,-.10,1.18),(.09 if heavy else .045,.18,.065 if heavy else .045),'secondary',bone);bar('Forged barrel',(x,-.10,1.20),(x,-.10-length,1.20),r,'metal',bone);ell('Muzzle socket',(x,-.10-length,1.20),(r*1.15,.016,r*1.15),'dark',bone);box('Grip',(x,-.02,1.075),(.026,.035,.08),'leather',bone)
   for i in range(3):box('Barrel bands',(x,-.18-i*length*.23,1.20),(r*1.1,.015,r*1.1),'metal',bone,.008)
   return(x,-.12-length,1.20)
  if w in ['rifle','electric_rifle','relic_cannon','launcher','cannon','crossbow']:
   muzzle=gun(1,1.18 if w=='relic_cannon' else .85 if w in['rifle','launcher','cannon']else .56,w in['relic_cannon','launcher','cannon']);muzzle_bone='R_hand'
   if w=='rifle':bar('Rifle scope',(.4,-.19,1.30),(.4,-.44,1.30),.035,'metal','R_hand')
   if w=='launcher':ell('Rocket shark jaw',(.4,-.75,1.2),(.13,.2,.11),'light','R_hand');ell('Shark eye',(.51,-.7,1.26),(.015,.03,.025),'energy','R_hand')
   if w=='electric_rifle':curve('Electric conduit',[(.35,-.1,1.26),(.35,-.3,1.29),(.4,-.57,1.26)],.016,'energy','R_hand')
   if w=='relic_cannon':box('Relic upper housing',(.4,-.5,1.24),(.16,.32,.15),'cloth','R_hand');curve('Relic light',[(.24,-.25,1.3),(.24,-.6,1.32),(.4,-1.08,1.3)],.014,'energy','R_hand')
  if w in ['pistols','blade_pistol']:muzzle=gun(1,.32);muzzle_bone='R_hand';gun(-1,.32)
  if w in ['bow','crossbows','crossbow']:
   for side in([-1,1]if w=='crossbows'else[-1]if w=='bow'else[1]):
    x=side*.4;bone=('L'if side<0 else'R')+'_hand';curve('Curved bow limbs',[(x,-.03,.60),(x-.16,-.1,.90),(x-.18,-.13,1.16),(x-.16,-.1,1.46),(x,-.03,1.70)],.022,'metal',bone);curve('Bow string',[(x,-.03,.60),(x,.05,1.16),(x,-.03,1.70)],.003,'light',bone);bar('Bow grip',(x,0,1.0),(x,0,1.27),.026,'leather',bone)
   if w=='bow':muzzle=(-.4,-.17,1.16);muzzle_bone='L_hand'
  if w in ['axes','blade_pistol','spear','crossblade','feathers']:
   for side in[-1,1]if w=='axes'else[-1]:
    x=side*.4;bone=('L'if side<0 else'R')+'_hand';bar('Weapon haft',(x,0,.86),(x,0,1.62 if w!='spear'else 2.10),.025,'leather',bone)
    if w=='axes':patch('Crescent axe head',[(x-.04,0,1.52),(x-.27,0,1.37),(x-.34,0,1.63),(x-.22,0,1.82),(x+.05,0,1.66)],[(0,1,2,3,4)],'metal',bone)
    elif w=='spear':patch('Spectral spearhead',[(x-.07,0,2.08),(x,0,2.44),(x+.07,0,2.08)],[(0,1,2)],'energy',bone);muzzle=(x,-.02,2.40);muzzle_bone=bone
    elif w=='blade_pistol':patch('Curved sword',[(x-.04,0,1.30),(x-.04,0,2.12),(x+.10,0,2.34),(x+.045,0,1.30)],[(0,1,2,3)],'metal',bone)
    elif w=='crossblade':
     for i in range(4):
      a=i*math.pi/2;dx,dz=math.cos(a),math.sin(a);patch('Crossblade edge',[(x+dx*.09,0,1.15+dz*.09),(x+dx*.48,0,1.15+dz*.48),(x+dx*.24-dz*.10,0,1.15+dz*.24+dx*.10)],[(0,1,2)],'metal',bone)
     ell('Crossblade core',(x,-.015,1.15),(.09,.03,.09),'energy',bone)
    else:
     for i in range(5):curve('Violet feather',[(x,0,1.12),(x+(i-2)*.04,-.1,1.35),(x+(i-2)*.09,-.13,1.61)],.016,'energy',bone,True)
   if w=='axes':muzzle=(.4,-.10,1.52)
  if w=='spirit_orbs':
   for i in range(5):a=i*math.pi*2/5;ell('Spirit bead',(math.cos(a)*.55,-.06,1.42+math.sin(a)*.31),(.075,.075,.075),'energy','chest');curve('Prayer sash',[(-.11,-.12,1.74),(0,-.18,1.55),(.13,-.10,1.28)],.016,'light','spine')
  if p['rig']=='yordle':
   center=Vector((0,0,2.075))
   for obj,bone in parts:
    if bone=='head':
     obj.location=center+(obj.location-center)*1.35;obj.scale*=1.35
  if w in ['rifle','electric_rifle','relic_cannon','launcher','cannon','crossbow','crossbows','pistols','blade_pistol']:
   bpy.context.view_layer.update()
   for obj,bone in parts[weapon_start:]:
    if 'barrel' in obj.name.lower() or w!='blade_pistol' or bone=='R_hand':
     center=Vector((-.4 if bone=='L_hand' else .4,0,1.12));obj.matrix_world=Matrix.Translation(center)@Matrix.Rotation(math.pi/2,4,'X')@Matrix.Translation(-center)@obj.matrix_world
  scale=.72 if p['rig']=='yordle'else 1.06 if p['body']=='tall'else 1.0
 elif p['rig']=='vehicle':
  defs={'hips':((0,0,.7),(0,0,.95),None),'chest':((0,0,.9),(0,0,1.1),'hips'),'head':((0,0,1.1),(0,0,1.4),'chest'),'L_wing':((-.2,0,.8),(-.95,0,.8),'hips'),'R_wing':((.2,0,.8),(.95,0,.8),'hips'),'propeller':((0,-.63,.76),(0,-.75,.76),'hips')}
  ell('Aircraft fuselage',(0,0,.72),(.29,.68,.26),'secondary','hips',24,14);box('Cockpit rim',(0,.04,.93),(.21,.25,.07),'metal','hips');ell('Pilot body',(0,.04,1.09),(.14,.13,.15),'cloth','chest');ell('Pilot head',(0,.01,1.34),(.14,.13,.13),'skin','head');ell('Aviator helmet',(0,.035,1.42),(.155,.135,.075),'leather','head')
  for s,side in[(-1,'L'),(1,'R')]:box('Airfoil',(s*.67,.04,.71),(.55,.20,.035),'cloth',side+'_wing');bar('Wing brace',(s*.23,0,.96),(s*.77,0,.76),.012,'metal',side+'_wing');ell('Pilot lens',(s*.05,-.122,1.35),(.047,.02,.036),'metal','head');bar('Forward gun',(s*.24,-.15,.79),(s*.24,-.68,.79),.033,'metal','hips')
  bar('Propeller',(-.02,-.69,.41),(.02,-.69,1.07),.034,'light','propeller');ell('Engine spinner',(0,-.73,.73),(.065,.07,.065),'metal','hips');box('Tailplane',(0,.56,.86),(.31,.10,.027),'cloth','hips');muzzle=(0,-.80,.8);muzzle_bone='hips';scale=1.15
 else:
  dragon=p['rig']=='dragon';defs={'hips':((0,.18,.55),(0,.08,.8),None),'chest':((0,.08,.70),(0,-.19,.80),'hips'),'head':((0,-.18,.85),(0,-.43,1.15),'chest'),'tail':((0,.30,.64),(0,.75,.48),'hips')}
  ell('Organic torso',(0,.08,.60),(.30,.47,.29),'skin','hips',24,16);ell('Belly plate',(0,-.04,.45),(.26,.37,.19),'light','hips');ell('Neck',(0,-.26,.84),(.16,.18,.24),'skin','chest');ell('Expressive head',(0,-.4,1.06),(.27,.24,.23),'skin','head',24,16);ell('Muzzle',(0,-.6,.97),(.20,.18,.12),'secondary','head');ell('Mouth opening',(0,-.747,.945),(.19,.036,.115 if not dragon else .07),'dark','head');
  if not dragon:
   for i in range(9):
    x=(i-4)*.035;bar('Jagged tooth',(x,-.767,1.025),(x,-.771,.967),.011,'light','head')
   for i in range(5):curve('Dorsal spine',[(0,.40-i*.15,.75),(0,.45-i*.15,.96),(0,.52-i*.15,1.02)],.025,'metal','hips',True)
  curve('Articulated tail',[(0,.31,.64),(0,.57,.47),(.12,.89,.35),(.28,1.12,.39)],.075,'skin','tail',True)
  for s,side in[(-1,'L'),(1,'R')]:
   for j in[0,1]:
    bone=side+('_front'if j==0 else'_back');z=.51;yy=-.18 if j==0 else .34;defs[bone]=((s*.21,yy,z),(s*.29,yy,.13),'hips');bar('Creature leg',(s*.23,yy,.54),(s*.30,yy,.14),.075,'skin',bone);ell('Clawed foot',(s*.31,yy-.04,.12),(.12,.16,.075),'secondary',bone)
    for k in range(3):bar('Ivory claw',(s*.31+(k-1)*.04,yy-.11,.12),(s*.31+(k-1)*.04,yy-.22,.095),.012,'light',bone)
   ell('Large eye',(s*.16,-.56,1.16),(.085,.041,.075),'white','head');ell('Eye iris',(s*.16,-.597,1.16),(.037,.009,.042),'energy','head');ell('Eye pupil',(s*.16,-.608,1.16),(.012,.004,.029),'dark','head');curve('Curving horn',[(s*.21,-.25,1.13),(s*.27,-.19,1.36),(s*.20,-.22,1.46)],.035,'metal','head',True)
   if dragon:
    bone=side+'_wing';defs[bone]=((s*.18,.05,.83),(s*.75,.08,1.20),'chest');patch('Wing membrane',[(s*.20,.05,.82),(s*.48,.04,1.26),(s*1.02,.03,1.18),(s*.76,.22,.91),(s*.56,.19,.98)],[(0,1,2,3,4)],'secondary',bone)
    for end in[(s*.48,.04,1.26),(s*1.02,.03,1.18),(s*.76,.22,.91)]:bar('Wing finger',(s*.20,.05,.82),end,.016,'metal',bone)
   else:
    for i in range(4):ell('Carapace segment',(s*.24,.25-i*.16,.7),(.09,.12,.17),'cloth','hips');ell('Acid sac',(s*.20,-.43,.79),(.065,.07,.07),'energy','chest')
  muzzle=(0,-.80,.98);muzzle_bone='head';scale=1.2
 # Armature and distance-based blended weights for continuous shoulders and knees.
 arm=bpy.data.armatures.new(name+' skeleton');rig=bpy.data.objects.new(name+' skinned rig',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 for n,(a,b,parent)in defs.items():e=arm.edit_bones.new(n);e.head=a;e.tail=b
 for n,(a,b,parent)in defs.items():
  if parent:arm.edit_bones[n].parent=arm.edit_bones[parent]
 bpy.ops.object.mode_set(mode='OBJECT')
 def dist(v,a,b):a,b=Vector(a),Vector(b);d=b-a;t=max(0,min(1,(v-a).dot(d)/d.length_squared));return(v-a-d*t).length
 for o,bone in parts:
  groups={n:o.vertex_groups.new(name=n)for n in([bone]if bone else defs.keys())}
  for v in o.data.vertices:
   if bone:groups[bone].add([v.index],1,'REPLACE')
   else:
    co=o.matrix_world@v.co;side='L'if co.x<0 else'R';candidates=[side+'_arm',side+'_forearm',side+'_hand']if abs(co.x)>.27 else[side+'_thigh',side+'_shin',side+'_foot','hips']if co.z<1.19 else['neck','head','chest']if co.z>1.80 else['hips','spine','chest'];near=sorted((dist(co,defs[n][0],defs[n][1]),n)for n in candidates)[:2];weights=[1/(d+.04)**5 for d,n in near];total=sum(weights)
    for(_,n),w in zip(near,weights):groups[n].add([v.index],w/total,'REPLACE')
  o.parent=rig;mod=o.modifiers.new('Skin deformation','ARMATURE');mod.object=rig
 bpy.ops.object.select_all(action='DESELECT')
 for o,b in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0][0];bpy.ops.object.join();skin=bpy.context.object;skin.name=name+' continuous skinned model';rig.scale=(scale,)*3
 socket=bpy.data.objects.new('socket_muzzle',None);bpy.context.collection.objects.link(socket);socket.parent=rig;socket.parent_type='BONE';socket.parent_bone=muzzle_bone;socket.matrix_world.translation=Vector(muzzle)*scale
 clips={'Idle':3,'Walk':1.2,'AA':p['attack']['study_duration'],'P':p['passive']['study_duration'],**{s:a['study_duration']for s,a in p['skills'].items()}}
 def perform(action,u,t):
  for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0)
  def rot(n,x=0,y=0,z=0):
   if n in rig.pose.bones:rig.pose.bones[n].rotation_euler=(x,y,z)
  w=smooth(u/.22)*(1-smooth((u-.70)/.30));pulse=math.sin(max(0,min(1,(u-.33)/.34))*math.pi)*.12;phase=t/1.2*math.pi*2
  rot('cape',math.sin(t*2.6)*.035+(math.sin(phase)*.045 if action=='Walk'else w*.08));rot('hair',math.sin(t*2.0)*.025+(math.sin(phase+.4)*.06 if action=='Walk'else w*.03));rot('tail',.05,math.sin(t*3)*.12,0)
  if not human:
   rot('propeller',0,0,t*30);rot('head',math.sin(t*2)*.025);rot('L_wing',math.sin(t*3)*.04);rot('R_wing',-math.sin(t*3)*.04)
   if action=='Walk':
    for side in['L','R']:
     for j in['front','back']:rot(side+'_'+j,math.sin(phase+(math.pi if(side=='L')==(j=='front')else 0))*.22)
    if p['rig']=='vehicle':rig.pose.bones['hips'].location.z=math.sin(t*4)*.035;rot('L_wing',math.sin(t*2)*.09);rot('R_wing',math.sin(t*2)*.09)
   elif action not in ['Idle']:
    rot('head',-.12*w+pulse,0,math.sin(t*5)*w*.025);rot('chest',-.07*w);rot('hips',0,0,math.sin(t*12)*.025*w if action in['AA','Q','R']else 0)
    if action=='E'and p['rig']=='dragon':rot('L_wing',-.35*w,0,-.45*w);rot('R_wing',-.35*w,0,.45*w)
    if action=='R':rot('head',-.30*w);rot('L_wing',-.25*w,0,-.22*w);rot('R_wing',-.25*w,0,.22*w)
   return
  rot('L_arm',-.14,0,-.10);rot('R_arm',-.12,0,.10);
  carry=p['weapon']in['rifle','electric_rifle','relic_cannon','launcher','cannon','crossbow']
  if carry:rot('R_arm',-.60,0,.10);rot('R_forearm',-.22);rot('L_arm',-.70,0,.25);rot('L_forearm',-.55)
  rot('spine',math.sin(t*2)*.009);rot('head',0,math.sin(t)*.014)
  if action=='Walk':
   for s,side in[(-1,'L'),(1,'R')]:
    a=phase+(math.pi if s<0 else 0);forward=math.cos(a)*.18;lift=max(0,math.sin(a))*.07;l1=.47;l2=.46;reach=.905-lift;d=min(l1+l2-.001,math.hypot(reach,forward));knee=math.pi-math.acos(max(-1,min(1,(l1*l1+l2*l2-d*d)/(2*l1*l2))));hip=math.atan2(forward,reach)+math.acos(max(-1,min(1,(l1*l1+d*d-l2*l2)/(2*l1*d))));rot(side+'_thigh',-hip);rot(side+'_shin',knee);rot(side+'_foot',hip-knee);rot(side+'_arm',-math.sin(a)*.15,0,s*.10);rot(side+'_forearm',-.14)
   if carry:rot('R_arm',-.60+math.sin(phase)*.07,0,.10);rot('R_forearm',-.22);rot('L_arm',-.70+math.sin(phase)*.04,0,.25);rot('L_forearm',-.55)
   rig.pose.bones['hips'].location.y=-.025;rot('chest',.025,math.sin(phase)*.045)
   return
  if action=='Idle':return
  pose=p['attack']['pose']if action=='AA'else p['passive']['pose']if action=='P'else p['skills'][action]['pose'];rot('L_thigh',.09*w);rot('L_shin',-.16*w);rot('L_foot',.07*w);rot('R_thigh',.045*w);rot('R_shin',-.085*w);rot('R_foot',.04*w);rig.pose.bones['hips'].location.y=-.018*w;rot('chest',-.03*w,-.13*w)
  if action=='AA':w=smooth(u/.13)*(1-smooth((u-.43)/.57))
  if 'bow'in pose or(p['weapon']=='bow'and action=='AA'):
   draw=smooth(u/.32)*(1-smooth((u-.51)/.25));rot('L_arm',-1.45*w,0,-.18*w);rot('L_forearm',-.12*w);rot('L_hand',1.57*w);rot('R_arm',-.86*w,.65*w,.44*w);rot('R_forearm',-1.6*draw);rot('chest',0,-.32*w);rot('head',0,.18*w)
  elif any(k in pose for k in ['rifle','cannon','kneel','rocket','crossbow'])or p['weapon']in['rifle','electric_rifle','relic_cannon','launcher','cannon','crossbow','crossbows']and action=='AA':
   rot('R_arm',(-1.45+pulse)*w,0,.12*w);rot('R_forearm',-.17*w);rot('L_arm',-1.03*w,0,.26*w);rot('L_forearm',-.83*w);rot('chest',.04*w,-.09*w)
   if 'kneel'in pose:rot('R_thigh',.5*w);rot('R_shin',-1.0*w);rig.pose.bones['hips'].location.y=-.10*w
   if action=='R':rot('chest',(.04+math.sin(t*24)*.045)*w,-.08*w)
  elif 'spin'in pose:rot('hips',0,math.sin(u*math.pi*2)*1.5*w);rot('L_arm',-.9*w,0,-.8*w);rot('R_arm',-.9*w,0,.8*w);rot('chest',.08*w)
  elif any(k in pose for k in['roll','dash','blink','slide','jump','leap']):
   rot('spine',.27*w);rot('L_arm',-.63*w,0,-.32*w);rot('R_arm',-.55*w,0,.32*w);rot('L_thigh',.32*w);rot('L_shin',-.59*w);rot('R_thigh',-.15*w);rot('R_shin',.2*w)
   if 'roll'in pose:rot('hips',u*math.pi*2*w)
  elif 'pistol'in pose or'dual'in pose or p['weapon']=='pistols'and action=='AA':
   rot('R_arm',(-1.4+pulse)*w,0,.14*w);rot('R_forearm',-.12*w)
   if 'dual'in pose or name=='Miss Fortune'and action=='R':rot('L_arm',(-1.4+pulse)*w,0,-.14*w);rot('L_forearm',-.12*w)
  elif 'throw'in pose or'brandish'in pose:
   pull=smooth(u/.25)*(1-smooth((u-.35)/.25));rot('L_arm',(-.55-1.0*smooth((u-.25)/.22))*w,.3*pull,-.23*w);rot('L_forearm',-.70*pull);rot('R_arm',-.6*w,0,.22*w);rot('chest',.03*w,-.33*pull)
  elif pose in['buff','guard','rally','passive','fade','ascend']:
   rot('L_arm',-.65*w,0,-.36*w);rot('R_arm',-.64*w,0,.36*w);rot('L_forearm',-.8*w);rot('R_forearm',-.8*w);rot('head',-.10*w)
  else:
   rot('R_arm',-1.24*w,0,.15*w);rot('R_forearm',-.32*w);rot('L_arm',-.72*w,0,-.28*w);rot('L_forearm',-.60*w);rot('chest',-.07*w,-.22*w)
  if name=="Kai'Sa":rot('L_pod',-.12*w,0,-.12*w);rot('R_pod',-.12*w,0,.12*w)
 rig.animation_data_create();bpy.context.scene.render.fps=30
 for action,duration in clips.items():
  rig.animation_data.action=bpy.data.actions.new(action);count=round(duration*30)
  for i in range(count+1):
   u=i/count;perform(action,u,u*duration)
   for b in rig.pose.bones:b.keyframe_insert('rotation_euler',frame=i);b.keyframe_insert('location',frame=i)
  a=rig.animation_data.action;track=rig.animation_data.nla_tracks.new();track.name=action;track.strips.new(action,0,a);track.mute=True;rig.animation_data.action=None
 perform('Idle',0,0);directory=OUT/p['id'];directory.mkdir(exist_ok=True)
 def export(path,selected):
  bpy.ops.object.select_all(action='DESELECT')
  for o in selected:o.select_set(True)
  bpy.context.view_layer.objects.active=rig;bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_yup=True,export_materials='EXPORT')
 export(directory/'character.glb',[rig,skin,socket]);preview=skin.copy();preview.data=skin.data.copy();bpy.context.collection.objects.link(preview);preview.name=name+' CPU budget';bpy.context.view_layer.objects.active=preview;bpy.ops.object.select_all(action='DESELECT');preview.select_set(True);rig.data.pose_position='REST';dec=preview.modifiers.new('CPU budget','DECIMATE');dec.ratio=.16 if len(skin.data.polygons)>18000 else .28
 while preview.modifiers.find(dec.name)>0:bpy.ops.object.modifier_move_up(modifier=dec.name)
 bpy.ops.object.modifier_apply(modifier=dec.name);rig.data.pose_position='POSE';export(directory/'preview.glb',[rig,preview,socket]);triangles=sum(len(f.vertices)-2 for f in preview.data.polygons);bpy.data.objects.remove(preview,do_unlink=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(directory/'source.blend'))
 # Reproducible review render, outside the exported character.
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.resolution_x=420;scene.render.resolution_y=500;scene.render.resolution_percentage=100;scene.world.color=(.13,.13,.13)
 bpy.ops.mesh.primitive_plane_add(size=100);floor=bpy.context.object;floor.data.materials.append(M['dark'])
 for pos,power,color,size in [((-3,-4,5),420,(1,.88,.75),4),((3,-2,3),260,(.65,.80,1),3),((1,3,4),480,(.6,.9,1),2)]:
  bpy.ops.object.light_add(type='AREA',location=pos);lamp=bpy.context.object;lamp.data.energy=power;lamp.data.color=color;lamp.data.size=size;lamp.rotation_euler=(Vector((0,0,1.1))-lamp.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add(location=(3.2,-5.4,2.9));cam=bpy.context.object;focus=(0,0,1.22*scale)if human else(0,0,.70);cam.rotation_euler=(Vector(focus)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=3.2 if human else 2.7;scene.camera=cam
 review=ROOT/'docs/art-review/roster-v7';review.mkdir(parents=True,exist_ok=True);perform('Idle',0,0);bpy.context.view_layer.update();scene.render.filepath=str(review/(p['id']+'.png'));bpy.ops.render.render(write_still=True)

 record={'champion':name,'id':p['id'],'bones':len(defs),'animations':clips,'full_triangles':sum(len(f.vertices)-2 for f in skin.data.polygons),'preview_triangles':triangles,'materials':len(skin.data.materials),'silhouette':p['art_brief'],'weapon':p['weapon'],'source_sha256':SIGN,'status':'original authored stylized asset; not extracted Wild Rift game art'}
 (directory/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('ROSTER_READY',name,record,flush=True)
 return record
records={}
for name in SELECT:
 p=CAT[name]
 if name=='Ezreal':
  old=ROOT/'assets/marksman-3d/studies/ezreal-v2';target=OUT/p['id'];target.mkdir(exist_ok=True)
  for a,b in [('ezreal-v2.glb','character.glb'),('ezreal-v2-preview.glb','preview.glb'),('ezreal-v2.blend','source.blend')]:shutil.copy2(old/a,target/b)
  record={'champion':name,'id':p['id'],'bones':17,'animations':json.loads((old/'manifest.json').read_text())['animations'],'source_sha256':SIGN,'status':'existing Blender Ezreal v2 retained'};(target/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');records[name]=record
 else:records[name]=build(name,p)
# A full invocation creates the reusable source package and roster index.
if set(SELECT)==set(CAT):
 (OUT/'manifest.json').write_text(json.dumps({'schema':1,'source_sha256':SIGN,'champions':records},indent=2)+'\n')
 with zipfile.ZipFile(OUT/'sharpwr-skinned-roster.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6)as archive:
  archive.write(Path(__file__),'build_marksman_roster.py')
  for folder in OUT.iterdir():
   if folder.is_dir():
    for file in folder.iterdir():
     if file.suffix in['.glb','.blend','.json']:archive.write(file,folder.name+'/'+file.name)
 print('SKINNED_ROSTER_COMPLETE',len(records),flush=True)
