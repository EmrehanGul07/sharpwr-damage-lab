"""Blender-authored original Ezreal study; run with Blender 4.5 --background --python.
No extracted Riot mesh/animation. A production study, not a final game asset.
"""
import bpy, math, json, hashlib, zipfile
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
# Editable source and intermediate GLBs are build outputs (not tracked); the roster build copies them to static/.
OUT=ROOT/'build/ezreal-v2'
RELEASE=ROOT/'build/release'
MANIFEST=ROOT/'assets/marksman-3d/studies/ezreal-v2/manifest.json'
for folder in (OUT,RELEASE,MANIFEST.parent):folder.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def material(name,color,metal=0,rough=.5,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 return m
M={
 'skin':material('Warm skin',(0.68,.39,.23),rough=.55),
 'jacket':material('Petrol blue leather',(.026,.15,.23),rough=.57),
 'pants':material('Warm leather trousers',(.17,.10,.067),rough=.65),
 'boots':material('Dark leather',(.025,.03,.045),rough=.5),
 'shirt':material('Ivory linen',(.64,.60,.49),rough=.85),
 'gold':material('Brushed brass',(.55,.32,.10),.75,.3),
 'hair':material('Golden blond hair',(.57,.35,.09),rough=.5),
 'hair_light':material('Blond highlights',(.81,.58,.21),rough=.45),
 'white':material('Eye white',(.76,.81,.81),rough=.35),
 'iris':material('Blue iris',(.04,.32,.49),rough=.25),
 'dark':material('Pupil and lashes',(.012,.016,.02),rough=.4),
 'gem':material('Arcane cyan',(.06,.68,.94),.25,.22,1.8),
 'lip':material('Lip warmth',(.39,.18,.13),rough=.58),
}
parts=[]
def ell(name,loc,scale,mat,bone=None,segments=24,rings=16):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(M[mat]);
 for p in o.data.polygons:p.use_smooth=True
 parts.append((o,bone));return o
def bar(name,a,b,r,mat,bone):
 a,b=Vector(a),Vector(b);o=ell(name,(a+b)/2,(r,r,(b-a).length/2+r*.4),mat,bone,16,10);o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(b-a);return o
def curve(name,points,r,mat,bone):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for i,(v,co) in enumerate(zip(s.bezier_points,points)):
  v.co=co;v.handle_left_type='AUTO';v.handle_right_type='AUTO';v.radius=[.65,1,.8,.035][i] if name=='Swept lock' else 1
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(M[mat]);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;parts.append((o,bone));o.select_set(False);return o
def patch(name,vertices,faces,mat,bone):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.data.materials.append(M[mat]);sub=o.modifiers.new('Tailored bevel','BEVEL');sub.width=.013;sub.segments=3;sol=o.modifiers.new('Leather thickness','SOLIDIFY');sol.thickness=.012
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 for p in o.data.polygons:p.use_smooth=True
 o.select_set(False);parts.append((o,bone));return o
# A continuous remeshed base, weighted below. Face/accessories have independent skin groups.
body=[]
body.append(ell('Torso core',(0,0,1.49),(.24,.13,.35),'jacket'))
body.append(ell('Pelvis',(0,.01,1.12),(.22,.12,.18),'pants'))
body.append(ell('Neck',(0,0,1.88),(.069,.071,.12),'skin'))
for s,side in [(-1,'L'),(1,'R')]:
 body.append(bar('Shoulder', (s*.16,0,1.74),(s*.34,0,1.74),.11,'jacket',None))
 body.append(bar('Upper arm',(s*.32,0,1.73),(s*.37,0,1.40),.077,'jacket',None))
 body.append(bar('Forearm',(s*.37,0,1.4),(s*.40,-.005,1.12),.062,'skin',None))
 body.append(ell('Palm',(s*.40,-.006,1.07),(.050,.035,.07),'skin',side+'_hand'))
 body.append(bar('Thigh',(s*.12,0,1.13),(s*.145,-.01,.66),.095,'pants',None))
 body.append(bar('Calf',(s*.145,-.01,.66),(s*.145,0,.20),.074,'pants',None))
 ell('Tall boot',(s*.145,0,.27),(.083,.083,.18),'boots',side+'_shin')
 ell('Boot toe',(s*.145,-.073,.10),(.092,.16,.075),'boots',side+'_foot')
 for z in [.22,.38]:curve('Boot strap',[(s*.145-.072,-.05,z),(s*.145,-.088,z),(s*.145+.072,-.05,z)],.009,'pants',side+'_shin')
# Fuse connected body sections for real skin deformation at shoulder/elbow/knee.
parts=[(o,b) for o,b in parts if o not in body]
bpy.ops.object.select_all(action='DESELECT')
for o in body:
 if o.name=='Palm':continue
 o.select_set(True)
bpy.context.view_layer.objects.active=body[0];bpy.ops.object.join();skin=bpy.context.object;skin.name='Continuous weighted body'
remesh=skin.modifiers.new('Connected silhouette','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.017;remesh.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=remesh.name)
sm=skin.modifiers.new('Surface relaxation','SMOOTH');sm.factor=.7;sm.iterations=5;bpy.ops.object.modifier_apply(modifier=sm.name)
skin.data.materials.clear()
for k in ['jacket','pants','skin','shirt']:skin.data.materials.append(M[k])
for p in skin.data.polygons:
 c=skin.matrix_world@p.center;p.material_index=2 if (c.z>1.86 and abs(c.x)<.12) or (abs(c.x)>.28 and c.z<1.47) else 1 if c.z<1.20 else 3 if c.y<-.10 and abs(c.x)<.105 and 1.38<c.z<1.80 else 0;p.use_smooth=True
parts.append((skin,None))
# Shaped jaw/cheek head with narrow chin, not a spherical toy face.
head=ell('Shaped face',(0,-.004,2.075),(.145,.117,.205),'skin','head',40,28)
for v in head.data.vertices:
 z=v.co.z/.205;v.co.x*=.77+.23*min(1,max(0,(z+.9)/.85));v.co.y-=.010*math.exp(-((z+.05)/.35)**2)
ell('Jaw plane',(0,-.045,1.975),(.095,.071,.065),'skin','head')
ell('Nose bridge',(0,-.119,2.074),(.021,.025,.047),'skin','head')
ell('Nose tip',(0,-.14,2.051),(.026,.025,.019),'skin','head')
for s in [-1,1]:
 ell('Ear',(s*.143,.006,2.065),(.027,.014,.05),'skin','head')
 ell('Eye',(s*.054,-.119,2.094),(.033,.014,.015),'white','head')
 ell('Iris',(s*.054,-.132,2.094),(.012,.004,.012),'iris','head')
 ell('Pupil',(s*.054,-.136,2.094),(.005,.002,.008),'dark','head')
 ell('Eye catchlight',(s*.052,-.138,2.099),(.0025,.001,.0025),'white','head',12,8)
 curve('Upper lid',[(s*.024,-.131,2.096),(s*.053,-.134,2.108),(s*.084,-.118,2.098)],.0035,'skin','head')
 curve('Blond eyebrow',[(s*.024,-.121,2.13),(s*.053,-.124,2.14),(s*.087,-.109,2.134)],.007,'hair','head')
curve('Upper lip',[(-.029,-.112,2.008),(0,-.123,2.012),(.029,-.112,2.008)],.004,'lip','head')
curve('Lower lip',[(-.026,-.111,2.005),(0,-.12,2.001),(.026,-.111,2.005)],.0038,'skin','head')
# Swept hair in tapered, individually shaped locks.
ell('Hair cap',(0,.026,2.205),(.151,.124,.10),'hair','head')
for i in range(11):
 x=(i-5)*.025
 curve('Swept lock',[(x,.08,2.21),(x-.025,-.012,2.285),(x-.045,-.09,2.25),(x-.04,-.137,2.16+abs(i-5)*.007)],.016 if i%2 else .020,'hair_light' if i%3==0 else 'hair','head')
# Goggles worn on forehead, eyes remain visible.
for s in [-1,1]:
 ell('Goggle brass frame',(s*.07,-.147,2.192),(.05,.020,.032),'gold','head')
 ell('Goggle dark lens',(s*.07,-.164,2.193),(.037,.009,.022),'boots','head')
 curve('Goggle edge',[(s*.105,-.106,2.208),(s*.14,-.06,2.213),(s*.147,.013,2.214)],.008,'pants','head')
bar('Goggle bridge',(-.025,-.163,2.193),(.025,-.163,2.193),.007,'gold','head')
# Open jacket, ivory shirt, seams, straps and utility pouches.
# Undershirt is a flush region of the continuous torso surface.
for s in [-1,1]:
 patch('Blue jacket lapel',[(s*.075,-.162,1.80),(s*.20,-.114,1.75),(s*.15,-.164,1.45),(s*.10,-.172,1.55)],[(0,1,2,3)],'jacket','chest')
 curve('Jacket seam',[(s*.19,-.115,1.74),(s*.20,-.119,1.52),(s*.17,-.112,1.24)],.004,'hair_light','spine')
 ell('Hip pouch',(s*.22,-.065,1.15),(.054,.052,.085),'pants','hips')
 patch('Coat hem',[(s*.07,-.12,1.29),(s*.22,-.07,1.29),(s*.25,-.07,1.05),(s*.09,-.12,1.04)],[(0,1,2,3)],'jacket','hips')
curve('Diagonal leather strap',[(-.19,-.143,1.77),(-.11,-.17,1.60),(.10,-.17,1.26)],.016,'pants','spine')
curve('Waist belt',[(-.22,-.065,1.23),(-.13,-.13,1.23),(0,-.14,1.23),(.13,-.13,1.23),(.22,-.065,1.23)],.018,'pants','hips')
ell('Brass buckle',(.03,-.159,1.23),(.033,.010,.027),'gold','hips')
curve('Neck scarf',[(-.06,-.069,1.88),(0,-.086,1.855),(.06,-.069,1.88)],.024,'shirt','neck')
patch('Scarf tail',[(-.075,.057,1.85),(-.16,.12,1.70),(-.12,.15,1.45),(-.035,.08,1.67)],[(0,1,2,3)],'shirt','chest')
# Fingers and the left-hand arcane gauntlet, each weighted to its hand.
for s,side in [(-1,'L'),(1,'R')]:
 for f in range(4):bar('Finger',(s*.40+(f-1.5)*.016,-.012,1.04),(s*.40+(f-1.5)*.016,-.030,1.00),.009,'skin',side+'_hand')
 bar('Thumb',(s*.40+s*.041,-.004,1.08),(s*.40+s*.052,-.025,1.04),.014,'skin',side+'_hand')
ell('Left brass gauntlet',(-.40,-.001,1.21),(.086,.074,.13),'gold','L_forearm')
ell('Gauntlet dorsal plate',(-.40,-.065,1.165),(.080,.034,.083),'gold','L_hand')
ell('Cyan focal crystal',(-.40,-.097,1.173),(.050,.023,.052),'gem','L_hand',20,12)
for x in [-.448,-.40,-.352]:curve('Gauntlet etched channel',[(x,-.065,1.29),(x,-.079,1.24),(x,-.085,1.195)],.004,'gem','L_forearm')
# Real armature and bone skin weights.
arm=bpy.data.armatures.new('Explorer skeleton');rig=bpy.data.objects.new('Ezreal_v2',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
defs={
 'hips':((0,0,1.12),(0,0,1.32),None),'spine':((0,0,1.32),(0,0,1.59),'hips'),
 'chest':((0,0,1.59),(0,0,1.80),'spine'),'neck':((0,0,1.80),(0,0,1.95),'chest'),
 'head':((0,0,1.95),(0,0,2.23),'neck')}
for s,side in [(-1,'L'),(1,'R')]:
 defs[side+'_arm']=((s*.32,0,1.73),(s*.37,0,1.40),'chest')
 defs[side+'_forearm']=((s*.37,0,1.40),(s*.40,0,1.12),side+'_arm')
 defs[side+'_hand']=((s*.40,0,1.12),(s*.40,-.018,1.02),side+'_forearm')
 defs[side+'_thigh']=((s*.12,0,1.13),(s*.145,-.01,.66),'hips')
 defs[side+'_shin']=((s*.145,-.01,.66),(s*.145,0,.20),side+'_thigh')
 defs[side+'_foot']=((s*.145,0,.20),(s*.145,-.15,.10),side+'_shin')
for n,(a,b,parent)in defs.items():e=arm.edit_bones.new(n);e.head=a;e.tail=b
for n,(a,b,parent)in defs.items():
 if parent:arm.edit_bones[n].parent=arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
def distance(v,a,b):a,b=Vector(a),Vector(b);ab=b-a;u=max(0,min(1,(v-a).dot(ab)/ab.length_squared));return (v-a-ab*u).length
for o,bone in parts:
 if o.name not in bpy.data.objects:continue
 groups={n:o.vertex_groups.new(name=n) for n in ([bone] if bone else defs.keys())}
 for v in o.data.vertices:
  if bone:groups[bone].add([v.index],1,'REPLACE')
  else:
   co=o.matrix_world@v.co;side='L' if co.x<0 else 'R'
   candidates=[side+'_arm',side+'_forearm',side+'_hand'] if abs(co.x)>.27 else [side+'_thigh',side+'_shin',side+'_foot','hips'] if co.z<1.19 else ['neck','head','chest'] if co.z>1.8 else ['hips','spine','chest']
   near=sorted((distance(co,defs[n][0],defs[n][1]),n)for n in candidates)[:2];w=[1/(d+.04)**5 for d,n in near];total=sum(w)
   for (_,n),weight in zip(near,w):groups[n].add([v.index],weight/total,'REPLACE')
 mod=o.modifiers.new('Skin deformation','ARMATURE');mod.object=rig;o.parent=rig
socket=bpy.data.objects.new('socket_muzzle',None);bpy.context.collection.objects.link(socket);socket.location=(-.40,-.119,1.173);socket.parent=rig;socket.parent_type='BONE';socket.parent_bone='L_hand';socket.matrix_world.translation=(-.40,-.119,1.173)
bpy.context.scene.render.fps=30
bpy.context.scene.frame_start=0
# Merge by shared armature; glTF splits only by material, reducing draw calls.
bpy.ops.object.select_all(action='DESELECT')
for o,b in parts:
 if o.name in bpy.data.objects:o.select_set(True)
bpy.context.view_layer.objects.active=skin;bpy.ops.object.join();skin=bpy.context.object;skin.name='Ezreal skinned character';parts=[(skin,None)]
clips={'Idle':3,'Walk':1.2,'AA':.9,'P':2,'Q':.95,'W':.95,'E':.95,'R':1.4}
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def performance(name,u,t):
 for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0)
 def rot(n,x=0,y=0,z=0):rig.pose.bones[n].rotation_euler=(x,y,z)
 breath=math.sin(t*math.pi*2/3)*.012
 rot('spine',breath,0,0);rot('head',0,math.sin(t*2)*.018,0);rot('L_arm',-.12,0,-.1);rot('R_arm',-.08,0,.1)
 if name=='Walk':
  phase=u*math.pi*2
  for s,side in [(-1,'L'),(1,'R')]:
   a=phase+(math.pi if s<0 else 0);forward=math.cos(a)*.18;lift=max(0,math.sin(a))*.075;l1=.4701;l2=.4601;reach=.90+abs(math.sin(phase))*.008-lift;d=min(l1+l2-.001,math.hypot(reach,forward));knee=math.pi-math.acos(max(-1,min(1,(l1*l1+l2*l2-d*d)/(2*l1*l2))));hip=math.atan2(forward,reach)+math.acos(max(-1,min(1,(l1*l1+d*d-l2*l2)/(2*l1*d))))
   rot(side+'_thigh',-hip);rot(side+'_shin',knee);rot(side+'_foot',hip-knee);rot(side+'_arm',-math.sin(a)*.17,0,s*.09);rot(side+'_forearm',-.16)
  rig.pose.bones['hips'].location.y=-.03+abs(math.sin(phase))*.008;rot('spine',.035,math.sin(phase)*.035,0)
 elif name not in ['Idle','Walk']:
  w=smooth(u/.22)*(1-smooth((u-.68)/.32));release=smooth((u-.30)/.16);recoil=math.sin(max(0,min(1,(u-.45)/.25))*math.pi)*.075
  rot('L_thigh',.10*w);rot('L_shin',-.18*w);rot('L_foot',.08*w);rot('R_thigh',.06*w);rot('R_shin',-.11*w);rot('R_foot',.05*w);rig.pose.bones['hips'].location.y=-.022*w
  if name=='AA':
   quick=smooth(u/.14)*(1-smooth((u-.43)/.57));rot('L_arm',-.70*quick,-.025*quick,-.11*quick);rot('L_forearm',-.75*quick);rot('R_arm',-.14*quick,0,.07*quick);rot('chest',0,-.065*quick,0);rig.pose.bones['hips'].location.y=-.01*quick
  elif name in ['Q','W']:
   rot('L_arm',(-1.15-.30*release+recoil)*w,-.07*w,-.16*w);rot('L_forearm',(-.45+.37*release)*w);rot('L_hand',-.10*w)
   rot('R_arm',-.35*w,0,.12*w);rot('R_forearm',-.25*w);rot('chest',-.035*w,-.18*w,0);rot('hips',0,.07*w,0);rot('head',0,.1*w,0)
   if name=='W':rot('L_hand',-.1*w,.32*w,0);rot('L_arm',-1.30*w,-.2*w,-.12*w)
  elif name=='R':
   charge=smooth(u/.35);extend=smooth((u-.42)/.18)
   rot('L_arm',(-.72-extend*.72)*w,-.28*w,-.15*w);rot('L_forearm',(-1.25+extend*1.14)*w);rot('R_arm',(-.72-extend*.48)*w,.33*w,.3*w);rot('R_forearm',(-1.35+extend*.76)*w)
   rot('chest',(-.08+recoil)*w,-.06*w,0);rot('head',-.05*w,.05*w,0)
  elif name=='E':rot('spine',.2*w);rot('L_arm',-.75*w,0,-.32*w);rot('R_arm',-.5*w,0,.28*w);rot('L_thigh',.28*w);rot('L_shin',-.5*w);rig.pose.bones['hips'].location.y=-.08*w
  elif name=='P':rot('L_arm',-.6*w,-.3*w,-.18*w);rot('L_forearm',-1.22*w);rot('head',.11*w,0,0)
 # Keep loop endpoints exact and deterministic.
 if name in ['Idle','Walk'] and u==1:performance(name,0,0)
rig.animation_data_create()
for name,duration in clips.items():
 rig.animation_data.action=bpy.data.actions.new(name);count=round(duration*30)
 for i in range(count+1):
  u=i/count;performance(name,u,u*duration)
  for b in rig.pose.bones:b.keyframe_insert('rotation_euler',frame=i);b.keyframe_insert('location',frame=i)
 action=rig.animation_data.action;track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,0,action);track.mute=True;rig.animation_data.action=None
performance('Idle',0,0)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
for o,b in parts:
 if o.name in bpy.data.objects:o.select_set(True)
socket.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(OUT/'ezreal-v2.glb'),export_format='GLB',use_selection=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_yup=True,export_materials='EXPORT')
# Geometry budget for browsers without WebGL; authored skin weights remain intact.
preview=skin.copy();preview.data=skin.data.copy();bpy.context.collection.objects.link(preview);preview.name='Ezreal CPU preview';bpy.ops.object.select_all(action='DESELECT');preview.select_set(True);bpy.context.view_layer.objects.active=preview
rig.data.pose_position='REST';dec=preview.modifiers.new('Preview geometry budget','DECIMATE');dec.ratio=.12
while preview.modifiers.find(dec.name)>0:bpy.ops.object.modifier_move_up(modifier=dec.name)
bpy.ops.object.modifier_apply(modifier=dec.name);rig.data.pose_position='POSE';rig.select_set(True);socket.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'ezreal-v2-preview.glb'),export_format='GLB',use_selection=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_yup=True,export_materials='EXPORT')
bpy.data.objects.remove(preview,do_unlink=True)
# Save editable source and review scene. Assets exported above contain no lights/camera.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.world.color=(.07,.07,.07)
ground=material('Review floor',(.025,.043,.048),rough=.82);bpy.ops.mesh.primitive_plane_add(size=200);bpy.context.object.data.materials.append(ground)
def light(name,pos,energy,color,size):bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.3))-o.location).to_track_quat('-Z','Y').to_euler()
light('Key',(-3,-4,5),450,(1,.85,.7),4);light('Fill',(3,-2,3),230,(.55,.78,1),3);light('Rim',(1,2,4),550,(.45,.85,1),2)
bpy.ops.object.camera_add(location=(3.1,-5.2,2.8));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.22))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.8;scene.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ezreal-v2.blend'))
review=ROOT/'docs/art-review';review.mkdir(parents=True,exist_ok=True)
for name,u in [('Idle',0),('Q',.5),('R',.45),('Walk',.2)]:
 performance(name,u,u*clips[name]);bpy.context.view_layer.update();scene.render.filepath=str(review/('ezreal-v2-'+name.lower()+'.png'));bpy.ops.render.render(write_still=True)
meta={'schema':1,'champion':'Ezreal','tool':'Blender 4.5.14 LTS','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'bones':len(defs),'animations':clips,'status':'original stylized production study; not final Wild Rift fidelity'}
MANIFEST.write_text(json.dumps(meta,indent=2)+'\n')
with zipfile.ZipFile(RELEASE/'sharpwr-ezreal-v2-source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for file in [OUT/'ezreal-v2.blend',OUT/'ezreal-v2.glb',OUT/'ezreal-v2-preview.glb',MANIFEST,Path(__file__)]:z.write(file,file.name)
print('EZREAL_V2_COMPLETE',str(OUT))
