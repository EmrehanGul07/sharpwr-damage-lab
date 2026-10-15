# 04 · Server-authoritative networking design

Online play arrives in M5+. The design is fixed now because it constrains the sim: every
milestone before then must keep the sim **snapshot-able, deterministic and command-driven**.

## Model

**Server-authoritative simulation with client-side prediction of the local champion's
movement and cast presentation, entity interpolation for everything else.** Not lockstep:
lockstep exposes full state to every client (map hacks defeat fog of war) and one slow phone
stalls the match.

```
Client                                   Server (headless .NET 8, same com.sharpwr.sim)
 input → Command{tick, seq, kind, aim}  ──UDP──►  command buffer (per player, per tick)
 predict own movement locally                    sim.Step() at 30 Hz, authoritative
 ◄── Snapshot{tick, acked seq, entities (fog-filtered, delta-compressed), events}
 reconcile: rewind own state to snapshot, replay unacked commands
 interpolate others ~100 ms in the past
```

## Messages (Contracts)

| Message | Fields | Notes |
|---|---|---|
| `Command` | tick, seq, kind (Move, Stop, Attack, Cast, LevelUp, Buy…), target id, aim (Fix64 x,z) | ≤ 24 bytes; redundantly sent in the last 3 packets |
| `Snapshot` | tick, last processed seq per player, per-entity delta vs acked baseline, events since baseline | per-client interest management |
| `StateHash` | tick, FNV-1a 64 | every 30 ticks; mismatch on a debug client triggers a full-state dump for diffing |
| `Join/Welcome` | content hash, sim version, seed, roster | refuse mismatched content/sim versions |

## Authority rules

* The server validates every command with the same gates as offline (`03-combat-event-model.md`
  §5). Clients cannot submit damage, hits, positions or cooldown state.
* Skillshot hits are decided on the server. **Lag compensation**: the server tests a projectile
  against target positions rewound by the shooter's measured latency, capped at 150 ms, only
  for the cast's first frame of travel (favor-the-shooter bounded).
* Fog of war: snapshots include only entities visible to the receiving team; hidden enemy
  casts never leave the server. AI uses the same visibility API.
* Anti-cheat baseline: rate limits per command kind, aim vectors clamped to ability range,
  movement target validation, server-side cooldown/mana truth.

## Transport and budgets

* UDP with a reliability layer (candidates: a maintained C# library such as LiteNetLib, or
  Unity Transport on the client + a compatible .NET server). Choice made in M5 with a spike;
  requirements: unreliable-sequenced snapshots, reliable-ordered control channel, encryption.
* Tick 30 Hz; snapshots 15–30 Hz adaptive; target ≤ 12 KB/s down, ≤ 3 KB/s up per mobile client
  in 5v5 (to be measured).
* Playable up to 150 ms RTT and 3% loss; degraded beyond.

## What the sim must provide (from M1 onward)

1. `Step(commands)` pure w.r.t. (state, content, commands).
2. `SaveState()/LoadState()` of the whole world into a byte buffer (rollback for reconciliation
   of the local champion; full-state dumps for desync).
3. Per-tick `StateHash`.
4. Visibility query per team.
5. No hidden state in static fields or presentation objects.
QA keeps a determinism suite that runs the same match twice (and on ARM vs x64 in CI) and
compares hashes every tick.
