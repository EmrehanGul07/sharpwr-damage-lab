# 07 · Performance targets

Targets, not measurements. Each milestone report must include measured numbers on the
reference devices (`01-architecture.md` §6) and flag misses.

## Frame and tick budgets

| Item | Minimum Android (30 fps) | Recommended (60 fps) |
|---|---|---|
| Frame time | ≤ 33.3 ms p95 | ≤ 16.6 ms p95 |
| Main-thread render + UI | ≤ 14 ms | ≤ 8 ms |
| Simulation per tick (30 Hz), 5v5 + ~150 minions + 12 towers + jungle | ≤ 4 ms | ≤ 2 ms |
| Sim catch-up | max 3 ticks per frame, then slow-motion (offline) / resync (online) | same |
| GC allocations in sim tick | 0 B steady state | 0 B |
| GC allocations per frame (presentation) | ≤ 1 KB average | ≤ 1 KB |

Headless server: ≥ 20 concurrent 5v5 matches per 4-vCPU instance at ≤ 50% CPU (M6 target).

## Memory and size

| Item | Target |
|---|---|
| RAM (minimum tier) | ≤ 900 MB resident in match |
| Install size (first playable) | ≤ 300 MB APK/AAB, map + 1 champion |
| Champion model | ≤ 15k triangles, ≤ 60 bones, 1 material + atlas; LOD1 at 50% |
| Minion model | ≤ 2.5k triangles, GPU-instanced/skinned batches |
| Draw calls in match | ≤ 150 (minimum tier) |

The Damage Lab measured its 23 skinned GLBs at 37.4 MB raw → 9.1 MB with meshopt
(`docs/architecture.md`); those models are Riot likenesses and cannot be shipped, but the
pipeline lesson (meshopt, no texture palette) carries over to original art.

## Simulation scaling rules

* Struct-of-arrays, no per-tick allocations, pooled event buffers.
* Spatial hash grid (fixed-point cells) for range queries and collision; O(n) per tick.
* Fog of war recomputed every 2nd tick on a coarse grid; per-team bitsets.
* Minion pathing on a precomputed lane flow field; champions use A* on a navigation grid with
  path caching; no Unity NavMesh inside the sim.

## Network

| Item | Target |
|---|---|
| Downlink per client (5v5) | ≤ 12 KB/s average |
| Uplink per client | ≤ 3 KB/s |
| Input-to-own-movement latency | ≤ 1 frame (prediction) |
| Playable RTT / loss | 150 ms / 3% |

## Benchmarks to automate (M1+)

`SimBench` (BenchmarkDotNet in `game/sim`): 10 champions + 150 minions for 10,000 ticks;
report µs/tick and allocations; CI fails on > 20% regression against the stored baseline.
