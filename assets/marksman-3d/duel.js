/* Real-time two-way base-kit duel. Uses Practice's database numbers and legal cast/movement
 * rules. Both actors share the same fixed clock and collision rules, independent of AI mode. */
(function(scope){'use strict';
const node=typeof module!=='undefined'&&module.exports,P=node?require('./practice.js'):scope.MarksmanPractice,G=node?require('./geometry.js'):scope.MarksmanGeometry,Bot=node?require('./duel-bot.js'):scope.MarksmanDuelBot,Mechanics=node?require('./duel-mechanics.js'):scope.MarksmanDuelMechanics;
const DT=1/120,dist=(a,b)=>Math.hypot(a[0]-b[0],a[2]-b[2]),clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function health(p,level){const l=p.practice.levels,i=level-1;for(const k of['hp','armor','mr'])if(!Number.isFinite(l[k]?.[i]))throw Error('Missing duel stat: '+p.name+' '+k);return{label:p.name,max:l.hp[i],hp:l.hp[i],armor:l.armor[i],mr:l.mr[i],aaReduction:0,mark:null,lastHit:-Infinity,defeatedAt:null,first:null,total:0,count:0};}
function create(playerProfile,botProfile,{level=15,difficulty='medium',seed=1,movements={},arena=null,distance=600,duration=180}={}){
 if(!Number.isInteger(level)||level<1||level>15||!Number.isFinite(distance)||distance<100||distance>2000||!Number.isFinite(duration)||duration<=0)throw Error('Invalid duel settings');
 const d={time:0,accumulator:0,finished:false,result:null,duration,bot:Bot.create(difficulty,seed),player:P.create(playerProfile,{movements,arena}),enemy:P.create(botProfile,{movements,arena}),resolveHit,mechanics:Mechanics};
 for(const s of[d.player,d.enemy]){P.setLevel(s,level);s.health=health(s.profile,level);s.duel=d;Mechanics.init(s);}
 d.player.hero=[-distance/200,0,0];d.enemy.hero=[distance/200,0,0];d.player.dummy=d.enemy.health;d.enemy.dummy=d.player.health;
 for(const s of[d.player,d.enemy]){s.destination=s.hero.slice();s.previous=s.hero.slice();}sync(d);Bot.observe(d.bot,{time:0,enemy:publicActor(d.player)});return d;
}
function sync(d){d.player.target=d.enemy.hero.slice();d.enemy.target=d.player.hero.slice();}
function segment(p,a,b){const dx=b[0]-a[0],dz=b[2]-a[2],u=clamp(((p[0]-a[0])*dx+(p[2]-a[2])*dz)/(dx*dx+dz*dz||1e-9),0,1);return Math.hypot(a[0]+dx*u-p[0],a[2]+dz*u-p[2]);}
function resolveHit(s,h,previous,time){const e=h.event,shape=e.indicator.shape;if(time<e.launch)return false;let hit=false;
 if(h.trap)hit=time>=h.arm&&time<=h.at&&dist(s.target,e.indicator.endpoint)<=(e.indicator.radius||0)+.35;
 else if(h.bolt){if(!h.acquired){h.acquired=true;h.valid=dist(e.landing,s.target)<=(e.indicator.radius||0)+.35;e.target=s.target.slice();const speed=s.profile.practice.duel.bolt_speed;h.at=e.launch+dist(e.landing,s.target)*100/speed;e.arrive=h.at;e.fxEnd=Math.max(e.fxEnd,h.at+.35);}hit=h.valid&&time>=h.at;}
 else if(h.attack||shape==='target'||shape==='target-dash')hit=time>=h.at;
 else if(['line','recoil'].includes(shape)&&e.arrive>e.launch){const at=t=>{const u=clamp((t-e.launch)/(e.arrive-e.launch),0,1);return e.hero.map((v,i)=>v+(e.target[i]-v)*u);};hit=segment(s.target,at(Math.max(previous,e.launch)),at(time))<=e.indicator.width/2+.35;}
 else if(time>=h.at)hit=P.reaches(s,h.slot,e.indicator,e.landing);
 if(hit){h.at=time;e.hit=true;e.arrive=time;e.fxEnd=Math.max(e.start+e.duration,time+.35);}else e.hit=false;return hit;
}
function publicActor(s){const before=s.previous||s.hero;return{champion:s.profile.name,position:s.hero.slice(),velocity:s.moving?[(s.hero[0]-before[0])/DT,0,(s.hero[2]-before[2])/DT]:[0,0,0],hp:s.health.hp,max:s.health.max,range:P.stats(s).range/100,
 casts:s.events.filter(e=>s.time>=e.start&&s.time<e.fxEnd&&e.slot!=='AA').map(e=>({slot:e.slot,startTime:e.start,cooldown:s.profile.practice.slots[e.slot]?.cooldown?.[(s.ranks[e.slot]||1)-1]||0,shape:e.indicator.shape,from:e.hero.slice(),to:e.target.slice(),width:e.indicator.width,radius:e.indicator.radius||0,endTime:e.trap?e.fxEnd:e.arrive})),
 hits:s.log.filter(h=>h.dealt>0&&s.time-h.t<1.2).map(h=>({slot:h.slot,time:h.t}))};}
function selfActor(s){const skills={};for(const slot of['Q','W','E','R']){const t=s.profile.practice.slots[slot],r=s.ranks[slot]||1,spec=G.spec(s.profile,slot,{rank:r,level:s.level}),travel=t.travel?.[4]||0;skills[slot]={rank:s.ranks[slot],ready:s.deadlines[slot]||0,range:spec.global?30:(spec.range??(t.reach?.[r-1]/100))||0,cast:t.cast,speed:travel?10/travel:0,mode:t.mode,buff:!!t.buff||s.profile.skills[slot]?.cast==='instant',mobility:!!s.movements[s.profile.name]?.[slot],targeted:['target','target-dash'].includes(spec.shape)};}
 if(s.profile.practice.duel){for(const[slot,info]of Object.entries(skills)){info.cost=Mechanics.cost(s,slot);info.affordable=Mechanics.canCast(s,slot);if(s.profile.name==='Jinx'&&slot==='Q')info.mode='toggle';if(s.profile.name==='Jinx'&&slot==='R')info.mode='hit';}}
 return{...publicActor(s),rooted:s.combat.rootUntil>s.time,mana:s.resource?.mana,rocketCost:s.profile.practice.duel?.costs.Q[(s.ranks.Q||1)-1],weapon:s.combat.weapon,baseRange:s.profile.practice.levels.range[s.level-1]/100,rocketRange:(s.profile.practice.levels.range[s.level-1]+(s.profile.practice.duel?.minigun?.[(s.ranks.Q||1)-1]?.range||0))/100,attackReady:s.deadlines.AA||0,locked:s.events.some(e=>s.time>=e.start&&s.time<e.lockEnd),skills};}
function step(d,dt){if(!Number.isFinite(dt)||dt<0)throw Error('Invalid duel timestep');if(d.finished)return d;d.accumulator+=Math.min(dt,.25);
 while(d.accumulator+1e-9>=DT&&!d.finished){d.accumulator-=DT;sync(d);const command=Bot.decide(d.bot,selfActor(d.enemy),d.time);if(command){if(command.move)P.move(d.enemy,command.move);if(command.cast)P.cast(d.enemy,command.cast,command.aim);}
  // Movement/cast commands use the previous shared snapshot; no side gets an extra decision.
  d.player.previous=d.player.hero.slice();d.enemy.previous=d.enemy.hero.slice();Mechanics.step(d.player,DT);Mechanics.step(d.enemy,DT);P.step(d.player,DT);P.step(d.enemy,DT);d.time=d.player.time;sync(d);Bot.observe(d.bot,{time:d.time,enemy:publicActor(d.player)});
  const a=d.player.health.hp<=0,b=d.enemy.health.hp<=0;if(a||b||d.time>=d.duration){d.finished=true;d.result=a&&b?'draw':a?'defeat':b?'victory':'timeout';for(const s of[d.player,d.enemy]){s.attackHeld=false;s.pending=null;s.destination=s.hero.slice();}}
 }return d;
}
function frame(d,options={}){const f=P.frame(d.player,options),enemy=P.frame(d.enemy,options);return{...f,buffs:f.buffs.concat(Mechanics.snapshot(d.player)),showTarget:false,duel:true,opponent:{...enemy,buffs:enemy.buffs.concat(Mechanics.snapshot(d.enemy)),champion:d.enemy.profile.name},playerHealth:{...d.player.health},dummy:{...d.enemy.health,defeated:d.enemy.health.hp<=0},result:d.result,difficulty:d.bot.difficulty};}
const API={create,step,frame,selfActor,publicActor,DT};if(node)module.exports=API;else scope.MarksmanDuel=API;
})(typeof globalThis!=='undefined'?globalThis:this);
