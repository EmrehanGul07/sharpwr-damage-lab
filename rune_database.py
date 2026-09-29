"""SharpWR rune database — Patch 7.3 user-verified tooltip dataset.

Keep utility/defensive runes here even when the current AA simulator does not consume
those effects yet. Unknown exact per-level curves are stored as ranges, never guessed.
"""

RUNE_DATABASE = {
# KEY RUNES (12)
"First Strike":{"tree":"Key Rune","kind":"damage","tooltip":"Initiating champion combat (or damaging within 0.25s of engaging) grants 10 gold and First Strike for 3s: deal 7% bonus true damage. Bonus gold: ranged 45%, melee 60% of bonus damage. Cooldown 20–13s (level scaling).","data":{"bonus_true_damage_pct":7,"duration":3,"cooldown_range":[20,13]}},
"Ice Overlord":{"tree":"Key Rune","kind":"cc_defense_damage","tooltip":"Immobilizing a champion creates ice for 3s. Slow: (1% bonus HP + 15)%. Gain 35 + 75% bonus Armor/MR for 2.5s. Explosion deals 15–100 (level scaling) + 5% bonus HP magic damage. Cooldown 20s.","data":{"magic_damage_range":[15,100],"bonus_hp_ratio":0.05,"cooldown":20}},
"Phase Rush":{"tree":"Key Rune","kind":"mobility_haste","tooltip":"Hit a champion 3 times with attacks/abilities within 4s: gain movement speed and +10 Basic Ability Haste for 3s and reduce remaining basic ability cooldowns by 20%. Cooldown 21–7s.","data":{"hits":3,"window":4,"basic_ah":10,"remaining_cd_reduction_pct":20,"duration":3}},
"Arcane Comet":{"tree":"Key Rune","kind":"ability_damage","tooltip":"Ability damage launches a comet. Damage: 15–100 (level scaling) + 2 × total champion hits + 10% bonus AD + 5% AP. Cooldown 16–8s.","data":{"damage_range":[15,100],"bonus_ad_ratio":0.10,"ap_ratio":0.05}},
"Aery":{"tree":"Key Rune","kind":"damage_shield","tooltip":"Attacks/abilities send Aery. Damage: 15–70 (level scaling) + 10% bonus AD + 5% AP. Shield: 25–120 (level scaling) + 10% bonus AD + 5% AP. Cannot resend until Aery returns.","data":{"damage_range":[15,70],"shield_range":[25,120],"bonus_ad_ratio":0.10,"ap_ratio":0.05}},
"Guardian":{"tree":"Key Rune","kind":"shield","tooltip":"Guard nearby allies for 2.5s. On sufficient champion damage, shield both for 1.5s. Shield: 40–165 + 6% bonus HP + 15% AP. Cooldown 55–25s.","data":{"shield_range":[40,165],"bonus_hp_ratio":0.06,"ap_ratio":0.15}},
"Grasp of the Undying":{"tree":"Key Rune","kind":"damage_heal_growth","tooltip":"Every 3s in combat, next champion attack: 3.3% max HP bonus magic damage, heal 1.3% max HP, permanently +10 HP. Ranged effects reduced by 60%.","data":{"charge_time":3,"max_hp_damage_pct":3.3,"max_hp_heal_pct":1.3,"permanent_hp":10,"ranged_multiplier":0.40}},
"Conqueror":{"tree":"Key Rune","kind":"adaptive_force","tooltip":"Separate attacks/abilities grant Adaptive Force for 6s, max 6 stacks. Each stack: 3–5 bonus AD or 5–8 AP (level scaling). At full stacks: ranged 5% / melee 9% bonus Omnivamp.","data":{"max_stacks":6,"ad_per_stack_range":[3,5],"ap_per_stack_range":[5,8],"ranged_omnivamp_pct":5}},
"Fleet Footwork":{"tree":"Key Rune","kind":"sustain_mobility","tooltip":"At 100 Energy, next attack gains 40% AS, heals 15–110 + 15% bonus AD + 10% AP, and grants 20% MS for 1s. Champion hit restores 8% missing Mana/Energy.","data":{"energy":100,"attack_speed_pct":40,"heal_range":[15,110],"bonus_ad_ratio":0.15,"ap_ratio":0.10}},
"Lethal Tempo":{"tree":"Key Rune","kind":"attack_speed_damage","tooltip":"Champion attacks grant AS for 6s, max 6 stacks. Ranged: +4.8% AS/stack. At max, attacks fire 6–20 adaptive damage (level scaling), increased 0.33% per 1% bonus AS.","data":{"max_stacks":6,"ranged_as_per_stack_pct":4.8,"ranged_damage_range":[6,20],"ranged_bonus_as_damage_ratio":0.0033}},
"Empowerment":{"tree":"Key Rune","kind":"damage_amp","tooltip":"3 consecutive champion hits deal 40–165 adaptive damage (level scaling) and amplify damage dealt by 8% until leaving combat. Cooldown 4s.","data":{"hits":3,"damage_range":[40,165],"damage_amp_pct":8,"cooldown":4}},
"Dark Harvest":{"tree":"Key Rune","kind":"damage_growth","tooltip":"Damaging a champion below 50% HP deals 35 + 11 per soul + 10% bonus AD + 5% AP adaptive damage and harvests a soul. Cooldown 20s; 1s after takedown.","data":{"threshold_pct":50,"base_damage":35,"damage_per_soul":11,"bonus_ad_ratio":0.10,"ap_ratio":0.05,"cooldown":20}},

# PRECISION (9)
"Brutal":{"tree":"Precision","kind":"attack_damage","tooltip":"Attacks deal 6 + 8% bonus AD bonus adaptive damage to champions.","data":{"base_damage":6,"bonus_ad_ratio":0.08}},
"Triumph":{"tree":"Precision","kind":"takedown_sustain","tooltip":"Champion takedowns restore 10% missing Health and 10% max Mana/Energy and grant 35 Movement Speed for 2s.","data":{"missing_hp_restore_pct":10,"resource_restore_pct":10,"movement_speed":35,"duration":2}},
"Battle Zeal":{"tree":"Precision","kind":"ability_damage","tooltip":"While in champion combat, gain 1.4% stacking basic ability damage amplification each second, up to 3 stacks.","data":{"amp_per_stack_pct":1.4,"max_stacks":3}},
"Last Stand":{"tree":"Precision","kind":"damage_amp","tooltip":"Below 60% own HP, attacks vs champions deal 5–11% bonus damage; maximum below 30% HP.","data":{"start_hp_pct":60,"max_hp_pct":30,"amp_range_pct":[5,11]}},
"Cut Down":{"tree":"Precision","kind":"damage_amp","tooltip":"Attacks deal 6.5% bonus damage to champions above 60% Health.","data":{"target_hp_above_pct":60,"amp_pct":6.5}},
"Coup de Grace":{"tree":"Precision","kind":"damage_amp","tooltip":"Deal 8% bonus damage to champions below 40% Health.","data":{"target_hp_below_pct":40,"amp_pct":8}},
"Legend: Alacrity":{"tree":"Precision","kind":"attack_speed","tooltip":"Gain 3% Attack Speed. Takedowns grant up to an additional 18% Attack Speed (21% total max). Exact stack progression not supplied.","data":{"base_as_pct":3,"additional_as_max_pct":18,"total_as_max_pct":21}},
"Legend: Haste":{"tree":"Precision","kind":"haste","tooltip":"Takedowns grant Ability Haste, capped at 15. Exact stack progression not supplied.","data":{"max_ability_haste":15}},
"Legend: Bloodline":{"tree":"Precision","kind":"omnivamp","tooltip":"Gain 1% Omnivamp. Takedowns grant up to an additional 7% (8% total max). Exact stack progression not supplied.","data":{"base_omnivamp_pct":1,"additional_max_pct":7,"total_max_pct":8}},

# DOMINATION (9)
"Eyeball Collection":{"tree":"Domination","kind":"adaptive_force","tooltip":"Champion or epic monster takedown grants 1.5 AD, max 8 stacks (+12 AD).","data":{"ad_per_stack":1.5,"max_stacks":8}},
"Hubris":{"tree":"Domination","kind":"takedown_adaptive_force","tooltip":"Champion takedown grants 5 + champion kill count Adaptive Force for 30s.","data":{"base_force":5,"duration":30}},
"Tyrant":{"tree":"Domination","kind":"damage","tooltip":"Against a champion below 50% HP, deal 20–70 (level scaling) + 6% bonus AD + 3% AP adaptive damage. Cooldown 10s.","data":{"threshold_pct":50,"damage_range":[20,70],"bonus_ad_ratio":0.06,"ap_ratio":0.03,"cooldown":10}},
"Chain Assault":{"tree":"Domination","kind":"ability_mark_damage","tooltip":"Ability damage marks a target. Next 2 attacks/active abilities deal 12–38 (level scaling) + 3% bonus AD + 1.5% AP adaptive damage. Cooldown 15s.","data":{"charges":2,"damage_range":[12,38],"bonus_ad_ratio":0.03,"ap_ratio":0.015,"cooldown":15}},
"Sudden Impact":{"tree":"Domination","kind":"true_damage","tooltip":"After dash/leap/blink/teleport/stealth, next attack/ability within 4s deals 10–65 true damage (level scaling). Cooldown 15s.","data":{"damage_range":[10,65],"window":4,"cooldown":15}},
"Cheap Shot":{"tree":"Domination","kind":"true_damage","tooltip":"Damage to a movement-impaired champion deals 10–45 true damage (level scaling). Cooldown 7s.","data":{"damage_range":[10,45],"cooldown":7}},
"Zombie Ward":{"tree":"Domination","kind":"adaptive_force_utility","tooltip":"Enemy ward takedowns spawn a Zombie Ward for 120s and grant 3 AD or 6 AP, max 5 stacks. Default: max stacks.","data":{"ad_per_stack":3,"ap_per_stack":6,"max_stacks":5,"default_stacks":5}},
"Empowered Attack":{"tree":"Domination","kind":"attack_damage","tooltip":"Every 8s next champion attack deals 20–60 bonus adaptive damage (level scaling). Ranged champions deal 80% of this damage.","data":{"damage_range":[20,60],"ranged_multiplier":0.80,"cooldown":8}},
"Relentless Hunter":{"tree":"Domination","kind":"movement","tooltip":"Gain 10 out-of-combat Movement Speed. Champion/epic monster takedowns grant +2 OOC MS, max 5 stacks. Default: max stacks.","data":{"base_ooc_ms":10,"ooc_ms_per_stack":2,"max_stacks":5,"default_stacks":5}},

# RESOLVE (10)
"Overgrowth":{"tree":"Resolve","kind":"health_growth","tooltip":"Every 3 nearby enemy minions or 3 monsters killed permanently grants +3 max HP. At 30 stacks gain +3% Health. Default progression input: 60 nearby units.","data":{"units_per_proc":3,"hp_per_proc":3,"threshold_stacks":30,"health_amp_pct":3,"default_units":60}},
"Bone Plating":{"tree":"Resolve","kind":"damage_reduction","tooltip":"After champion damage, current and next 3 champion attacks/abilities within 1.5s deal 30–60 (level scaling) less damage. Cooldown 40s.","data":{"reduction_range":[30,60],"hits":4,"window":1.5,"cooldown":40}},
"Second Wind":{"tree":"Resolve","kind":"healing","tooltip":"Gain 5 Health every 5s. After champion damage regenerate 3 + 1.5% missing Health over 5s. Doubled for melee.","data":{"passive_heal":5,"passive_interval":5,"missing_hp_ratio":0.015,"duration":5}},
"Perseverance":{"tree":"Resolve","kind":"tenacity_defense","tooltip":"Gain 10% Tenacity. When immobilized gain 10–15 Armor and MR (level scaling) for 1.5s.","data":{"tenacity_pct":10,"resist_range":[10,15],"duration":1.5}},
"Revitalize":{"tree":"Resolve","kind":"heal_shield_amp","tooltip":"Gain 5% amplification when healing or shielding. If target Health is below 40%, gain an additional 10% amplification.","data":{"base_amp_pct":5,"low_hp_threshold_pct":40,"additional_amp_pct":10}},
"Nullifying Orb":{"tree":"Resolve","kind":"shield","tooltip":"Champion damage that drops you below 35% max HP grants a 60–180 (level scaling) shield for 4s. Cooldown 60s.","data":{"threshold_pct":35,"shield_range":[60,180],"duration":4,"cooldown":60}},
"Unshakeable":{"tree":"Resolve","kind":"defense","tooltip":"Gain 3% Armor/MR plus 2% per nearby enemy champion, max 3. At max nearby enemies also gain 20% Slow Resist. Default: 3 nearby enemies.","data":{"base_resist_pct":3,"resist_per_enemy_pct":2,"max_enemies":3,"default_enemies":3,"max_slow_resist_pct":20}},
"Courage of the Colossus":{"tree":"Resolve","kind":"shield","tooltip":"Immobilizing an enemy champion grants a shield absorbing 25–45 (level scaling) + 1% max Health for 3s. Cooldown 18s.","data":{"shield_range":[25,45],"max_hp_ratio":0.01,"duration":3,"cooldown":18}},
"Font of Life":{"tree":"Resolve","kind":"healing","tooltip":"Attacks/abilities hitting a champion heal you and the lowest-health nearby ally. Ally: 1.5% max HP + 5% AP. You: 1% max HP + 5% AP. Cooldown 20s. Healing is 130% effective for melee. Does not trigger at full health/no ally.","data":{"self_max_hp_ratio":0.01,"ally_max_hp_ratio":0.015,"ap_ratio":0.05,"melee_multiplier":1.30,"cooldown":20}},
"Demolish":{"tree":"Resolve","kind":"turret_damage","tooltip":"Third attack against a turret deals bonus physical damage. Ranged: 50 + 20% max Health; melee: 85 + 28% max Health. Cooldown 30s.","data":{"attack_number":3,"ranged_base":50,"ranged_max_hp_ratio":0.20,"melee_base":85,"melee_max_hp_ratio":0.28,"cooldown":30}},

# SORCERY (11)
"Gathering Storm":{"tree":"Sorcery","kind":"scaling_adaptive_force","tooltip":"At 6 minutes gain +2 AD; then every 3 minutes increases following the verified sequence 2 → 5 → 9 → 14 → 20 → 27… Exact continuation formula not supplied.","data":{"first_minute":6,"interval_minutes":3,"verified_ad_sequence":[2,5,9,14,20,27]}},
"Absolute Focus":{"tree":"Sorcery","kind":"adaptive_force","tooltip":"While above 65% own Health, gain 2–20 AD (level scaling).","data":{"threshold_pct":65,"ad_range":[2,20]}},
"Scorch":{"tree":"Sorcery","kind":"ability_damage","tooltip":"Ability hit deals 21–49 magic damage after 1s. Cooldown 8s.","data":{"damage_range":[21,49],"delay":1,"cooldown":8}},
"Axiom Arcanist":{"tree":"Sorcery","kind":"ultimate","tooltip":"Ultimate damage/heal/shield +10%; AoE ultimate damage increase +5%. Champion takedown reduces remaining ultimate cooldown by 7%.","data":{"ultimate_amp_pct":10,"aoe_ultimate_damage_pct":5,"takedown_cd_reduction_pct":7}},
"Manaflow Band":{"tree":"Sorcery","kind":"mana_growth","tooltip":"Ability or empowered-attack champion hits permanently grant +30 max Mana, up to +300. Default: full +300.","data":{"mana_per_stack":30,"max_mana":300,"default_mana":300}},
"Transcendence":{"tree":"Sorcery","kind":"haste","tooltip":"Level 1: +5 Ability Haste. Level 5: +5 more. Level 9: basic ability hit reduces ability cooldown time by 8%; this effect has 8s cooldown.","data":{"level1_ah":5,"level5_additional_ah":5,"level9_cd_reduction_pct":8,"proc_cooldown":8}},
"Celerity":{"tree":"Sorcery","kind":"movement","tooltip":"Gain 2% Movement Speed. All Movement Speed bonuses on you are increased by 7%.","data":{"movement_speed_pct":2,"bonus_ms_amp_pct":7}},
"Nimbus Cloak":{"tree":"Sorcery","kind":"movement","tooltip":"After using a summoner spell gain 10–40% Movement Speed (level scaling) for 3s.","data":{"movement_speed_range_pct":[10,40],"duration":3}},
"Ixtali Seedjar":{"tree":"Sorcery","kind":"utility","tooltip":"After destroying a plant, gain a seed replacing your trinket for 60s. Seeds become obtainable 2 minutes after game start. Each plant has a unique 30s cooldown.","data":{"seed_duration":60,"available_after_minutes":2,"plant_cooldown":30}},
"Hexflash":{"tree":"Sorcery","kind":"mobility","tooltip":"While Flash is on cooldown, channel up to 2s to blink; distance depends on channel time. Cooldown 18s; becomes 6s when entering champion combat.","data":{"max_channel":2,"cooldown":18,"combat_cooldown":6}},
"Botanist":{"tree":"Sorcery","kind":"plant_utility","tooltip":"Destroying a plant grants 10 gold and empowers it. Honeyfruit healing +20%; Scryer's Bloom vision duration +20%; Blast Cone grants 40% Movement Speed for 2.5s after knockback.","data":{"gold":10,"honeyfruit_heal_amp_pct":20,"scryer_vision_amp_pct":20,"blast_cone_ms_pct":40,"blast_cone_ms_duration":2.5}},
}

RUNE_TREES = {
    tree: [name for name, rune in RUNE_DATABASE.items() if rune["tree"] == tree]
    for tree in ("Key Rune","Precision","Domination","Resolve","Sorcery")
}

RUNE_SLOTS = {
    "Domination": {
        1:["Cheap Shot","Sudden Impact","Empowered Attack"],
        2:["Chain Assault","Tyrant","Hubris"],
        3:["Eyeball Collection","Relentless Hunter","Zombie Ward"],
    },
    "Precision": {
        1:["Brutal","Triumph","Battle Zeal"],
        2:["Last Stand","Cut Down","Coup de Grace"],
        3:["Legend: Alacrity","Legend: Haste","Legend: Bloodline"],
    },
    "Resolve": {
        1:["Demolish","Font of Life","Courage of the Colossus","Unshakeable"],
        2:["Second Wind","Nullifying Orb","Bone Plating"],
        3:["Overgrowth","Revitalize","Perseverance"],
    },
    "Sorcery": {
        1:["Axiom Arcanist","Manaflow Band","Botanist","Hexflash"],
        2:["Transcendence","Celerity","Absolute Focus"],
        3:["Scorch","Nimbus Cloak","Gathering Storm","Ixtali Seedjar"],
    },
}

assert len(RUNE_DATABASE) == 51
assert {k:len(v) for k,v in RUNE_TREES.items()} == {
    "Key Rune":12,"Precision":9,"Domination":9,"Resolve":10,"Sorcery":11
}
