# Stormrazor movement charge, V5.80.0

Replaces the previous fixed seven-carrier-hit cadence. Charge is capped at 100, increases by travelled distance × 26/700 and by nine per basic attack. Ezreal Q and Phantom Hit grant no attack charge. Repeated projectiles sharing an attack ID grant attack charge only once. A ready hit adds the existing 120 raw magic damage and resets charge. RFC and Shiv keep their user-calibrated cadence.

Both combat adapters pass cumulative walking, lateral kiting and movement-skill path to the shared kernel. Target gap is not used as travelled path. Galeforce and timed Samira E are included. Generic movement skill distances remain provisional, are overrideable through movement_skill_distances, and are credited at cast; they do not introduce changes to the existing target-gap policy. Ezreal maximum E is calibrated to 16 charge (inferred 430.769 path units).

Open validation: threshold-crossing AA proc order, charged Q consumption, generic dash travel timing and exact distances. These choices are model assumptions rather than new user-confirmed facts. Starting Energized option remains authoritative for initial 100 charge.
