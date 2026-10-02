# Yunara normal W — V5.72.0

Source: previously supplied WR ability screenshots plus explicit user confirmation on 2026-10-02: four additional ticks, 0.25s interval, one-second duration. Existing screenshot observations already contained the interval, duration and low tick coefficients; they were not connected to the combat runtime.

Normal W now schedules one initial hit plus four separate hits at +0.25/+0.50/+0.75/+1.00 seconds from initial contact for the stationary target remaining inside the effect. Tick damage is magic: 8/14/20/26 + 0.12 bonus AD + 0.075 AP. Initial damage remains 60/110/160/210 + 0.85 bonus AD + 0.50 AP. Empowered Arc of Ruin remains one hit and uses the R-rank formula.

Normal versus empowered W is captured at cast time so R activation during projectile flight or linger does not transform an already-cast normal W. All ticks share one cast ID: no extra mana cost, no extra casts, Muramana Shock once for the whole W. Death stops pending ticks. Damage classification remains explicitly unresolved WR metadata. Projectile endpoint/contact geometry against moving targets remains outside this stationary-target confirmation.

Validation: five specific regressions cover count/timing/damage, empowered single hit, R during flight, once-per-cast Shock and death truncation. A 30-test engine/integration run passed. Recomputed the 18 affected Yunara item-adoption cells and aggregate ranking; unchanged champions keep their prior results.
