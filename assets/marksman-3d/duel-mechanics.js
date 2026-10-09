/* Ezreal/Jinx pilot. All numbers are exported from repository evidence/Kit into practice.duel.
 * Other champions retain their base-kit sandbox, but can receive crowd control from the pilot. */
(function(scope){'use strict';
const node=typeof module!=='undefined'&&module.exports,P=node?require('./practice.js'):scope.MarksmanPractice;
const config=s=>s.profile.practice.duel,rank=(s,slot)=>(s.ranks[slot]||1)-1;
function init(s){const c=config(s),i=s.level-1;s.combat={weapon:'minigun',stacks:0,stackUntil:0,carry:false,rootUntil:0,slowUntil:0,slow:0,excitedUntil:0};
 if(c)s.resource={mana:c.resources.mana[i]||0,max:c.resources.mana[i]||0,manaRegen:c.resources.mana_regen_per_5s[i]/5,hpRegen:c.resources.hp_regen_per_5s[i]/5};}
function other(s){if(s.duel.hitVictim)return s.duel.hitVictim.actor||null;return s.duel.player===s?s.duel.enemy:s.duel.player;}
function cost(s,slot){const c=config(s);return !c?0:slot==='AA'?(s.profile.name==='Jinx'&&s.combat.weapon==='rockets'?c.costs.Q[rank(s,'Q')]:0):slot==='P'?0:s.profile.name==='Jinx'&&slot==='Q'?0:c.costs[slot]?.[rank(s,slot)];}
function canCast(s,slot,commit=false){if(s.combat?.rootUntil>s.time&&s.movements[s.profile.name]?.[slot])return false;const c=config(s);if(!c)return true;
 if(slot==='AA'&&s.combat.weapon==='rockets'&&s.resource.mana<cost(s,slot)){if(!commit)return true;s.combat.weapon='minigun';s.combat.carry=false;}
 const value=cost(s,slot);return Number.isFinite(value)&&s.resource.mana+1e-9>=value;}
function specialCast(s,slot){if(s.profile.name!=='Jinx'||!config(s)||slot!=='Q')return null;if(s.events.some(e=>s.time>=e.start&&s.time<e.lockEnd))return false;
 s.combat.weapon=s.combat.weapon==='minigun'?'rockets':'minigun';s.combat.carry=s.combat.weapon==='rockets'&&s.combat.stacks>0;
 s.deadlines.Q=s.time+s.profile.practice.slots.Q.cooldown[rank(s,'Q')];s.log.push({t:s.time,slot:'Q',text:s.combat.weapon});if(s.log.length>40)s.log.shift();return true;}
function bonusAS(s,t){const c=config(s),b=s.combat;if(!c||!b)return 0;
 if(s.profile.name!=='Ezreal'&&s.profile.name!=='Jinx')return 0;
 if(s.profile.name==='Ezreal')return c.passive_as[b.stacks];
 const stack=b.stacks,row=c.minigun[rank(s,'Q')];return(s.ranks.Q&&(b.weapon==='minigun'||b.carry)?row.as[stack]:0)+(t<b.excitedUntil?c.excited_as:0);}
function rangeBonus(s){if(s.profile.name==='Caitlyn'&&s.dummy?.netUntil>s.time)return s.profile.practice.levels.range[s.level-1];return config(s)&&s.profile.name==='Jinx'&&s.combat.weapon==='rockets'&&s.ranks.Q?config(s).minigun[rank(s,'Q')].range:0;}
function moveMultiplier(s){const b=s.combat;if(!b)return 1;if(s.time<b.rootUntil)return 0;const excited=config(s)&&s.time<b.excitedUntil?config(s).excited_ms*(b.excitedUntil-s.time)/config(s).excited_duration:0;return(1+excited)*(s.time<b.slowUntil?1-b.slow:1);}
function attackDamage(s,raw){return config(s)&&s.profile.name==='Jinx'&&s.combat.weapon==='rockets'?{...raw,physical:raw.physical*config(s).rocket_multiplier}:raw;}
function rescaleAttack(s,before){const after=P.stats(s).as;if(before>0&&after>0&&(s.deadlines.AA||0)>s.time)s.deadlines.AA=s.time+(s.deadlines.AA-s.time)*before/after;}
function onCast(s,e){const c=config(s);if(!c)return;if(s.profile.name==='Lucian'&&e.slot!=='AA')s.combat.lightslingerUntil=s.time+3.5;e.manaSpent=cost(s,e.slot);s.resource.mana=Math.max(0,s.resource.mana-e.manaSpent);const hits=s.hits.filter(h=>h.event===e);if(s.profile.name==='Lucian'&&e.slot==='AA'&&s.time<s.combat.lightslingerUntil){s.combat.lightslingerUntil=0;for(const h of hits)h.lightslingerFirst=true;}
 if(e.slot==='AA'&&s.profile.name==='Jinx'){e.weapon=s.combat.weapon;if(e.weapon==='rockets'){e.empowered='rocket';e.colorSlot='Q';}const speed=e.weapon==='rockets'?c.rocket_speed:c.minigun_speed;e.arrive=e.launch+Math.hypot(s.target[0]-e.hero[0],s.target[2]-e.hero[2])*100/speed;for(const h of hits)h.at=e.arrive;e.fxEnd=Math.max(e.fxEnd,e.arrive+.35);}
 if(s.profile.name==='Ezreal'&&e.slot==='E'){e.launch=Math.max(e.launch,e.dashEnd||e.launch);e.boltOrigin=e.landing.slice();for(const h of hits){h.bolt=true;h.acquired=false;h.at=e.launch+1;}e.arrive=e.launch+1;e.fxEnd=Math.max(e.fxEnd,e.arrive+.35);}
 if(s.profile.name==='Jinx'&&e.slot==='E'){e.trap=true;e.target=e.indicator.endpoint.slice();const dx=e.target[0]-e.hero[0],dz=e.target[2]-e.hero[2],len=Math.hypot(dx,dz)||1;e.traps=[-1,0,1].map(i=>[e.target[0]-dz/len*i*.5,0,e.target[2]+dx/len*i*.5]);e.hit=false;e.arrive=e.start+c.trap_arm;e.fxEnd=e.start+c.trap_duration+.35;for(const h of hits){h.trap=true;h.arm=e.arrive;h.at=e.start+c.trap_duration;}}
 if(s.profile.name==='Jinx'&&e.slot==='R')for(const h of hits){delete h.skip;h.execute=true;h.raw={physical:0};}
}
function onCancel(s,e){if(s.resource&&e.slot==='AA'&&s.time<e.launch)s.resource.mana=Math.min(s.resource.max,s.resource.mana+(e.manaSpent||0));}
function beforeHit(s,h){const c=config(s);rosterHit(s,h);if(h.execute){const i=rank(s,'R'),flight=Math.max(0,s.time-h.event.launch),scale=1+9*Math.min(1,flight);h.raw={physical:(c.execute_base[i]+c.execute_bonus_ad*P.stats(s).bonusAD)*scale+c.execute_missing[i]*(s.dummy.max-s.dummy.hp)};}}
function rosterHit(s,h){if(h.rosterResolved)return;h.rosterResolved=true;const d=s.dummy,b=s.combat,name=s.profile.name,ap=s.loadout?.stats.ability_power||0;
 if(name==='Caitlyn'&&h.attack){b.headshots=(b.headshots||0)+1;if(b.headshots>=6||d.netUntil>s.time){h.raw={...h.raw,physical:(h.raw.physical||0)+.6*P.stats(s).ad};b.headshots=0;d.netUntil=0;}}
 if(name==='Caitlyn'&&h.slot==='E'){d.netUntil=s.time+4;const target=other(s);if(target){target.combat.slow=.5;target.combat.slowUntil=s.time+1;}}
 if(name==='Vayne'&&s.ranks.W&&(h.attack||h.slot==='E')){d.silver=(d.silverUntil>s.time?d.silver:0)+1;d.silverUntil=s.time+3.5;if(d.silver>=3){d.silver=0;h.raw={...h.raw,true:(h.raw.true||0)+Math.max([50,65,80,95][rank(s,'W')],d.max*[.06,.07,.08,.09][rank(s,'W')])};}}
 if(name==="Kai'Sa"&&(h.attack||h.slot==='W')){d.plasma=(d.plasmaUntil>s.time?d.plasma:0)+(h.attack?1:2);d.plasmaUntil=s.time+4;const extra=h.attack?5+.12*ap+Math.max(0,d.plasma-1)*(2+.02*ap):0;h.raw={...h.raw,magic:(h.raw.magic||0)+extra};if(d.plasma>=5){h.raw.magic+=(.15+.00025*ap)*Math.max(0,d.max-d.hp);d.plasma=0;}}
 if(name==='Ashe'){const target=other(s);if(target){target.combat.slow=h.slot==='W'?.4:.2;target.combat.slowUntil=s.time+2;}}
 if(name==='Corki'&&h.attack)h.raw={...h.raw,true:(h.raw.true||0)+.16*(h.raw.physical||0)};
}
function onHit(s,h,flux){const c=config(s);if(!c)return;if(s.profile.name==='Lucian'&&h.attack&&(h.lightslingerFirst||h.lightslingerSecond)){s.deadlines.E=Math.max(s.time,(s.deadlines.E||0)-(s.duel.hitVictim?.kind==='champion'?2:1));if(h.lightslingerFirst)s.hits.push({...h,done:false,at:s.time+.05,event:{...h.event,projectile:(h.victim?.position||s.target).slice(),launch:s.time+.05},lightslingerFirst:false,lightslingerSecond:true,raw:{...h.raw,physical:h.raw.physical*(s.duel.hitVictim?.kind==='minion'?1:.4)}});}if(s.profile.name==="Kai'Sa"&&h.attack)s.deadlines.E=Math.max(s.time,(s.deadlines.E||0)-.5);const b=s.combat,before=P.stats(s).as;
 if(s.profile.name==='Ezreal'){
  if(!h.attack&&!h.mark){b.stacks=Math.min(4,b.stacks+1);b.stackUntil=s.time+c.passive_duration;}
  if(h.slot==='Q')for(const slot of['Q','W','E','R'])s.deadlines[slot]=Math.max(s.time,(s.deadlines[slot]||0)-c.q_refund);
  if(flux&&!h.attack)s.resource.mana=Math.min(s.resource.max,s.resource.mana+c.flux_refund[rank(s,'W')]);
 }else if(s.profile.name==='Jinx'){
  if(h.attack&&h.event.weapon==='minigun'&&s.ranks.Q){b.stacks=Math.min(3,b.stacks+1);b.stackUntil=s.time+c.stack_duration;}
  const target=other(s);if(h.slot==='W'&&target){target.combat.slow=c.slow[rank(s,'W')];target.combat.slowUntil=s.time+c.slow_duration;}
  if(h.trap&&target){target.combat.rootUntil=s.time+c.root[rank(s,'E')];target.destination=target.hero.slice();target.queued=null;
   for(const e of target.events)if(e.motion&&e.motion.kind!=='blink'&&!e.landed&&target.time<e.lockEnd){e.landed=true;e.lockEnd=target.time;e.animEnd=target.time;}}
 }rescaleAttack(s,before);
}
function takedown(s,victim){const c=config(s);if(s.profile.name!=='Jinx'||!c||!['champion','tower','epic'].includes(victim.kind)||s.time-(victim.health.contributors?.[s.side]??-Infinity)>3)return;s.combat.excitedUntil=s.time+c.excited_duration;s.resource.mana=Math.min(s.resource.max,s.resource.mana+(s.resource.max-s.resource.mana)*c.excited_mana);}
function step(s,dt){const c=config(s);if(!c)return;const b=s.combat,before=P.stats(s).as;
 if(s.profile.name==='Jinx'){while(b.stacks&&s.time>=b.stackUntil){b.stacks--;b.stackUntil+=c.stack_decay;}for(const e of s.events)if(e.slot==='AA'&&e.weapon==='rockets'&&!e.released&&s.time+dt>=e.launch){e.released=true;b.carry=false;}}
 else if(s.profile.name==='Ezreal'&&s.time>=b.stackUntil)b.stacks=0;
 rescaleAttack(s,before);if(s.health.hp>0){s.resource.mana=Math.min(s.resource.max,s.resource.mana+s.resource.manaRegen*dt);s.health.hp=Math.min(s.health.max,s.health.hp+s.resource.hpRegen*dt);}}
function snapshot(s){const b=s.combat||{},out=[];if(config(s)){out.push({slot:'Mana',label:`MANA ${Math.floor(s.resource.mana)} / ${Math.floor(s.resource.max)}`});if(s.profile.name==='Jinx')out.push({slot:'Weapon',label:b.weapon.toUpperCase()});if(b.stacks)out.push({slot:'P',label:`${s.profile.name==='Ezreal'?'SPELL FORCE':'MINIGUN'} ${b.stacks}`});if(b.excitedUntil>s.time)out.push({slot:'P',label:'GET EXCITED'});}
 if(b.rootUntil>s.time)out.push({slot:'Root',label:`ROOT ${(b.rootUntil-s.time).toFixed(1)}s`});if(b.slowUntil>s.time)out.push({slot:'Slow',label:`SLOW ${Math.round(b.slow*100)}%`});return out;}
const API={init,cost,canCast,specialCast,bonusAS,rangeBonus,moveMultiplier,attackDamage,onCast,onCancel,beforeHit,onHit,takedown,step,snapshot};if(node)module.exports=API;else scope.MarksmanDuelMechanics=API;
})(typeof globalThis!=='undefined'?globalThis:this);
