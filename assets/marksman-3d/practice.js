/* Practice sandbox: database ranges and endpoint-accurate movement.
   With profile.practice (the engine's numbers from sharpwr/practice_data.py) it is the Practice Tool:
   real attack speed, movement speed, cast times and projectile travel, and damage on a training dummy. */
(function(scope){'use strict';
const Geo=typeof module!=='undefined'&&module.exports?require('./geometry.js'):scope.MarksmanGeometry;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),length=(a,b)=>Math.hypot(a[0]-b[0],a[2]-b[2]),valid=p=>Array.isArray(p)&&p.length===3&&p.every(Number.isFinite);
// Practice Tool constants (tool choices, not game data): dummy size, how long numbers and impact
// effects stay, and when the dummy heals or stands up again.
const UNITS=100,DUMMY_RADIUS=.65,TAIL=.35,IMPACT_AT=.74,HEAL_AFTER=5,RESPAWN_AFTER=1.5,NUMBER_LIFE=1.1,BOUNDS=[11.5,8],BUFFER=.6,HERO_RADIUS=.35;
// Instant self buffs (art direction cast:'instant') have no cast time: they apply on the press,
// never freeze the hero or wait for a clip, and last buff_seconds at the current rank.
function buffSeconds(profile,slot,rank){const s=profile.skills?.[slot];if(s?.cast!=='instant')return null;const v=s.buff_seconds||[];return v.length?v[Math.min(rank-1,v.length-1)]:0;}
function empowered(state){const hit=state.buffs.filter(b=>state.time>=b.start&&state.time<b.end&&state.profile.skills[b.slot]?.empowered_attack).at(-1);return hit?{empowered:state.profile.skills[hit.slot].empowered_attack,colorSlot:hit.slot}:{};}
function create(profile,{movements={},arena=null,autoApproach=true}={}){const state={profile,time:0,hero:[-2,0,0],destination:[-2,0,0],target:[2,0,0],facing:Math.PI/2,events:[],buffs:[],deadlines:{},aim:null,aimSlot:null,moving:false,gaitPhase:0,autoApproach,rank:1,level:1,movements,arena};if(profile.practice)Object.assign(state,{level:15,ranks:{...profile.practice.ranks[14]},noCooldowns:false,attackHeld:false,pending:null,queued:null,hits:[],numbers:[],log:[],nextAttack:null,dummy:dummy({hp:2000,armor:0,mr:0})});return state;}
function move(state,point){if(!valid(point)||state.duel&&(state.health.hp<=0||state.duel.finished))return;const to=[clamp(point[0],-(state.arena?.layout?.bounds||BOUNDS)[0],(state.arena?.layout?.bounds||BOUNDS)[0]),0,clamp(point[2],-(state.arena?.layout?.bounds||BOUNDS)[1],(state.arena?.layout?.bounds||BOUNDS)[1])];if(state.arena){const p=state.arena.project(to);to[0]=p[0];to[2]=p[2];}if(tool(state)){outside(state,to);if(!interrupt(state,to))return;}state.destination=to;}
function aim(state,slot,point){state.aim=valid(point)?point.slice():state.target.slice();state.aimSlot=slot;return indicatorFor(state,slot,state.aim);}
function indicatorFor(state,slot,point){const options={rank:rankOf(state,slot)||1,level:state.level,bounds:state.arena?.layout?.bounds},reach=tool(state)?.slots[slot]?.reach;if(reach){const r=at(reach,(rankOf(state,slot)||1)-1);if(r!=null)options.fallbackRange=r/UNITS;}const ind=Geo.indicator(state.profile,slot,state.hero,point,state.target,options,state.movements);if(state.arena&&state.movements[state.profile.name]?.[slot])ind.endpoint=state.arena.trace(state.hero,ind.endpoint,state.movements[state.profile.name][slot].kind);return ind;}
function cast(state,slot,point){if(point&&!valid(point)||!['AA','P','Q','W','E','R'].includes(slot))return false;if(tool(state))return castTool(state,slot,point);const ranks=state.profile.hud?.abilities?.[slot]?.cooldowns,cd=slot==='AA'?state.profile.attack.study_duration:slot==='P'?0:ranks?.[Math.min(state.rank-1,ranks.length-1)];if((state.deadlines[slot]||0)>state.time)return false;
 const seconds=slot==='AA'||slot==='P'?null:buffSeconds(state.profile,slot,state.rank);
 if(seconds!==null){if(Number.isFinite(cd))state.deadlines[slot]=state.time+cd/(1+(state.loadout?.stats.ability_haste||0)/100);state.buffs=state.buffs.filter(b=>b.slot!==slot);state.buffs.push({slot,start:state.time,end:state.time+seconds,seed:301+state.events.length+state.buffs.length});return true;}
 if(state.events.some(e=>state.time<e.start+e.duration))return false;
 const indicator=Geo.indicator(state.profile,slot,state.hero,point||state.target,state.target,{rank:state.rank,level:state.level},state.movements),duration=slot==='AA'?state.profile.attack.study_duration:slot==='P'?state.profile.passive.study_duration:state.profile.skills[slot].study_duration,release=state.profile.presentation?.release?.[slot]??.35,target=Geo.castTarget(indicator,state.target),hero=state.hero.slice(),direction=point||state.target;
 if(slot==='AA'&&indicator.range!==null&&length(hero,state.target)>indicator.range+.01)return false;
 state.facing=Math.atan2(direction[0]-hero[0],direction[2]-hero[2]);state.destination=hero.slice();if(Number.isFinite(cd))state.deadlines[slot]=state.time+cd/(1+(state.loadout?.stats.ability_haste||0)/100);const motion=state.movements[state.profile.name]?.[slot],landing=motion?indicator.endpoint.slice():null;if(landing){landing[0]=clamp(landing[0],-(state.arena?.layout?.bounds||BOUNDS)[0],(state.arena?.layout?.bounds||BOUNDS)[0]);landing[2]=clamp(landing[2],-(state.arena?.layout?.bounds||BOUNDS)[1],(state.arena?.layout?.bounds||BOUNDS)[1]);}
 state.events.push({slot,start:state.time,duration,release,hero,target,landing,motion,indicator,seed:state.events.length+71,...(slot==='AA'?empowered(state):{})});return true;}
function destinationFor(e,movements,name){if(e.landing)return e.landing;const move=movements[name]?.[e.slot];if(!move)return null;const sign=move.kind==='recoil'?-1:1;return Geo.point(e.hero,e.target,move.distance*sign);}
function step(state,dt,movements=state.movements){if(!Number.isFinite(dt)||dt<0)throw Error('Invalid timestep');if(tool(state))return stepTool(state,dt,movements);const previous=state.time;state.time+=dt;
 for(const e of state.events)if(previous<e.start+e.duration&&state.time>=e.start+e.duration){const to=destinationFor(e,movements,state.profile.name);if(to){state.hero=to.slice();state.hero[1]=0;state.destination=state.hero.slice();}}
 const active=state.events.find(e=>state.time>=e.start&&state.time<e.start+e.duration);state.moving=false;
 if(active){const move=active.motion||movements[state.profile.name]?.[active.slot],to=destinationFor(active,movements,state.profile.name),u=(state.time-active.start)/active.duration;if(move&&to)dashPosition(state,active,move,to,u);}
 else walk(state,dt,2.3);
 state.events=state.events.filter(e=>state.time<e.start+e.duration+.45);state.buffs=state.buffs.filter(b=>state.time<b.end);return state;}
function dashPosition(state,e,move,to,u){const f=move.kind==='blink'?(u>=.38?1:0):clamp((u-.16)/.46,0,1),ease=move.kind==='blink'?f:f*f*(3-2*f);state.hero=e.hero.map((v,i)=>v+(to[i]-v)*ease);state.hero[1]=move.kind==='jump'?Math.sin(clamp((u-.16)/.62,0,1)*Math.PI)*.65:0;state.destination=state.hero.slice();state.destination[1]=0;}
function walk(state,dt,speed){state.hero[1]=0;const dist=length(state.hero,state.destination);if(dist>.015){const distance=Math.min(dist,dt*speed),dx=(state.destination[0]-state.hero[0])/dist,dz=(state.destination[2]-state.hero[2])/dist,next=[state.hero[0]+dx*distance,0,state.hero[2]+dz*distance],p=state.arena?state.arena.trace(state.hero,next,'walk'):next;const travelled=length(state.hero,p);state.moving=travelled>.0001;if(state.moving)state.gaitPhase+=travelled/2.76*Math.PI*2;state.hero=p;state.facing=Math.atan2(dx,dz);}}
function frame(state,{particles=true,range=false}={}){if(tool(state))return frameTool(state,{particles,range});const active=state.events.find(e=>state.time>=e.start&&state.time<e.start+e.duration),action=active?.slot||(state.moving?'Walk':'Idle'),progress=active?clamp((state.time-active.start)/active.duration,0,1):state.time%1.2/1.2,effects=particles?state.events.filter(e=>state.time>=e.start&&state.time<e.start+e.duration).map(e=>({slot:e.slot,progress:(state.time-e.start)/e.duration,age:state.time-e.start,seed:e.seed,release:e.release,launchTime:e.start+e.release*e.duration,launchHero:e.boltOrigin||e.hero,launchTarget:e.target,projectile:e.projectile,flightTarget:e.flightTarget,traps:e.traps,trapSpent:e.trapSpent,start:e.hero,end:e.landing||undefined,empowered:e.empowered,colorSlot:e.colorSlot})).concat(buffEffects(state)):[],impacts=state.events.filter(e=>['AA','Q','R'].includes(e.slot)).map(e=>({action:e.slot,point:e.target.slice(),age:state.time-e.start-e.duration*(state.profile.presentation?.impact?.[e.slot]??.74),seed:e.seed})).filter(e=>e.age>=0&&e.age<.35),indicator=state.aimSlot?Geo.indicator(state.profile,state.aimSlot,state.hero,state.aim||state.target,state.target,{rank:state.rank,level:state.level},state.movements):null;
 return{champion:state.profile.name,time:state.time,hero:state.hero.slice(),target:state.target.slice(),turntable:state.facing,blendSeconds:active?Math.max(.015,Math.min(.07,(Number.isFinite(active.launch)?active.launch-active.start:active.duration*active.release)*.65)):.12,action,progress,speed:state.moving?1:0,gaitPhase:state.gaitPhase,loopDuration:action==='Walk'?1.2:action==='Idle'?3:0,effects,impacts,showTarget:true,showRange:range,range:(Geo.spec(state.profile,'AA',{level:state.level}).range||0)*Geo.UNITS,attackCursor:action==='AA',practice:true,buffs:state.buffs.map(b=>({slot:b.slot,remaining:Math.max(0,b.end-state.time)})),aim:state.aim,indicator,destination:state.destination.slice()};}
function buffEffects(state){return state.buffs.filter(b=>state.time>=b.start&&state.time<b.end).map(b=>({slot:b.slot,progress:.5,age:state.time-b.start,seed:b.seed,persistent:true}));}

// ---------------------------------------------------------------- Practice Tool
function tool(state){return state.profile.practice||null;}
function at(list,i){return Array.isArray(list)&&list.length?list[clamp(i,0,list.length-1)]:null;}
function levelIndex(state){return clamp(state.level,1,15)-1;}
function rankOf(state,slot){return state.ranks?.[slot]??state.rank;}
function activeBuffs(state,t=state.time){return state.buffs.filter(b=>t>=b.start&&t<b.end);}
function bonusAS(state,t=state.time){let v=(state.loadout?.bonusAs?.(t)||0)+(state.loadout?(state.loadout.stats.attack_speed-tool(state).levels.as[levelIndex(state)])/tool(state).as_ratio:0)+(state.duel?.mechanics?.bonusAS(state,t)||0);for(const b of activeBuffs(state,t))v+=b.as||0;for(const[slot,values]of Object.entries(tool(state).rank_as||{})){const r=rankOf(state,slot);if(r)v+=at(values,r-1);}return v;}
function attackSpeed(state,t=state.time){const T=tool(state);if(state.loadout&&state.profile.name==='Jhin')return state.loadout.stats.attack_speed;const value=(state.loadout?.attackSpeed()||T.levels.as[levelIndex(state)])+T.as_ratio*(bonusAS(state,t)-(state.loadout?(state.loadout.stats.attack_speed-T.levels.as[levelIndex(state)])/T.as_ratio:0));return state.loadout?Math.min(state.profile.name==='Zeri'?1.5:state.combat?.excitedUntil>t?Infinity:3,value):value;}
function bonusAD(state,t=state.time){return (state.loadout?.bonusAd?.(t)||0)+(state.loadout?state.loadout.stats.attack_damage-tool(state).levels.ad[levelIndex(state)]:0)+activeBuffs(state,t).reduce((v,b)=>v+(b.ad||0),0);}
function attackRange(state,t=state.time){return(tool(state).levels.range[levelIndex(state)]+(state.duel?.mechanics?.rangeBonus(state)||0)+activeBuffs(state,t).reduce((v,b)=>v+(b.range||0),0))/UNITS;}
function moveSpeed(state){return (state.loadout?.stats.movement_speed||tool(state).levels.ms[levelIndex(state)])/UNITS*(state.duel?.mechanics?.moveMultiplier(state)??1);}
// Windup by bonus attack speed, interpolated in the engine's 0.1 steps.
function windup(state,t=state.time){const w=tool(state).attack.windup,x=clamp(bonusAS(state,t),0,(w.length-1)/10)*10,i=Math.floor(x),f=x-i;return w[i]*(1-f)+w[Math.min(i+1,w.length-1)]*f;}
// Projectile travel from the engine's table (seconds every 250 units).
function travelTime(table,distance){if(!table)return 0;const x=clamp(distance*UNITS/250,0,table.length-1),i=Math.floor(x),f=x-i;return table[i]*(1-f)+table[Math.min(i+1,table.length-1)]*f;}
function stats(state){const T=tool(state),i=levelIndex(state);return{ad:T.levels.ad[i]+bonusAD(state),bonusAD:bonusAD(state),as:attackSpeed(state),bonusAS:bonusAS(state),range:attackRange(state)*UNITS,ms:moveSpeed(state)*UNITS};}
function rawDamage(state,slot){const s=tool(state).slots[slot],r=rankOf(state,slot);if(!s?.damage||!r)return null;const out={};for(const[kind,rows]of Object.entries(s.damage))out[kind]=at(at(rows,r-1),levelIndex(state));for(const[stat,kinds]of Object.entries(s.scaling||{})){const amount=stat==='ad'?bonusAD(state):(state.loadout?.stats.ability_power||0);for(const[kind,rows]of Object.entries(kinds))out[kind]=(out[kind]||0)+at(at(rows,r-1),levelIndex(state))*amount;}return out;}
function attackDamage(state){const T=tool(state),raw={physical:state.loadout?stats(state).ad:at(T.attack.damage.physical,levelIndex(state))+bonusAD(state)},bonus=[];
 for(const b of activeBuffs(state))if(b.attackBonus){const extra=rawDamage(state,b.attackBonus);if(extra)bonus.push(extra);}
 if(state.nextAttack){bonus.push(state.nextAttack.raw);state.nextAttack=null;}
 for(const extra of bonus)for(const[kind,v]of Object.entries(extra))raw[kind]=(raw[kind]||0)+v;return state.duel?.mechanics?.attackDamage(state,raw)||raw;}
function dummy({hp,armor,mr,aaReduction=0,label='Custom'}){return{label,max:hp,hp,armor,mr,aaReduction,mark:null,lastHit:-Infinity,defeatedAt:null,first:null,total:0,count:0};}
function setDummy(state,values){const d=state.dummy;state.dummy=dummy({hp:values.hp??d.max,armor:values.armor??d.armor,mr:values.mr??d.mr,aaReduction:values.aaReduction??d.aaReduction,label:values.label??d.label});state.hits=state.hits.filter(h=>h.at>state.time+1e9);}
function resetDummy(state){if(state.dummy.count)state.lastCombo=summary(state);setDummy(state,{});}
function placeDummy(state,point){if(!valid(point))return;state.target=[clamp(point[0],-(state.arena?.layout?.bounds||BOUNDS)[0],(state.arena?.layout?.bounds||BOUNDS)[0]),0,clamp(point[2],-(state.arena?.layout?.bounds||BOUNDS)[1],(state.arena?.layout?.bounds||BOUNDS)[1])];if(state.arena)state.target=state.arena.project(state.target);outside(state,state.hero);state.destination=state.hero.slice();}
function setLevel(state,level){state.level=clamp(Math.round(level),1,15);state.ranks={...tool(state).ranks[state.level-1]};}
function setRank(state,slot,rank){state.ranks[slot]=clamp(Math.round(rank),0,slot==='R'?3:4);}
function holdAttack(state,on){if(on&&state.duel&&(state.health.hp<=0||state.duel.finished))return;state.attackHeld=!!on;if(on&&!state.pending)state.pending={slot:'AA'};}
function mitigate(state,kind,value,attack){const d=state.dummy;if(state.loadout?.mitigate)return state.loadout.mitigate(d,kind,value,attack);const m=kind==='physical'?100/(100+d.armor):kind==='magic'?100/(100+d.mr):1;return value*m*(attack?1-d.aaReduction:1);}
// Animation progress: the windup (0 → release) takes the engine's cast time or attack windup,
// the follow-through plays at the authored speed.
function animProgress(e,t){if(t<e.launch)return e.release*clamp((t-e.start)/Math.max(.001,e.launch-e.start),0,1);return clamp(e.release+(1-e.release)*(t-e.launch)/Math.max(.001,e.start+e.duration-e.launch),0,1);}
function timeAtProgress(e,p){return p<=e.release?e.start+(e.launch-e.start)*p/Math.max(.001,e.release):e.launch+(p-e.release)/(1-e.release)*(e.start+e.duration-e.launch);}
// Effect progress: windup to release, flight from launch to arrival (release → IMPACT_AT), then the impact tail.
function effectProgress(e,t){if(t<e.launch)return e.release*clamp((t-e.start)/Math.max(.001,e.launch-e.start),0,1);if(t<e.arrive)return e.release+(IMPACT_AT-e.release)*(t-e.launch)/Math.max(.001,e.arrive-e.launch);return clamp(IMPACT_AT+(1-IMPACT_AT)*(t-e.arrive)/TAIL,0,1);}
function locking(state,t=state.time){return state.events.find(e=>t>=e.start&&t<e.lockEnd);}
function animating(state,t=state.time){return state.events.find(e=>t>=e.start&&t<e.animEnd);}
// Movement input during an attack windup, a cast or a dash waits for it (the attack still fires) and
// then moves the hero where the input points at that moment; after that it cuts the follow-through.
function interrupt(state,to){state.pending=null;if(locking(state)){state.queued=to;return false;}const anim=animating(state);if(anim)anim.animEnd=state.time;return true;}
function cancelAttack(state,e){state.duel?.mechanics?.onCancel(state,e);state.events=state.events.filter(x=>x!==e);state.hits=state.hits.filter(h=>h.event!==e);state.deadlines.AA=e.previousDeadline;if(e.consumed)state.nextAttack=e.consumed;}
function inReach(state,slot,from=state.hero){const s=tool(state).slots[slot],reach=at(s.reach,rankOf(state,slot)-1),spec=Geo.spec(state.profile,slot,{rank:rankOf(state,slot),level:state.level}),r=spec.range??(reach==null?null:reach/UNITS);return r===null||length(from,state.target)<=r+DUMMY_RADIUS;}
function segmentDistance(p,a,b){const dx=b[0]-a[0],dz=b[2]-a[2],len2=dx*dx+dz*dz||1e-9,u=clamp(((p[0]-a[0])*dx+(p[2]-a[2])*dz)/len2,0,1);return Math.hypot(a[0]+dx*u-p[0],a[2]+dz*u-p[2]);}
// Does the cast reach the dummy? Shapes follow the indicator the player saw.
function reaches(state,slot,ind,landing){const d=state.target,hero=ind.hero,spec=Geo.spec(state.profile,slot,{rank:rankOf(state,slot),level:state.level});
 switch(ind.shape){
  case'target':return inReach(state,slot);
  case'self':return(spec.radius||spec.range)?length(hero,d)<=(spec.radius||spec.range)+DUMMY_RADIUS:inReach(state,slot);
  case'area':return length(ind.endpoint,d)<=(ind.radius||0)+DUMMY_RADIUS;
  case'cone':{const dx=ind.endpoint[0]-hero[0],dz=ind.endpoint[2]-hero[2],a=Math.atan2(dx,dz),b=Math.atan2(d[0]-hero[0],d[2]-hero[2]),diff=Math.abs(Math.atan2(Math.sin(a-b),Math.cos(a-b)));return diff<=.4&&length(hero,d)<=(ind.range??Math.hypot(dx,dz))+DUMMY_RADIUS;}
  case'blink':return!!landing&&length(landing,d)<=(ind.radius||0)+DUMMY_RADIUS;
  case'jump':return!!landing&&length(landing,d)<=(ind.radius||0)+DUMMY_RADIUS;
  case'dash':case'slide':case'roll':case'target-dash':return!!landing&&segmentDistance(d,hero,landing)<=(ind.width||.8)/2+DUMMY_RADIUS;
  default:{const end=ind.endpoint,reach=ind.shape==='recoil'?Geo.castTarget(ind,d):end;return segmentDistance(d,hero,reach)<=(ind.width||.8)/2+DUMMY_RADIUS&&((reach[0]-hero[0])*(d[0]-hero[0])+(reach[2]-hero[2])*(d[2]-hero[2]))>0;}
 }}
function startBuff(state,slot,start){const T=tool(state),s=T.slots[slot],b=s.buff,mode=s.mode==='attack'&&s.attacks==='buff'?slot:null,rank=rankOf(state,b?.by||slot)||1,seconds=b?at(b.duration,rank-1):buffSeconds(state.profile,slot,rankOf(state,slot)||1);if(!seconds)return;state.buffs=state.buffs.filter(x=>x.slot!==slot);state.buffs.push({slot,start,end:start+seconds,seed:301+state.events.length+state.buffs.length,as:b?at(b.as,rank-1)||0:0,ad:b?at(b.ad,rank-1)||0:0,range:b?at(b.range,rank-1)||0:0,attackBonus:mode});}
function castTool(state,slot,point){const T=tool(state),profile=state.profile,t=state.time,S=['AA','P'].includes(slot)?null:T.slots[slot];
 if(state.duel&&(state.health.hp<=0||state.duel.finished))return false;
 if(S&&!rankOf(state,slot))return false;
 if((slot==='AA'||!state.noCooldowns)&&(state.deadlines[slot]||0)>t+1e-9)return false;
 if(state.duel?.mechanics?.canCast(state,slot,true)===false)return false;
 const special=state.duel?.mechanics?.specialCast(state,slot);if(special!=null){if(special)state.loadout?.cast(slot,t);return special;}
 if(S&&profile.skills[slot]?.cast==='instant'){state.duel?.mechanics?.onCast(state,{slot,start:t,launch:t,fxEnd:t});state.loadout?.cast(slot,t);startBuff(state,slot,t);setCooldown(state,slot,S);log(state,{t,slot,text:'buff'});return true;}
 // A skill pressed during an attack windup cancels the attack; during another cast it waits (input buffer).
 const busy=locking(state);if(busy){if(slot!=='AA'&&busy.slot==='AA'&&t<busy.launch)cancelAttack(state,busy);else{if(slot!=='AA')state.buffered={slot,point,until:t+BUFFER};return false;}}
 const indicator=indicatorFor(state,slot,point||state.target);
 if(slot==='AA'&&length(state.hero,state.target)>attackRange(state)+DUMMY_RADIUS){if(state.autoApproach!==false){state.pending={slot:'AA'};approach(state,attackRange(state));}return false;}
 if(S&&indicator.shape==='target'&&!inReach(state,slot)){if(state.autoApproach===false)return false;state.pending={slot};const reach=at(S.reach,rankOf(state,slot)-1);approach(state,(Geo.spec(profile,slot,{rank:rankOf(state,slot),level:state.level}).range??reach/UNITS));return false;}
 const anim=animating(state);if(anim)anim.animEnd=t;state.pending=null;
 const release=profile.presentation?.release?.[slot]??.35,study=slot==='AA'?profile.attack.study_duration:slot==='P'?profile.passive.study_duration:profile.skills[slot].study_duration;
 let wind,lock,total,cooldown;
 if(slot==='AA'){const interval=1/attackSpeed(state);wind=windup(state);total=Math.max(wind+.12,Math.min(study,interval));lock=wind;cooldown=interval;}
 else if(slot==='P'){wind=Math.max(.06,study*release);total=study;lock=0;cooldown=0;}
 else{const channel=S.channel;let castTime=S.cast||0;if(state.duel&&S.cast_by_as){const x=Math.min(S.cast_by_as.length-1,bonusAS(state)*10),i=Math.floor(x);castTime=S.cast_by_as[i]+(S.cast_by_as[Math.min(i+1,S.cast_by_as.length-1)]-S.cast_by_as[i])*(x-i);}wind=Math.max(castTime,.06);if(channel){lock=channel.mobile?wind:channel.seconds;total=channel.seconds+.25;}else{lock=castTime;total=wind+(1-release)*study;}cooldown=null;}
 const hero=state.hero.slice(),motion=state.movements[profile.name]?.[slot],landing=motion?indicator.endpoint.slice():null,seed=state.events.length+71+Math.floor(t*7)%97;
 if(landing){landing[0]=clamp(landing[0],-(state.arena?.layout?.bounds||BOUNDS)[0],(state.arena?.layout?.bounds||BOUNDS)[0]);landing[2]=clamp(landing[2],-(state.arena?.layout?.bounds||BOUNDS)[1],(state.arena?.layout?.bounds||BOUNDS)[1]);}
 const e={slot,targetId:state.targetId,start:t,duration:total,release,hero,landing,motion,indicator,seed,launch:t+wind,lockEnd:t+lock,animEnd:t+total,previousDeadline:state.deadlines[slot]||0,...(slot==='AA'?empowered(state):{})};
 if(motion){const end=timeAtProgress(e,motion.kind==='blink'?.38:.62);e.lockEnd=Math.max(e.lockEnd,end);e.dashEnd=end;}
 const hit=slot==='AA'||(slot!=='P'&&S.mode!=='none'&&(state.duel||reaches(state,slot,indicator,landing))),from=indicator.shape==='blink'&&landing?landing:hero;
 e.hit=hit;e.target=hit?state.target.slice():Geo.castTarget(indicator,state.target);
 const distance=length(from,e.target);e.arrive=e.launch+(slot==='AA'?(T.attack.speed?distance*UNITS/T.attack.speed:0):slot==='P'?0:travelTime(S.travel,distance));e.fxEnd=Math.max(t+total,e.arrive+TAIL);
 // Duel skillshots keep the cast direction and travel to full range. Hit tests happen during
 // flight against the moving opponent; targeted attacks remain homing.
 if(state.duel&&S&&['line','recoil'].includes(indicator.shape)){
  e.target=Geo.castTarget({...indicator,shape:'line',endpoint:Geo.point(hero,indicator.aim,indicator.range||30)},[-999,0,-999]);
  e.arrive=e.launch+travelTime(S.travel,length(hero,e.target));e.fxEnd=Math.max(t+total,e.arrive+TAIL);
 }
 const direction=point||state.target;state.facing=Math.atan2(direction[0]-hero[0],direction[2]-hero[2]);state.destination=hero.slice();
 if(slot==='AA'){const consumed=state.nextAttack;state.hits.push({at:e.arrive,slot,event:e,attack:true,raw:attackDamage(state),seed});e.consumed=consumed;}
 else if(S&&hit&&S.mode==='hit')state.hits.push({at:e.arrive,slot,event:e,raw:rawDamage(state,slot),seed});
 else if(S&&hit&&S.mode==='mark')state.hits.push({at:e.arrive,slot,event:e,mark:{raw:rawDamage(state,slot),window:S.window},seed});
 else if(S&&hit&&S.mode==='skip')state.hits.push({at:e.arrive,slot,event:e,skip:S.reason,seed});
 if(S&&S.mode==='attack'&&S.attacks==='next')state.nextAttack={slot,raw:rawDamage(state,slot)};
 if(S&&(S.buff||profile.skills[slot]?.buff_seconds))startBuff(state,slot,e.launch);
 if(slot==='AA')state.deadlines.AA=t+cooldown;else if(S)setCooldown(state,slot,S);
 state.events.push(e);state.loadout?.cast(slot,t);state.duel?.mechanics?.onCast(state,e);return true;}
function setCooldown(state,slot,S){const cd=at(S.cooldown,rankOf(state,slot)-1);if(!state.noCooldowns&&Number.isFinite(cd))state.deadlines[slot]=state.time+cd/(1+(state.loadout?.stats.ability_haste||0)/100);}
// The dummy is solid: the hero stops at its edge (dashes may pass through, but never land inside).
function outside(state,p){if(state.arena){const q=state.arena.project(p);p[0]=q[0];p[2]=q[2];}const d=length(p,state.target),min=DUMMY_RADIUS+HERO_RADIUS;if(d>=min)return p;const dx=d>1e-6?(p[0]-state.target[0])/d:-1,dz=d>1e-6?(p[2]-state.target[2])/d:0;p[0]=state.target[0]+dx*min;p[2]=state.target[2]+dz*min;return state.arena?state.arena.project(p):p;}
function approach(state,range){const d=length(state.hero,state.target);if(d<=range+DUMMY_RADIUS)return;state.destination=Geo.point(state.target,state.hero,Math.max(.1,range+DUMMY_RADIUS-.15));}
function log(state,entry){state.log.push(entry);if(state.log.length>40)state.log.shift();}
function number(state,t,slot,kind,amount,extra={}){state.numberSeq=(state.numberSeq||0)+1;state.numbers.push({t,slot,kind,amount,point:state.target.slice(),seq:state.numberSeq,...extra});}
function land(state,h){const d=state.dummy,t=h.landAt??h.at;if(d.defeatedAt!==null)return;
 if(h.skip){number(state,t,h.slot,'none',0,{note:h.skip});log(state,{t,slot:h.slot,text:'hit · damage not simulated',note:h.skip});return;}
 if(h.mark){d.mark={slot:h.slot,raw:h.mark.raw,until:t+h.mark.window};number(state,t,h.slot,'none',0,{note:'mark'});log(state,{t,slot:h.slot,text:'mark applied'});state.duel?.mechanics?.onHit(state,h,false);return;}
 state.duel?.mechanics?.beforeHit(state,h);
 const beforeAS=attackSpeed(state),hpBefore=d.hp,resolved=state.loadout?.resolve(state,h);if(resolved&&(state.deadlines.AA||0)>state.time)state.deadlines.AA=state.time+(state.deadlines.AA-state.time)*beforeAS/attackSpeed(state);apply(state,t,h.slot,Object.fromEntries(Object.entries(resolved||h.raw||{}).map(([k,v])=>[k,v*(h.damageScale??1)])),h.attack,!!resolved);
 if(resolved&&h.attack&&state.health)state.health.hp=Math.min(state.health.max,state.health.hp+Math.min(hpBefore,resolved.physical||0)*(state.loadout.stats.lifesteal||0));
 let flux=false;if(d.mark&&d.mark.slot!==h.slot&&t<=d.mark.until){const m=d.mark;d.mark=null;apply(state,t,m.slot+' detonation',m.raw,false);flux=true;}if(!h.secondary||state.duel?.hitVictim?.kind==='champion')state.duel?.mechanics?.onHit(state,h,flux);}
function apply(state,t,slot,raw,attack,resolved=false){const d=state.dummy;let dealt=0;const parts={};for(const[kind,value]of Object.entries(raw||{})){if(!value)continue;const v=resolved?value:mitigate(state,kind,value,attack);parts[kind]={raw:value,dealt:v};dealt+=v;number(state,t,slot,kind,v);}
 if(d.first===null)d.first=t;d.total+=dealt;d.count++;d.lastHit=t;d.hp=Math.max(0,d.hp-dealt);if(d.hp<=0)d.defeatedAt=t;log(state,{t,slot,parts,dealt,point:state.target.slice()});}
function stepTool(state,dt,movements){const previous=state.time;state.time+=dt;const t=state.time,d=state.dummy;
 if(state.duel){for(const h of state.hits){if(state.duel.resolveHit(state,h,previous,t)){if(state.duel.withHitTarget)state.duel.withHitTarget(state,h,()=>land(state,h));else land(state,h);h.done=!h.keepAlive||t>=h.at;}else if(t>=h.at)h.done=true;}state.hits=state.hits.filter(h=>!h.done);}
 else{for(const h of state.hits.filter(h=>h.at<=t).sort((a,b)=>a.at-b.at))land(state,h);state.hits=state.hits.filter(h=>h.at>t);}
 if(d.mark&&t>d.mark.until)d.mark=null;
 if(!state.duel&&(d.defeatedAt!==null&&t>=d.defeatedAt+RESPAWN_AFTER||d.defeatedAt===null&&d.first!==null&&t>=d.lastHit+HEAL_AFTER))resetDummy(state);
 for(const e of state.events)if(e.landing&&!e.landed&&t>=e.dashEnd){e.landed=true;state.hero=outside(state,e.landing.slice());state.hero[1]=0;state.destination=state.hero.slice();}
 const active=animating(state),lock=locking(state);state.moving=false;
 if(lock&&lock.landing&&!lock.landed){const move=lock.motion,to=lock.landing;dashPosition(state,lock,move,to,animProgress(lock,t));}
 else if(!lock){if(state.buffered){const b=state.buffered;state.buffered=null;if(t<=b.until)cast(state,b.slot,b.point);}
  if(!locking(state)&&state.queued){state.destination=state.queued;state.queued=null;const anim=animating(state);if(anim)anim.animEnd=t;}
  if(state.attackHeld&&!state.pending)state.pending={slot:'AA'};const want=state.pending;if(want){const ready=(state.deadlines[want.slot]||0)<=t+1e-9||want.slot!=='AA'&&state.noCooldowns;if(ready){state.pending=null;cast(state,want.slot);}else if(state.autoApproach!==false&&want.slot==='AA'&&length(state.hero,state.target)>attackRange(state)+DUMMY_RADIUS)approach(state,attackRange(state));}
  if(!locking(state)){const anim=animating(state);if(!anim||length(state.hero,state.destination)>.015){if(anim&&length(state.hero,state.destination)>.015)anim.animEnd=t;walk(state,dt,moveSpeed(state));}}}
 if(!(lock&&lock.landing&&!lock.landed))outside(state,state.hero);
 state.events=state.events.filter(e=>t<e.fxEnd+.45);state.buffs=state.buffs.filter(b=>t<b.end);state.numbers=state.numbers.filter(n=>t-n.t<NUMBER_LIFE);return state;}
function frameTool(state,{particles,range}){const t=state.time,active=animating(state),action=active?.slot||(state.moving?'Walk':'Idle'),walkLoop=1.2*2.3/moveSpeed(state),progress=active?animProgress(active,t):action==='Walk'?(state.gaitPhase/(Math.PI*2))%1:t%3/3;
 const effects=particles?state.events.filter(e=>t>=e.start&&t<e.fxEnd).map(e=>({slot:e.slot,progress:effectProgress(e,t),impactAt:IMPACT_AT,age:t-e.start,seed:e.seed,release:e.release,launchTime:e.launch,launchHero:e.boltOrigin||e.hero,launchTarget:e.target,projectile:e.projectile,flightTarget:e.flightTarget,traps:e.traps,trapSpent:e.trapSpent,start:e.hero,end:e.landing||undefined,empowered:e.empowered,colorSlot:e.colorSlot})).concat(buffEffects(state)):[];
 const impacts=state.events.filter(e=>e.hit&&e.slot!=='P'&&!e.multiHits).map(e=>({action:e.slot,point:(e.impactPoint||e.target).slice(),age:t-e.arrive,seed:e.seed,empowered:e.empowered,colorSlot:e.colorSlot,mark:state.profile.practice.slots[e.slot]?.mode==='mark'})).concat(state.events.flatMap(e=>(e.laneImpacts||[]).map(h=>({...h,age:t-h.at})))).concat(state.log.filter(h=>h.slot==='W detonation').map(h=>({action:'W',detonation:true,point:(h.point||state.target).slice(),age:t-h.t,seed:71}))).filter(e=>e.age>=0&&e.age<TAIL),indicator=state.aimSlot?indicatorFor(state,state.aimSlot,state.aim||state.target):null,d=state.dummy;
 return{champion:state.profile.name,time:t,hero:state.hero.slice(),target:state.target.slice(),turntable:state.facing,blendSeconds:active?Math.max(.015,Math.min(.07,(Number.isFinite(active.launch)?active.launch-active.start:active.duration*active.release)*.65)):.12,action,progress,speed:state.moving?1:0,gaitPhase:state.gaitPhase,loopDuration:action==='Walk'?walkLoop:action==='Idle'?3:0,effects,impacts,showTarget:true,showRange:range,range:attackRange(state)*UNITS,attackAim:state.attackAim&&!state.duel?.finished?{start:state.hero.slice(),end:state.hero.map((v,i)=>v+state.attackAim[i]*attackRange(state)),range:attackRange(state)}:null,attackCursor:action==='AA',practice:true,buffs:state.buffs.map(b=>({slot:b.slot,remaining:Math.max(0,b.end-t)})),aim:state.aim,indicator,destination:state.destination.slice(),
  dummy:{hp:d.hp,max:d.max,label:d.label,defeated:d.defeatedAt!==null,mark:d.mark?{slot:d.mark.slot,remaining:d.mark.until-t}:null},numbers:state.numbers.map(n=>({slot:n.slot,kind:n.kind,amount:n.amount,note:n.note,point:n.point,seq:n.seq,age:t-n.t}))};}
function summary(state){const d=state.dummy,seconds=d.first===null?0:d.lastHit-d.first;return{total:d.total,count:d.count,seconds,dps:seconds>.25?d.total/seconds:d.total};}
const API={create,move,aim,cast,step,frame,buffSeconds,stats,setDummy,resetDummy,placeDummy,setLevel,setRank,holdAttack,summary,rawDamage,reaches,DUMMY_RADIUS};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanPractice=API;
})(typeof globalThis!=='undefined'?globalThis:this);
