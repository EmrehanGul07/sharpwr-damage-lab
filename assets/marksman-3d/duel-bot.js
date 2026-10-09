/* Decision-only opponent AI. No stat multipliers, cooldown edits or hidden enemy inputs.
 * Commands use delayed public observations and the bot's own legal cooldowns. */
(function(scope){'use strict';
const Geo=typeof module!=='undefined'&&module.exports?require('./geometry.js'):scope.MarksmanGeometry;
const MODES=Object.freeze({
 easy:Object.freeze({reaction:.65,think:.24,error:1.1,lead:0,dodge:.08,spacing:.58,miss:.25}),
 medium:Object.freeze({reaction:.30,think:.14,error:.55,lead:.35,dodge:.4,spacing:.76,miss:.10}),
 hard:Object.freeze({reaction:.14,think:.075,error:.18,lead:.8,dodge:.8,spacing:.90,miss:.025}),
 impossible:Object.freeze({reaction:.05,think:.035,error:0,lead:1,dodge:1,spacing:.96,miss:0})
});
const dist=(a,b)=>Math.hypot(a[0]-b[0],a[2]-b[2]);
function rng(seed){let s=seed>>>0;return()=>{s=(s+0x6D2B79F5)>>>0;let x=s;x=Math.imul(x^(x>>>15),x|1);x^=x+Math.imul(x^(x>>>7),x|61);return((x^(x>>>14))>>>0)/4294967296;};}
function create(difficulty='medium',seed=1){if(!MODES[difficulty])throw Error('Unknown bot difficulty: '+difficulty);return{difficulty,config:MODES[difficulty],random:rng(seed),next:0,history:[],last:null,dodgeUntil:0,decision:null,knownCooldowns:{},seenCasts:new Set(),seenHits:new Set()};}
function observe(bot,publicView){const v=structuredCopy(publicView);bot.history.push(v);while(bot.history.length>2&&bot.history[1].time<v.time-1.2)bot.history.shift();}
function structuredCopy(v){return JSON.parse(JSON.stringify(v));}
function visible(bot,time){const cutoff=time-bot.config.reaction;return bot.history.filter(v=>v.time<=cutoff+1e-9).at(-1)||null;}
function aim(bot,self,enemy,slot){const c=bot.config,s=self.skills[slot],d=dist(self.position,enemy.position),flight=s.speed?d/s.speed:0,horizon=Math.min(.8,c.reaction+(s.cast||0)+flight),noise=c.error*(bot.random()*2-1),angle=bot.random()*Math.PI*2;
 return[enemy.position[0]+enemy.velocity[0]*horizon*c.lead+Math.cos(angle)*noise,0,enemy.position[2]+enemy.velocity[2]*horizon*c.lead+Math.sin(angle)*noise];}
function threat(enemy,self,time){for(const e of enemy.casts){if(!['line','recoil','cone','area'].includes(e.shape)||e.endTime<time)continue;
 const a=e.from,b=e.to,dx=b[0]-a[0],dz=b[2]-a[2],l=Math.hypot(dx,dz)||1,u=((self.position[0]-a[0])*dx+(self.position[2]-a[2])*dz)/(l*l),side=Math.abs((self.position[0]-a[0])*dz-(self.position[2]-a[2])*dx)/l;
 if(e.shape==='area'?dist(self.position,b)<e.radius+.65:u>=0&&u<=1&&side<e.width/2+.7)return{dx:dx/l,dz:dz/l,width:e.width};
 }return null;}
function decide(bot,self,time){if(time+1e-9<bot.next||self.hp<=0)return null;bot.next=time+bot.config.think;const view=visible(bot,time);if(!view||view.enemy.hp<=0)return null;
 for(const cast of view.enemy.casts||[]){const key=cast.slot+':'+cast.startTime;if(!bot.seenCasts.has(key)){bot.seenCasts.add(key);bot.knownCooldowns[cast.slot]=cast.startTime+(cast.cooldown||0);}}
 for(const hit of view.enemy.hits||[]){const key=hit.slot+':'+hit.time;if(!bot.seenHits.has(key)){bot.seenHits.add(key);if(view.enemy.champion==='Ezreal'&&hit.slot==='Q')for(const slot of Object.keys(bot.knownCooldowns))bot.knownCooldowns[slot]=Math.max(hit.time,bot.knownCooldowns[slot]-1.5);}}
 if(time<bot.dodgeUntil)return null;
 const enemy=view.enemy,c=bot.config,d=dist(self.position,enemy.position),ready=s=>self.skills[s]?.rank>0&&self.skills[s].ready<=time+1e-9&&self.skills[s].affordable!==false,legal=s=>ready(s)&&(!self.skills[s].targeted||d<=self.skills[s].range+.65),danger=self.rooted?null:threat(enemy,self,time),away=Geo.point(enemy.position,self.position,Math.max(d,1)+1.5);
 // Dodge only telegraphed casts already observed; never inspect pending damage or player input.
 if(danger&&time>=bot.dodgeUntil&&bot.random()<c.dodge){bot.dodgeUntil=time+.35;const sign=bot.random()<.5?-1:1,point=[self.position[0]-danger.dz*sign*1.8,0,self.position[2]+danger.dx*sign*1.8],escape=Object.keys(self.skills).find(s=>legal(s)&&self.skills[s].mobility&&!self.skills[s].targeted);
  return remember(bot,{move:point,...(escape&&c.dodge>=.8&&!self.locked?{cast:escape,aim:point}:{}),reason:'dodge'});}
 if(self.locked)return null;
 if(self.champion==='Jinx'&&self.skills.Q?.mode==='toggle'&&ready('Q')){const rocket=d>self.baseRange+.2&&d<=self.rocketRange+1&&(self.mana||0)>=(self.rocketCost||0);if(rocket!==(self.weapon==='rockets'))return remember(bot,{cast:'Q',reason:'weapon'});}
 const punish=c.dodge>=.8&&enemy.champion==='Ezreal'&&(bot.knownCooldowns.E||0)>time&&self.hp/self.max>.5;
 const wanted=self.range*c.spacing*(punish?.85:1),tooClose=d<wanted-.45,tooFar=d>self.range+.45,point=tooClose?Geo.point(enemy.position,self.position,wanted):tooFar?Geo.point(enemy.position,self.position,wanted):Geo.point(enemy.position,self.position,Math.max(1,d));
 // Preserve attack windups; kite in the downtime, never raise the attack rate.
 const cmd={move:point,reason:tooClose?'kite':tooFar?'approach':'spacing'};
 if(bot.random()<c.miss)return remember(bot,cmd);
 const order=punish&&self.champion==='Jinx'?['E','W','R']:self.champion==='Ezreal'?['W','Q','R','E']:self.champion==='Tristana'?['E','Q','R','W']:self.champion==='Varus'?['W','Q','E','R']:['Q','W','E','R'];
 for(const slot of order){const s=self.skills[slot];if(!legal(slot)||s.mode==='toggle'||s.mode==='skip'||s.mode==='none'&&!s.buff)continue;
  if(s.mobility){if(self.hp/self.max>.28||d>self.range||c.dodge<.8)continue;cmd.cast=slot;cmd.aim=away;cmd.reason='escape';break;}
  if(s.buff&&d>self.range+.65)continue;
  if(!s.buff&&d>s.range+.65)continue;
  if(slot==='R'&&!s.buff&&c.dodge>=.8&&enemy.hp/enemy.max>.4&&self.hp/self.max>.35)continue;
  cmd.cast=slot;cmd.aim=aim(bot,self,enemy,slot);cmd.reason=s.buff?'buff':slot==='R'?'finish':'combo';break;
 }
 if(!cmd.cast&&self.attackReady<=time+1e-9&&d<=self.range+.65){cmd.cast='AA';cmd.aim=enemy.position.slice();cmd.reason='attack';}
 return remember(bot,cmd);
}
function remember(bot,cmd){bot.decision=cmd;return cmd;}
const API={MODES,create,observe,visible,decide};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanDuelBot=API;
})(typeof globalThis!=='undefined'?globalThis:this);
