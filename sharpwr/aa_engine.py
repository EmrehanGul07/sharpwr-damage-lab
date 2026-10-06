"""Shared auto-attack (AA) engine: level formulas, build validation and the multi-item hit kernel."""

from .catalog import B, C, GALEFORCE_COOLDOWN, K, dct, galeforce_damage


def gu(l):
    """Per-level growth factor: 0 at level 1, rising quadratically to level 15."""
    n = l - 1
    return n * (0.7025 + 0.0175 * n)


def stats(n, l, mist=0):
    """Champion base AD, AD at level l and attack-speed parameters (Senna mist adds 1.25 AD per stack)."""
    ba, g, r, b, bba, asg = C[n]
    u = gu(l)
    return {
        "basead": ba,
        "ad": ba + g * u + (mist * 1.25 if n == "Senna" else 0),
        "ratio": r,
        "baseas": b,
        "bba": bba,
        "lvbas": asg * u,
    }


def rm(x):
    """Damage multiplier for a resistance value; negative resistance amplifies damage."""
    return 100 / (100 + x) if x >= 0 else 2 - 100 / (100 - x)


def lvl_scale(lo, hi, lvl):
    """Linear value from lo at level 1 to hi at level 15."""
    return lo + (hi - lo) * (lvl - 1) / 14


def validate_build(items, db, boot=None):
    """Raise ValueError for an illegal build: over five items, duplicates, two Spellblades or boots in an item slot."""
    from .build_fight_optimizer import SPELLBLADE

    if len(set(items) & SPELLBLADE) > 1:
        raise ValueError("Only one Spellblade item is allowed.")
    if len(items) > 5:
        raise ValueError("At most five items are allowed.")
    if len(items) != len(set(items)):
        raise ValueError("Duplicate items are not allowed.")
    if any(x not in db or x in B or x == "Boots of Speed" for x in items):
        raise ValueError("Choose valid items; boots use the separate slot.")
    if boot is not None and boot not in B:
        raise ValueError("Unknown boots.")


def effective_resistance(value, pct=0.0, flat=0.0, cap=1.0):
    # Penetration cannot make a positive resistance negative; pre-existing negative resistance remains negative.
    """Resistance after percent then flat penetration."""
    return value if value < 0 else max(0.0, value * (1 - min(cap, max(0.0, pct))) - max(0.0, flat))


def sim_build(
    n,
    l,
    hp0,
    arm,
    mr,
    items,
    db,
    mist=0,
    bonus_hp=0,
    dist=550.0,
    target_aa_reduction=0.0,
    yuntal_start_stacks=0,
    base_mana=0.0,
    spell=False,
    energized=False,
    ult=False,
    execs=0,
    active_ready=False,
    boot=None,
    item_proc=True,
):
    """AA-only fight until the target dies or 500 attacks.

    Returns ([label, gold, TTK, attacks, DPS], per-attack log). TTK is inf if the target survives.
    """
    engine = combat_hits(
        n,
        l,
        hp0,
        arm,
        mr,
        items,
        db,
        mist,
        bonus_hp,
        dist,
        target_aa_reduction,
        yuntal_start_stacks,
        base_mana,
        spell,
        energized,
        ult,
        execs,
        active_ready,
        boot,
        item_proc,
    )
    next(engine)
    hp = float(hp0)
    t = 0.0
    log = []
    while hp > 0 and len(log) < 500:
        h = engine.send({"hp": hp, "time": t})
        before = hp
        hp -= h["damage"]
        if "The Collector" in items and item_proc and 0 < hp <= hp0 * min(1, 0.05 + 0.001 * execs):
            hp = 0
            h["notes"].append("Execute")
        log.append(
            [
                len(log) + 1,
                round(t, 3),
                round(h["as"], 4),
                round(h["crit"] * 100, 2),
                round(h["armor"], 1),
                round(before, 1),
                round(h["damage"], 1),
                round(max(hp, 0), 1),
                ", ".join(h["notes"]),
                h["rage"],
                h["light"],
                h["dark"],
            ]
        )
        t += 1 / h["as"]
    label = " + ".join(items) + ((" + " + boot) if boot else "")
    if hp > 0:
        label += " [NOT KILLED: 500 attacks]"
    gold = sum(dct(db[x])["gold"] for x in items) + (dct(B[boot])["gold"] if boot else 0)
    return [
        label,
        gold,
        round(t, 3) if hp <= 0 else float("inf"),
        len(log),
        round(sum(x[6] for x in log) / t, 1) if t else 0.0,
    ], log


def sim(
    n,
    l,
    hp0,
    arm,
    mr,
    it,
    db,
    mist,
    bonus_hp,
    dist,
    base_mana,
    spell,
    energized,
    ult,
    execs,
    item_proc=True,
    target_aa_reduction=0.0,
    active_ready=False,
    yuntal_start_stacks=0,
):
    """Single-item sim_build; log rows keep their first nine columns."""
    row, log = sim_build(
        n,
        l,
        hp0,
        arm,
        mr,
        [it],
        db,
        mist,
        bonus_hp,
        dist,
        target_aa_reduction,
        yuntal_start_stacks,
        base_mana,
        spell,
        energized,
        ult,
        execs,
        active_ready,
        item_proc=item_proc,
    )
    return row, [x[:9] for x in log]


def combat_hits(
    n,
    l,
    hp0,
    arm,
    mr,
    items,
    db,
    mist=0,
    bonus_hp=0,
    dist=550.0,
    target_aa_reduction=0.0,
    yuntal_start_stacks=0,
    base_mana=0.0,
    spell=False,
    energized=False,
    ult=False,
    execs=0,
    active_ready=False,
    boot=None,
    item_proc=True,
    initial_flurry=False,
):
    """Shared multi-item AA engine. Carries the audited single-item AA mechanics into item combinations.

    Generator: prime with next(), then send a state dict ({"hp", "time"} at minimum) for each attack
    and receive that hit as a dict (damage, attack speed, crit, effective armor/MR, item state).
    """
    items = list(items)
    from .combat_validation import benchmark, finite

    benchmark(
        n,
        l,
        hp0,
        arm,
        mr,
        mist=mist,
        bonus_hp=bonus_hp,
        distance=dist,
        reduction=target_aa_reduction,
        mana=base_mana,
        stacks=yuntal_start_stacks,
        executes=execs,
    )
    from .champion_database import champion_stat

    # Item melee/ranged class belongs to the champion, not distance to target.
    botrk_ratio = 0.085 if champion_stat(n, "attack_type") == "Melee" else 0.06
    validate_build(items, db, boot)
    s = stats(n, l, mist)
    qs = [dct(db[x]) for x in items]
    bootq = dct(B[boot]) if boot in B else dct(())
    total = lambda key: sum(float(q[key]) for q in qs) + float(bootq.get(key, 0))
    if base_mana <= 0:
        from .champion_database import level_stats

        base_mana = level_stats(n, int(l))["mana"] or 0.0
    mana = base_mana + total("mana")
    awe = 0.02 * mana if any(x in items for x in ("Manamune", "Muramana")) else 0.0
    ad = s["ad"] + total("ad") + awe
    hp = float(hp0)
    t = 0.0
    k = 0
    log = []
    rb = light = dark = rage_hits = pd_stacks = 0
    kraken_hits = 0
    energized_charge = 100.0 if energized else 0.0
    energized_path = 0.0
    energized_attacks = set()
    energized_launches = set()
    energized_pending = set()
    energized_items = [
        (name, magic, label)
        for name, magic, label in (
            ("Stormrazor", 120, "Storm Energized"),
            ("Rapid Firecannon", 80, "RFC Energized"),
            ("Statikk Shiv", 60, "Shiv Energized"),
        )
        if name in items
    ]
    energized_attack_charge = 14.0 if "Statikk Shiv" in items else 9.0
    terminus_hits = 0
    ytcrit = min(0.25, max(0, int(yuntal_start_stacks)) * 0.002)
    yt_until = -1.0
    yt_cd = 0.0
    spellblade_ready = 0.0
    fh = 0  # Only an actual ultimate_cast_time event arms Opening Barrage.
    fiend_until = 8.0
    last_ult_cast = None
    spell_pending = bool(spell)
    galeforce_ready = 0.0
    duskblade_ready = 0.0
    if initial_flurry and "Yun Tal Wildarrows" in items and item_proc:
        yt_until = 6.0
        yt_cd = 25.0
    state = yield None
    last_event_time = -1.0
    while k < 500 or (state.get("event_driven", False) and k < 10000):
        finite(
            state.get("hp", hp) if state.get("event_phase") == "attack_launch" else state.get("hp"),
            "live target HP",
            0,
        )
        event_time = finite(
            (
                state.get("time", t)
                if state.get("event_phase") == "attack_launch"
                else state.get("time")
            ),
            "event time",
            0,
        )
        if event_time < last_event_time:
            raise ValueError("Combat events must be monotonic")
        last_event_time = event_time
        for _field in (
            "movement_distance",
            "distance",
            "max_mana",
            "bonus_as",
            "spellblade_crit",
            "crit",
            "armor_override",
            "mr_override",
            "attack_physical",
            "critical_attack_physical",
            "nonbasic_attack_physical",
            "primary_external_damage",
            "on_hit_health_multiplier",
        ):
            if state.get(_field) is not None:
                finite(
                    state[_field],
                    _field,
                    None if _field in ("armor_override", "mr_override") else 0,
                    1 if _field in ("crit", "spellblade_crit") else None,
                )
        if "bonus_ad" in state:
            finite(state["bonus_ad"], "bonus AD")
        # Charge consumption occurs at projectile launch, damage at impact.
        if energized_items and item_proc:
            travelled = max(energized_path, float(state.get("movement_distance", energized_path)))
            energized_charge = min(
                100.0, energized_charge + (travelled - energized_path) * 26.0 / 700.0
            )
            energized_path = travelled
            if "energized_ready" in state:
                energized_charge = 100.0 if state["energized_ready"] else 0.0
        if state.get("event_phase") == "attack_launch":
            attack_id = state["attack_id"]
            if attack_id not in energized_launches:
                energized_launches.add(attack_id)
                if energized_items and item_proc and energized_charge >= 100.0 - 1e-9:
                    energized_pending.add(attack_id)
                    energized_charge = 0.0
            state = yield {
                "energized_charge": energized_charge,
                "stormrazor_charge": energized_charge,
                "movement_distance": energized_path,
                "energized_reserved": attack_id in energized_pending,
            }
            continue
        hp = float(state["hp"])
        t = float(state["time"])
        k += 1
        current_ad = ad + float(state.get("bonus_ad", 0))
        event_driven = bool(state.get("event_driven", False))
        skill_on_hit = bool(state.get("skill_on_hit", False))
        if event_driven:
            _cast_times = state.get("spell_cast_times", [t] if state.get("spell_cast") else [])
            for _cast_time in _cast_times:
                if _cast_time >= spellblade_ready:
                    spell_pending = True
            _ult_time = state.get("ultimate_cast_time")
            if _ult_time is not None and _ult_time != last_ult_cast:
                last_ult_cast = _ult_time
                fiend_until = _ult_time + 8
                if "Fiendhunter Bolts" in items and item_proc:
                    fh = 3
        dyn = (0.08 * rb if ("Guinsoo's Rageblade" in items and item_proc) else 0.0) + (
            0.06 * pd_stacks if ("Phantom Dancer" in items and item_proc) else 0.0
        )
        if ("Yun Tal Wildarrows" in items and item_proc) and t < yt_until:
            dyn += 0.35
        asp = min(
            3,
            s["baseas"]
            + s["ratio"]
            * (s["bba"] + s["lvbas"] + total("as") + dyn + float(state.get("bonus_as", 0))),
        )
        crit = min(
            1,
            total("crit")
            + (mist // 20 * 0.10 if n == "Senna" else 0)
            + (ytcrit if ("Yun Tal Wildarrows" in items and item_proc) else 0),
        )
        spellblade_crit = float(state.get("spellblade_crit", crit))
        crit = float(state.get("crit", crit))
        cd = 2.3 if "Infinity Edge" in items else 2.0
        if n == "Senna":
            cd *= 0.9
        pct = total("pctpen") + (0.10 * dark if ("Terminus" in items and item_proc) else 0)
        if "Terminus" in items and item_proc:
            pct = min(0.40, pct)
        ea = float(state.get("armor_override", effective_resistance(arm, pct, total("flatpen"))))
        # Patch 7.3 Rageblade no longer disables critical strikes; crit remains normal AA expected damage.
        phy = float(state.get("attack_physical", current_ad * (1 + crit * (cd - 1))))
        onp = 0.0
        onm = 0.0
        true = 0.0
        note = []
        item_components = []

        if fh and t <= fiend_until and not skill_on_hit:
            asp = min(3, asp + s["ratio"] * 0.50)
            phy = float(state.get("critical_attack_physical", current_ad * cd)) * 0.80
            true = current_ad * 0.15 * crit
            note.append("Opening Barrage")
        if "Hexoptics C44" in items and not skill_on_hit:
            from .damage_classification import magnification

            hit_dist = (
                state.get("distance")
                if state.get("distance") is not None
                else (0.0 if state.get("melee", False) else dist)
            )
            factor = magnification(hit_dist, ["BasicAttack"])
            secondary = float(state.get("nonbasic_attack_physical", 0.0))
            phy = (phy - secondary) * factor + secondary
            # Opening Barrage is a separate item effect, not the attack base.
            note.append(f"C44 {(factor-1)*100:.0f}% basic only")
        if (
            "Galeforce" in items
            and active_ready
            and not event_driven
            and not skill_on_hit
            and t >= galeforce_ready
        ):
            onp += galeforce_damage(l, current_ad - s["basead"])
            note.append("Cloudburst")
            galeforce_ready = t + GALEFORCE_COOLDOWN
        if "Blade of the Ruined King" in items:
            onp += max(15, botrk_ratio * hp)
        if "Terminus" in items and item_proc:
            onm += 30
        if "Wit's End" in items:
            onm += 40
        if "Nashor's Tooth" in items:
            onm += 15 + 0.20 * total("ap")
        if "Recurve Bow" in items:
            onp += 15
        if "Muramana" in items and not skill_on_hit:
            onp += 0.015 * float(mana if state.get("max_mana") is None else state["max_mana"])

        rage_extra = False
        if "Guinsoo's Rageblade" in items and item_proc:
            onm += 30
            # The AA that reaches four stacks is eligible hit 1: user AA6/AA9 confirmation.
            if rb >= 3:
                rage_hits += 1
                if rage_hits >= 3:
                    rage_extra = True
                    rage_hits = 0

        # Resolve ordinary and Phantom on-hits in order. Magic lands before
        # Juxtaposition advances; physical attack/procs use the updated penetration.
        primary_onm = onm
        primary_em = effective_resistance(
            mr,
            total("pctmpen") + (0.10 * dark if "Terminus" in items and item_proc else 0),
            total("flatmpen"),
            cap=0.40 if "Terminus" in items and item_proc else 1.0,
        )
        if "Terminus" in items and item_proc:
            terminus_hits += 1
            if terminus_hits % 2:
                light = min(3, light + 1)
            else:
                dark = min(3, dark + 1)
            ea = effective_resistance(
                arm, min(0.40, total("pctpen") + 0.10 * dark), total("flatpen")
            )
        if "Kraken Slayer" in items and item_proc:
            kraken_hits += 1
            if kraken_hits >= 3:
                base = 120 + (l - 1) / 14 * 48
                miss = max(0, min(1, (hp0 - hp) / hp0))
                onp += base * (1 + min(0.75, 0.75 * miss))
                note.append("Kraken")
                kraken_hits -= 3

        primary_onp = onp
        if rage_extra:
            onm += 30
            if "Blade of the Ruined King" in items:
                primary_damage = (phy + primary_onp) * rm(ea) + primary_onm * rm(primary_em) + true
                if "Lord Dominik's Regards" in items:
                    primary_damage *= 1 + min(0.12, max(0, bonus_hp) / 125 * 0.01)
                if boot == "Immortal Treads":
                    primary_damage *= 1.05
                if target_aa_reduction and not skill_on_hit:
                    primary_damage *= 1 - target_aa_reduction
                primary_damage *= float(state.get("on_hit_health_multiplier", 1.0))
                phantom_hp = max(
                    0.0, hp - primary_damage - float(state.get("primary_external_damage", 0.0))
                )
                onp += max(15, botrk_ratio * phantom_hp)

            if "Terminus" in items and item_proc:
                onm += 30
            if "Wit's End" in items:
                onm += 40
            if "Nashor's Tooth" in items:
                onm += 15 + 0.20 * total("ap")
            if "Recurve Bow" in items:
                onp += 15
            # Muramana Shock is once per attack/cast, so Phantom cannot repeat it.
            if "Terminus" in items and item_proc:
                terminus_hits += 1
                if terminus_hits % 2:
                    light = min(3, light + 1)
                else:
                    dark = min(3, dark + 1)
            if "Kraken Slayer" in items and item_proc:
                kraken_hits += 1
                if kraken_hits >= 3:
                    base = 120 + (l - 1) / 14 * 48
                    miss = max(0, min(1, (hp0 - hp) / hp0))
                    onp += base * (1 + min(0.75, 0.75 * miss))
                    note.append("Kraken (Phantom)")
                    kraken_hits -= 3
            note.append("Phantom Hit")

        # All three items share the user-confirmed Energized charge/cadence.
        if energized_items and item_proc:
            attack_id = state.get("attack_id")
            new_attack = attack_id is None or attack_id not in energized_attacks
            reserved = attack_id is not None and attack_id in energized_pending
            proc = reserved or (
                energized_charge >= 100.0 - 1e-9
                and (skill_on_hit or new_attack and attack_id not in energized_launches)
            )
            if proc:
                for _, magic, label in energized_items:
                    onm += magic
                    note.append(label)
                if reserved:
                    energized_pending.remove(attack_id)
                else:
                    energized_charge = 0.0
            if not skill_on_hit and new_attack:
                if not proc:
                    energized_charge = min(100.0, energized_charge + energized_attack_charge)
                if attack_id is not None:
                    energized_attacks.add(attack_id)

        if "Kircheis Shard" in items and energized and k == 1:
            onm += 40
            note.append("Jolt")

        # Legacy pre-cast means ONE initial cast; cooldown alone never rearms.
        if not event_driven and spell and k == 1:
            spell_pending = True
        if spell_pending and t >= spellblade_ready:
            choices = []
            if "Essence Reaver" in items and item_proc:
                choices.append(
                    (1.35, 1.35 * s["basead"] + min(80, 0.8 * spellblade_crit * 100), "ER")
                )
            if "Trinity Force" in items and item_proc:
                choices.append((2.0, 2 * s["basead"], "Trinity"))
            if "Iceborn Gauntlet" in items and item_proc:
                choices.append((1.0, s["basead"] + 0.25 * total("armor"), "Iceborn"))
            if "Sheen" in items:
                choices.append((1.0, s["basead"], "Sheen"))
            if choices:
                _, amount, label = max(choices, key=lambda x: (x[0], x[1]))
                onp += amount
                note.append(label)
                spellblade_ready = t + 1.5
                spell_pending = False

        if (
            ("Duskblade of Draktharr" in items and item_proc)
            and not skill_on_hit
            and t >= duskblade_ready
        ):
            onp += 60 + (l - 1) / 14 * 100
            note.append("Nightstalker")
            duskblade_ready = t + 10

        if onp:
            item_components.append(
                {
                    "damage_type": "physical",
                    "raw_amount": onp,
                    "tags": ["Item"],
                    "status": "unknown_WR",
                    "component": "item additional damage",
                    "effects": list(note),
                }
            )
        if onm:
            item_components.append(
                {
                    "damage_type": "magic",
                    "raw_amount": onm,
                    "tags": ["Item"],
                    "status": "unknown_WR",
                    "component": "item additional damage",
                    "effects": list(note),
                }
            )
        if true:
            item_components.append(
                {
                    "damage_type": "true",
                    "raw_amount": true,
                    "tags": ["Item"],
                    "status": "unknown_WR",
                    "component": "Opening Barrage",
                }
            )
        phy += onp
        if "Lord Dominik's Regards" in items:
            gs = min(0.12, max(0, bonus_hp) / 125 * 0.01)
            phy *= 1 + gs
            onm *= 1 + gs
            primary_onm *= 1 + gs
            true *= 1 + gs
            if gs:
                note.append(f"Giant Slayer {gs*100:.0f}%")
        em = effective_resistance(
            mr,
            total("pctmpen")
            + (0.10 * dark if ("Terminus" in items and item_proc) and item_proc else 0),
            total("flatmpen"),
            cap=0.40 if ("Terminus" in items and item_proc) else 1.0,
        )
        em = float(state.get("mr_override", em)) if not ("Terminus" in items and item_proc) else em
        magic_damage = onm * rm(em)
        if "Terminus" in items and item_proc:
            # Preserve the two resistances rather than multiplying merged raw magic.
            magic_damage = primary_onm * rm(primary_em) + (onm - primary_onm) * rm(em)
        dmg = phy * rm(ea) + magic_damage + true
        if boot == "Immortal Treads":
            dmg *= 1.05
        if target_aa_reduction and not skill_on_hit:
            dmg *= 1 - target_aa_reduction
        on_hit_events = [
            {
                "kind": "primary",
                "magic_raw": primary_onm,
                "magic_damage": primary_onm * rm(primary_em),
                "physical_proc_raw": primary_onp,
            }
        ]
        if rage_extra:
            on_hit_events.append(
                {
                    "kind": "phantom",
                    "magic_raw": onm - primary_onm,
                    "magic_damage": (onm - primary_onm) * rm(em),
                    "physical_proc_raw": onp - primary_onp,
                }
            )
        before = hp

        if ("Phantom Dancer" in items and item_proc) and (not skill_on_hit or n == "Ezreal"):
            pd_stacks = min(5, pd_stacks + 1)
        if "Guinsoo's Rageblade" in items and item_proc:
            rb = min(4, rb + 1)
        if ("Yun Tal Wildarrows" in items and item_proc) and not skill_on_hit:
            ytcrit = min(0.25, ytcrit + 0.002)
            if yt_cd <= t:
                yt_until = t + 6
                yt_cd = t + 25
                note.append("Flurry")
            else:
                yt_cd = max(t, yt_cd - (1.0 + crit))

        if fh and t <= fiend_until and not skill_on_hit:
            fh -= 1
        state = yield {
            "energized_charge": energized_charge,
            "stormrazor_charge": energized_charge,
            "movement_distance": energized_path,
            "damage": dmg,
            "as": asp,
            "crit": crit,
            "armor": ea,
            "mr": em,
            "physical": phy,
            "magic": onm,
            "physical_damage": phy * rm(ea),
            "magic_damage": magic_damage,
            "on_hit_events": on_hit_events,
            "true": true,
            "notes": note,
            "damage_components": item_components,
            "rage": rb,
            "light": light,
            "dark": dark,
            "phantom_dancer": pd_stacks,
            "kraken": kraken_hits,
            "yuntal_crit": ytcrit,
            "ad": current_ad,
            "fiend_remaining": fh,
            "fiend_until": fiend_until,
            "yuntal_until": yt_until,
            "bonus_as_total": s["bba"]
            + s["lvbas"]
            + total("as")
            + dyn
            + float(state.get("bonus_as", 0)),
        }
