/* Pure cooldown state for the art preview. Base rank 1, zero haste; no resource/reset simulation. */
(function(scope){'use strict';
function cooldown(profile,slot,rank=1){if(slot==='AA')return profile.attack.study_duration;if(slot==='P')return 0;const ranks=profile.hud?.abilities?.[slot]?.cooldowns;const v=ranks?.[Math.min(Math.max(0,rank-1),ranks.length-1)];return Number.isFinite(v)&&v>=0?v:null;}
function remaining(deadlines,slot,clock){return Math.max(0,(deadlines[slot]??0)-clock);}
function cast(deadlines,profile,slot,clock){if(remaining(deadlines,slot,clock)>1e-6)return false;const cd=cooldown(profile,slot);if(cd!==null)deadlines[slot]=clock+cd;return true;}
function fightDeadlines(profile,events,time){const deadlines={};for(const e of events){if(e.start>time)continue;const cd=cooldown(profile,e.slot);if(cd!==null)deadlines[e.slot]=e.start+cd;}return deadlines;}
const API={cooldown,remaining,cast,fightDeadlines};if(typeof module!=='undefined'&&module.exports)module.exports=API;else scope.MarksmanHUD=API;
})(typeof globalThis!=='undefined'?globalThis:this);
