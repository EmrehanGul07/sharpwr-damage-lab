using SharpWR.Sim.Abilities;
using SharpWR.Sim.Combat;
using SharpWR.Sim.Content;
using SharpWR.Sim.Contracts;
using SharpWR.Sim.Core;
using SharpWR.Sim.Entities;
using SharpWR.Sim.Numerics;
using SharpWR.Sim.World;

namespace SharpWR.Sim.Champions.Samira
{
    /// <summary>
    /// Samira reference kit, mirroring sharpwr/fight_engine.py replay_samira(timed_combat=True).
    /// Every number comes from content "kit" (provenance there). Deliberate gaps are listed in
    /// the content's unsupported_mechanics; this class rejects them instead of guessing.
    /// </summary>
    public sealed class SamiraKit : IChampionKit
    {
        private const byte StyleAa = 1, StyleQ = 2, StyleW = 3, StyleE = 4;
        private const int ExpireStyle = 1, ExpireChannel = 2;

        private readonly int _maxStyle;
        private readonly SimTime _styleDuration;
        private readonly Fix64 _passiveFlat, _passiveRatioBase, _passiveRatioPerLevel;
        private readonly SimTime _qCast;
        private readonly Fix64 _qSpeed, _qSlashRange, _qHalfWidth, _qRange;
        private readonly SimTime _wCast;
        private readonly SimTime[] _wOffsets;
        private readonly Fix64 _wRadius;
        private readonly Fix64 _eTargetRange, _eDashDistance, _eDashSpeed, _eHitWidth;
        private readonly Fix64[] _eAttackSpeed;
        private readonly SimTime _eAttackSpeedDuration;
        private readonly int _rRequiredStyle, _rShots;
        private readonly Fix64 _rRadius, _rSpeed;
        private readonly SimTime _rChannel, _rWindow;

        public SamiraKit(JsonNode kit, JsonNode abilities)
        {
            JsonNode style = kit["style"], passive = kit["passive_melee_bonus"], q = kit["q"], w = kit["w"],
                     e = kit["e"], r = kit["r"];
            _maxStyle = KitData.Int(style["max_stacks"], "style.max_stacks");
            _styleDuration = SimTime.FromSeconds(KitData.Fix(style["expiry_seconds"], "style.expiry_seconds"));
            _passiveFlat = KitData.Fix(passive["level_flat"], "passive.level_flat");
            _passiveRatioBase = KitData.Fix(passive["ad_ratio_base"], "passive.ad_ratio_base");
            _passiveRatioPerLevel = KitData.Fix(passive["ad_ratio_per_level"], "passive.ad_ratio_per_level");
            MeleeAttackRange = KitData.Fix(kit["melee_attack_range"], "melee_attack_range");

            _qCast = SimTime.FromSeconds(KitData.Fix(q["cast_seconds"], "q.cast_seconds"));
            _qSpeed = KitData.Fix(q["projectile_speed"], "q.projectile_speed");
            _qSlashRange = KitData.Fix(q["slash_range"], "q.slash_range");
            JsonNode qGeometry = abilities["Q"]["geometry"];
            _qRange = KitData.Fix(qGeometry["range"], "Q.geometry.range");
            _qHalfWidth = KitData.Fix(qGeometry["width"], "Q.geometry.width") / Fix64.Two;

            _wCast = SimTime.FromSeconds(KitData.Fix(w["cast_seconds"], "w.cast_seconds"));
            JsonNode offsets = w["hit_offsets_seconds"];
            _wOffsets = new SimTime[offsets.Items.Count];
            for (int i = 0; i < _wOffsets.Length; i++)
                _wOffsets[i] = SimTime.FromSeconds(KitData.Fix(offsets.Items[i], "w.hit_offsets_seconds"));
            _wRadius = KitData.Fix(w["radius"], "w.radius");

            _eTargetRange = KitData.Fix(e["target_range"], "e.target_range");
            _eDashDistance = KitData.Fix(e["dash_distance"], "e.dash_distance");
            _eDashSpeed = KitData.Fix(e["dash_speed"], "e.dash_speed");
            _eHitWidth = KitData.Fix(e["hit_width"], "e.hit_width");
            JsonNode eAs = e["attack_speed_by_rank"];
            _eAttackSpeed = new Fix64[eAs.Items.Count];
            for (int i = 0; i < _eAttackSpeed.Length; i++)
                _eAttackSpeed[i] = KitData.Fix(eAs.Items[i], "e.attack_speed_by_rank");
            _eAttackSpeedDuration = SimTime.FromSeconds(KitData.Fix(e["attack_speed_seconds"], "e.attack_speed_seconds"));

            _rRequiredStyle = KitData.Int(r["required_style"], "r.required_style");
            _rRadius = KitData.Fix(r["radius"], "r.radius");
            _rChannel = SimTime.FromSeconds(KitData.Fix(r["channel_seconds"], "r.channel_seconds"));
            _rWindow = SimTime.FromSeconds(KitData.Fix(r["shot_window_seconds"], "r.shot_window_seconds"));
            _rShots = KitData.Int(r["shots"], "r.shots");
            _rSpeed = KitData.Fix(r["projectile_speed"], "r.projectile_speed");
        }

        /// <summary>Blade (melee) attack range; copied into the unit definition by the loader.</summary>
        public Fix64 MeleeAttackRange { get; }

        public static int StyleOf(Match match, int unit) => match.Get(unit).KitStacks;

        // ---- validation -------------------------------------------------------------------

        public RejectReason? Validate(Match match, int unit, AbilitySlot slot, in Command command, SimTime now)
        {
            Unit u = match.Get(unit);
            bool channel = now < u.KitChannelUntil;
            bool spin = now < u.KitSpinUntil;
            bool dashing = match.IsDashing(unit, now);
            switch (slot)
            {
                case AbilitySlot.Q:
                    if (channel || spin) return RejectReason.Locked;
                    if (dashing) return RejectReason.UnsupportedMechanic;   // E-Q explosives (unsupported)
                    return AimOf(match, unit, command, now).Equals(match.PositionAt(unit, now))
                        ? RejectReason.InvalidTarget : (RejectReason?)null;
                case AbilitySlot.W:
                    if (channel || dashing) return RejectReason.Locked;    // Damage Lab buffers W to dash end (not modelled)
                    return null;
                case AbilitySlot.E:
                    if (dashing) return RejectReason.Locked;
                    if (command.TargetUnit < 1 || command.TargetUnit > match.UnitCount ||
                        !match.IsEnemy(unit, command.TargetUnit) || !match.Get(command.TargetUnit).Alive)
                        return RejectReason.InvalidTarget;
                    return FixVec2.WithinRange(match.PositionAt(unit, now), match.PositionAt(command.TargetUnit, now), _eTargetRange)
                        ? (RejectReason?)null : RejectReason.OutOfRange;
                default:
                    if (channel) return RejectReason.Locked;
                    if (u.KitStacks < _rRequiredStyle) return RejectReason.RequirementNotMet;
                    return NearestEnemy(match, unit, now, _rRadius) == 0 ? RejectReason.OutOfRange : (RejectReason?)null;
            }
        }

        private static FixVec2 AimOf(Match match, int unit, in Command command, SimTime now)
        {
            if (command.TargetUnit >= 1 && command.TargetUnit <= match.UnitCount && command.TargetUnit != unit)
                return match.PositionAt(command.TargetUnit, now);
            return command.Point;
        }

        // ---- casts --------------------------------------------------------------------------

        public void Execute(Match match, int unit, AbilitySlot slot, in Command command, SimTime now, int actionId)
        {
            ref Unit u = ref match.Mutable(unit);
            switch (slot)
            {
                case AbilitySlot.Q:
                    u.CastLockUntil = now + _qCast;
                    u.KitAimPoint = AimOf(match, unit, command, now);
                    u.KitAimTarget = NearestEnemy(match, unit, now, _qSlashRange);
                    match.Schedule(now + _qCast, EventPhase.CastStart, CombatEventKind.AbilityCast, unit, 0, actionId);
                    break;
                case AbilitySlot.W:
                    u.CastLockUntil = now + _wCast;
                    u.KitSpinCast = actionId;
                    u.KitSpinUntil = now + _wCast + _wOffsets[_wOffsets.Length - 1];
                    for (int i = 0; i < _wOffsets.Length; i++)
                        match.Schedule(now + _wCast + _wOffsets[i], EventPhase.Impact, CombatEventKind.AbilityImpact, unit, 0, actionId, i);
                    break;
                case AbilitySlot.E:
                {
                    FixVec2 from = match.PositionAt(unit, now);
                    FixVec2 target = match.PositionAt(command.TargetUnit, now);
                    FixVec2 direction = (target - from).NormalizedOr(new FixVec2(Fix64.One, Fix64.Zero));
                    match.StartDash(unit, from + direction * _eDashDistance, _eDashSpeed, now);
                    SimTime arrival = now + SimTime.FromSeconds(FixVec2.Distance(from, target) / _eDashSpeed);
                    match.Schedule(arrival, EventPhase.Impact, CombatEventKind.AbilityImpact, unit, command.TargetUnit, actionId);
                    int rank = match.DefinitionOf(unit).AbilityRanks[(int)AbilitySlot.E];
                    ref Unit dasher = ref match.Mutable(unit);
                    dasher.BonusAsBuff = _eAttackSpeed[rank - 1];
                    dasher.BonusAsBuffUntil = now + _eAttackSpeedDuration;
                    break;
                }
                default:
                    u.KitChannelCast = actionId;
                    u.KitChannelUntil = now + _rChannel;
                    u.KitSpinCast = 0;                 // R ends W early
                    u.KitSpinUntil = now;
                    for (int shot = 0; shot < _rShots; shot++)
                    {
                        long offset = _rShots > 1 ? _rWindow.Micros * shot / (_rShots - 1) : 0;
                        match.Schedule(now + new SimTime(offset), EventPhase.CastStart, CombatEventKind.AbilityCast, unit, 0, actionId, shot);
                    }
                    match.Schedule(now + _rChannel, EventPhase.StatusExpiry, CombatEventKind.StatusExpired, unit, 0, actionId, ExpireChannel);
                    break;
            }
        }

        // ---- scheduled events ---------------------------------------------------------------

        public void OnEvent(Match match, in ScheduledEvent e)
        {
            if (!match.Get(e.Source).Alive && e.Kind != CombatEventKind.StatusExpired) return;
            if (e.Kind == CombatEventKind.StatusExpired) { OnExpired(match, e); return; }
            AbilitySlot slot = ActionIds.SlotOf(e.ActionId);
            if (e.Kind == CombatEventKind.AbilityCast)
            {
                if (slot == AbilitySlot.Q) ReleaseQ(match, e);
                else if (slot == AbilitySlot.R) FireRShot(match, e);
                return;
            }
            switch (slot)
            {
                case AbilitySlot.Q: HitQ(match, e); break;
                case AbilitySlot.W: HitW(match, e); break;
                case AbilitySlot.E: HitE(match, e); break;
                case AbilitySlot.R: HitR(match, e); break;
            }
        }

        private void ReleaseQ(Match match, in ScheduledEvent e)
        {
            Unit u = match.Get(e.Source);
            if (u.KitAimTarget != 0 && match.Get(u.KitAimTarget).Alive)
            {
                // Slash: resolves at cast end on the nearest enemy (cone geometry unsupported).
                match.Schedule(e.Time, EventPhase.Impact, CombatEventKind.AbilityImpact, e.Source, u.KitAimTarget, e.ActionId, 1);
                return;
            }
            FixVec2 origin = match.PositionAt(e.Source, e.Time);
            FixVec2 direction = (u.KitAimPoint - origin).NormalizedOr(FixVec2.Zero);
            int best = 0;
            Fix64 bestDistance = Fix64.Zero;
            for (int id = 1; id <= match.UnitCount; id++)
            {
                if (!match.IsEnemy(e.Source, id) || !match.Get(id).Alive) continue;
                FixVec2 relative = match.PositionAt(id, e.Time) - origin;
                Fix64 along = FixVec2.Dot(relative, direction);
                if (along < Fix64.Zero || along > _qRange) continue;
                Fix64 reach = _qHalfWidth + match.DefinitionOf(id).Radius;
                if (relative.LengthSquared - along * along > reach * reach) continue;
                if (best == 0 || along < bestDistance) { best = id; bestDistance = along; }
            }
            if (best == 0) return; // missed (collision checked at release; no swept dodge yet)
            match.Schedule(e.Time + SimTime.FromSeconds(bestDistance / _qSpeed), EventPhase.Impact,
                           CombatEventKind.AbilityImpact, e.Source, best, e.ActionId, 0);
        }

        private void HitQ(Match match, in ScheduledEvent e)
        {
            if (!match.Get(e.Target).Alive) return;
            Fix64 before = match.Get(e.Target).Health;
            match.DealDamage(e.Time, e.Source, e.Target, e.ActionId, match.DefinitionOf(e.Source).Abilities[0].DamageType,
                             match.AbilityRawDamage(e.Source, AbilitySlot.Q));
            if (e.Param == 1) Passive(match, e.Source, e.Target, e.Time, e.ActionId, before);
            GainStyle(match, e.Source, StyleQ, e.Time);
        }

        private void HitW(Match match, in ScheduledEvent e)
        {
            if (match.Get(e.Source).KitSpinCast != e.ActionId) return; // cancelled (R ends W)
            FixVec2 center = match.PositionAt(e.Source, e.Time);
            bool hitAny = false;
            for (int id = 1; id <= match.UnitCount; id++)
            {
                if (!match.IsEnemy(e.Source, id) || !match.Get(id).Alive) continue;
                if (!FixVec2.WithinRange(center, match.PositionAt(id, e.Time), _wRadius + match.DefinitionOf(id).Radius)) continue;
                Fix64 before = match.Get(id).Health;
                match.DealDamage(e.Time, e.Source, id, e.ActionId, match.DefinitionOf(e.Source).Abilities[1].DamageType,
                                 match.AbilityRawDamage(e.Source, AbilitySlot.W));
                Passive(match, e.Source, id, e.Time, e.ActionId, before);
                hitAny = true;
            }
            if (hitAny) GainStyle(match, e.Source, StyleW, e.Time);
        }

        private void HitE(Match match, in ScheduledEvent e)
        {
            if (!match.Get(e.Target).Alive) return;
            if (!FixVec2.WithinRange(match.PositionAt(e.Source, e.Time), match.PositionAt(e.Target, e.Time),
                                     _eHitWidth + match.DefinitionOf(e.Target).Radius)) return;
            Fix64 before = match.Get(e.Target).Health;
            match.DealDamage(e.Time, e.Source, e.Target, e.ActionId, match.DefinitionOf(e.Source).Abilities[2].DamageType,
                             match.AbilityRawDamage(e.Source, AbilitySlot.E));
            Passive(match, e.Source, e.Target, e.Time, e.ActionId, before);
            GainStyle(match, e.Source, StyleE, e.Time);
        }

        private void FireRShot(Match match, in ScheduledEvent e)
        {
            if (match.Get(e.Source).KitChannelCast != e.ActionId) return;
            int target = NearestEnemy(match, e.Source, e.Time, _rRadius);
            if (target == 0) return;
            Fix64 distance = FixVec2.Distance(match.PositionAt(e.Source, e.Time), match.PositionAt(target, e.Time));
            match.Schedule(e.Time + SimTime.FromSeconds(distance / _rSpeed), EventPhase.Impact,
                           CombatEventKind.AbilityImpact, e.Source, target, e.ActionId, e.Param);
        }

        private void HitR(Match match, in ScheduledEvent e)
        {
            if (!match.Get(e.Target).Alive) return;
            if (!FixVec2.WithinRange(match.PositionAt(e.Source, e.Time), match.PositionAt(e.Target, e.Time), _rRadius)) return;
            match.DealDamage(e.Time, e.Source, e.Target, e.ActionId, match.DefinitionOf(e.Source).Abilities[3].DamageType,
                             match.AbilityRawDamage(e.Source, AbilitySlot.R));   // R never gains Style or the melee passive
        }

        private void OnExpired(Match match, in ScheduledEvent e)
        {
            ref Unit u = ref match.Mutable(e.Source);
            if (e.Param == ExpireChannel)
            {
                if (u.KitChannelCast != e.ActionId) return;
                u.KitChannelCast = 0;
                u.KitStacks = 0;               // Style consumed at channel end
                u.KitLastAction = 0;
                return;
            }
            if (e.Param == ExpireStyle && u.KitStacksExpireAt == e.Time && e.Time >= u.KitChannelUntil)
            {
                u.KitStacks = 0;
                u.KitLastAction = 0;
            }
        }

        // ---- basic attack hooks -------------------------------------------------------------

        public SimTime AttackBlockedUntil(Match match, int unit)
        {
            Unit u = match.Get(unit);
            return u.KitSpinUntil > u.KitChannelUntil ? u.KitSpinUntil : u.KitChannelUntil;
        }

        public void OnAttackHit(Match match, int unit, int target, SimTime now, bool melee, int actionId, Fix64 healthBefore)
        {
            if (melee) Passive(match, unit, target, now, actionId, healthBefore);
            GainStyle(match, unit, StyleAa, now);
        }

        public void OnDeath(Match match, int unit)
        {
            ref Unit u = ref match.Mutable(unit);
            u.KitStacks = 0; u.KitLastAction = 0; u.KitChannelCast = 0; u.KitChannelUntil = SimTime.Zero;
            u.KitSpinCast = 0; u.KitSpinUntil = SimTime.Zero; u.KitAimTarget = 0;
        }

        // ---- passive ------------------------------------------------------------------------

        /// <summary>
        /// (level + flat + (base + perLevel*level) * AD) * (1 + missing/max) magic, using the
        /// target's HP before this hit (Damage Lab provisional interpolation, labelled in content).
        /// </summary>
        private void Passive(Match match, int unit, int target, SimTime now, int actionId, Fix64 healthBefore)
        {
            if (!match.Get(target).Alive) return;
            UnitDefinition d = match.DefinitionOf(unit);
            Fix64 level = Fix64.FromInt(d.Level);
            Fix64 maxHealth = match.DefinitionOf(target).MaxHealth;
            Fix64 raw = (level + _passiveFlat + (_passiveRatioBase + _passiveRatioPerLevel * level) * d.AttackDamage)
                        * (Fix64.One + (maxHealth - healthBefore) / maxHealth);
            match.DealDamage(now, unit, target, actionId, DamageType.Magic, raw);
        }

        private void GainStyle(Match match, int unit, byte action, SimTime now)
        {
            ref Unit u = ref match.Mutable(unit);
            if (action != u.KitLastAction)
            {
                if (u.KitStacks < _maxStyle) u.KitStacks++;
                u.KitLastAction = action;
            }
            u.KitStacksExpireAt = now + _styleDuration;
            match.Schedule(u.KitStacksExpireAt, EventPhase.StatusExpiry, CombatEventKind.StatusExpired, unit, 0, 0, ExpireStyle);
        }

        private static int NearestEnemy(Match match, int unit, SimTime now, Fix64 range)
        {
            FixVec2 origin = match.PositionAt(unit, now);
            int best = 0;
            Fix64 bestSq = Fix64.Zero;
            for (int id = 1; id <= match.UnitCount; id++)
            {
                if (!match.IsEnemy(unit, id) || !match.Get(id).Alive) continue;
                Fix64 reach = range + match.DefinitionOf(id).Radius;
                Fix64 sq = (match.PositionAt(id, now) - origin).LengthSquared;
                if (sq > reach * reach) continue;
                if (best == 0 || sq < bestSq) { best = id; bestSq = sq; }
            }
            return best;
        }
    }
}
