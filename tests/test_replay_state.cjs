const assert=require('node:assert/strict');const S=require('../assets/replay_state.js');
const hits=[{time:1,order:4,hp_after:200},{time:1,order:5,action:'W detonation',hp_after:100},{time:2,order:8,hp_after:0}];
assert.equal(S.lastAt(hits,0),null);
assert.equal(S.lastAt(hits,1,4).hp_after,200);
assert.equal(S.lastAt(hits,1,5).hp_after,100);
assert.equal(S.lastAt(hits,1).hp_after,100);
assert.equal(S.lastAt(hits,2).hp_after,0);
assert.equal(S.visible(hits[1],1,4),false);
const casts=[{time:.1,order:1,impact_time:.5}];
assert.equal(S.markActive(casts,hits,.4),false);
assert.equal(S.markActive(casts,hits,.9),true);
assert.equal(S.markActive(casts,hits,1,4),true);
assert.equal(S.markActive(casts,hits,1,5),false);
assert.equal(S.markActive(casts,[],4.5),false);
assert.equal(S.markActive([...casts,{time:2,order:9,impact_time:2.5}],hits,3),true);
console.log('Replay state: event ordering, W application/consumption/expiry/reapplication passed.');

const stackEvents=[{phase:'impact',time:1,order:2,after:{conqueror:1,items:{rage:1}}},{phase:'impact',time:1,order:3,after:{conqueror:2,items:{rage:2}}}];
assert.equal(S.stackSnapshot(stackEvents,0),null);
assert.deepEqual(S.stackSnapshot(stackEvents,1,2).values,[['conqueror',1],['rage',1]]);
assert.deepEqual(S.stackSnapshot(stackEvents,1).values,[['conqueror',2],['rage',2]]);
assert.equal(S.stackSnapshot(stackEvents,.5),null); // seeking backwards clears the HUD
