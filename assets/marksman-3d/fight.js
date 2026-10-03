/* Seekable 20-second art choreography. No game damage or balance calculations. */
(function(scope){'use strict';
const DURATION=20;
const SCHEDULE=[[1,'AA'],[2.3,'Q'],[3.7,'AA'],[5,'W'],[6.4,'AA'],[7.8,'E'],[9.2,'AA'],[10.5,'P'],[11.8,'AA'],[13.1,'R'],[16.5,'Q'],[18.1,'AA']];
const PATH=[[0,-3.3,-.5],[1,-2.3,0],[3,-2.5,-.65],[5,-2.1,.75],[7,-2.8,.3],[9,-1.8,-.65],[11,-2.2,.45],[13,-2.4,0],[16,-2.4,0],[18,-1.9,.55],[20,-2.5,0]];
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function position(time,side){const t=clamp(time,0,DURATION);let i=0;while(i<PATH.length-2&&t>PATH[i+1][0])i++;const a=PATH[i],b=PATH[i+1],u=clamp((t-a[0])/(b[0]-a[0]),0,1),s=u*u*(3-2*u);return[(a[1]+(b[1]-a[1])*s)*side,0,(a[2]+(b[2]-a[2])*s)*side];}
function clipDuration(p,slot){return slot==='AA'?p.attack.study_duration:slot==='P'?p.passive.study_duration:p.skills[slot].study_duration;}
function actor(profiles,name,time,side){const p=profiles[name];if(!p)throw Error('Unknown champion: '+name);const pos=position(time,side),other=position(time,-side),events=SCHEDULE.map(([start,slot],index)=>({start:start+(side===-1?.55:0),slot,index,duration:clipDuration(p,slot)})),active=events.find(e=>time>=e.start&&time<e.start+e.duration),prior=position(Math.max(0,time-.03),side),motion=Math.hypot(pos[0]-prior[0],pos[2]-prior[2])/.03,action=active?.slot||(motion>.025?'Walk':'Idle');
 const effects=events.filter(e=>time>=e.start&&time<e.start+e.duration).map(e=>({slot:e.slot,progress:clamp((time-e.start)/e.duration,0,1),age:time-e.start,seed:100+e.index+side*31,release:.35}));
 const impacts=events.filter(e=>!['P','E','W'].includes(e.slot)).map(e=>({action:e.slot,age:time-e.start-e.duration*.72,seed:200+e.index})).filter(e=>e.age>=0&&e.age<.55);
 return{champion:name,position:pos,action,progress:active?clamp((time-active.start)/active.duration,0,1):(time%1.2)/1.2,speed:action==='Walk'?clamp(motion,0,1):0,gaitPhase:time/1.2*Math.PI*2,loopDuration:action==='Walk'?1.2:action==='Idle'?3:0,effects,impacts};}
function frame(profiles,heroName,opponentName,time,{particles=true}={}){if(!Number.isFinite(time))throw Error('Fight time must be finite');time=clamp(time,0,DURATION);const hero=actor(profiles,heroName,time,1),opponent=actor(profiles,opponentName,time,-1);if(!particles){hero.effects=[];hero.impacts=[];opponent.effects=[];opponent.impacts=[];}return{champion:heroName,time,hero:hero.position,target:opponent.position,action:hero.action,progress:hero.progress,speed:hero.speed,gaitPhase:hero.gaitPhase,loopDuration:hero.loopDuration,effects:hero.effects,impacts:hero.impacts,opponent,showTarget:false,showRange:false,demo:true};}
const API={DURATION,SCHEDULE,frame};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanFight=API;
})(typeof globalThis!=='undefined'?globalThis:this);
