// Pure trace readers. Never simulate damage, movement or ability decisions.
const ReplayState={
 stackSnapshot(events,time,order=Infinity){
  const hit=this.lastAt(events.filter(e=>e.phase==='impact'&&e.after),time,order);
  if(!hit)return null;
  const state=hit.after,values=[];
  for(const key of ['conqueror','lethal_tempo','style'])if(typeof state[key]==='number'&&state[key]>0)values.push([key.replaceAll('_',' '),state[key]]);
  for(const [key,value] of Object.entries(state.items||{}))if(typeof value==='number'&&value>0)values.push([key.replaceAll('_',' '),value]);
  return {time:hit.time,values};
 },
 lastAt(events,time,order=Infinity){let lo=0,hi=events.length;while(lo<hi){const m=(lo+hi)>>1,e=events[m];if(e.time<time-1e-9||(e.time<=time+1e-9&&(e.order??0)<=order))lo=m+1;else hi=m;}return lo>0?events[lo-1]:null;},
 visible(event,time,order=Infinity){return event.time<time-1e-9||(event.time<=time+1e-9&&(event.order??0)<=order);},
 markActive(casts,events,time,order=Infinity){const cast=[...casts].reverse().find(e=>e.impact_time<=time&&this.visible(e,time,order));return !!cast&&time<cast.impact_time+4&&!events.some(e=>e.action==='W detonation'&&e.time>=cast.impact_time&&this.visible(e,time,order));}
};
if(typeof module!=='undefined')module.exports=ReplayState;
