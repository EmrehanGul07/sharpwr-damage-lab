/* Practice Tool: walk around with any champion, cast every skill and hit a training dummy, and keep
   notes on how each champion differs from Wild Rift. Shared by the web page and the phone app.
   Needs MarksmanScene, MarksmanPractice, MarksmanFight (movement table) and MarksmanGeometry. */
(function(scope){'use strict';
const SLOTS=['AA','P','Q','W','E','R'],NOTE_FIELDS=['General','AA','P','Q','W','E','R'],NOTES_KEY='sharpwr.practiceNotes';
const AIM_PIXELS=90,CAMERA_YAW=-.78;
function el(tag,attrs={},...children){const node=document.createElement(tag);for(const[k,v]of Object.entries(attrs)){if(v==null||v===false)continue;if(k.startsWith('on'))node.addEventListener(k.slice(2),v);else if(k==='class')node.className=v;else if(k==='text')node.textContent=v;else node.setAttribute(k,v===true?'':v);}for(const c of children.flat())if(c!=null)node.append(c);return node;}
function capture(node,e){try{node.setPointerCapture(e.pointerId);}catch{}}
function localStore(){return{get(key){try{return localStorage.getItem(key);}catch{return null;}},set(key,value){try{localStorage.setItem(key,value);return true;}catch{return false;}}};}

// ---------------------------------------------------------------- notes (kept on this device)
function loadNotes(store){try{const data=JSON.parse(store.get(NOTES_KEY)||'{}');return data&&typeof data==='object'&&data.champions?data:{version:1,champions:{}};}catch{return{version:1,champions:{}};}}
function noteText(entry){return NOTE_FIELDS.some(f=>(entry?.[f]||'').trim());}
function notesMarkdown(notes,catalogue,date=new Date()){const names=Object.keys(catalogue.champions),done=names.filter(n=>notes.champions[n]?.tested).length,lines=['# SharpWR Practice Tool notes','',`Exported ${date.toISOString().slice(0,10)} · ${done}/${names.length} champions tested`,''];
 for(const name of names){const entry=notes.champions[name];if(!entry||!(entry.tested||noteText(entry)))continue;lines.push(`## ${name}${entry.tested?' (tested)':''}`,'');const abilities=catalogue.champions[name].hud?.abilities||{};
  for(const field of NOTE_FIELDS){const text=(entry[field]||'').trim();if(!text)continue;const label=field==='General'?'General':field==='AA'?'Basic attack':`${field} · ${abilities[field]?.name||field}`;lines.push(`- **${label}:** ${text.replace(/\n+/g,' / ')}`);}lines.push('');}
 return lines.join('\n');}
async function copyText(text){try{await navigator.clipboard.writeText(text);return true;}catch{const area=el('textarea',{style:'position:fixed;opacity:0'});area.value=text;document.body.append(area);area.select();let ok=false;try{ok=document.execCommand('copy');}catch{}area.remove();return ok;}}

// ---------------------------------------------------------------- what the tool simulates, per champion
function travelSpeed(travel){if(!travel)return null;const seconds=travel[4];return seconds>0?Math.round(1000/seconds):null;}
function slotSummary(profile,slot,ranks){const rank=ranks[slot]||1,s=profile.practice.slots[slot],name=profile.hud?.abilities?.[slot]?.name||slot,cd=s.cooldown?.[Math.max(0,rank-1)],speed=travelSpeed(s.travel),parts=[];
 if(profile.skills[slot]?.cast==='instant')parts.push('instant');else parts.push(`cast ${s.cast.toFixed(2)} s`);
 if(speed)parts.push(`projectile ${speed} u/s`);if(Number.isFinite(cd))parts.push(`cooldown ${cd} s`);if(s.channel)parts.push(`channel ${s.channel.seconds} s`);
 const mode=s.mode==='hit'?'damage number on hit':s.mode==='mark'?`mark, detonated by your next hit within ${s.window} s`:s.mode==='attack'?(s.attacks==='buff'?'adds its damage to attacks during the buff':'adds its damage to your next attack'):s.mode==='none'?'no direct damage':`hit shown without a number (${s.reason})`;
 let buff='';if(s.buff){const i=Math.max(0,(ranks[s.buff.by]||1)-1),bits=[];if(s.buff.as)bits.push(`+${Math.round(s.buff.as[Math.min(i,s.buff.as.length-1)]*100)}% attack speed`);if(s.buff.ad)bits.push(`+${s.buff.ad[Math.min(i,s.buff.ad.length-1)]} AD`);if(s.buff.range)bits.push(`+${s.buff.range[Math.min(i,s.buff.range.length-1)]} range`);buff=` · ${bits.join(', ')} for ${s.buff.duration[Math.min(i,s.buff.duration.length-1)]} s`;}
 return{title:`${slot} · ${name}`,text:parts.join(' · ')+' · '+mode+buff};}

// ---------------------------------------------------------------- mount
async function mount(root,{catalogue,champion='Ezreal',storage=localStore(),quality=null,sceneOptions={},allowDownload=true,compact=false,nativeFullscreen=true,orientation=null}={}){
 const P=catalogue.champions,Practice=scope.MarksmanPractice,Fight=scope.MarksmanFight,names=Object.keys(P);
 if(!P[champion])champion=names[0];
 let state=null,duel=null,duelRunning=false,active=false,started=false,entering=false,scene=null,raf=0,last=0,disposed=false,joystick=null,attackPointer=null,aiming=null,placing=false,cursor=null,keys=new Set(),notes=loadNotes(storage),preset='Squishy • Jinx',lastLog=null,lastSummary='';
 const audio=scope.MarksmanEffects.createCombatAudio();
 let farmPointer=null;
 let attackDrag=null;
 const profileOf=name=>({...P[name],name});
 const inputYaw=()=>CAMERA_YAW;
 const screenDelta=(dx,dy)=>wrap.dataset.rotated==='true'?[dy,-dx]:[dx,dy];
 function begin(){if(!active||entering||disposed||duel?.finished)return false;audio.unlock();if(!started){started=true;duelRunning=true;last=0;wrap.dataset.phase='playing';}return true;}
 // ---- layout
 const stage=el('div',{class:'pt-stage','aria-label':'Practice arena'});
 const status=el('div',{class:'pt-loading',text:'Loading the arena…'});stage.append(status);
 const statsLine=el('div',{class:'pt-stats'}),buffLine=el('div',{class:'pt-buffs'}),combo=el('div',{class:'pt-combo'});
 const stick=el('div',{class:'pt-joystick',role:'button','aria-label':'Movement joystick',tabindex:'0'},el('i'));
 const hud=el('div',{class:'pt-hud',role:'group','aria-label':'Attack and skills'});
 const focusButton=el('button',{class:'pt-focus',type:'button',text:'✕ Exit practice','aria-label':'Exit practice','aria-pressed':'false'});
 const restartButton=el('button',{class:'pt-restart',type:'button',text:'↻ Restart','aria-label':'Restart practice'});
 const finishButton=el('button',{class:'pt-finish',type:'button',text:'Finish session','aria-label':'Finish training session'}),report=el('section',{class:'pt-results','aria-label':'Training results',hidden:true}),farmButton=el('button',{class:'pt-skill','data-slot':'Farm',type:'button',text:'Farm','aria-label':'Farm minions or attack tower',hidden:true});hud.append(farmButton);
 const clearTargetButton=el('button',{class:'pt-target-clear',type:'button',text:'Clear target','aria-label':'Clear target lock',hidden:true});clearTargetButton.addEventListener('click',()=>{if(duel)scope.MarksmanDuel.lockTarget(duel,state,null);});
 const readyHint=el('div',{class:'pt-ready-hint',text:'Touch the joystick or a skill to begin'});
 const previewLabel=el('div',{class:'pt-preview-label',text:'DRAGON LANE · ARENA PREVIEW'});
 const wrap=el('div',{class:'pt-stage-wrap','data-phase':'preview'},stage,el('div',{class:'pt-overlay-top'},statsLine,buffLine),combo,stick,hud,focusButton,restartButton,finishButton,clearTargetButton,report,readyHint,previewLabel);
 const championSelect=el('select',{'aria-label':'Champion'},names.map(n=>el('option',{value:n,text:n})));championSelect.value=champion;
 const levelSelect=el('select',{'aria-label':'Champion level'},Array.from({length:15},(_,i)=>el('option',{value:String(i+1),text:'Level '+(i+1)})));levelSelect.value='15';
 const qualitySelect=el('select',{'aria-label':'Render quality'},[['high','High quality'],['balanced','Balanced'],['low','Lightweight']].map(([v,t])=>el('option',{value:v,text:t})));qualitySelect.value=quality||(compact?'balanced':'high');
 const modeSelect=el('select',{'aria-label':'Arena mode'},[['practice','Training dummy'],['duel','1v1 bot']].map(([value,text])=>el('option',{value,text})));
 const opponentSelect=el('select',{'aria-label':'Bot champion'},names.map(n=>el('option',{value:n,text:n})));opponentSelect.value='Jinx';
 const difficultySelect=el('select',{'aria-label':'Bot difficulty'},['easy','medium','hard','impossible'].map(v=>el('option',{value:v,text:v[0].toUpperCase()+v.slice(1)})));difficultySelect.value='medium';
 const startButton=el('button',{class:'pt-start',type:'button',text:'Start Practice',disabled:true});
 const laneBox=el('input',{type:'checkbox',checked:true,'aria-label':'Minions and towers'});
 const duelSettings=el('div',{class:'pt-row pt-duel-settings'},opponentSelect,difficultySelect,el('label',{class:'pt-check'},laneBox,'Minions and towers'),el('span',{class:'pt-small',text:'Equal champion stats · prototype lane rules · gold does not change stats'}));duelSettings.hidden=true;
 const rankSelects=Object.fromEntries(['Q','W','E','R'].map(slot=>[slot,el('select',{'aria-label':slot+' rank'},Array.from({length:slot==='R'?4:5},(_,r)=>el('option',{value:String(r),text:r?slot+' '+r:slot+' –'})))]));
 const soundBox=el('input',{type:'checkbox',checked:true,'aria-label':'Combat sound'});soundBox.addEventListener('change',()=>audio.setEnabled(soundBox.checked));
 const noCd=el('input',{type:'checkbox'}),effectsBox=el('input',{type:'checkbox',checked:true}),rangeBox=el('input',{type:'checkbox'});
 const presetSelect=el('select',{'aria-label':'Dummy'},[...Object.keys(catalogue.practice_targets||{}),'Custom'].map(n=>el('option',{value:n,text:n==='Custom'?'Custom dummy':n+' (by level)'})));presetSelect.value=preset;
 const hpInput=el('input',{type:'number',min:'1',max:'99999',step:'1','aria-label':'Dummy health',inputmode:'numeric'}),armorInput=el('input',{type:'number',min:'0',max:'999',step:'1','aria-label':'Dummy armor',inputmode:'numeric'}),mrInput=el('input',{type:'number',min:'0',max:'999',step:'1','aria-label':'Dummy magic resistance',inputmode:'numeric'});
 const placeButton=el('button',{type:'button',text:'Move dummy'}),resetButton=el('button',{type:'button',text:'Reset dummy'}),resetCd=el('button',{type:'button',text:'Reset cooldowns'});
 const cameraButtons=[['rift','Rift'],['tactical','Tactical'],['portrait','Character']].map(([v,t])=>el('button',{type:'button','data-camera':v,class:v==='rift'?'active':'',text:t}));
 const controls=el('div',{class:'pt-controls'},
  el('div',{class:'pt-row'},modeSelect,championSelect,levelSelect,qualitySelect),duelSettings,
  el('div',{class:'pt-row'},el('span',{class:'pt-label',text:'Skill ranks'}),...Object.values(rankSelects),el('label',{class:'pt-check'},noCd,'No cooldowns'),resetCd),
  el('div',{class:'pt-row'},el('span',{class:'pt-label',text:'Dummy'}),presetSelect,el('label',{class:'pt-field'},'HP',hpInput),el('label',{class:'pt-field'},'Armor',armorInput),el('label',{class:'pt-field'},'MR',mrInput),resetButton,placeButton),
  el('div',{class:'pt-row'},el('span',{class:'pt-label',text:'View'}),...cameraButtons,el('label',{class:'pt-check'},effectsBox,'Effects'),el('label',{class:'pt-check'},rangeBox,'Attack range'),el('label',{class:'pt-check'},soundBox,'Combat sound')));
 const help=el('p',{class:'pt-help',text:compact?'Joystick or arrow keys to move. Tap a skill to cast it at the dummy, or drag from the skill to aim. Hold Attack to keep attacking.':'Click or tap the ground (or use the arrow keys) to move. Q W E R cast toward the mouse, or at the dummy; Space attacks (hold to keep attacking). On touch screens use the joystick and drag from a skill to aim.'});
 const logList=el('ol',{class:'pt-log'}),simulated=el('div',{class:'pt-sim'});
 const noteInputs=Object.fromEntries(NOTE_FIELDS.map(f=>[f,el('textarea',{rows:f==='General'?'3':'2','aria-label':f+' notes'})]));
 const testedBox=el('input',{type:'checkbox'}),progress=el('span',{class:'pt-progress'}),savedNote=el('span',{class:'pt-saved'});
 const exportArea=el('textarea',{class:'pt-export',rows:'10',readonly:true,'aria-label':'All notes as text'});
 const copyButton=el('button',{type:'button',text:'Copy all notes'}),downloadButton=allowDownload?el('button',{type:'button',text:'Download .md'}):null,showButton=el('button',{type:'button',text:'Show all notes'});
 const noteLabels=Object.fromEntries(NOTE_FIELDS.map(f=>[f,el('span',{class:'pt-note-label'})]));
 const notesPanel=el('section',{class:'pt-panel pt-notes'},el('h3',{text:'Your notes: differences from Wild Rift'}),
  el('div',{class:'pt-row'},el('label',{class:'pt-check'},testedBox,'Tested this champion'),progress),
  ...NOTE_FIELDS.map(f=>el('label',{class:'pt-note'},noteLabels[f],noteInputs[f])),
  el('div',{class:'pt-row'},copyButton,downloadButton,showButton,savedNote),exportArea,
  el('p',{class:'pt-small',text:'Notes are saved on this device only. Copy them to send them on.'}));
 exportArea.hidden=true;
 const panels=el('div',{class:'pt-panels'},
  el('section',{class:'pt-panel'},el('h3',{text:'Damage log'}),el('p',{class:'pt-small',text:'Newest first. Raw damage → after the dummy’s armor or magic resistance.'}),logList),
  el('section',{class:'pt-panel'},el('h3',{text:'What this practice simulates'}),simulated),notesPanel);
 root.replaceChildren(el('div',{class:'pt'+(compact?' pt-compact':'')},wrap,startButton,help,controls,panels));

 // ---- HUD buttons
 function selectFarm(){if(!duel?.lane)return false;const D=scope.MarksmanDuel,m=D.farmTarget(duel,state)||duel.lane.towers.find(t=>t.side!==state.side&&t.health.hp>0&&Math.hypot(t.position[0]-state.hero[0],t.position[2]-state.hero[2])<=Practice.stats(state).range/100+.35);return m?D.selectTarget(duel,state,m.id):false;}
 farmButton.addEventListener('pointerdown',e=>{e.stopPropagation();if(farmPointer!==null||!state||!begin())return;e.preventDefault();capture(farmButton,e);attackPointer=null;attackDrag=null;state.attackAim=null;if(duel)scope.MarksmanDuel.lockTarget(duel,state,null);farmPointer=e.pointerId;if(selectFarm())Practice.holdAttack(state,true);});
 const endFarm=e=>{e.stopPropagation();if(e.pointerId!==farmPointer)return;farmPointer=null;Practice.holdAttack(state,false);state.pending=null;if(duel)scope.MarksmanDuel.selectTarget(duel,state,'enemy');};for(const type of['pointerup','pointercancel','lostpointercapture'])farmButton.addEventListener(type,endFarm);
 finishButton.addEventListener('click',()=>{if(duel){scope.MarksmanDuel.finish(duel);clearKeys();updateHud(scope.MarksmanDuel.frame(duel,{particles:true}));}});
 const buttons={};
 for(const slot of SLOTS){const b=el('button',{type:'button',class:'pt-skill','data-slot':slot},slot==='AA'?el('span',{class:'pt-aa',text:'Attack'}):el('img',{alt:'',draggable:'false'}),el('span',{class:'pt-shade'}),el('span',{class:'pt-cd'}),slot==='AA'?null:el('span',{class:'pt-key',text:slot}));buttons[slot]=b;hud.append(b);bindSkill(b,slot);}
 function bindSkill(b,slot){
  b.addEventListener('contextmenu',e=>e.preventDefault());
  b.addEventListener('pointerdown',e=>{e.stopPropagation();if(!state||!begin()||(slot==='AA'?attackPointer!==null:!!aiming))return;e.preventDefault();capture(b,e);if(slot==='AA'){farmPointer=null;if(duel)scope.MarksmanDuel.selectTarget(duel,state,scope.MarksmanDuel.targetLock(duel,state)?.id||'enemy');attackPointer=e.pointerId;attackDrag={x:e.clientX,y:e.clientY,previous:state.lockedTarget||null};Practice.holdAttack(state,true);cast('AA');return;}aiming={slot,pointerId:e.pointerId,x:e.clientX,y:e.clientY,moved:false};Practice.aim(state,slot,state.target);});
  b.addEventListener('pointermove',e=>{e.stopPropagation();if(slot==='AA'){if(attackPointer!==e.pointerId||!attackDrag)return;const [dx,dy]=screenDelta(e.clientX-attackDrag.x,e.clientY-attackDrag.y),len=Math.hypot(dx,dy);if(len<10){state.attackAim=null;return;}state.attackAim=[(dx*Math.cos(inputYaw())+dy*Math.sin(inputYaw()))/len,0,(-dx*Math.sin(inputYaw())+dy*Math.cos(inputYaw()))/len];const scale=Math.min(1,len/AIM_PIXELS)*Practice.stats(state).range/100/len,point=[state.hero[0]+(dx*Math.cos(inputYaw())+dy*Math.sin(inputYaw()))*scale,0,state.hero[2]+(-dx*Math.sin(inputYaw())+dy*Math.cos(inputYaw()))*scale],id=duel?scope.MarksmanDuel.pickTarget(duel,state,point):null;if(id)scope.MarksmanDuel.lockTarget(duel,state,id);return;}if(!aiming||aiming.slot!==slot||aiming.pointerId!==e.pointerId)return;const [dx,dy]=screenDelta(e.clientX-aiming.x,e.clientY-aiming.y);if(Math.hypot(dx,dy)>8){aiming.moved=true;Practice.aim(state,slot,aimPoint(slot,dx,dy));}});
  const end=e=>{e.stopPropagation();if(slot==='AA'){if(attackPointer!==e.pointerId)return;if(e.type!=='pointerup'&&duel)scope.MarksmanDuel.lockTarget(duel,state,attackDrag?.previous||null);attackPointer=null;attackDrag=null;if(state){state.attackAim=null;Practice.holdAttack(state,false);}if(state?.pending?.slot==='AA')state.pending=null;return;}if(!aiming||aiming.slot!==slot||aiming.pointerId!==e.pointerId)return;const point=aiming.moved?state.aim:null;aiming=null;state.aim=null;state.aimSlot=null;if(e.type==='pointerup')cast(slot,point);};
  b.addEventListener('pointerup',end);b.addEventListener('pointercancel',end);b.addEventListener('lostpointercapture',end);
  b.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();cast(slot);}});}
 // Drag from a skill button: the drag direction on screen becomes the aim direction on the ground
 // (as on the Wild Rift HUD); AIM_PIXELS of drag reaches the skill's full range.
 function aimPoint(slot,dx,dy){const ind=Practice.aim(state,slot,state.target),range=ind.range||Practice.stats(state).range/100,len=Math.hypot(dx,dy),scale=Math.min(1,len/AIM_PIXELS)*range/(len||1),wx=(dx*Math.cos(inputYaw())+dy*Math.sin(inputYaw()))*scale,wz=(-dx*Math.sin(inputYaw())+dy*Math.cos(inputYaw()))*scale;return[state.hero[0]+wx,0,state.hero[2]+wz];}
 function cast(slot,point){if(!state||!begin()||duel&&slot==='P')return;if(duel&&(slot!=='AA'||farmPointer===null))scope.MarksmanDuel.selectTarget(duel,state,scope.MarksmanDuel.targetLock(duel,state)?.id||'enemy');Practice.cast(state,slot,point||undefined);}

 // ---- champion / settings
 function dummyValues(){if(presetSelect.value==='Custom')return null;const row=catalogue.practice_targets[presetSelect.value][state.level-1];return{hp:Math.round(row.hp),armor:Math.round(row.armor),mr:Math.round(row.mr),aaReduction:row.aa_reduction||0,label:presetSelect.value.split(' • ')[0]+' dummy'};}
 function applyDummy(){const v=dummyValues();if(v){Practice.setDummy(state,v);hpInput.value=v.hp;armorInput.value=v.armor;mrInput.value=v.mr;}else Practice.setDummy(state,{hp:clampNumber(hpInput.value,1,99999,2000),armor:clampNumber(armorInput.value,0,999,0),mr:clampNumber(mrInput.value,0,999,0),aaReduction:0,label:'Custom dummy'});}
 function clampNumber(v,a,b,fallback){const n=Number(v);return Number.isFinite(n)?Math.max(a,Math.min(b,n)):fallback;}
 // Hero and dummy start a few steps apart; on a portrait screen the dummy stands "up" the screen.
 function startPositions(){return{hero:[-3,0,0],target:[3,0,0]};}
 function selectChampion(name){lastLog=undefined;lastSummary='';champion=name;const keep=state?{hero:state.hero.slice(),target:state.target.slice()}:startPositions();keep.hero[1]=0;state=Practice.create(profileOf(name),{movements:Fight.MOVEMENT,autoApproach:false});state.arena=scope.MarksmanArena.navigation;state.hero=state.arena.project(keep.hero);state.destination=state.hero.slice();state.target=state.arena.project(keep.target);Practice.setLevel(state,Number(levelSelect.value));state.noCooldowns=noCd.checked;if(modeSelect.value==='duel')prepareDuel();else{duel=null;applyDummy();}syncRanks();refreshIcons();refreshSimulated();loadChampionNotes();}
 function prepareDuel(){duel=scope.MarksmanDuel.create(profileOf(champion),profileOf(opponentSelect.value),{level:Number(levelSelect.value),difficulty:difficultySelect.value,movements:Fight.MOVEMENT,arena:scope.MarksmanArena.navigation,lane:laneBox.checked,seed:1});state=duel.player;state.autoApproach=false;attackPointer=null;attackDrag=null;farmPointer=null;report.hidden=true;delete report.dataset.done;duelRunning=false;placing=false;joystick=null;keys.clear();aiming=null;last=0;started=false;wrap.dataset.phase=active?'ready':'preview';syncRanks();}
 function setMode(){const on=modeSelect.value==='duel';duelSettings.hidden=!on;controls.children[3].hidden=on;noCd.parentElement.hidden=on;resetCd.hidden=on;help.textContent=on?'1v1: move with the joystick, arrow keys. Hold Attack; tap a skill at the bot or drag to aim. Both sides use normal cooldowns.':'Joystick or arrow keys to move. Tap a skill to cast it at the dummy, or drag from the skill to aim. Hold Attack to keep attacking.';for(const input of[...Object.values(rankSelects),noCd,resetCd,presetSelect,hpInput,armorInput,mrInput,resetButton,placeButton])input.disabled=on;selectChampion(champion);if(on){scene?.setCamera('rift');for(const b of cameraButtons)b.classList.toggle('active',b.dataset.camera==='rift');}}
 modeSelect.addEventListener('change',setMode);
 for(const input of[opponentSelect,difficultySelect,laneBox])input.addEventListener('change',()=>{if(duel)prepareDuel();});
 startButton.addEventListener('click',enterPractice);
 restartButton.addEventListener('click',resetRound);
 function syncRanks(){for(const[slot,select]of Object.entries(rankSelects))select.value=String(state.ranks[slot]);}
 function refreshIcons(){const p=P[champion];for(const slot of SLOTS){const b=buttons[slot],img=b.querySelector('img'),name=slot==='AA'?'Basic attack':p.hud?.abilities?.[slot]?.name||slot;if(img){img.src=p.hud?.icons?.[slot]||'';}b.title=slot+' · '+name;b.setAttribute('aria-label',slot==='AA'?'Basic attack (hold to keep attacking)':slot+' · '+name);}}
 function refreshSimulated(){const p=profileOf(champion),T=p.practice,rows=[el('p',{class:'pt-small',text:'Numbers come from the SharpWR engine for this champion with no items or runes, after the target’s armor and magic resistance. '+(duel&&T.duel?'Mana, regeneration, stack/weapon mechanics and crowd control are active for this champion.':'Mana costs are not simulated.')}),el('div',{class:'pt-sim-row'},el('strong',{text:'Basic attack'}),el('span',{text:`windup ${T.attack.windup[0].toFixed(2)} s · ${T.attack.speed?'projectile '+Math.round(T.attack.speed)+' u/s':'instant hit'} · AD as physical damage; ${duel&&T.duel?'weapon/passive stacks are active':'on-hit passives are not simulated'}.${T.attack.note?' '+T.attack.note:''}`}))];
  for(const slot of['Q','W','E','R']){const s=slotSummary(p,slot,state.ranks);if(duel&&T.duel&&champion==='Jinx'&&slot==='R')s.text='Missing-health execute damage is active at impact. Distance amplification is unresolved: reference minimum-flight component.';if(duel&&T.duel&&champion==='Jinx'&&slot==='E')s.text='Persistent trap area, 5 s lifetime, rank-based root. Arming uses the reference provisional 1 s.';rows.push(el('div',{class:'pt-sim-row'},el('strong',{text:s.title}),el('span',{text:s.text})));}
  rows.push(el('div',{class:'pt-sim-row'},el('strong',{text:'P · '+(p.hud?.abilities?.P?.name||'Passive')}),el('span',{text:duel&&T.duel?(champion==='Ezreal'?'Ability damage builds Spell Force stacks (max 4, 8 s).':'Minigun stacks and weapon switching are active. Get Excited triggers on the round-winning kill.'):'Plays the passive animation; passive effects are not simulated.'})));simulated.replaceChildren(...rows);}
 championSelect.addEventListener('change',()=>{selectChampion(championSelect.value);});
 levelSelect.addEventListener('change',()=>{if(duel)prepareDuel();else{Practice.setLevel(state,Number(levelSelect.value));syncRanks();applyDummy();}refreshSimulated();});
 for(const[slot,select]of Object.entries(rankSelects))select.addEventListener('change',()=>{Practice.setRank(state,slot,Number(select.value));refreshSimulated();});
 noCd.addEventListener('change',()=>{state.noCooldowns=noCd.checked;if(noCd.checked)for(const slot of['Q','W','E','R'])delete state.deadlines[slot];});
 resetCd.addEventListener('click',()=>{for(const slot of['Q','W','E','R'])delete state.deadlines[slot];});
 presetSelect.addEventListener('change',applyDummy);
 for(const input of[hpInput,armorInput,mrInput])input.addEventListener('change',()=>{presetSelect.value='Custom';applyDummy();});
 resetButton.addEventListener('click',()=>Practice.resetDummy(state));
 placeButton.addEventListener('click',()=>{placing=!placing;placeButton.classList.toggle('active',placing);placeButton.textContent=placing?'Tap the ground…':'Move dummy';});
 for(const b of cameraButtons)b.addEventListener('click',()=>{scene?.setCamera(b.dataset.camera);for(const x of cameraButtons)x.classList.toggle('active',x===b);});
 qualitySelect.addEventListener('change',()=>loadScene());
 // After picking from a list, give the keys back to the arena (Q W E R would otherwise change the list).
 for(const select of[modeSelect,opponentSelect,difficultySelect,championSelect,levelSelect,qualitySelect,presetSelect,...Object.values(rankSelects)])select.addEventListener('change',()=>select.blur());
 // Landscape session: true native lock where supported, rotated landscape surface elsewhere.
 const priorOverflow=document.body.style.overflow;
 function resizeArena(){if(!active)return;const w=window.innerWidth,h=window.innerHeight,rotate=w<h;wrap.dataset.rotated=String(rotate);wrap.style.width=(rotate?h:w)+'px';wrap.style.height=(rotate?w:h)+'px';wrap.style.left=(rotate?w:0)+'px';wrap.style.transform=rotate?'rotate(90deg)':'';}
 function resetRound(){clearKeys();stopStick();aiming=null;cursor=null;started=false;last=0;lastLog=undefined;lastSummary='';if(modeSelect.value==='duel')prepareDuel();else{state=null;selectChampion(champion);}wrap.dataset.phase=active?'ready':'preview';if(state)updateHud(duel?scope.MarksmanDuel.frame(duel,{particles:true}):Practice.frame(state,{particles:true}));}
 async function enterPractice(){if(active||entering||!scene)return;active=true;entering=true;wrap.classList.add('pt-full');document.body.style.overflow='hidden';focusButton.setAttribute('aria-pressed','true');resizeArena();resetRound();
  // Call browser fullscreen before awaiting anything to preserve the initiating user gesture.
  const full=nativeFullscreen&&document.fullscreenEnabled&&wrap.requestFullscreen?wrap.requestFullscreen().catch(()=>{}):Promise.resolve();
  try{await full;if(orientation)await orientation.enter();else await screen.orientation?.lock?.('landscape').catch(()=>{});}catch{}finally{entering=false;if(!active||disposed){void orientation?.leave();return;}resizeArena();last=0;}}
 async function exitPractice(){if(!active)return;active=false;started=false;duelRunning=false;clearKeys();stopStick();aiming=null;state.aim=null;state.aimSlot=null;wrap.classList.remove('pt-full');wrap.dataset.phase='preview';wrap.dataset.rotated='false';for(const key of['width','height','left','transform'])wrap.style[key]='';document.body.style.overflow=priorOverflow;focusButton.setAttribute('aria-pressed','false');
  if(document.fullscreenElement===wrap)await document.exitFullscreen().catch(()=>{});if(orientation)await orientation.leave().catch(()=>{});else screen.orientation?.unlock?.();resetRound();}
 focusButton.addEventListener('click',exitPractice);
 const onFullscreen=()=>{if(active&&nativeFullscreen&&!document.fullscreenElement)void exitPractice();};document.addEventListener('fullscreenchange',onFullscreen);window.addEventListener('resize',resizeArena);

 // ---- notes
 function entry(name=champion){return notes.champions[name]||(notes.champions[name]={tested:false});}
 function loadChampionNotes(){const e=entry(),abilities=P[champion].hud?.abilities||{};for(const f of NOTE_FIELDS){noteInputs[f].value=e[f]||'';noteLabels[f].textContent=f==='General'?champion+' · general':f==='AA'?'Basic attack':`${f} · ${abilities[f]?.name||f}`;}testedBox.checked=!!e.tested;refreshProgress();savedNote.textContent='';}
 function refreshProgress(){const done=names.filter(n=>notes.champions[n]?.tested).length;progress.textContent=`${done}/${names.length} champions tested`;if(!exportArea.hidden)exportArea.value=notesMarkdown(notes,catalogue);}
 let saveTimer=0;function save(){clearTimeout(saveTimer);saveTimer=setTimeout(()=>{entry().updated=new Date().toISOString();savedNote.textContent=storage.set(NOTES_KEY,JSON.stringify(notes))?'Saved':'Could not save on this device';refreshProgress();},300);}
 for(const f of NOTE_FIELDS)noteInputs[f].addEventListener('input',()=>{entry()[f]=noteInputs[f].value;save();});
 testedBox.addEventListener('change',()=>{entry().tested=testedBox.checked;save();});
 copyButton.addEventListener('click',async()=>{savedNote.textContent=await copyText(notesMarkdown(notes,catalogue))?'Copied':'Copy failed: use Show all notes';});
 downloadButton?.addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([notesMarkdown(notes,catalogue)],{type:'text/markdown'})),a=el('a',{href:url,download:'sharpwr-practice-notes.md'});document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 showButton.addEventListener('click',()=>{exportArea.hidden=!exportArea.hidden;showButton.textContent=exportArea.hidden?'Show all notes':'Hide all notes';if(!exportArea.hidden){exportArea.value=notesMarkdown(notes,catalogue);exportArea.focus();exportArea.select();}});

 // ---- movement input
 stick.addEventListener('pointerdown',e=>{e.stopPropagation();const rect=stick.getBoundingClientRect();if(Math.hypot(e.clientX-rect.left-rect.width/2,e.clientY-rect.top-rect.height/2)>Math.min(rect.width,rect.height)/2||joystick||!begin())return;e.preventDefault();capture(stick,e);joystick={pointerId:e.pointerId,x:e.clientX,y:e.clientY,dx:0,dz:0};});
 stick.addEventListener('pointermove',e=>{e.stopPropagation();if(!joystick||joystick.pointerId!==e.pointerId)return;const [dx,dy]=screenDelta(e.clientX-joystick.x,e.clientY-joystick.y),len=Math.hypot(dx,dy),f=Math.min(1,30/(len||1));stick.firstChild.style.transform=`translate(${dx*f}px,${dy*f}px)`;joystick.dx=(dx*Math.cos(inputYaw())+dy*Math.sin(inputYaw()))/Math.max(30,len);joystick.dz=(-dx*Math.sin(inputYaw())+dy*Math.cos(inputYaw()))/Math.max(30,len);});
 const stopStick=e=>{if(e){e.stopPropagation();if(!joystick||e.pointerId!==joystick.pointerId)return;}joystick=null;stick.firstChild.style.transform='';if(state){state.destination=state.hero.slice();state.queued=null;}};stick.addEventListener('pointerup',stopStick);stick.addEventListener('pointercancel',stopStick);stick.addEventListener('lostpointercapture',stopStick);
 stage.addEventListener('pointermove',e=>{cursor={x:e.clientX,y:e.clientY};});stage.addEventListener('pointerleave',()=>{cursor=null;});
 const typing=e=>{const t=e.target;return t.tagName==='TEXTAREA'||t.tagName==='SELECT'||t.tagName==='INPUT'&&!['checkbox','radio','button','range'].includes(t.type);};
 const onKey=e=>{if(disposed||!state||typing(e))return;const key=e.key.length===1?e.key.toUpperCase():e.key;
  if(e.type==='keyup'){keys.delete(key);if(e.code==='Space')Practice.holdAttack(state,false);return;}
  if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(key)){if(!begin())return;e.preventDefault();keys.add(key);return;}
  if(e.repeat)return;if(e.code==='Space'){if(!begin())return;e.preventDefault();Practice.holdAttack(state,true);cast('AA');return;}
  if('QWER'.includes(key)&&key.length===1){if(!root.isConnected||!wrap.getBoundingClientRect().height)return;e.preventDefault();const point=cursor&&scene?scene.pickGround(cursor.x,cursor.y):null;cast(key,point);}
  if(key==='Escape'&&wrap.classList.contains('pt-full'))focusButton.click();};
 const clearKeys=()=>{keys.clear();attackPointer=null;attackDrag=null;farmPointer=null;joystick=null;stick.firstChild.style.transform='';aiming=null;if(state){state.attackAim=null;Practice.holdAttack(state,false);state.pending=null;state.buffered=null;state.queued=null;state.destination=state.hero.slice();state.aim=null;state.aimSlot=null;}};
 document.addEventListener('keydown',onKey);document.addEventListener('keyup',onKey);window.addEventListener('blur',clearKeys);

 // ---- scene
 async function loadScene(){scene?.dispose();scene=null;stage.replaceChildren(status);status.textContent='Loading the arena…';qualitySelect.disabled=true;
  try{scene=await scope.MarksmanScene.createScene(stage,P,{studio:true,quality:qualitySelect.value,study:true,followHero:true,terrain:'dragon-lane',...sceneOptions});if(disposed){scene.dispose();return;}status.remove();scene.setCamera(cameraButtons.find(b=>b.classList.contains('active')).dataset.camera);
   scene.setInteraction(point=>{if(!placing||!state||!begin())return;if(placing){Practice.placeDummy(state,point);placing=false;placeButton.classList.remove('active');placeButton.textContent='Move dummy';return;}});}
  catch(error){console.error(error);status.textContent='The 3D arena could not load. Check the connection and try again.';stage.append(status);}finally{qualitySelect.disabled=false;startButton.disabled=!scene||disposed;}}
 modeSelect.value='duel';setMode();await loadScene();

 // ---- loop
 const ARROWS={ArrowUp:[-1,0],ArrowDown:[1,0],ArrowLeft:[0,-1],ArrowRight:[0,1]};
 function tick(ts){if(disposed)return;if(!root.isConnected){dispose();return;}raf=requestAnimationFrame(tick);const dt=last?Math.min(.1,(ts-last)/1000):0;last=ts;if(!state||document.hidden)return;
  if(farmPointer!==null){Practice.holdAttack(state,selectFarm());}
  if(joystick&&(joystick.dx||joystick.dz))Practice.move(state,[state.hero[0]+joystick.dx*1.5,0,state.hero[2]+joystick.dz*1.5]);
  if(keys.size){let dy=0,dx=0;for(const k of keys){const a=ARROWS[k];if(a){dy+=a[0];dx+=a[1];}}if(dx||dy){const len=Math.hypot(dx,dy),sx=dx/len*40,sy=dy/len*40,wx=(sx*Math.cos(inputYaw())+sy*Math.sin(inputYaw()))/40,wz=(-sx*Math.sin(inputYaw())+sy*Math.cos(inputYaw()))/40;Practice.move(state,[state.hero[0]+wx*1.5,0,state.hero[2]+wz*1.5]);}}
  const options={particles:effectsBox.checked,range:rangeBox.checked};if(active&&started){if(duel){if(duelRunning)scope.MarksmanDuel.step(duel,dt);}else Practice.step(state,dt);}const f=duel?scope.MarksmanDuel.frame(duel,options):Practice.frame(state,options);scene?.render(f);audio.update(duel?[{state:duel.player},{state:duel.enemy,enemy:true}]:[{state}]);updateHud(f);}
 function updateHud(f){const s=Practice.stats(state);statsLine.textContent=`${champion} · Lv ${state.level} · AD ${s.ad.toFixed(1)}${s.bonusAD?' (+'+s.bonusAD+')':''} · AS ${s.as.toFixed(3)} · Range ${Math.round(s.range)} · MS ${s.ms}`;
  clearTargetButton.hidden=!f.targetLock;clearTargetButton.disabled=!active||!!duel?.finished;if(f.targetLock)statsLine.textContent+=' · Locked: '+f.targetLock.label;
  farmButton.hidden=!duel?.lane;farmButton.disabled=!active||!!duel?.finished;finishButton.hidden=!duel;finishButton.disabled=!active||!!duel?.finished;report.hidden=!duel?.finished;
  if(duel?.finished&&!report.dataset.done){const r=scope.MarksmanDuel.summary(duel),p=r.player;report.dataset.done='true';report.replaceChildren(el('h3',{text:`${r.result.toUpperCase()} · ${r.duration.toFixed(1)}s`}),el('p',{text:`Damage to champion: ${Math.round(p.damage)} · All damage taken: ${Math.round(p.taken)} · ${p.damagePerSecond.toFixed(1)} DPS`}),el('p',{text:`Skill accuracy: ${p.accuracy===null?'—':p.accuracy+'%'} (${p.hits}/${p.casts}) · CS: ${p.cs} · Gold score: ${p.gold}`}),el('p',{text:`AA-ready idle: ${p.attackIdle.toFixed(1)}s · Moving while recently under attack: ${p.kiteDistance.toFixed(1)}m · Tower hits taken: ${p.towerHits}`}),el('p',{text:p.towerHits?'Tip: back away from enemy tower aggro.':p.attackIdle>2?'Tip: use attack-ready windows while in range.':p.accuracy!==null&&p.accuracy<50?'Tip: lead your skillshots and account for minion blockers.':'Good run: compare another difficulty or champion.'}),el('small',{text:r.rules}));}
  buffLine.replaceChildren(...f.buffs.map(b=>el('span',{class:'pt-chip',text:b.label||`${b.slot} ${b.remaining.toFixed(1)}s`})));
  if(duel){const result=duel.result?{victory:'VICTORY',defeat:'DEFEAT',draw:'DRAW',timeout:'TIME LIMIT',stopped:'SESSION COMPLETE'}[duel.result]:started?'FIGHT':'READY';combo.textContent=`${result} · ${difficultySelect.value.toUpperCase()} · ${duel.time.toFixed(1)}s · YOU ${Math.ceil(state.health.hp)} / ${Math.ceil(state.health.max)} HP · ${opponentSelect.value} ${Math.ceil(duel.enemy.health.hp)} HP${duel.lane?' · CS '+state.training.cs+' · Gold '+state.training.gold:''}`;}
  const sum=Practice.summary(state),show=sum.count?sum:state.lastCombo,text=show?`${sum.count?'Combo':'Last combo'} ${Math.round(show.total)} damage · ${show.count} hits · ${show.seconds.toFixed(2)} s · ${Math.round(show.dps)} DPS`:'Hit the dummy to start a combo';if(!duel&&text!==lastSummary){combo.textContent=text;lastSummary=text;}
  for(const slot of SLOTS){const b=buttons[slot],learned=slot==='AA'||slot==='P'||state.ranks[slot]>0,left=Math.max(0,(state.deadlines[slot]||0)-state.time),T=state.profile.practice,total=slot==='AA'?1/s.as:slot==='P'?0:T.slots[slot].cooldown?.[Math.max(0,state.ranks[slot]-1)]||0,cd=b.querySelector('.pt-cd'),shade=b.querySelector('.pt-shade'),shown=slot!=='AA'&&left>.05;
   b.disabled=!active||entering||!!duel&&(duel.finished||slot==='P');b.classList.toggle('locked',!learned||!!duel&&slot==='P');b.classList.toggle('cooling',shown);shade.style.setProperty('--cd',shown&&total?String(Math.min(1,left/total)):'0');cd.textContent=shown?(left>=1?Math.ceil(left):left.toFixed(1)):'';b.classList.toggle('active',f.action===slot||state.buffs.some(x=>x.slot===slot&&x.end>state.time));}
  const latest=state.log.at(-1);if(latest!==lastLog){lastLog=latest;logList.replaceChildren(...state.log.slice(-14).reverse().map(logRow));}}
 function logRow(l){const parts=l.parts?Object.entries(l.parts).map(([k,v])=>`${Math.round(v.raw)} → ${Math.round(v.dealt)} ${k}`).join(' + '):(l.text||'');return el('li',{},el('span',{class:'pt-time',text:l.t.toFixed(2)+'s'}),el('strong',{text:l.slot}),el('span',{text:parts}),l.note?el('em',{text:l.note}):null);}
 raf=requestAnimationFrame(tick);
 function dispose(){if(disposed)return;disposed=true;audio.dispose();cancelAnimationFrame(raf);document.removeEventListener('keydown',onKey);document.removeEventListener('keyup',onKey);window.removeEventListener('blur',clearKeys);document.removeEventListener('fullscreenchange',onFullscreen);window.removeEventListener('resize',resizeArena);void exitPractice();scene?.dispose();scene=null;}
 return{dispose,get state(){return state;},get duel(){return duel;},get scene(){return scene;},get phase(){return wrap.dataset.phase;},select:name=>{championSelect.value=name;selectChampion(name);}};
}
const API={mount,notesMarkdown,loadNotes,NOTES_KEY,NOTE_FIELDS,slotSummary};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanPracticeTool=API;
})(typeof globalThis!=='undefined'?globalThis:this);
