/* Recorded-trace adapter. No simulation, damage calculation or invented events. */
(async()=>{'use strict';
 const profiles=window.MarksmanArtProfiles;if(!profiles?.[D.champion])return;
 const stage=document.createElement('div');stage.id='stage3d';canvas.before(stage);
 const tools=document.createElement('div');tools.className='replay-tools';tools.innerHTML='<div class="camera-modes"><button data-camera="duel" class="active">Duel</button><button data-camera="tactical">Tactical</button><button data-camera="follow">Follow</button><button id="cameraReset">Reset camera</button></div><div><label><input id="range3d" type="checkbox" checked> AA range</label><label><input id="path3d" type="checkbox"> Movement trail</label><button id="focusView">Focus view</button><button id="loopReplay" aria-pressed="false">Loop OFF</button></div>';stage.before(tools);
 $('focusView').onclick=()=>{const on=document.querySelector('.wrap').classList.toggle('cinema');$('focusView').textContent=on?'Exit focus':'Focus view';};
 $('loopReplay').onclick=()=>{window.replayLoop=!window.replayLoop;$('loopReplay').textContent=window.replayLoop?'Loop ON':'Loop OFF';$('loopReplay').setAttribute('aria-pressed',String(window.replayLoop));};
 let scene=null;
 function fallback(){canvas.style.display='block';stage.style.display='none';tools.style.display='none';window.render3d=null;scene?.dispose();}
 try{
 scene=await MarksmanScene.createScene(stage,profiles,window.MarksmanReplaySceneOptions||{});canvas.style.display='none';
 const banner=document.createElement('div');banner.className='action-banner';stage.append(banner);const skillHud=document.createElement('div');skillHud.className='skill-hud';for(const slot of ['Q','W','E','R']){const cell=document.createElement('div'),label=document.createElement('b'),value=document.createElement('span');label.textContent=slot;cell.append(label,value);cell.dataset.slot=slot;skillHud.append(cell);}stage.append(skillHud);
 tools.querySelectorAll('[data-camera]').forEach(b=>b.onclick=()=>{scene.setCamera(b.dataset.camera);tools.querySelectorAll('[data-camera]').forEach(x=>x.classList.toggle('active',x===b));});$('cameraReset').onclick=()=>scene.resetCamera();
 const commands=D.attacks.filter(e=>['attack','cast'].includes(e.kind)),impacts=D.events.filter(e=>e.phase==='impact');
 // Instant self buffs have no cast time in the engine: they never take over the hero's pose.
 // Their aura lasts the recorded buff window, and basic attacks launched inside it look empowered.
 const skillSpec=slot=>profiles[D.champion].skills[slot],isInstant=slot=>skillSpec(slot)?.cast==='instant',animated=commands.filter(c=>!(c.kind==='cast'&&isInstant(c.action)));
 const buffWindows=(D.buff_windows||[]).filter(b=>isInstant(b.action));
 const boostAt=time=>{const b=buffWindows.filter(w=>time>=w.start&&time<w.end&&skillSpec(w.action).empowered_attack).at(-1);return b?{empowered:skillSpec(b.action).empowered_attack,colorSlot:b.action}:{};};
 const at=t=>{const p=pos(t),angle=D.champion==='Samira'?0:Math.asin(Math.sin((p.kite_arc||0)/Math.max(1,p.attack_range||550)*3))/3;return[-p.distance/100*Math.cos(angle),0,p.distance/100*Math.sin(angle)];};
 window.render3d=t=>{
  const order=selected>=0?D.events[selected].order:Infinity,visible=e=>ReplayState.visible(e,t,order),p=pos(t),hero=at(t),before=at(Math.max(0,t-.03)),after=at(Math.min(D.duration,t+.03));
  const moving=Math.hypot(after[0]-before[0],after[2]-before[2])>.004;
  let command=ReplayState.lastAt(animated,t,order);
  let animationWindow=command?(D.animation_windows||[]).find(w=>w.order===command.order):null;
  let finish=command?Math.max(animationWindow?.end??command.windup_end??command.cast_end??command.time,animationWindow?.channel_end??command.time):0;
  if(!command||t>finish+.16){const channelCommand=animated.filter(c=>visible(c)&&(D.animation_windows||[]).some(w=>w.order===c.order&&w.channel_end>t)).at(-1);if(channelCommand){command=channelCommand;animationWindow=D.animation_windows.find(w=>w.order===command.order);finish=animationWindow.channel_end;}}
  const active=command&&t>=command.time&&t<=finish,span=command?Math.max(.001,finish-command.time):1;
  // Cast anticipation reaches release at the recorded end. Channels retain the
  // pose across their recorded window. Recovery is visual only and gives way to
  // the next command; it never creates locks or postpones an engine hit.
  const channel=command&&(animationWindow?.channel_end??command.time)>command.time;
  const recovery=command&&!active&&t-finish<.16;
  const action=active||recovery?command.action:moving?'Walk':'Idle';
  const progress=active?(channel?.28+.4*(t-command.time)/span:.5*(t-command.time)/span):recovery?.5+.5*(t-finish)/.16:0;
  const effects=[];
  if(active&&profiles[D.champion].skills[command.action])effects.push({slot:command.action,progress:channel?.35+.34*(t-command.time)/span:.5*(t-command.time)/span,age:t-command.time,release:.35,impact:false,seed:command.order});
  for(const f of D.visual_flights||[]){if(t<f.launch||t>f.impact||!visible({time:f.time??f.launch,order:f.order??0}))continue;if(t===f.launch&&selected>=0&&order<(f.launch_order??f.order??0))continue;
   const flightSpan=f.impact-f.launch;if(flightSpan<=0)continue;
   // Launched from the weapon's muzzle socket in the pose at release, flying the recorded travel time.
   effects.push({slot:f.action,progress:.35+.39*(t-f.launch)/flightSpan,age:t-f.launch,launchTime:f.launch,launchHero:at(f.launch),launchTarget:[0,0,0],release:.35,impact:false,seed:f.order??1,...(f.action==='AA'?boostAt(f.launch):{})});
  }
  // Non-projectile casts receive their signature utility visual on the recorded
  // command, never a synthetic hit. Persistent game duration is not inferred.
  for(const b of buffWindows)if(visible({time:b.start,order:b.order??0})&&t>=b.start&&t<b.end)effects.push({slot:b.action,progress:.5,age:t-b.start,persistent:true,impact:false,seed:b.order??1});
  if(command&&visible(command)&&!active&&!channel&&t-finish>=0&&t-finish<.35&&!D.visual_flights.some(f=>f.order===command.order)&&profiles[D.champion].skills[command.action])effects.push({slot:command.action,progress:.35+.39*(t-finish)/.35,age:t-command.time,impact:false,seed:command.order});
  if(D.champion==='Ezreal'&&ReplayState.markActive(commands.filter(e=>e.action==='W'),impacts,t,order))effects.push({slot:'W',progress:.8,age:t,source:[0,1.12,0],target:[0,1.12,0],seed:1,impact:false});
  const recent=impacts.filter(e=>visible(e)&&t-e.time>=0&&t-e.time<.9&&e.damage>0).map(e=>({action:e.action,age:t-e.time,damage:e.damage,seed:e.order,...(e.action.startsWith('AA')?boostAt(e.time):{})})),hit=ReplayState.lastAt(impacts,t,order),resource=ReplayState.lastAt(D.events.filter(e=>e.mana_after!==undefined||e.mana!==undefined),t,order);
  const cd=ReplayState.lastAt(D.events.filter(e=>e.cooldowns),t,order);banner.textContent=active?action+' · '+(channel?'CHANNEL':'CAST / WINDUP')+' · '+Math.max(0,finish-t).toFixed(2)+'s':moving?'REPOSITIONING':'READY';banner.dataset.action=action;for(const cell of skillHud.children){const remaining=Math.max(0,(cd?.cooldowns?.[cell.dataset.slot]??0)-(t-(cd?.time??t)));cell.classList.toggle('cooling',remaining>0);cell.classList.toggle('casting',active&&action===cell.dataset.slot);cell.querySelector('span').textContent=remaining>0?remaining.toFixed(1)+'s':'READY';}
  const trail=$('path3d').checked?Array.from({length:17},(_,i)=>{const v=at(Math.max(0,t-1.6+i*.1));v[1]=.06;return v;}):[];
  scene.render({champion:D.champion,time:t,hero,target:[0,0,0],action,progress,weight:active?MarksmanRig.smooth((t-command.time)/Math.max(.03,span*.18)):recovery?1-(t-finish)/.16:0,speed:moving?1:0,gaitPhase:(p.kite_arc||0)/18+p.distance/22,showRange:$('range3d').checked,range:p.attack_range,trail,effects,impacts:recent,stats:{hp:hit?.hp_after??D.max_hp,max_hp:D.max_hp,target:D.target.split(' • ').pop(),mana:resource?.mana_after??resource?.mana}});
 };
 stage.addEventListener('artcontextlost',fallback);window.addEventListener('pagehide',()=>scene?.dispose(),{once:true});window.render3d(now);
 }catch(error){fallback();console.warn('Marksman 3D unavailable; showing trace canvas',error);}
})();
