# WR on-hit order, v5.75.0

User Smolder level15 tests confirm Phantom AA6/9/12, Kraken AA3/6/8/10/12 with Rageblade, and Terminus advancement by Phantom. Magic on-hit uses penetration before the current stack update; physical attack uses penetration after it. On AA6 Rageblade + Terminus deals 36 then 38 magic. Three-item test repeats that sequence.

The kernel now tracks individual on-hit events and advances both counters for Phantom. Existing 10% penetration per Dark stack remains unchanged. Regression tests reproduce standalone Terminus physical/magic progression and Rageblade + Terminus progression. Kraken proc positions match both combined tests.

Exact Kraken values are not forced to fit: triple AA6 currently rounds to 249 versus user display250, and AA12 separate physical indicators need independent rounding/missing-health snapshot verification. Target HP at each proc and precise combat timing were not recorded. This stays TODO rather than inventing a coefficient.
