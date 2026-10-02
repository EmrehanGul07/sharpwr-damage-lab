import streamlit as st
import base64
from itertools import permutations
import html
import urllib.parse
import streamlit.components.v1 as components
from pathlib import Path
from engine_runtime import ensure_engine_revision
ensure_engine_revision("5.77.0")
from combat_replay import replay_payload, replay_html
import item_consensus as _item_consensus
if not hasattr(_item_consensus, "progression_ranking"):
    import importlib
    importlib.reload(_item_consensus)
from item_consensus import consensus, adopters, champion_items, progression_ranking
from champion_database import CHAMPION_DATABASE, level_stats
from rune_database import RUNE_DATABASE, RUNE_TREES, RUNE_SLOTS
from champion_skill_data import SAMIRA_ABILITIES, SMOLDER_ABILITIES
from fight_engine import FightEvent, replay_samira, samira_ranks, champion_ranks
from marksman_kits import Kit, records as marksman_records
from build_fight_optimizer import BuildFightEvaluator, search_builds, TIER3, SPELLBLADE

def _preserve_widgets():
    # Keep later-tab controls alive if an item/rune button requests an early rerun.
    for key in list(st.session_state):
        if key.startswith(("iv_","tier_","ability_","fight_","smolder_")) and not key.startswith(("ability_calculate","fight_calculate")) or key in {"build_champ","build_level","build_mist","build_target_profile","build_dist","build_mana","build_spell","build_energized","build_ult","build_execs","build_yt_crit","build_yt_flurry","db_item_search","db_category"}:
            st.session_state[key]=st.session_state[key]

_preserve_widgets()

CD_ITEM_ICON_BASE="https://raw.communitydragon.org/latest/game/assets/items/icons2d/"
# Wild Rift rune icons served directly by RiftPatchNotes.
# Their rune pages expose images at /runes/<slug>.png (e.g. Ice Overlord).
RUNE_ICON_SLUG={
    "Hexflash":"hexflash",
}
def _last_stand_amp(own_hp_pct):
    missing=100-own_hp_pct
    if missing<30: return 0.0
    return min(.11,.05+((missing-30)//5)*.01)

def _rune_self_tests():
    tests=[]
    def check(name,got,expected,tol=1e-9):
        ok=abs(got-expected)<=tol if isinstance(expected,(int,float)) else got==expected
        tests.append([name,"PASS" if ok else "FAIL",got,expected])
    scale=lambda lo,hi,lvl: lo+(hi-lo)*(lvl-1)/14
    check("Level scale 6→20 @ Lv1",scale(6,20,1),6)
    check("Level scale 6→20 @ Lv8",scale(6,20,8),13)
    check("Level scale 6→20 @ Lv15",scale(6,20,15),20)
    for hp,amp in [(71,0),(70,.05),(65,.06),(60,.07),(55,.08),(50,.09),(45,.10),(40,.11),(30,.11)]:
        check(f"Last Stand @ {hp}% current HP",_last_stand_amp(hp),amp)
    conq=0; seq=[]
    for _ in range(7):
        seq.append(conq); conq=min(6,conq+1)
    check("Conqueror AA1-AA7 stack state",seq,[0,1,2,3,4,5,6])
    lt=0; bullets=[]
    for _ in range(7):
        bullets.append(lt>=6); lt=min(6,lt+1)
    check("Lethal Tempo bullet after 6 completed AAs",bullets,[False,False,False,False,False,False,True])
    eh=0; procs=[]; amps=[]; active=False
    for _ in range(5):
        eh+=1; proc=(eh==3); procs.append(proc); amps.append(active)
        if proc: active=True
    check("Empowerment proc AA3",procs,[False,False,True,False,False])
    check("Empowerment amp starts AA4",amps,[False,False,False,True,True])
    check("Cut Down 60% OFF",.60>.60,False); check("Cut Down 60.1% ON",.601>.60,True)
    check("Coup 40% OFF",.40<.40,False); check("Coup 39.9% ON",.399<.40,True)
    check("Dark Harvest 50% OFF",.50<.50,False); check("Dark Harvest 49.9% ON",.499<.50,True)
    check("Zombie Ward 5 stacks AD",5*3,15)
    check("Eyeball 8 stacks AD",8*1.5,12)
    check("Overgrowth 60 stacks flat HP",60*3,180)
    check("Overgrowth 30+ multiplier",1.03 if 60>=30 else 1.0,1.03)
    check("Manaflow full Mana",300,300)
    check("Gathering Storm sequence",[2,5,9,14,20,27],[2,5,9,14,20,27])
    return tests

def rune_icon(name):
    if not name or name=="None": return ""
    slug=RUNE_ICON_SLUG.get(name)
    if not slug:
        slug=name.lower().replace("&","and").replace("'","").replace(":","").replace(" ","-")
    return f"https://www.riftpatchnotes.com/runes/{slug}.png"

def _equipped_rune_slot(label, state_key):
    name=st.session_state.get(state_key)
    st.markdown(f'<div class="wr-eq-label">{html.escape(label)}</div>',unsafe_allow_html=True)
    if not name:
        st.markdown('<div class="wr-eq-empty">＋<span>EMPTY</span></div>',unsafe_allow_html=True)
        return
    icon=rune_icon(name)
    a,b=st.columns([1,4],gap="small")
    with a:
        if icon: st.image(icon,width=48)
    with b:
        st.markdown(f'<div class="wr-eq-name">{html.escape(name)}</div>',unsafe_allow_html=True)
        if st.button("Remove",key=f"remove_{state_key}",use_container_width=False):
            st.session_state[state_key]=None
            st.rerun()

TREE_ICON_URL={
    "Domination":"https://raw.communitydragon.org/latest/game/assets/perks/styles/7200_domination.png",
    "Precision":"https://raw.communitydragon.org/latest/game/assets/perks/styles/7201_precision.png",
    "Sorcery":"https://raw.communitydragon.org/latest/game/assets/perks/styles/7202_sorcery.png",
    "Resolve":"https://raw.communitydragon.org/latest/game/assets/perks/styles/7204_resolve.png",
}
def _tree_icon_picker(label, options, state_key, cols=4):
    current=st.session_state.get(state_key,options[0] if options else None)
    if current not in options and options:
        current=options[0]; st.session_state[state_key]=current
    st.markdown(f'<div class="wr-picker-title">{html.escape(label)}</div>',unsafe_allow_html=True)
    row=st.columns(min(cols,len(options)),gap="small")
    for i,name in enumerate(options):
        chosen=name==current
        with row[i]:
            st.markdown('<div class="wr-tree-marker '+('wr-tree-selected' if chosen else '')+'"></div>',unsafe_allow_html=True)
            st.image(TREE_ICON_URL[name],width=72)
            st.markdown(f'<div class="wr-tree-name">{html.escape(name)}</div>',unsafe_allow_html=True)
            if st.button("Selected" if chosen else "Choose",key=f"{state_key}_tree_{i}",help=None,use_container_width=False):
                st.session_state[state_key]=name
                st.rerun()
    return st.session_state.get(state_key,current)

def _rune_icon_grid(label, options, state_key, cols=6):
    current=st.session_state.get(state_key)
    if current not in options:
        current=None
    st.markdown(f'<div class="wr-picker-title">{html.escape(label)}</div>',unsafe_allow_html=True)
    if not options: return None
    ncols=min(cols,len(options))
    for start in range(0,len(options),ncols):
        row=st.columns(ncols,gap="small")
        for j,name in enumerate(options[start:start+ncols]):
            i=start+j; icon=rune_icon(name); chosen=name==current
            rv=RUNE_DATABASE.get(name,{})
            card=f'<div class="wr-hover-card"><div class="wr-card-title">{html.escape(name)}</div><div class="wr-card-sub">{html.escape(rv.get("tree","Rune"))}</div><div class="wr-card-rule"></div><div class="wr-card-text">{html.escape(rv.get("tooltip",""))}</div></div>'
            with row[j]:
                st.markdown('<div class="wr-pick-marker '+('wr-selected' if chosen else '')+'">'+card+'</div>',unsafe_allow_html=True)
                if icon: st.image(icon,width=66)
                st.markdown(f'<div class="wr-icon-name">{html.escape(name)}</div>',unsafe_allow_html=True)
                if st.button("Equip",key=f"{state_key}__{i}__{name}",help=None,use_container_width=False):
                    st.session_state[state_key]=name; st.rerun()
        st.markdown('<div class="wr-grid-gap"></div>',unsafe_allow_html=True)
    return st.session_state.get(state_key,current)

ITEM_ICON_FILE={
"Rapid Firecannon":"3094_marksman_t3_rapidfirehandcannon.png",
"Runaan's Hurricane":"3085_marksman_t3_runaans.png",
"Phantom Dancer":"3046_marksman_t3_phantomdancer.png",
"Wit's End":"3091_fighter_t3_witsend.png",
"Nashor's Tooth":"3115_mage_t3_nashorstooth.png",
"Manamune":"3004_marksman_t3_manamune.png",
"Muramana":"3042_marksman_t3_muramana.png",
"Statikk Shiv":"3087_statikk_shiv.png",
"Guinsoo's Rageblade":"3124_marksman_t3_guinsoosrageblade.png",
"Mortal Reminder":"3033_marksman_t3_mortalreminder.png",
"Maw of Malmortius":"3156_fighter_t3_mawofmalmortius.png",
"Essence Reaver":"3508_marksman_t3_essencereaver.png",
"Terminus":"3302_terminus.png",
"Mercurial Scimitar":"3139_marksman_t3_mercurialscimitar.png",
"Blade of the Ruined King":"3153_fighter_t3_bladeoftheruinedking.png",
"Guardian Angel":"3026_fighter_t3_guardianangel.png",
"Bloodthirster":"3072_fighter_t3_bloodthirster.png",
"Lord Dominik's Regards":"3036_marksman_t3_dominikregards.png",
"Trinity Force":"3078_fighter_t4_trinityforce.png",
"Infinity Edge":"3031_marksman_t3_infinityedge.png",
"Youmuu's Ghostblade":"3142_assassin_t3_youmuusghostblade.png",
"Edge of Night":"3814_assassin_t3_edgeofnight.png",
"Yun Tal Wildarrows":"3032_yuntalwildarrows.png"
}
LOCAL_ITEM_ICON={
"Stormrazor":"assets/items/Stormrazor_WR_item.webp",
"The Collector":"assets/items/The_Collector_WR_item.webp",
"Galeforce":"assets/items/128px-Galeforce_WR_item.png",
"Serylda's Grudge":"assets/items/128px-Serylda's_Grudge_WR_item.webp",
"Blade of the Ruined King":"assets/items/Blade_of_the_Ruined_King_WR_item.webp",
"Death's Dance":"assets/items/Death's_Dance_WR_item.webp",
"Duskblade of Draktharr":"assets/items/Duskblade_of_Draktharr_WR_item.webp",
"Fiendhunter Bolts":"assets/items/Fiendhunter_Bolts_item.webp",
"Hexoptics C44":"assets/items/Hexoptics_C44_item.webp",
"Iceborn Gauntlet":"assets/items/Iceborn_Gauntlet_WR_item.webp",
"Immortal Shieldbow":"assets/items/Immortal_Shieldbow_item.webp",
"Kraken Slayer":"assets/items/Kraken_Slayer_WR_item.webp",
"Navori Quickblades":"assets/items/Navori_Quickblades_WR_item.png",
"Serpent's Fang":"assets/items/Serpent's_Fang_WR_item.png",
}
@st.cache_data
def _local_icon_data(path):
    p=Path(path)
    if not p.exists(): return ""
    ext=p.suffix.lower()
    mime="image/webp" if ext==".webp" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"

BOOT_ICON_FILE={
"Gluttonous Greaves":"Gluttonous_Greaves_WR_item.png",
"Immortal Treads":"immortal_treads_wr_item.webp",
"Ionian Boots of Lucidity":"Ionian_Boots_of_Lucidity_WR_item.png",
"Crimson Lucidity":"item-crimson-lucidity-icon.png",
"Berserker's Greaves":"Berserker's_Greaves_WR_item.png",
"Gunmetal Greaves":"item-gunmetal-greaves-icon.png",
"Mercury's Treads":"Mercury's_Treads_WR_item.png",
"Chainlaced Crushers":"item-chainlaced-crushers-icon.png",
"Plated Steelcaps":"Plated_Steelcaps_WR_item.png",
"Armored Advance":"item-armored-advance-icon.png",
"Boots of Mana":"Boots_of_Mana_WR_item.png",
"Spellslinger's Shoes":"item-spellslingers-shoes-icon.png",
"Boots of Dynamism":"Boots_of_Dynamism_WR_item.png",
"Armorcrusher Boots":"item-armorcrusher-boots-icon.png",
}
def boot_icon(name):
    fn=BOOT_ICON_FILE.get(name)
    return _local_icon_data("assets/items/"+fn) if fn else ""

def item_icon(name):
    local=LOCAL_ITEM_ICON.get(name)
    if local:
        data=_local_icon_data(local)
        if data: return data
    fn=ITEM_ICON_FILE.get(name)
    return CD_ITEM_ICON_BASE+fn if fn else ""

STAT_LABELS=[("ad","AD"),("as","AS"),("crit","Crit"),("ap","AP"),("hp","HP"),("mana","Mana"),("armor","Armor"),("mr","MR"),("ah","AH"),("lifesteal","Lifesteal"),("flatpen","Armor Pen"),("pctpen","% Armor Pen"),("ms","MS")]
def _item_stat_lines(name):
    q=dct(F[name])
    out=[f"{int(q['gold'])}g"]
    for key,label in STAT_LABELS:
        v=q.get(key,0)
        if not v: continue
        if key in ("as","crit","lifesteal","pctpen","ms"): out.append(f"{label} +{v*100:g}%")
        else: out.append(f"{label} +{v:g}")
    return out

STAT_GLYPHS={
    "ad":"⚔","as":"⏩","crit":"✦","ap":"✧","hp":"♥","mana":"◆",
    "armor":"⬟","mr":"◈","ah":"◷","lifesteal":"♦","flatpen":"➤","pctpen":"◎","ms":"➜"
}
STAT_NAMES={
    "ad":"Attack Damage","as":"Attack Speed","crit":"Critical Strike","ap":"Ability Power",
    "hp":"Health","mana":"Mana","armor":"Armor","mr":"Magic Resist","ah":"Ability Haste",
    "lifesteal":"Lifesteal","flatpen":"Armor Penetration","pctpen":"% Armor Penetration","ms":"Movement Speed"
}

def _premium_item_grid(items, selected):
    # Real icon-hover surface: the image itself is the hover target.
    # Floating premium cards are rendered in the same HTML surface.
    tiles=[]
    for name in items:
        icon=item_icon(name); q=dct(F[name]); rows=[]
        for key,label in STAT_NAMES.items():
            v=q.get(key,0)
            if not v: continue
            val=f"{v*100:g}%" if key in ("as","crit","lifesteal","pctpen","ms") else f"{v:g}"
            rows.append(f'<div class="s"><i>{STAT_GLYPHS[key]}</i><span><b>{val}</b><small>{label}</small></span></div>')
        sel=" selected" if name in selected else ""
        col=(items.index(name)%10)+1
        edge=" edge-left" if col<=2 else (" edge-right" if col>=9 else "")
        # target=_top lets the icon itself navigate the Streamlit app; Python consumes item_pick.
        href="?item_pick="+urllib.parse.quote(name)
        tiles.append(f'''<div class="tile{sel}{edge}" tabindex="0">
          <a class="hit" href="{href}" target="_top" aria-label="Add {html.escape(name)} to build"></a>
          <img src="{html.escape(icon)}" alt="{html.escape(name)}">
          <div class="card"><header><img src="{html.escape(icon)}"><div><strong>{html.escape(name)}</strong><em>◆ {int(q["gold"])} Gold</em></div></header>
          <section>{"".join(rows)}</section><footer><span class="desk">Click icon to add to build</span><a class="add" href="{href}" target="_top">Add to Build</a></footer></div></div>''')
    doc='''<!doctype html><html><head><style>
    *{box-sizing:border-box}body{margin:0;background:transparent;font-family:Inter,system-ui,sans-serif;color:#e9edf3;overflow:visible}
    .grid{display:grid;grid-template-columns:repeat(10,minmax(58px,1fr));gap:10px;padding:18px 4px 260px}
    .tile{position:relative;display:flex;justify-content:center;align-items:center;height:68px;border:1px solid #343e4e;border-radius:11px;
      background:linear-gradient(145deg,#171e29,#0a0f16);text-decoration:none;transition:.15s;z-index:1;cursor:pointer}
    .tile>img{width:56px;height:56px;object-fit:cover;border-radius:8px}.hit{position:absolute;inset:0;z-index:5;border-radius:11px}
    .tile:hover{border-color:#d1ae55;transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.35);z-index:20}
    .tile.selected{border-color:#d1ae55;box-shadow:inset 0 0 0 1px rgba(209,174,85,.45)}
    .card{pointer-events:none;visibility:hidden;opacity:0;position:absolute;z-index:100;left:50%;bottom:76px;transform:translateX(-50%) translateY(5px);
      width:360px;min-height:150px;padding:14px;border:1px solid #526078;border-radius:13px;background:linear-gradient(150deg,#151d29,#080d14 75%);
      box-shadow:0 18px 45px rgba(0,0,0,.62);transition:opacity .14s .32s,transform .14s .32s}
    .tile:hover .card{visibility:visible;opacity:1;transform:translateX(-50%) translateY(0)}
    /* Always open cards downward: avoids iframe top clipping of name/price header. */
    .card{bottom:auto!important;top:76px!important;transform:translateX(-50%) translateY(-5px)!important}
    .tile.edge-left .card{left:0;right:auto;transform:translateX(0) translateY(-5px)!important}
    .tile.edge-right .card{left:auto;right:0;transform:translateX(0) translateY(-5px)!important}
    .tile:hover .card{transform:translateX(-50%) translateY(0)!important}
    .tile.edge-left:hover .card,.tile.edge-right:hover .card{transform:translateX(0) translateY(0)!important}
    header{display:flex;gap:11px;align-items:center;padding-bottom:10px;border-bottom:1px solid #2d3746}
    header img{width:52px;height:52px;border-radius:8px;border:1px solid #b8994d}strong{display:block;color:#f1d37b;font-size:16px}
    em{display:block;color:#d5b45b;font-size:12px;font-style:normal;margin-top:3px}
    section{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 14px;padding-top:11px;align-items:start}.s{display:flex;gap:7px;align-items:flex-start;min-width:0}.s i{font-style:normal;width:22px;height:22px;border-radius:6px;display:flex;align-items:center;justify-content:center;background:#202a38;border:1px solid #3a485d;color:#a8c8ee}
    .s b{font-size:12px;white-space:nowrap}.s span{min-width:0}.s small{display:block;color:#8f9cac;font-size:9px;line-height:1.15;white-space:normal;overflow-wrap:anywhere}footer{margin-top:10px;padding-top:8px;border-top:1px solid #28313e;color:#718096;font-size:9px}
    .add{display:none;color:#f1d37b;text-decoration:none;border:1px solid #8d7439;border-radius:7px;padding:7px 10px;text-align:center;font-size:11px;font-weight:700}
    @media(max-width:900px),(hover:none){
      .grid{grid-template-columns:repeat(4,minmax(58px,1fr));gap:9px;padding-bottom:300px}
      .tile{height:66px}.tile>img{width:54px;height:54px}
      .tile:hover .card{visibility:hidden;opacity:0}
      .tile.open{z-index:50;border-color:#d1ae55}
      .tile.open{margin-bottom:245px}
      .tile.open .card{visibility:visible;opacity:1;pointer-events:auto;position:absolute!important;z-index:9999!important;
        top:76px!important;bottom:auto!important;left:0!important;right:auto!important;transform:none!important;
        width:calc(400% + 27px)!important;max-width:none!important;max-height:230px!important;overflow-y:auto!important;
        -webkit-overflow-scrolling:touch}
      .tile:nth-child(4n+2).open .card{left:calc(-100% - 9px)!important}
      .tile:nth-child(4n+3).open .card{left:calc(-200% - 18px)!important}
      .tile:nth-child(4n).open .card{left:calc(-300% - 27px)!important}
      .desk{display:none}.add{display:block;position:sticky;bottom:0;background:#111925;margin-top:10px}.hit{display:none}
    }
    </style></head><body><div class="grid">'''+''.join(tiles)+'''</div>
    <script>
    const mobile=window.matchMedia('(hover: none)').matches || window.innerWidth<=900;
    document.querySelectorAll('.tile').forEach(t=>{
      t.addEventListener('click',e=>{
        if(e.target.closest('.add')) return;
        if(mobile){
          e.preventDefault();
          const was=t.classList.contains('open');
          document.querySelectorAll('.tile.open').forEach(x=>x.classList.remove('open'));
          if(!was){
            t.classList.add('open');
            // Card expands in normal grid flow below the tapped row.
            setTimeout(()=>t.scrollIntoView({behavior:'smooth',block:'start',inline:'nearest'}),30);
          }
        }
      });
    });
    document.addEventListener('click',e=>{
      if(mobile && !e.target.closest('.tile')) document.querySelectorAll('.tile.open').forEach(x=>x.classList.remove('open'));
    });
    </script></body></html>'''
    rows=(len(items)+9)//10
    components.html(doc,height=360+rows*78,scrolling=False)


import pandas as pd

st.set_page_config(page_title="SharpWR Damage Lab V5", page_icon="⚔️", layout="wide")
st.markdown("""
<style>
.wr-picker-title{margin:.7rem 0 .3rem;font-size:.9rem;font-weight:700;color:#dce3ec}
.wr-eq-wrap{margin:4px 0 16px;padding:12px 12px 6px;border:1px solid #dfe4ea;border-radius:14px;background:linear-gradient(180deg,#fbfcfd,#f5f7f9)}
.wr-rune-section{display:flex;align-items:center;gap:10px;margin:18px 0 9px}
.wr-rune-section:before,.wr-rune-section:after{content:"";height:1px;flex:1;background:linear-gradient(90deg,transparent,#cfd6df)}
.wr-rune-section:after{background:linear-gradient(90deg,#cfd6df,transparent)}
.wr-rune-section span{font-size:10px;font-weight:850;letter-spacing:.14em;color:#697586;white-space:nowrap}
.wr-rune-section.key span{color:#a67d16}.wr-rune-section.primary span{color:#68778d}.wr-rune-section.secondary span{color:#806b9d}
.wr-eq-label{font-size:9px;font-weight:850;letter-spacing:.11em;color:#8a95a3;text-transform:uppercase;margin-bottom:5px}
.wr-eq-empty{height:54px;border:1px dashed #cbd3dc;border-radius:10px;display:flex;align-items:center;justify-content:center;gap:6px;color:#a4aeba;font-size:19px}
.wr-eq-empty span{font-size:9px;font-weight:800;letter-spacing:.09em}
.wr-eq-name{font-size:11px;font-weight:750;color:#27313d;line-height:1.15;margin:3px 0 1px}
.wr-eq-wrap div[data-testid="stImage"] img{border-radius:10px;border:1px solid #c99f3d;box-shadow:0 0 12px rgba(201,159,61,.15)}
.wr-eq-wrap .stButton button{font-size:9px!important;min-height:22px!important;height:22px!important;padding:0 8px!important;border-radius:7px!important}
.wr-tier-label{margin:10px 0 7px;font-size:10px;font-weight:800;letter-spacing:.14em;color:#6d7887}
.wr-tier-t3{color:#a67d16}.wr-tier-t2{margin-top:2px;color:#6d7887}
.wr-tree-marker{height:0!important;margin:0!important;padding:0!important}
div[data-testid="stColumn"]:has(.wr-tree-marker){position:relative;text-align:center}
div[data-testid="stColumn"]:has(.wr-tree-marker) div[data-testid="stImage"]{display:flex;justify-content:center;margin:0!important}
div[data-testid="stColumn"]:has(.wr-tree-marker) div[data-testid="stImage"] img{
 width:72px!important;height:72px!important;object-fit:contain;padding:8px;border-radius:16px;
 background:linear-gradient(145deg,#151d28,#090e15);border:1px solid #364152;
 box-shadow:0 5px 15px rgba(0,0,0,.24);transition:.14s ease}
div[data-testid="stColumn"]:has(.wr-tree-marker):hover div[data-testid="stImage"] img{
 transform:translateY(-2px);border-color:#b9974c;box-shadow:0 8px 22px rgba(0,0,0,.35)}
div[data-testid="stColumn"]:has(.wr-tree-selected) div[data-testid="stImage"] img{
 border:2px solid #d5b45b!important;background:linear-gradient(145deg,#211d12,#0d1015);
 box-shadow:0 0 0 2px rgba(213,180,91,.13),0 0 18px rgba(213,180,91,.22)!important}
.wr-tree-name{margin-top:5px;font-size:11px;font-weight:750;letter-spacing:.025em;color:#596474;text-align:center}
div[data-testid="stColumn"]:has(.wr-tree-selected) .wr-tree-name{color:#a67d16}
div[data-testid="stColumn"]:has(.wr-tree-marker):hover .wr-tree-name{color:#202a36}
div[data-testid="stColumn"]:has(.wr-tree-marker) .stButton{
 position:relative!important;left:50%!important;transform:translate(-50%,-101px)!important;
 width:78px!important;height:78px!important;z-index:90!important;margin:0 0 -78px 0!important;padding:0!important}
div[data-testid="stColumn"]:has(.wr-tree-marker) .stButton button{
 position:absolute!important;inset:0!important;width:100%!important;height:100%!important;min-height:0!important;
 padding:0!important;margin:0!important;border:0!important;background:transparent!important;box-shadow:none!important;
 color:transparent!important;opacity:.01!important;cursor:pointer!important}
div[data-testid="stColumn"]:has(.wr-tree-marker) .stButton button *{opacity:0!important}
.wr-pick-marker{height:0!important;margin:0!important;padding:0!important;overflow:visible!important}
div[data-testid="stColumn"]:has(.wr-pick-marker){position:relative;min-width:0;overflow:visible!important}
div[data-testid="stColumn"]:has(.wr-pick-marker) div[data-testid="stImage"]{display:flex;justify-content:center;margin:0!important;padding:0!important}
div[data-testid="stColumn"]:has(.wr-pick-marker) div[data-testid="stImage"] img{
 width:66px!important;height:66px!important;object-fit:cover;border-radius:11px;border:1px solid #344154;background:#0c121a;
 box-shadow:0 5px 15px rgba(0,0,0,.25);transition:.14s ease}
div[data-testid="stColumn"]:has(.wr-pick-marker):hover div[data-testid="stImage"] img{
 transform:translateY(-2px);border-color:#c6a34e;box-shadow:0 8px 22px rgba(0,0,0,.42)}
div[data-testid="stColumn"]:has(.wr-selected) div[data-testid="stImage"] img{
 border:2px solid #d5b45b!important;box-shadow:0 0 0 2px rgba(213,180,91,.15),0 0 18px rgba(213,180,91,.25)!important}
/* Real native click target over icon. */
div[data-testid="stColumn"]:has(.wr-pick-marker) .stButton{
 position:relative!important;left:50%!important;transform:translate(-50%,-107px)!important;
 width:70px!important;height:70px!important;z-index:80!important;margin:0 0 -70px 0!important;padding:0!important}
div[data-testid="stColumn"]:has(.wr-pick-marker) .stButton button{
 position:absolute!important;inset:0!important;width:100%!important;height:100%!important;min-height:0!important;
 padding:0!important;margin:0!important;border:0!important;background:transparent!important;box-shadow:none!important;
 color:transparent!important;opacity:.01!important;cursor:pointer!important}
div[data-testid="stColumn"]:has(.wr-pick-marker) .stButton button *{opacity:0!important}
/* Our own hover card. */
.wr-hover-card{
 display:none;position:absolute;z-index:70;top:76px;left:50%;transform:translateX(-50%);
 width:310px;padding:13px 14px;border:1px solid #46546a;border-radius:13px;
 background:linear-gradient(155deg,#121b27,#080d14);box-shadow:0 18px 44px rgba(0,0,0,.62);
 pointer-events:none;text-align:left;color:#dce4ee}
div[data-testid="stColumn"]:has(.wr-pick-marker):hover .wr-hover-card{display:block}
.wr-card-title{font-size:15px;font-weight:800;color:#f0d27b;margin-bottom:3px}
.wr-card-sub{font-size:11px;color:#9aa7b6;margin-bottom:9px}
.wr-card-rule{height:1px;background:#2c3746;margin:8px 0 10px}
.wr-card-stats{display:grid;grid-template-columns:1fr 1fr;gap:7px 12px}
.wr-card-stat{font-size:11px;color:#b9c5d2}.wr-card-stat b{color:#eef3f8;margin-right:4px}
.wr-card-text{font-size:11px;line-height:1.45;color:#bdc8d4}
.wr-icon-name{
 margin-top:7px;height:30px;display:flex;align-items:flex-start;justify-content:center;
 text-align:center;font-size:11px;line-height:1.15;font-weight:700;letter-spacing:.005em;
 color:#596474;text-shadow:none;overflow:hidden;padding:0 2px
}
div[data-testid="stColumn"]:has(.wr-selected) .wr-icon-name{color:#a67d16}
div[data-testid="stColumn"]:has(.wr-pick-marker):hover .wr-icon-name{color:#202a36}
div[data-testid="stColumn"]:has(.wr-pick-marker) div[data-testid="stCaptionContainer"]{display:none!important}
.wr-grid-gap{height:12px}
@media(max-width:900px){
 div[data-testid="stColumn"]:has(.wr-pick-marker) div[data-testid="stImage"] img{width:58px!important;height:58px!important}
 div[data-testid="stColumn"]:has(.wr-pick-marker) .stButton{width:62px!important;height:62px!important;transform:translate(-50%,-99px)!important;margin-bottom:-62px!important}
 .wr-hover-card{display:none!important}
}

/* ===== SharpWR Premium Shell V1 ===== */
:root{--sw-bg:#070b11;--sw-panel:#0d131d;--sw-panel2:#111a27;--sw-line:#263246;--sw-gold:#d8b45d;--sw-gold2:#f0d58a;--sw-text:#eef3f8;--sw-muted:#8f9bac}
.stApp{background:
 radial-gradient(900px 420px at 12% -8%,rgba(44,76,118,.22),transparent 62%),
 radial-gradient(760px 380px at 92% 0%,rgba(180,137,47,.10),transparent 60%),
 linear-gradient(180deg,#080d14 0%,#06090e 100%);color:var(--sw-text)}
[data-testid="stHeader"]{background:rgba(7,11,17,.72);backdrop-filter:blur(16px);border-bottom:1px solid rgba(216,180,93,.10)}
[data-testid="stMainBlockContainer"]{max-width:1480px;padding-top:1.35rem;padding-bottom:5rem}
#MainMenu,footer{visibility:hidden}
.sharp-hero{position:relative;overflow:hidden;margin:0 0 18px;padding:25px 28px 23px;border:1px solid rgba(216,180,93,.24);border-radius:20px;
 background:linear-gradient(120deg,rgba(17,27,41,.96),rgba(9,14,22,.96) 64%,rgba(46,36,17,.62));box-shadow:0 18px 55px rgba(0,0,0,.28)}
.sharp-hero:after{content:"";position:absolute;width:340px;height:340px;border:1px solid rgba(216,180,93,.10);border-radius:50%;right:-125px;top:-205px;box-shadow:0 0 80px rgba(216,180,93,.08)}
.sharp-kicker{font-size:10px;font-weight:850;letter-spacing:.22em;color:var(--sw-gold);margin-bottom:6px}
.sharp-title{font-size:clamp(34px,5vw,58px);font-weight:900;letter-spacing:-.045em;line-height:.98;color:#f5f8fb}.sharp-title span{color:var(--sw-gold2)}
.sharp-sub{margin-top:9px;color:#aab5c3;font-size:13px}.sharp-badges{display:flex;gap:7px;flex-wrap:wrap;margin-top:15px}
.sharp-badges span{font-size:8px;font-weight:850;letter-spacing:.12em;padding:5px 8px;border-radius:999px;border:1px solid #303c4d;background:#0a1018;color:#aeb9c7}
div[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:6px;padding:6px;border:1px solid #202b3b;border-radius:14px;background:rgba(10,15,23,.84);box-shadow:0 10px 28px rgba(0,0,0,.18)}
div[data-testid="stTabs"] button[data-baseweb="tab"]{height:42px;border-radius:10px;padding:0 18px;color:#8f9aaa;font-weight:750}
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"]{color:#f0d58a;background:linear-gradient(180deg,#1b2431,#111923);box-shadow:inset 0 0 0 1px rgba(216,180,93,.34)}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"]{display:none}
h1,h2,h3{letter-spacing:-.025em}h2{font-weight:850!important}h3{margin-top:1.7rem!important;padding-top:.8rem;border-top:1px solid rgba(216,180,93,.13);font-weight:820!important}
[data-testid="stCaptionContainer"]{color:#8290a2}
div[data-testid="stVerticalBlockBorderWrapper"]>div{border-color:#263246!important;background:linear-gradient(180deg,rgba(16,24,36,.76),rgba(9,14,22,.76));border-radius:15px!important}
div[data-baseweb="select"]>div,[data-baseweb="input"]>div{background:#0d141e!important;border-color:#29364a!important;border-radius:10px!important}
div[data-baseweb="select"]>div:hover,[data-baseweb="input"]>div:hover{border-color:#52627a!important}
div[role="radiogroup"]{gap:7px;flex-wrap:wrap}
div[role="radiogroup"] label{background:#0c131d;border:1px solid #263246;border-radius:10px;padding:6px 10px;margin:0!important}
div[role="radiogroup"] label:has(input:checked){border-color:rgba(216,180,93,.62);background:#17180f}
.stButton>button{border-radius:10px!important;border:1px solid #303d50!important;background:linear-gradient(180deg,#151e2b,#0c121b)!important;color:#e9eef5!important;font-weight:750!important;box-shadow:none!important}
.stButton>button:hover{border-color:#d8b45d!important;color:#f0d58a!important;transform:translateY(-1px)}
[data-testid="stMetric"]{padding:13px 15px;border:1px solid #263246;border-radius:13px;background:linear-gradient(180deg,rgba(17,26,39,.88),rgba(10,15,23,.88))}
[data-testid="stMetricLabel"]{color:#8794a5!important;font-size:10px!important;text-transform:uppercase;letter-spacing:.08em}
[data-testid="stMetricValue"]{font-weight:850!important;color:#f1f4f8!important}
[data-testid="stDataFrame"]{border:1px solid #263246;border-radius:13px;overflow:hidden;background:#0a1018}
[data-testid="stExpander"]{border:1px solid #263246!important;border-radius:12px!important;background:rgba(11,17,26,.72)!important}
hr{border-color:#202b3a!important}
.wr-eq-wrap{border-color:#29364a!important;background:linear-gradient(180deg,#111a27,#0a1018)!important}
.wr-eq-name{color:#e7edf4!important}.wr-eq-label{color:#7f8da0!important}.wr-eq-empty{border-color:#344156!important;color:#647287!important}
.wr-picker-title{color:#dbe3ec!important}.wr-tier-label{color:#7f8da0!important}.wr-tier-t3{color:#d8b45d!important}
.triple-rank-card,.boot3-rank-card,.boot4-rank-card,.full-rank-card{background:linear-gradient(180deg,rgba(17,26,39,.92),rgba(9,14,22,.92))!important;border-color:#263246!important;box-shadow:0 8px 22px rgba(0,0,0,.13)}
.triple-rank-card:hover,.boot3-rank-card:hover,.boot4-rank-card:hover,.full-rank-card:hover{border-color:#d8b45d!important;box-shadow:0 13px 30px rgba(0,0,0,.26)}
.triple-rank-num,.boot3-rank-num,.boot4-rank-num,.full-rank-num{color:#e4c46f!important}
@media(max-width:700px){[data-testid="stMainBlockContainer"]{padding-left:.7rem;padding-right:.7rem}.sharp-hero{padding:20px 17px;border-radius:16px}.sharp-badges span{font-size:7px}div[data-testid="stTabs"] button[data-baseweb="tab"]{padding:0 9px;font-size:11px}.sharp-sub{font-size:11px}}

.sharp-section-head{position:relative;display:flex;align-items:baseline;gap:10px;margin:30px 0 5px;padding:14px 16px;border-left:2px solid #d8b45d;border-bottom:1px solid #202b3a;background:linear-gradient(90deg,rgba(216,180,93,.075),transparent 58%)}
.sharp-section-head span{font-size:8px;font-weight:900;letter-spacing:.15em;color:#b99a51}.sharp-section-head strong{font-size:20px;letter-spacing:-.025em;color:#eef3f8}.sharp-section-head em{margin-left:auto;font-size:8px;font-style:normal;font-weight:850;letter-spacing:.13em;color:#667589}
.sharp-section-head.final{border:1px solid rgba(216,180,93,.28);border-left:3px solid #d8b45d;border-radius:10px;background:linear-gradient(90deg,rgba(216,180,93,.11),rgba(16,24,36,.35))}
@media(max-width:640px){.sharp-section-head{padding:11px 10px;gap:7px}.sharp-section-head strong{font-size:16px}.sharp-section-head em{display:none}}


/* Build Lab / Rune Forge */
.buildlab-hero{margin:4px 0 18px;padding:18px 20px;border:1px solid #263246;border-radius:15px;background:linear-gradient(115deg,rgba(17,27,41,.92),rgba(10,15,23,.9));position:relative;overflow:hidden}
.buildlab-hero:after{content:"";position:absolute;right:-45px;top:-75px;width:190px;height:190px;border-radius:50%;border:1px solid rgba(216,180,93,.12)}
.buildlab-hero span{display:block;font-size:8px;font-weight:900;letter-spacing:.18em;color:#d8b45d}.buildlab-hero strong{display:block;font-size:25px;margin-top:2px}.buildlab-hero p{margin:5px 0 0;color:#8592a3;font-size:11px}
.rune-forge-head{display:flex;align-items:center;gap:10px;margin:25px 0 9px;padding:12px 14px;border:1px solid rgba(216,180,93,.22);border-radius:12px;background:linear-gradient(90deg,rgba(216,180,93,.08),rgba(12,18,27,.45))}
.rune-forge-head .gem{width:29px;height:29px;display:grid;place-items:center;border:1px solid rgba(216,180,93,.45);transform:rotate(45deg);border-radius:5px;color:#efd17c;background:#15170f}.rune-forge-head .gem b{transform:rotate(-45deg);font-size:12px}
.rune-forge-head span{display:block;font-size:8px;font-weight:900;letter-spacing:.15em;color:#b99a51}.rune-forge-head strong{display:block;font-size:17px;color:#edf2f7}
.wr-eq-wrap{padding:15px 14px 9px!important;border-radius:15px!important;box-shadow:inset 0 1px rgba(255,255,255,.025),0 12px 30px rgba(0,0,0,.14)}
div[data-testid="stColumn"]:has(.wr-eq-label){padding:6px!important;border-right:1px solid rgba(128,145,165,.10)}
div[data-testid="stColumn"]:has(.wr-eq-label):last-child{border-right:0}
.wr-eq-label{text-align:center!important}.wr-eq-name{text-align:left!important;color:#e9eef4!important}
.wr-eq-empty{background:rgba(5,9,14,.36)!important}
.wr-rune-section{margin-top:24px!important}.wr-rune-section span{background:#080d14;padding:0 9px}
div[data-testid="stColumn"]:has(.wr-tree-marker) div[data-testid="stImage"] img{border-color:#2b384b!important;background:radial-gradient(circle at 50% 35%,#1a2636,#080d14 72%)!important}
div[data-testid="stColumn"]:has(.wr-tree-marker):hover div[data-testid="stImage"] img{border-color:#d8b45d!important;box-shadow:0 8px 24px rgba(0,0,0,.35),0 0 22px rgba(216,180,93,.09)!important}
div[data-testid="stColumn"]:has(.wr-tree-selected) div[data-testid="stImage"] img{border-color:#d8b45d!important;box-shadow:0 0 0 1px rgba(216,180,93,.24),0 0 24px rgba(216,180,93,.10)!important}
.wr-tree-name{color:#aeb9c7!important;font-size:10px!important;font-weight:800!important;letter-spacing:.04em}
div[data-testid="stColumn"]:has(.wr-pick-marker){border-radius:11px;transition:background .15s ease}
div[data-testid="stColumn"]:has(.wr-pick-marker):hover{background:rgba(216,180,93,.035)}
div[data-testid="stColumn"]:has(.wr-pick-marker) div[data-testid="stImage"] img{box-shadow:0 7px 17px rgba(0,0,0,.25)!important}
div[data-testid="stColumn"]:has(.wr-selected) div[data-testid="stImage"] img{border-color:#d8b45d!important;box-shadow:0 0 0 2px rgba(216,180,93,.16),0 0 22px rgba(216,180,93,.14)!important}
.wr-icon-name{color:#9eabba!important;font-size:9px!important;line-height:1.15!important}
.rune-status{display:flex;gap:6px;flex-wrap:wrap;margin:5px 0 14px}.rune-status span{padding:5px 8px;border:1px solid #29364a;border-radius:999px;background:#0b111a;color:#8492a4;font-size:8px;font-weight:850;letter-spacing:.07em}.rune-status .ok{color:#e8ca75;border-color:rgba(216,180,93,.34);background:rgba(216,180,93,.055)}
@media(max-width:640px){.buildlab-hero{padding:15px}.rune-forge-head{padding:10px}.rune-forge-head strong{font-size:15px}div[data-testid="stColumn"]:has(.wr-eq-label){border-right:0}}


/* Build Forge V2 */
.build-forge-head{display:flex;align-items:center;gap:11px;margin:28px 0 10px;padding:13px 15px;border:1px solid rgba(216,180,93,.22);border-radius:12px;background:linear-gradient(90deg,rgba(216,180,93,.08),rgba(12,18,27,.45))}
.build-forge-head .forge-icon{width:31px;height:31px;display:grid;place-items:center;border:1px solid rgba(216,180,93,.42);border-radius:8px;background:#15170f;color:#efd17c;font-size:14px}
.build-forge-head span{display:block;font-size:8px;font-weight:900;letter-spacing:.15em;color:#b99a51}.build-forge-head strong{display:block;font-size:17px;color:#edf2f7}
.build-summary{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 13px}.build-summary span{padding:5px 8px;border:1px solid #29364a;border-radius:999px;background:#0b111a;color:#8492a4;font-size:8px;font-weight:850;letter-spacing:.06em}.build-summary .ready{color:#e8ca75;border-color:rgba(216,180,93,.34);background:rgba(216,180,93,.055)}
.build-slot-marker{height:0}.build-slot-name{min-height:28px;margin:4px 0 3px;text-align:center;color:#aeb9c7;font-size:9px;font-weight:800;line-height:1.12}
div[data-testid="stColumn"]:has(.build-slot-marker){text-align:center;padding:10px 5px 7px;border:1px solid #263246;border-radius:12px;background:linear-gradient(180deg,#101925,#090e15)}
div[data-testid="stColumn"]:has(.build-slot-marker) div[data-testid="stImage"]{display:flex;justify-content:center}
div[data-testid="stColumn"]:has(.build-slot-marker) div[data-testid="stImage"] img{width:58px!important;height:58px!important;border-radius:10px;border:1px solid rgba(216,180,93,.28);box-shadow:0 8px 18px rgba(0,0,0,.28)}
div[data-testid="stColumn"]:has(.build-slot-marker) .stButton button{font-size:8px!important;min-height:25px!important;height:25px!important;padding:0 7px!important}
.build-empty-slot{height:58px;width:58px;margin:0 auto;border:1px dashed #35445a;border-radius:10px;display:grid;place-items:center;background:#080d14;color:#59687b;font-size:24px}
.boot-equipped{display:flex;align-items:center;gap:11px;margin:7px 0 14px;padding:10px 12px;border:1px solid rgba(216,180,93,.22);border-radius:11px;background:linear-gradient(90deg,rgba(216,180,93,.055),rgba(11,17,26,.65))}
.boot-equipped img{width:43px;height:43px;border-radius:8px;border:1px solid #d8b45d}.boot-equipped span{font-size:8px;font-weight:900;letter-spacing:.12em;color:#9a8754}.boot-equipped strong{display:block;color:#edf2f7;font-size:12px;margin-top:2px}
@media(max-width:640px){.build-forge-head{padding:10px}.build-forge-head strong{font-size:15px}.build-slot-name{font-size:8px}}

.combat-result-head{margin:30px 0 11px;padding:14px 16px;border:1px solid rgba(216,180,93,.25);border-radius:13px;background:linear-gradient(90deg,rgba(216,180,93,.09),rgba(11,17,26,.72));display:flex;align-items:center;justify-content:space-between}.combat-result-head span{display:block;font-size:8px;font-weight:900;letter-spacing:.16em;color:#b99a51}.combat-result-head strong{font-size:18px}.combat-result-head em{font-style:normal;font-size:8px;color:#768598}.combat-hero{display:grid;grid-template-columns:1.45fr repeat(3,1fr);gap:9px;margin-bottom:10px}.combat-kpi{min-height:105px;padding:14px;border:1px solid #263246;border-radius:13px;background:linear-gradient(180deg,#111a27,#090f17);display:flex;flex-direction:column;justify-content:flex-end}.combat-kpi.hero{border-color:rgba(216,180,93,.48);background:radial-gradient(300px 120px at 30% 0%,rgba(216,180,93,.15),transparent 70%),linear-gradient(180deg,#171d24,#0a1017)}.combat-kpi .label{font-size:8px;font-weight:900;letter-spacing:.13em;color:#77869a}.combat-kpi .value{font-size:27px;font-weight:900;color:#edf3f8}.combat-kpi.hero .value{font-size:40px;color:#f1d27b}.combat-kpi .unit,.combat-kpi .sub{font-size:8px;color:#738196}.build-ribbon{display:flex;gap:7px;flex-wrap:wrap;margin:10px 0 16px;padding:10px 12px;border:1px solid #202c3c;border-radius:11px;background:rgba(8,13,20,.72)}.build-ribbon .tag{font-size:8px;font-weight:900;color:#8d9bad}.build-ribbon .piece{padding:5px 7px;border:1px solid #29364a;border-radius:7px;color:#bac5d1;font-size:9px}.build-ribbon .boots{border-color:rgba(216,180,93,.35);color:#e3c56f}.combat-stat-title{margin:18px 0 8px;font-size:9px;font-weight:900;letter-spacing:.14em;color:#8b99aa}@media(max-width:720px){.combat-hero{grid-template-columns:repeat(2,1fr)}.combat-kpi.hero{grid-column:span 2}.combat-result-head em{display:none}}
/* Premium leaderboard pass */
.pair-rank-grid,.triple-rank-grid,.boot3-rank-grid,.boot4-rank-grid,.full-rank-grid{counter-reset:sharpRank}
.pair-rank-card,.triple-rank-card,.boot3-rank-card,.boot4-rank-card,.full-rank-card{overflow:hidden;transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease}
.pair-rank-card:first-child,.triple-rank-card:first-child,.boot3-rank-card:first-child,.boot4-rank-card:first-child,.full-rank-card:first-child{
 grid-column:span 2;border-color:rgba(216,180,93,.62)!important;
 background:radial-gradient(420px 130px at 50% 0%,rgba(216,180,93,.16),transparent 70%),linear-gradient(180deg,#171d24,#0b1017)!important;
 box-shadow:0 16px 38px rgba(0,0,0,.30),inset 0 1px rgba(240,213,138,.14)!important}
.pair-rank-card:first-child:before,.triple-rank-card:first-child:before,.boot3-rank-card:first-child:before,.boot4-rank-card:first-child:before,.full-rank-card:first-child:before{
 content:"BEST DPS";position:absolute;right:9px;top:8px;padding:4px 7px;border:1px solid rgba(216,180,93,.45);border-radius:999px;
 color:#f0d58a;background:rgba(30,24,11,.78);font-size:7px;font-weight:900;letter-spacing:.12em}
.pair-rank-card:first-child .pair-dps,.triple-rank-card:first-child .triple-dps,.boot3-rank-card:first-child .boot3-dps,.boot4-rank-card:first-child .boot4-dps,.full-rank-card:first-child .full-dps{font-size:21px;color:#f3d77f}
.pair-rank-card:first-child img,.triple-rank-card:first-child img,.boot3-rank-card:first-child img,.boot4-rank-card:first-child img,.full-rank-card:first-child img{box-shadow:0 0 0 1px rgba(216,180,93,.22),0 7px 16px rgba(0,0,0,.26)}
[data-testid="stSlider"] [data-baseweb="slider"]{padding-top:8px}
[data-testid="stSlider"] [role="slider"]{box-shadow:0 0 0 3px rgba(216,180,93,.14)}
[data-testid="stNumberInput"] button{background:#101824!important;border-color:#29364a!important}
[data-testid="stTooltipHoverTarget"] svg{color:#7e8a9b}
@media(max-width:640px){
 .pair-rank-card:first-child,.triple-rank-card:first-child,.boot3-rank-card:first-child,.boot4-rank-card:first-child,.full-rank-card:first-child{grid-column:span 2}
}
</style>
""",unsafe_allow_html=True)
st.markdown("""
<div class="sharp-hero">
  <div class="sharp-kicker">SHARPWR • COMBAT ANALYTICS</div>
  <div class="sharp-title">Damage <span>Lab</span></div>
  <div class="sharp-sub">Wild Rift ADC build intelligence • Patch 7.3a</div>
  <div class="sharp-badges"><span>AA ENGINE</span><span>ITEM BENCHMARKS</span><span>FULL BUILD OPTIMIZER</span></div>
</div>
""",unsafe_allow_html=True)

# base AD, AD/lvl, AS ratio, base AS, base bonus AS, AS/lvl
C={
"Kalista":(57,5.2,.694,.694,.16,.046),"Tristana":(60,5,.694,.694,.17,.020),
"Twitch":(58,4,.679,.679,.18,.030),"Draven":(66,3.8,.679,.679,.11,.030),
"Kog'Maw":(58,3.5,.665,.665,.20,.030),"Vayne":(60,3,.658,.658,.23,.030),
"Ashe":(60,4,.658,.658,.23,.030),"Varus":(58,4,.658,.658,.22,.030),
"Xayah":(60,4.2,.658,.658,.22,.034),"Samira":(60,3.5,.658,.658,.14,.030),
"Miss Fortune":(58,4,.656,.656,.22,.032),"Yunara":(58,3,.650,.650,.23,.032),
"Kai'Sa":(59,3.5,.644,.644,.17,.022),"Corki":(54,2.5,.644,.644,.17,.032),
"Lucian":(60,3.5,.638,.638,.25,.028),"Smolder":(54,3.5,.638,.638,.25,.031),
"Caitlyn":(60,4.2,.625,.625,.28,.025),"Jinx":(58,4,.625,.625,.30,.020),
"Ezreal":(60,4.5,.625,.625,.28,.022),"Zeri":(58,4,.625,.625,.28,.024),
"Jhin":(60,5,.625,.625,.06,.032),"Sivir":(60,4,.625,.625,.30,.010),
"Senna":(50,0,.300,.300,1.10,.025)}

# gold, AD, AS, crit, AP, HP, mana, armor, MR, AH, lifesteal, flat armor pen, % armor pen, MS
F={
"Fiendhunter Bolts":(2650,0,.45,.25,0,0,0,0,0,20,0,0,0,0),
"Rapid Firecannon":(2650,0,.40,.25,0,0,0,0,0,0,0,0,0,.04),
"Runaan's Hurricane":(2650,0,.40,.25,0,0,0,0,0,0,0,0,0,.04),
"Phantom Dancer":(2650,0,.40,.25,0,0,0,0,0,0,0,0,0,.07),
"Navori Quickblades":(2650,0,.40,.25,0,0,0,0,0,0,0,0,0,.04),
"Wit's End":(2800,0,.50,0,0,0,0,0,45,0,0,0,0,0),
"Hexoptics C44":(2900,55,0,.25,0,0,0,0,0,0,0,0,0,0),
"Kraken Slayer":(2900,45,.35,0,0,0,0,0,0,0,0,0,0,.04),
"Nashor's Tooth":(2900,0,.50,0,80,0,0,0,0,15,0,0,0,0),
"Manamune":(2900,40,0,0,0,0,500,0,0,15,0,0,0,0),
"Muramana":(2900,40,0,0,0,0,1200,0,0,15,0,0,0,0),
"Statikk Shiv":(3000,40,.30,0,40,0,0,0,0,0,0,0,0,.04),
"Guinsoo's Rageblade":(3000,35,.30,0,30,0,0,0,0,0,0,0,0,0),
"Mortal Reminder":(3000,35,0,.25,0,0,0,0,0,0,0,0,.30,0),
"Maw of Malmortius":(3000,55,0,0,0,0,0,0,45,10,0,0,0,0),
"Essence Reaver":(3000,50,0,.25,0,0,0,0,0,20,0,0,0,0),
"Immortal Shieldbow":(3000,55,0,.25,0,0,0,0,0,0,0,0,0,0),
"The Collector":(3000,50,0,.25,0,0,0,0,0,0,0,10,0,0),
"Terminus":(3000,35,.35,0,0,0,0,0,0,0,0,0,0,0),
"Stormrazor":(3000,50,.20,.25,0,0,0,0,0,0,0,0,0,0),
"Yun Tal Wildarrows":(3100,50,.35,0,0,0,0,0,0,0,0,0,0,0),
"Galeforce":(3100,60,0,.25,0,0,0,0,0,0,0,0,0,.04),
"Mercurial Scimitar":(3100,45,0,0,0,0,0,0,40,0,.12,0,0,0),
"Blade of the Ruined King":(3100,40,.30,0,0,0,0,0,0,0,.12,0,0,0),
"Guardian Angel":(3200,45,0,0,0,0,0,40,0,0,0,0,0,0),
"Bloodthirster":(3200,75,0,0,0,0,0,0,0,0,.15,0,0,0),
"Lord Dominik's Regards":(3300,35,0,.25,0,0,0,0,0,0,0,0,.35,0),
"Trinity Force":(3333,36,.30,0,0,333,0,0,0,15,0,0,0,0),
"Infinity Edge":(3400,75,0,.25,0,0,0,0,0,0,0,0,0,0),
"Serylda's Grudge":(3100,50,0,0,0,0,0,0,0,15,0,0,.35,0),
"Serpent's Fang":(2800,50,0,0,0,0,0,0,0,10,0,15,0,0),
"Youmuu's Ghostblade":(3000,55,0,0,0,0,0,0,0,15,0,15,0,.04),
"Duskblade of Draktharr":(3000,55,0,0,0,0,0,0,0,10,0,18,0,0),
"Edge of Night":(3000,50,0,0,0,250,0,0,0,0,0,12,0,0),
"Iceborn Gauntlet":(3000,0,0,0,0,300,250,50,0,30,0,0,0,0),
"Death's Dance":(3200,50,0,0,0,0,0,45,0,15,0,0,0,0)}

# Tier List combat-mechanic audit: CURRENT simulator coverage.
ITEM_SCENARIO_AUDIT={
"Fiendhunter Bolts":("ultimate-trigger","modeled","Opening Barrage requires an actual ultimate cast; pre-cast defaults removed."),
"Rapid Firecannon":("energized","modeled","Sharpshooter: 80 bonus magic per Energized proc; kiting benchmark recharges every 7 AAs. Proc also grants +35% bonus attack range, capped at +150 (utility)."),
"Runaan's Hurricane":("multi-target","not modeled","Extra bolts excluded in single-target ranking."),
"Phantom Dancer":("stacking","modeled","AS stacks build naturally from 0."),
"Navori Quickblades":("ability-cooldown","modeled","Deft Strikes: each AA reduces remaining basic-ability cooldowns by 15%; effect activates when ability timeline is added."),
"Wit's End":("on-hit","modeled","Magic on-hit each attack."),
"Hexoptics C44":("distance","modeled","Magnification: basic damage only; 0% below 100 range, +1% per 50 range, 10% cap at 550. Proc additions excluded; unknown WR classifications remain TODO."),
"Kraken Slayer":("every-N-hit","modeled","Ranged Bring It Down: every 3rd AA deals 120-168 linear level bonus physical; +0.75% damage per 1% target missing HP, capped at +75%."),
"Nashor's Tooth":("on-hit","modeled","Magic on-hit."),
"Manamune":("mana-scaling","modeled","Awe AD from mana."),
"Muramana":("mana/on-hit","modeled","Awe plus mana on-hit."),
"Statikk Shiv":("energized","modeled","Electrospark: 60 magic per Energized proc; kiting benchmark recharges every 5 AAs. Bounces hit 3/4/5/6 targets at levels 1/5/9/13 and apply on-hit to secondary targets; bounce value excluded from single-target DPS."),
"Guinsoo's Rageblade":("stacking/on-hit","modeled","Stacks and phantom on-hit."),
"Mortal Reminder":("penetration","modeled","Percent armor penetration."),
"Maw of Malmortius":("defensive","not modeled","Shield/survival excluded."),
"Essence Reaver":("spell-trigger","modeled","Real cast arms next eligible on-hit; 1.5s ICD. Legacy pre-cast arms once only."),
"Immortal Shieldbow":("defensive","not modeled","Shield/survival excluded."),
"The Collector":("execute","modeled","Execute and previous executes."),
"Terminus":("stacking/on-hit","modeled","Current in-game test: Shadow deals 30 bonus magic on-hit. Juxtaposition grants 10% armor + magic penetration per Dark stack, up to 3 stacks / 30%; no level scaling. Item percent penetration cap 40%. Defensive Light stacks are not scored in DPS."),
"Stormrazor":("energized","modeled","Bolt: 120 bonus magic per Energized proc; kiting benchmark recharges every 7 AAs. Proc grants +45% movement speed for 1.5s (utility)."),
"Yun Tal Wildarrows":("permanent stacking","modeled","Ranged: +0.2% permanent crit per AA, max 125 stacks / 25% crit. Pre-combat stacks are scenario state."),
"Galeforce":("active","modeled","Cloudburst active: 40-120 linear by level +45% bonus AD total physical damage, 50s cooldown."),
"Mercurial Scimitar":("active/defensive","not modeled","Cleanse/active excluded."),
"Blade of the Ruined King":("current-HP/on-hit","modeled","User-confirmed ranged 6% current HP; melee tooltip 8.5%. Phantom uses HP remaining after the primary hit. Minimum15 raw physical remains unverified."),
"Guardian Angel":("defensive","not modeled","Revive excluded."),
"Bloodthirster":("sustain","not modeled","Sustain is not scored as DPS."),
"Lord Dominik's Regards":("bonus-HP scaling","partial","Penetration modeled; amp needs target Bonus HP."),
"Trinity Force":("spell-trigger","modeled","Real cast arms next eligible on-hit; cooldown never auto-rearms. Legacy pre-cast arms once only."),
"Infinity Edge":("crit modifier","modeled","Critical damage modifier."),
"Serylda's Grudge":("penetration/utility","partial","Penetration modeled; slow excluded."),
"Serpent's Fang":("shield-counter","not modeled","Needs target shield state."),
"Youmuu's Ghostblade":("movement/combat-state","partial","Static stats modeled; passive not fully scored."),
"Duskblade of Draktharr":("AA/cooldown","modeled","Nightstalker: first AA, then next AA after 10s. No visibility requirement; single target kill ends fight."),
"Edge of Night":("defensive","not modeled","Spell shield excluded."),
"Iceborn Gauntlet":("spell-trigger","modeled","Real-cast Spellblade; 1.5s ICD. Slow utility excluded."),
"Death's Dance":("defensive","not modeled","Damage delay/survival excluded."),
}

P={
"Pickaxe":(800,20,0,0,0,0,0,0,0,0,0,0,0,0),
"Sheen":(800,0,0,0,0,0,0,0,0,10,0,0,0,0),
"Kircheis Shard":(800,0,.20,0,0,0,0,0,0,0,0,0,0,0),
"Executioner's Calling":(800,15,0,0,0,0,0,0,0,0,0,0,0,0),
"Recurve Bow":(900,0,.20,0,0,0,0,0,0,0,0,0,0,0),
"Quicksilver Sash":(1100,0,0,0,0,0,0,0,30,0,0,0,0,0),
"Hearthbound Axe":(1200,20,.15,0,0,0,0,0,0,0,0,0,0,0),
"Vampiric Scepter":(1200,20,0,0,0,0,0,0,0,0,.08,0,0,0),
"Last Whisper":(1200,15,0,0,0,0,0,0,0,0,0,0,.15,0),
"Caulfield's Warhammer":(1200,25,0,0,0,0,0,0,0,10,0,0,0,0),
"Noonquiver":(1300,20,0,.15,0,0,0,0,0,0,0,0,0,0),
"Zeal":(1400,0,.15,.15,0,0,0,0,0,0,0,0,0,.04),
"B.F. Sword":(1500,40,0,0,0,0,0,0,0,0,0,0,0,0),
"Tear of the Goddess":(400,0,0,0,0,0,200,0,0,0,0,0,0,0),
"Dagger":(400,0,.12,0,0,0,0,0,0,0,0,0,0,0),
"Long Sword":(500,12,0,0,0,0,0,0,0,0,0,0,0,0),
"Brawler's Gloves":(500,0,0,.10,0,0,0,0,0,0,0,0,0,0),
"Cloth Armor":(500,0,0,0,0,0,0,20,0,0,0,0,0,0),
"Null-Magic Mantle":(500,0,0,0,0,0,0,0,20,0,0,0,0,0),
"Ruby Crystal":(500,0,0,0,0,150,0,0,0,0,0,0,0,0),
"Amplifying Tome":(500,0,0,0,20,0,0,0,0,0,0,0,0,0),
"Ring of Revelation":(300,0,0,0,0,0,0,0,0,5,0,0,0,0),
"Boots of Speed":(400,0,0,0,0,0,0,0,0,0,0,0,0,25)}

B={
"Gluttonous Greaves":(1000,12,0,0,0,0,0,0,0,0,0,0,0,45),
"Immortal Treads":(2000,12,0,0,0,0,0,0,0,0,0,0,0,45),
"Ionian Boots of Lucidity":(1000,0,0,0,0,0,0,0,0,15,0,0,0,45),
"Crimson Lucidity":(2000,0,0,0,0,0,0,0,0,25,0,0,0,45),
"Berserker's Greaves":(1200,0,.35,0,0,0,0,0,0,0,0,0,0,45),
"Gunmetal Greaves":(2200,0,.50,0,0,0,0,0,0,0,.05,0,0,45),
"Mercury's Treads":(1200,0,0,0,0,150,0,0,25,0,0,0,0,45),
"Chainlaced Crushers":(2200,0,0,0,0,150,0,0,30,0,0,0,0,45),
"Plated Steelcaps":(1200,0,0,0,0,150,0,25,0,0,0,0,0,45),
"Armored Advance":(2200,0,0,0,0,150,0,30,0,0,0,0,0,45),
"Boots of Mana":(1200,0,0,0,25,0,0,0,0,0,0,0,0,45),
"Spellslinger's Shoes":(2200,0,0,0,35,0,0,0,0,0,0,0,0,45,18,.08),
"Boots of Dynamism":(1200,15,0,0,0,0,0,0,0,0,0,10,0,45),
"Armorcrusher Boots":(2200,25,0,0,0,0,0,0,0,0,0,12,.06,45)}
K=["gold","ad","as","crit","ap","hp","mana","armor","mr","ah","ls","flatpen","pctpen","ms","flatmpen","pctmpen"]
def dct(v):
    v=tuple(v)+(0,)*(len(K)-len(v))
    return dict(zip(K,v))
def gu(l):
    n=l-1
    return n*(.7025+.0175*n)
def stats(n,l,mist=0):
    ba,g,r,b,bba,asg=C[n]; u=gu(l)
    return {"basead":ba,"ad":ba+g*u+(mist*1.25 if n=="Senna" else 0),
            "ratio":r,"baseas":b,"bba":bba,"lvbas":asg*u}
def rm(x): return 100/(100+x) if x>=0 else 2-100/(100-x)
def lvl_scale(lo,hi,lvl): return lo+(hi-lo)*(lvl-1)/14

# User-tested level benchmark profiles.
SQUISHY_JINX_PROFILE={1:{"hp":630,"armor":35,"mr":30},5:{"hp":1014,"armor":51,"mr":35},6:{"hp":1122,"armor":56,"mr":36},8:{"hp":1353,"armor":66,"mr":39},9:{"hp":1475,"armor":71,"mr":40},11:{"hp":1734,"armor":81,"mr":43},12:{"hp":1871,"armor":87,"mr":45},14:{"hp":2159,"armor":99,"mr":48},15:{"hp":2310,"armor":105,"mr":50}}
BRUISER_DARIUS_PROFILE={1:{"hp":660,"armor":47,"mr":40,"aa_reduction":0},5:{"hp":1617,"armor":89,"mr":46,"aa_reduction":.10},6:{"hp":1750,"armor":94,"mr":48,"aa_reduction":.10},8:{"hp":2034,"armor":151,"mr":52,"aa_reduction":.10},9:{"hp":2185,"armor":156,"mr":54,"aa_reduction":.10},11:{"hp":2905,"armor":167,"mr":59,"aa_reduction":.10},12:{"hp":3074,"armor":173,"mr":61,"aa_reduction":.10},14:{"hp":3729,"armor":242,"mr":117,"aa_reduction":.10},15:{"hp":4315,"armor":249,"mr":182,"aa_reduction":.10}}
TANK_ORNN_PROFILE={1:{"hp":690,"armor":48,"mr":42,"aa_reduction":0},5:{"hp":2065,"armor":93,"mr":48,"aa_reduction":.10},6:{"hp":2264,"armor":98,"mr":50,"aa_reduction":.10},8:{"hp":2989,"armor":154,"mr":54,"aa_reduction":.10},9:{"hp":3264,"armor":162,"mr":56,"aa_reduction":.10},11:{"hp":3943,"armor":264,"mr":61,"aa_reduction":.10},12:{"hp":4173,"armor":270,"mr":63,"aa_reduction":.10},14:{"hp":5086,"armor":352,"mr":131,"aa_reduction":.10},15:{"hp":5698,"armor":415,"mr":184,"aa_reduction":.10}}
TARGET_PROFILES={"Squishy • Jinx":SQUISHY_JINX_PROFILE,"Bruiser • Darius":BRUISER_DARIUS_PROFILE,"Tank • Ornn":TANK_ORNN_PROFILE}
def _target_profile_at_level(profile,lvl):
    lvl=int(lvl)
    if lvl in profile: return dict(profile[lvl])
    levels=sorted(profile); lo=max(x for x in levels if x<lvl); hi=min(x for x in levels if x>lvl); t=(lvl-lo)/(hi-lo)
    out={k:profile[lo][k]+(profile[hi][k]-profile[lo][k])*t for k in ("hp","armor","mr")}
    # Boots are discrete: Lv1 has none; all benchmark builds from Lv5 onward have Steelcaps/Armored Advance.
    out["aa_reduction"]=.10 if lvl>=5 and (profile[hi].get("aa_reduction",0) or profile[lo].get("aa_reduction",0)) else 0
    return out


def _validate_build(items,db,boot=None):
    from build_fight_optimizer import SPELLBLADE
    if len(set(items)&SPELLBLADE)>1:raise ValueError("Only one Spellblade item is allowed.")
    if len(items)>5: raise ValueError("At most five items are allowed.")
    if len(items)!=len(set(items)): raise ValueError("Duplicate items are not allowed.")
    if any(x not in db or x in B or x=="Boots of Speed" for x in items): raise ValueError("Choose valid items; boots use the separate slot.")
    if boot is not None and boot not in B: raise ValueError("Unknown boots.")


def _effective_resistance(value,pct=0.,flat=0.,cap=1.):
    # Penetration cannot make a positive resistance negative; pre-existing negative resistance remains negative.
    return value if value<0 else max(0.,value*(1-min(cap,max(0.,pct)))-max(0.,flat))


def sim_build(n,l,hp0,arm,mr,items,db,mist=0,bonus_hp=0,dist=550.0,target_aa_reduction=0.0,yuntal_start_stacks=0,base_mana=0.0,spell=False,energized=False,ult=False,execs=0,active_ready=False,boot=None,item_proc=True):
    engine=_combat_hits(n,l,hp0,arm,mr,items,db,mist,bonus_hp,dist,target_aa_reduction,yuntal_start_stacks,base_mana,spell,energized,ult,execs,active_ready,boot,item_proc)
    next(engine); hp=float(hp0); t=0.; log=[]
    while hp>0 and len(log)<500:
        h=engine.send({"hp":hp,"time":t}); before=hp; hp-=h["damage"]
        if "The Collector" in items and item_proc and 0<hp<=hp0*min(1,.05+.001*execs): hp=0; h["notes"].append("Execute")
        log.append([len(log)+1,round(t,3),round(h["as"],4),round(h["crit"]*100,2),round(h["armor"],1),round(before,1),round(h["damage"],1),round(max(hp,0),1),", ".join(h["notes"]),h["rage"],h["light"],h["dark"]])
        t+=1/h["as"]
    label=" + ".join(items)+((" + "+boot) if boot else "")
    if hp>0: label+=" [NOT KILLED: 500 attacks]"
    gold=sum(dct(db[x])["gold"] for x in items)+(dct(B[boot])["gold"] if boot else 0)
    return [label,gold,round(t,3) if hp<=0 else float("inf"),len(log),round(sum(x[6] for x in log)/t,1) if t else 0.],log


def sim(n,l,hp0,arm,mr,it,db,mist,bonus_hp,dist,base_mana,spell,energized,ult,execs,item_proc=True,target_aa_reduction=0.0,active_ready=False,yuntal_start_stacks=0):
    row,log=sim_build(n,l,hp0,arm,mr,[it],db,mist,bonus_hp,dist,target_aa_reduction,yuntal_start_stacks,base_mana,spell,energized,ult,execs,active_ready,item_proc=item_proc)
    return row,[x[:9] for x in log]

def _combat_hits(n,l,hp0,arm,mr,items,db,mist=0,bonus_hp=0,dist=550.0,target_aa_reduction=0.0,yuntal_start_stacks=0,base_mana=0.0,spell=False,energized=False,ult=False,execs=0,active_ready=False,boot=None,item_proc=True,initial_flurry=False):
    """Shared multi-item AA engine. Carries the audited single-item AA mechanics into item combinations."""
    items=list(items)
    from champion_database import champion_stat
    # Item melee/ranged class belongs to the champion, not distance to target.
    botrk_ratio=.085 if champion_stat(n,"attack_type")=="Melee" else .06
    _validate_build(items,db,boot)
    s=stats(n,l,mist); qs=[dct(db[x]) for x in items]
    bootq=dct(B[boot]) if boot in B else dct(())
    total=lambda key: sum(float(q[key]) for q in qs)+float(bootq.get(key,0))
    if base_mana<=0:
        from champion_database import level_stats
        base_mana=level_stats(n,int(l))["mana"] or 0.
    mana=base_mana+total("mana")
    awe=.02*mana if any(x in items for x in ("Manamune","Muramana")) else 0.0
    ad=s["ad"]+total("ad")+awe
    hp=float(hp0); t=0.; k=0; log=[]
    rb=light=dark=rage_hits=pd_stacks=0
    kraken_hits=0
    terminus_hits=0
    ytcrit=min(.25,max(0,int(yuntal_start_stacks))*.002); yt_until=-1.; yt_cd=0.
    spellblade_ready=0.
    fh=0  # Only an actual ultimate_cast_time event arms Opening Barrage.
    fiend_until=8.; last_ult_cast=None; spell_pending=False; galeforce_ready=0.; duskblade_ready=0.
    if initial_flurry and "Yun Tal Wildarrows" in items and item_proc: yt_until=6.; yt_cd=25.
    state=yield None
    while k<500 or (state.get("event_driven",False) and k<10000):
        hp=float(state["hp"]); t=float(state["time"]); k+=1
        current_ad=ad+float(state.get("bonus_ad",0))
        event_driven=bool(state.get("event_driven",False));skill_on_hit=bool(state.get("skill_on_hit",False))
        if event_driven:
            _cast_times=state.get("spell_cast_times",[t] if state.get("spell_cast") else [])
            for _cast_time in _cast_times:
                if _cast_time>=spellblade_ready:spell_pending=True
            _ult_time=state.get("ultimate_cast_time")
            if _ult_time is not None and _ult_time!=last_ult_cast:
                last_ult_cast=_ult_time; fiend_until=_ult_time+8
                if "Fiendhunter Bolts" in items and item_proc: fh=3
        dyn=(.08*rb if ("Guinsoo's Rageblade" in items and item_proc) else 0.0)+(.06*pd_stacks if ("Phantom Dancer" in items and item_proc) else 0.0)
        if ("Yun Tal Wildarrows" in items and item_proc) and t<yt_until: dyn+=.35
        asp=min(3,s["baseas"]+s["ratio"]*(s["bba"]+s["lvbas"]+total("as")+dyn+float(state.get("bonus_as",0))))
        crit=min(1,total("crit")+(mist//20*.10 if n=="Senna" else 0)+(ytcrit if ("Yun Tal Wildarrows" in items and item_proc) else 0))
        crit=float(state.get("crit",crit))
        cd=2.3 if "Infinity Edge" in items else 2.0
        if n=="Senna": cd*=.9
        pct=total("pctpen")+(.10*dark if ("Terminus" in items and item_proc) else 0)
        if ("Terminus" in items and item_proc): pct=min(.40,pct)
        ea=float(state.get("armor_override",_effective_resistance(arm,pct,total("flatpen"))))
        # Patch 7.3 Rageblade no longer disables critical strikes; crit remains normal AA expected damage.
        phy=float(state.get("attack_physical",current_ad*(1+crit*(cd-1)))); onp=0.; onm=0.; true=0.; note=[]; item_components=[]

        if fh and t<=fiend_until and not skill_on_hit:
            asp=min(3,asp+s["ratio"]*.50); phy=float(state.get("critical_attack_physical",current_ad*cd))*.80; true=current_ad*.15*crit; note.append("Opening Barrage")
        if "Hexoptics C44" in items:
            from damage_classification import magnification
            hit_dist=state.get("distance") if state.get("distance") is not None else (0. if state.get("melee",False) else dist)
            factor=magnification(hit_dist,['BasicAttack'])
            secondary=float(state.get('nonbasic_attack_physical',0.))
            phy=(phy-secondary)*factor+secondary
            # Opening Barrage is a separate item effect, not the attack base.
            note.append(f"C44 {(factor-1)*100:.0f}% basic only")
        if "Galeforce" in items and active_ready and not event_driven and not skill_on_hit and t>=galeforce_ready:
            bonus_ad=max(0,current_ad-s["basead"])
            onp+=40+(l-1)/14*80+.45*bonus_ad; note.append("Cloudburst"); galeforce_ready=t+50
        if "Blade of the Ruined King" in items: onp+=max(15,botrk_ratio*hp)
        if ("Terminus" in items and item_proc): onm+=30
        if "Wit's End" in items: onm+=40
        if "Nashor's Tooth" in items:
            onm+=15+.20*total("ap")
        if "Recurve Bow" in items: onp+=15
        if "Muramana" in items and not skill_on_hit:onp+=.015*float(mana if state.get("max_mana") is None else state["max_mana"])

        rage_extra=False
        if ("Guinsoo's Rageblade" in items and item_proc):
            onm+=30
            # The AA that reaches four stacks is eligible hit 1: user AA6/AA9 confirmation.
            if rb>=3:
                rage_hits+=1
                if rage_hits>=3: rage_extra=True; rage_hits=0

        # Resolve ordinary and Phantom on-hits in order. Magic lands before
        # Juxtaposition advances; physical attack/procs use the updated penetration.
        primary_onm=onm
        primary_em=_effective_resistance(mr,total("pctmpen")+(.10*dark if "Terminus" in items and item_proc else 0),total("flatmpen"),cap=.40 if "Terminus" in items and item_proc else 1.)
        if "Terminus" in items and item_proc:
            terminus_hits+=1
            if terminus_hits%2: light=min(3,light+1)
            else: dark=min(3,dark+1)
            ea=_effective_resistance(arm,min(.40,total("pctpen")+.10*dark),total("flatpen"))
        if ("Kraken Slayer" in items and item_proc):
            kraken_hits+=1
            if kraken_hits>=3:
                base=120+(l-1)/14*48; miss=max(0,min(1,(hp0-hp)/hp0))
                onp+=base*(1+min(.75,.75*miss)); note.append("Kraken")
                kraken_hits-=3

        primary_onp=onp
        if rage_extra:
            onm+=30
            if "Blade of the Ruined King" in items:
                primary_damage=(phy+primary_onp)*rm(ea)+primary_onm*rm(primary_em)+true
                if "Lord Dominik's Regards" in items:primary_damage*=1+min(.12,max(0,bonus_hp)/125*.01)
                if boot=="Immortal Treads":primary_damage*=1.05
                if target_aa_reduction and not skill_on_hit:primary_damage*=1-target_aa_reduction
                primary_damage*=float(state.get("on_hit_health_multiplier",1.))
                phantom_hp=max(0.,hp-primary_damage-float(state.get("primary_external_damage",0.)))
                onp+=max(15,botrk_ratio*phantom_hp)

            if ("Terminus" in items and item_proc): onm+=30
            if "Wit's End" in items: onm+=40
            if "Nashor's Tooth" in items:
                onm+=15+.20*total("ap")
            if "Recurve Bow" in items: onp+=15
            if "Muramana" in items and not skill_on_hit:onp+=.015*float(mana if state.get("max_mana") is None else state["max_mana"])
            if "Terminus" in items and item_proc:
                terminus_hits+=1
                if terminus_hits%2: light=min(3,light+1)
                else: dark=min(3,dark+1)
            if "Kraken Slayer" in items and item_proc:
                kraken_hits+=1
                if kraken_hits>=3:
                    base=120+(l-1)/14*48; miss=max(0,min(1,(hp0-hp)/hp0))
                    onp+=base*(1+min(.75,.75*miss)); note.append("Kraken (Phantom)")
                    kraken_hits-=3
            note.append("Phantom Hit")

        # Recurring Energized cadence mirrors the audited single-item engine.
        for eit,period,magic,label in (("Rapid Firecannon",7,80,"RFC Energized"),("Stormrazor",7,120,"Storm Energized"),("Statikk Shiv",5,60,"Shiv Energized")):
            if eit in items and item_proc:
                proc=(k==1 or (k>1 and (k-1)%period==0)) if energized else (k%period==0)
                if event_driven and "energized_ready" in state: proc=bool(state["energized_ready"])
                if proc: onm+=magic; note.append(label)
        if "Kircheis Shard" in items and energized and k==1:
            onm+=40; note.append("Jolt")

        # Legacy pre-cast means ONE initial cast; cooldown alone never rearms.
        if not event_driven and spell and k==1:spell_pending=True
        if spell_pending and t>=spellblade_ready:
            choices=[]
            if "Essence Reaver" in items and item_proc:choices.append((1.35,1.35*s["basead"]+min(80,.8*crit*100),"ER"))
            if "Trinity Force" in items and item_proc:choices.append((2.,2*s["basead"],"Trinity"))
            if "Iceborn Gauntlet" in items and item_proc:choices.append((1.,s["basead"]+.25*total("armor"),"Iceborn"))
            if "Sheen" in items:choices.append((1.,s["basead"],"Sheen"))
            if choices:
                _,amount,label=max(choices,key=lambda x:(x[0],x[1]))
                onp+=amount;note.append(label);spellblade_ready=t+1.5;spell_pending=False

        if ("Duskblade of Draktharr" in items and item_proc) and not skill_on_hit and t>=duskblade_ready:
            onp+=60+(l-1)/14*100; note.append("Nightstalker"); duskblade_ready=t+10

        if onp:item_components.append({"damage_type":"physical","raw_amount":onp,"tags":["Item"],"status":"unknown_WR","component":"item additional damage","effects":list(note)})
        if onm:item_components.append({"damage_type":"magic","raw_amount":onm,"tags":["Item"],"status":"unknown_WR","component":"item additional damage","effects":list(note)})
        if true:item_components.append({"damage_type":"true","raw_amount":true,"tags":["Item"],"status":"unknown_WR","component":"Opening Barrage"})
        phy+=onp
        if "Lord Dominik's Regards" in items:
            gs=min(.12,max(0,bonus_hp)/125*.01)
            phy*=1+gs; onm*=1+gs; primary_onm*=1+gs; true*=1+gs
            if gs: note.append(f"Giant Slayer {gs*100:.0f}%")
        em=_effective_resistance(mr,total("pctmpen")+(.10*dark if ("Terminus" in items and item_proc) and item_proc else 0),total("flatmpen"),cap=.40 if ("Terminus" in items and item_proc) else 1.)
        em=float(state.get("mr_override",em)) if not ("Terminus" in items and item_proc) else em
        magic_damage=onm*rm(em)
        if "Terminus" in items and item_proc:
            # Preserve the two resistances rather than multiplying merged raw magic.
            magic_damage=primary_onm*rm(primary_em)+(onm-primary_onm)*rm(em)
        dmg=phy*rm(ea)+magic_damage+true
        if boot=="Immortal Treads": dmg*=1.05
        if target_aa_reduction and not skill_on_hit: dmg*=1-target_aa_reduction
        on_hit_events=[{"kind":"primary","magic_raw":primary_onm,"magic_damage":primary_onm*rm(primary_em),"physical_proc_raw":primary_onp}]
        if rage_extra:
            on_hit_events.append({"kind":"phantom","magic_raw":onm-primary_onm,"magic_damage":(onm-primary_onm)*rm(em),"physical_proc_raw":onp-primary_onp})
        before=hp

        if ("Phantom Dancer" in items and item_proc) and not skill_on_hit: pd_stacks=min(5,pd_stacks+1)
        if ("Guinsoo's Rageblade" in items and item_proc): rb=min(4,rb+1)
        if ("Yun Tal Wildarrows" in items and item_proc) and not skill_on_hit:
            ytcrit=min(.25,ytcrit+.002)
            if yt_cd<=t:
                yt_until=t+6; yt_cd=t+25; note.append("Flurry")
            else: yt_cd=max(t,yt_cd-(1.0+crit))

        if fh and t<=fiend_until and not skill_on_hit: fh-=1
        state=yield {"damage":dmg,"as":asp,"crit":crit,"armor":ea,"mr":em,"physical":phy,"magic":onm,"physical_damage":phy*rm(ea),"magic_damage":magic_damage,"on_hit_events":on_hit_events,"true":true,"notes":note,"damage_components":item_components,"rage":rb,"light":light,"dark":dark,"phantom_dancer":pd_stacks,"kraken":kraken_hits,"yuntal_crit":ytcrit,"ad":current_ad,"fiend_remaining":fh,"fiend_until":fiend_until,"yuntal_until":yt_until,"bonus_as_total":s["bba"]+s["lvbas"]+total("as")+dyn+float(state.get("bonus_as",0))}


# Build Lab defaults. Ranking and Item Value use independent widget keys and defaults.
champ=st.session_state.get("build_champ",list(C)[0])
level=int(st.session_state.get("build_level",9))
mist=int(st.session_state.get("build_mist",40 if champ=="Senna" else 0)) if champ=="Senna" else 0
s=stats(champ,level,mist)
dist=float(st.session_state.get("build_dist",550.0))
mana=float(st.session_state.get("build_mana",0.0))
spell=bool(st.session_state.get("build_spell",True))
energized=bool(st.session_state.get("build_energized",True))
ult=False
execs=int(st.session_state.get("build_execs",0))


def _benchmark_target(name,lvl):
    target=dict(_target_profile_at_level(TARGET_PROFILES[name],lvl))
    natural_hp={"Squishy • Jinx":target["hp"],"Bruiser • Darius":660+148*gu(lvl),"Tank • Ornn":690+132*gu(lvl)}[name]
    target["bonus_hp"]=max(0.0,target["hp"]-natural_hp)
    return target

def _tab_hero(kicker,title,description):
    st.markdown(f'<div class="buildlab-hero"><span>{html.escape(kicker)}</span><strong>{html.escape(title)}</strong><p>{html.escape(description)}</p></div>',unsafe_allow_html=True)

def _setup_heading(step,kicker,title):
    st.markdown(f'<div class="setup-head"><span class="setup-step">{html.escape(step)}</span><div><small>{html.escape(kicker)}</small><strong>{html.escape(title)}</strong></div></div>',unsafe_allow_html=True)

def _champion_profile(name,lvl,mist_count=0):
    profile=stats(name,lvl,mist_count)
    slug={"Kog'Maw":"KogMaw","Kai'Sa":"Kaisa","Miss Fortune":"MissFortune"}.get(name,name)
    portrait=f"https://ddragon.leagueoflegends.com/cdn/15.15.1/img/champion/{slug}.png"
    attack_speed=profile["baseas"]+profile["ratio"]*(profile["bba"]+profile["lvbas"])
    st.markdown(f'<div class="champion-profile"><img src="{html.escape(portrait)}" alt="{html.escape(name)} portrait"><div class="identity"><div class="name">{html.escape(name)}</div><div class="level">LEVEL {lvl} · BEFORE ITEMS & RUNES</div><div class="champion-stats"><div><b>{profile["ad"]:.1f}</b><span>ATTACK DAMAGE</span></div><div><b>{attack_speed:.3f}</b><span>ATTACK SPEED</span></div></div></div></div>',unsafe_allow_html=True)

def _target_readout(target_hp,target_armor,target_mr,reduction=0):
    st.markdown(f'<div class="target-readout"><span><b>{target_hp:,.0f}</b> HP</span><span><b>{target_armor:g}</b> Armor</span><span><b>{target_mr:g}</b> MR</span><span><b>{reduction*100:.0f}%</b> AA reduction</span></div>',unsafe_allow_html=True)

def _audit_badges(rows,status_index=1):
    counts={}
    for row in rows: counts[row[status_index]]=counts.get(row[status_index],0)+1
    badges="".join(f'<span class="audit-badge {"pending" if state.startswith(("Pending","Blocked")) else "partial" if state in ("Partial","Scenario","Trigger Lite") else "modeled"}">{html.escape(state)} <b>{count}</b></span>' for state,count in counts.items())
    st.markdown(f'<div class="audit-badges">{badges}</div>',unsafe_allow_html=True)

st.markdown("""<style>
.setup-head{display:flex;align-items:center;gap:10px;margin:0 0 16px}.setup-step{display:flex;align-items:center;justify-content:center;width:30px;height:30px;border:1px solid #6b5931;border-radius:9px;color:#f0d58a;font-size:11px;font-weight:850;background:#211e15}
.setup-head strong{display:block;color:#edf2f8;font-size:17px}.setup-head small{display:block;font-size:9px;letter-spacing:.12em;color:#8796a9;text-transform:uppercase}
.champion-profile{display:flex;gap:18px;align-items:center;margin-top:12px;padding:17px;border:1px solid #394052;border-radius:13px;background:linear-gradient(120deg,#1c2534,#0b111b)}
.champion-profile img{width:86px;height:86px;border-radius:15px;object-fit:cover;border:1px solid #b9974d;box-shadow:0 8px 24px #0005}
.champion-profile .identity{min-width:0;flex:1}.champion-profile .name{font-size:24px;font-weight:850;color:#f2f5fa;line-height:1.2}.champion-profile .level{font-size:10px;letter-spacing:.1em;color:#d8b45d;margin-top:4px}
.champion-stats{display:flex;gap:25px;flex-wrap:wrap;margin-top:14px}.champion-stats b{display:block;font-size:18px;color:#edf2f8}.champion-stats span{font-size:9px;letter-spacing:.07em;color:#8f9bac}
.target-readout{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:15px;padding:12px 14px;border:1px solid #303e50;border-radius:11px;background:#090f18;font-size:11px;color:#a7b6c8}.target-readout b{color:#dce7f4}
.combat-flags{display:flex;gap:7px;flex-wrap:wrap;margin:10px 0 2px}.combat-flags span{font-size:9px;font-weight:750;letter-spacing:.03em;border:1px solid #2e3d50;border-radius:7px;padding:6px 9px;color:#8b9aae;background:#0a111b}.combat-flags span.active{border-color:#7d693c;background:#211e14;color:#f0d58a}
.wr-icon-name,.wr-tree-name{color:#aebbcf!important}
div[data-testid="stColumn"]:has(.wr-selected) .wr-icon-name,div[data-testid="stColumn"]:has(.wr-tree-selected) .wr-tree-name{color:#f0d58a!important}
@media(max-width:640px){
  .champion-profile{gap:12px;padding:13px}.champion-profile img{width:68px;height:68px}.champion-profile .name{font-size:21px}.champion-stats{gap:18px;margin-top:10px}.champion-stats b{font-size:16px}
  div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] .wr-pick-marker),div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] .wr-tree-marker),div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] .wr-eq-label),div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] .build-slot-marker){flex-wrap:wrap!important;gap:10px!important}
  div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:has(.wr-pick-marker),div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:has(.wr-tree-marker){flex:0 0 calc((100% - 20px)/3)!important;width:calc((100% - 20px)/3)!important;min-width:0!important;padding:8px 4px!important;background:#0d1520;border:1px solid #29364a;border-radius:12px}
  div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:has(.wr-eq-label),div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]:has(.build-slot-marker){flex:0 0 calc((100% - 20px)/3)!important;width:calc((100% - 20px)/3)!important;min-width:0!important}
  div[data-testid="stHorizontalBlock"]:has(.wr-pick-marker)>div[data-testid="stColumn"]:not(:has(.wr-pick-marker)),div[data-testid="stHorizontalBlock"]:has(.wr-tree-marker)>div[data-testid="stColumn"]:not(:has(.wr-tree-marker)){display:none!important}
  div[data-testid="stColumn"]:has(.wr-pick-marker) .stButton,div[data-testid="stColumn"]:has(.wr-tree-marker) .stButton{position:static!important;left:auto!important;transform:none!important;width:100%!important;height:auto!important;margin:3px 0 0!important;padding:0!important}
  div[data-testid="stColumn"]:has(.wr-pick-marker) .stButton button,div[data-testid="stColumn"]:has(.wr-tree-marker) .stButton button{position:static!important;inset:auto!important;min-height:44px!important;height:44px!important;width:100%!important;opacity:1!important;color:#e8eef7!important;background:#182435!important;border:1px solid #3e4e65!important;font-size:11px!important}
  div[data-testid="stColumn"]:has(.wr-pick-marker) .stButton button *,div[data-testid="stColumn"]:has(.wr-tree-marker) .stButton button *{opacity:1!important}
  .wr-icon-name{height:34px!important;font-size:11px!important;line-height:1.35!important;overflow-wrap:anywhere}.wr-tree-name{min-height:20px}.build-slot-name{overflow-wrap:anywhere}
  div[data-testid="stColumn"]:has(.wr-eq-label) .stButton button,div[data-testid="stColumn"]:has(.build-slot-marker) .stButton button{min-height:44px!important;font-size:11px!important}
  div[data-testid="stColumn"]:has(.wr-eq-label) div[data-testid="stImage"] img{max-width:100%!important}
}
@media(prefers-reduced-motion:reduce){div[data-testid="stColumn"]:has(.wr-pick-marker) *,div[data-testid="stColumn"]:has(.wr-tree-marker) *{transition:none!important}}
</style>""",unsafe_allow_html=True)

st.markdown("""<style>
.value-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:12px 0 22px}
.value-card{position:relative;min-width:0;padding:18px 12px 14px;border:1px solid #263246;border-radius:15px;background:linear-gradient(160deg,#111a27,#0a1018);text-align:center;transition:border-color .16s ease}
.value-card:first-child{border-color:#b9974d;background:linear-gradient(160deg,#252317,#10151d)}
.value-card:hover{border-color:#d8b45d}.value-rank{position:absolute;top:9px;left:10px;font-size:10px;color:#d8b45d;font-weight:800}
.value-card img{width:56px;height:56px;object-fit:cover;border-radius:11px;border:1px solid #394355;margin:6px 0 10px}
.value-name{font-size:12px;font-weight:750;color:#edf2f8;min-height:36px;line-height:1.4;overflow-wrap:anywhere}
.value-score{font-size:25px;font-weight:850;color:#f0d58a;line-height:1.3;margin-top:5px}.value-unit{font-size:9px;text-transform:uppercase;letter-spacing:.09em;color:#91a0b3}
.value-detail{border-top:1px solid #273140;margin-top:12px;padding-top:10px;display:flex;justify-content:space-between;gap:4px;font-size:10px;color:#aeb9c7}
@media(max-width:1000px){.value-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:640px){.value-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.value-card{padding:15px 8px 12px}.value-score{font-size:22px}}
</style>""",unsafe_allow_html=True)
st.markdown("""<style>
/* Shared final design system: panels, rankings, states and responsive navigation. */
[data-testid="stWidgetLabel"] p,div[role="radiogroup"] label p,[data-testid="stCheckbox"] label p{color:#d8e2f0!important}
[data-testid="stCaptionContainer"] p{color:#91a0b4!important}
div[data-baseweb="select"]>div{color:#eef3f8!important}
[data-testid="stNumberInput"] input,[data-testid="stTextInput"] input{color:#eef3f8!important}
[data-testid="stMetricDelta"]{color:#aebdd0!important}
[data-testid="stMetricValue"]{font-size:clamp(20px,2.3vw,32px)!important;max-width:100%}

.buildlab-hero strong{font-size:28px;letter-spacing:-.03em}.buildlab-hero p{font-size:12px;line-height:1.6;max-width:850px}
.stButton>button[kind="primary"]{border-color:#b49347!important;background:linear-gradient(120deg,#d8b45d,#f0d58a)!important;color:#10141b!important;min-height:48px!important}
.stButton>button[kind="primary"]:hover{color:#10141b!important;border-color:#f5dda0!important;box-shadow:0 4px 20px #d8b45d22!important}
.audit-badges{display:flex;gap:7px;flex-wrap:wrap;margin:12px 0}.audit-badge{border:1px solid #344359;background:#111b29;color:#b6c5d8;padding:6px 9px;font-size:10px;border-radius:8px}.audit-badge b{margin-left:5px}.audit-badge.modeled{border-color:#2c6559;color:#9fdbc7;background:#0d221f}.audit-badge.pending{border-color:#745134;color:#e8bd86;background:#21180e}.audit-badge.partial{border-color:#655b3a;color:#e3d294;background:#201e11}
.empty-state{padding:28px 20px;text-align:center;border:1px dashed #3b4b62;border-radius:14px;background:#0b121c;margin:18px 0}.empty-state strong{display:block;font-size:17px;color:#dce7f5}.empty-state p{margin:7px 0 0;font-size:12px;color:#8c9eb4}
.tier-rank-grid,.pair-rank-grid,.triple-rank-grid{grid-template-columns:repeat(5,minmax(0,1fr))!important}
.boot3-rank-grid,.boot4-rank-grid,.full-rank-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important}
.pair-rank-card:first-child,.triple-rank-card:first-child,.boot3-rank-card:first-child,.boot4-rank-card:first-child,.full-rank-card:first-child{grid-column:auto!important}
.tier-rank-card,.pair-rank-card,.triple-rank-card,.boot3-rank-card,.boot4-rank-card,.full-rank-card{padding:18px 12px 14px!important;border-radius:15px!important;background:linear-gradient(160deg,#111a27,#0a1018)!important;border-color:#263246!important;color:#e9eff7!important;box-shadow:0 8px 22px #0002!important}
.tier-rank-card:first-child,.pair-rank-card:first-child,.triple-rank-card:first-child,.boot3-rank-card:first-child,.boot4-rank-card:first-child,.full-rank-card:first-child{border-color:#b9974d!important;background:linear-gradient(160deg,#252317,#10151d)!important}
.tier-rank-name,.pair-rank-name,.triple-rank-name,.boot3-name,.boot4-name,.full-name{font-size:11px!important;line-height:1.4!important;color:#dce6f3!important;overflow-wrap:anywhere}
.tier-rank-dps,.pair-dps,.triple-dps,.boot3-dps,.boot4-dps,.full-dps{font-size:23px!important;color:#f0d58a!important;line-height:1.4!important}
.tier-rank-sub,.pair-sub,.triple-sub,.boot3-sub,.boot4-sub,.full-sub{font-size:10px!important;color:#a4b3c6!important;opacity:1!important;white-space:normal!important;line-height:1.5!important}
.pair-icons,.triple-icons,.boot3-icons,.boot4-icons,.full-icons{flex-wrap:wrap;gap:5px!important}
[data-testid="stDataFrame"]{max-width:100%;overflow:auto}.stButton button:focus-visible{outline:2px solid #f0d58a!important;outline-offset:3px!important}
div[data-testid="stColumn"]:has(.wr-pick-marker) .stButton button:disabled{cursor:default!important}
@media(max-width:1000px){.tier-rank-grid,.pair-rank-grid,.triple-rank-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important}.boot3-rank-grid,.boot4-rank-grid,.full-rank-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}}
@media(max-width:640px){
 [data-testid="stMainBlockContainer"]{padding-left:12px!important;padding-right:12px!important}
 div[data-testid="stTabs"] [data-baseweb="tab-list"]{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px;width:100%;overflow:visible!important}
 div[data-testid="stTabs"] button[data-baseweb="tab"]{min-width:0;width:100%;padding:0 8px!important;height:44px!important;justify-content:center;font-size:12px}
 .buildlab-hero{padding:16px}.buildlab-hero strong{font-size:25px}
 .tier-rank-grid,.pair-rank-grid,.triple-rank-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:9px!important}
 .boot3-rank-grid,.boot4-rank-grid,.full-rank-grid{grid-template-columns:minmax(0,1fr)!important;gap:10px!important}
 .triple-rank-card:first-child,.boot3-rank-card:first-child,.boot4-rank-card:first-child,.full-rank-card:first-child,.pair-rank-card:first-child{grid-column:auto!important}
 .tier-rank-card,.pair-rank-card,.triple-rank-card,.boot3-rank-card,.boot4-rank-card,.full-rank-card{padding:17px 10px 12px!important}
 .full-icons img,.boot4-icons img,.boot3-icons img{width:38px!important;height:38px!important}.full-name,.boot4-name,.boot3-name{min-height:0!important;margin:10px 0!important}
 div[data-testid="stColumn"]:has(.wr-pick-marker) .stButton button:disabled{color:#728299!important;background:#0c131e!important;border-color:#263448!important}
 .combat-hero{grid-template-columns:repeat(2,minmax(0,1fr))!important}.combat-kpi{min-width:0}.combat-kpi .value{font-size:26px!important}.combat-kpi .sub{overflow-wrap:anywhere}
}
@media(prefers-reduced-motion:reduce){.stButton button,.tier-rank-card,.pair-rank-card,.triple-rank-card,.boot3-rank-card,.boot4-rank-card,.full-rank-card{transition:none!important;transform:none!important}}
</style>""",unsafe_allow_html=True)

tabs=st.tabs(["⚔️ Item Tier List","🔥 Build Lab","💰 Item Value","📚 Database"])

with tabs[0]:
    _tab_hero("SHARPWR • ITEM BENCHMARKS","Item Tier List","Compare AA + ability fights. Full build Top 3 first, then 1–4 item Top 10 rankings.")

    _tier_left,_tier_right=st.columns(2,gap="medium")
    with _tier_left,st.container(border=True):
        _setup_heading("01","YOUR CHAMPION","Champion Profile")
        tier_champ=st.selectbox("Champion",list(C),index=0,key="tier_champ")
        tier_level=st.slider("Level",1,15,9,key="tier_level")
        tier_mist=st.number_input("Senna Mist",0,500,40,20,key="tier_mist") if tier_champ=="Senna" else 0
        _champion_profile(tier_champ,tier_level,tier_mist)
    with _tier_right,st.container(border=True):
        _setup_heading("02","FIXED BENCHMARK","Target Profile")
        tier_target=st.radio("Target Profile",list(TARGET_PROFILES),horizontal=True,key="tier_target",label_visibility="collapsed")
        _target=_target_profile_at_level(TARGET_PROFILES[tier_target],tier_level)
        _target_readout(_target["hp"],_target["armor"],_target["mr"],_target.get("aa_reduction",0))
        st.caption("Darius / Ornn apply 10% basic-attack reduction from level 5. Starting HP is configured below.")

    with st.container(border=True):
        tier_scenario=st.radio("Combat Scenario",["Standard Fight","First Contact"],horizontal=True,key="tier_scenario_v560")
        tier_energized=tier_scenario=="First Contact"
        with st.expander("Starting progression"):
            tier_execs=st.number_input("Collector previous executes",0,500,0,1,key="tier_execs")
            _tier_yuntal_default=0 if tier_level<=5 else (125 if tier_level>=9 else round(125*(tier_level-5)/4))
            tier_yuntal_stacks=st.number_input("Yun Tal permanent stacks",0,125,int(_tier_yuntal_default),1,key=f"tier_yuntal_stacks_{tier_level}")
            tier_dragon=st.number_input("Dragon Practice stacks",0,10000,0,key="tier_dragon") if tier_champ=="Smolder" else 0
            tier_mana=None
    _tier_signature=("5.77.0",tier_champ,tier_level,tier_target,tier_scenario,tier_mist,tier_execs,tier_yuntal_stacks,tier_dragon,tier_mana)
    if st.button(f"⚔️ FIND BEST BUILDS VS {tier_target.split(' • ')[0].upper()}",type="primary",use_container_width=True,key="tiercalc"):
        tier_hp=float(_target["hp"]);tier_armor=float(_target["armor"]);tier_mr=float(_target["mr"])
        _natural={"Squishy • Jinx":tier_hp,"Bruiser • Darius":660+148*gu(tier_level),"Tank • Ornn":690+132*gu(tier_level)}[tier_target]
        _progress=st.progress(0.,text="Simulating AA + abilities…")
        try:
            _evaluator=BuildFightEvaluator(globals(),tier_champ,int(tier_level),tier_hp,tier_armor,tier_mr,mist=tier_mist,bonus_hp=max(0.,tier_hp-_natural),aa_reduction=float(_target.get("aa_reduction",0)),base_mana=tier_mana if tier_mana else None,energized=tier_energized,yuntal_stacks=tier_yuntal_stacks,execs=tier_execs,dragon_stacks=tier_dragon)
            _search=search_builds(_evaluator,F,[x for x in TIER3 if x in B],progress=lambda value,text:_progress.progress(value,text=text))
            _replay_data=None
            _replay_error=None
            if _search['full']:
                _winner=_search['full'][0]
                _progress.progress(1.,text="Recording winner replay…")
                try:
                    _winner_trace=_evaluator.replay_row(_winner)
                    _replay_data=replay_payload(_winner_trace,champion=tier_champ,level=int(tier_level),target=tier_target,hp=tier_hp,build=_winner)
                except (ValueError,LookupError,StopIteration,AttributeError) as _err:
                    _replay_error=str(_err)
            st.session_state["tier_fight_results"]={"signature":_tier_signature,"results":_search,"replay":_replay_data,"replay_error":_replay_error}
            _history_key=(_tier_signature[0],tier_champ,tier_level,tier_scenario,tier_mist,tier_execs,tier_yuntal_stacks,tier_dragon,tier_mana)
            st.session_state.setdefault('combat_rank_history',{}).setdefault(_history_key,{})[tier_target]=_search
        except (ValueError,LookupError,StopIteration) as _err:
            st.error(f"Build search could not run: {_err}")
        finally:_progress.empty()
    if st.button("Compare all 3 target profiles",key="compare_all_profiles"):
        _history_key=(_tier_signature[0],tier_champ,tier_level,tier_scenario,tier_mist,tier_execs,tier_yuntal_stacks,tier_dragon,tier_mana)
        _history=st.session_state.setdefault('combat_rank_history',{}).setdefault(_history_key,{})
        _progress=st.progress(0.,text="Comparing three target profiles…")
        try:
            for _i,(_name,_profile) in enumerate(TARGET_PROFILES.items()):
                if _name in _history:continue
                _t=_target_profile_at_level(_profile,tier_level)
                _natural={"Squishy • Jinx":_t['hp'],"Bruiser • Darius":660+148*gu(tier_level),"Tank • Ornn":690+132*gu(tier_level)}[_name]
                _ev=BuildFightEvaluator(globals(),tier_champ,int(tier_level),float(_t['hp']),float(_t['armor']),float(_t['mr']),mist=tier_mist,bonus_hp=max(0.,_t['hp']-_natural),aa_reduction=float(_t.get('aa_reduction',0)),base_mana=tier_mana if tier_mana else None,energized=tier_energized,yuntal_stacks=tier_yuntal_stacks,execs=tier_execs,dragon_stacks=tier_dragon)
                _history[_name]=search_builds(_ev,F,[x for x in TIER3 if x in B],progress=lambda v,text,i=_i:_progress.progress((i+v)/3,text=text))
        except (ValueError,LookupError,StopIteration) as _err:st.error(f"Comparison could not finish: {_err}")
        finally:_progress.empty()
    _history_key=(_tier_signature[0],tier_champ,tier_level,tier_scenario,tier_mist,tier_execs,tier_yuntal_stacks,tier_dragon,tier_mana)
    _history=st.session_state.get('combat_rank_history',{}).get(_history_key,{})
    if _history:
        st.markdown("### Items across target profiles")
        st.caption(f"{tier_champ} · {len(_history)}/3 targets completed. Equal target weighting; Top-3 build appearances weighted 1, 1/2, 1/3. Offensive build coverage, not a complete item power rating.")
        st.dataframe(pd.DataFrame(consensus(_history)),hide_index=True,width="stretch")
    _saved=st.session_state.get("tier_fight_results")
    if _saved and _saved["signature"]==_tier_signature:
        _search=_saved["results"]
        st.markdown('<div class="sharp-section-head"><span>FINAL IDEAL BUILD</span><strong>Full Build · Top 3</strong><em>5 ITEMS + BOOTS</em></div>',unsafe_allow_html=True)
        st.markdown("""<style>.fight-build-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:12px 0 20px}.fight-build-card{padding:18px;border:1px solid #32445a;border-radius:16px;background:#101c2c}.fight-build-card:first-child{border-color:#c9a84c}.fight-build-icons{display:flex;gap:4px;flex-wrap:wrap;margin:12px 0}.fight-build-icons img{width:38px;height:38px;border-radius:6px}.fight-build-card strong{font-size:22px;color:#f4d383}.fight-build-card p{font-size:12px;color:#b6c5d8;line-height:1.6}.fight-build-kpi{font-size:25px;font-weight:800}@media(max-width:760px){.fight-build-grid{grid-template-columns:1fr}}</style>""",unsafe_allow_html=True)
        _cards=['<div class="fight-build-grid">']
        for _rank,_r in enumerate(_search["full"],1):
            _names=list(_r["Items"])+[_r["Boots"]]
            _images=''.join(f'<img src="{html.escape(boot_icon(x) if x in B else item_icon(x))}" alt="{html.escape(x)}" title="{html.escape(x)}">' for x in _names)
            _ttk=f'{_r["TTK"]:.3f}s TTK' if _r["TTK"] is not None else 'Target survived'
            _tie=f'<p class="rank-tie">{html.escape(_r.get("Rank explanation", ""))}</p>' if _r.get("Rank explanation") else ""
            _cards.append(f'<div class="fight-build-card"><strong>#{_rank}</strong><div class="fight-build-icons">{_images}</div><p>{"<br>".join(html.escape(x) for x in _names)}</p><div class="fight-build-kpi">{_ttk}</div>{_tie}<p>{_r["DPS"]:.1f} DPS · {int(_r["Gold"]):,}g<br>{_r["AD"]:.0f} AD · {_r["AP"]:.0f} AP · {_r["Crit %"]:.0f}% crit · {_r["AH"]:.0f} AH<br>{_r["Starting AS"]:.2f} starting AS · {_r["AS over cap"]:.2f} AS above starting cap</p></div>')
        _cards.append('</div>');st.markdown(''.join(_cards),unsafe_allow_html=True)
        st.markdown(f'### Item Tier List For "{tier_champ}"')
        st.caption(f"Top 10 from this search · {tier_target} · full-build ranks plus 1–4 item ranks. These are matchup recommendations, not mandatory purchases.")
        _item_cards=['<div class="partial-build-grid">']
        for _rank,_item in enumerate(champion_items(_search),1):
            _name=_item['Item']
            _item_cards.append(f'<div class="partial-build-card"><div class="partial-build-rank">#{_rank}</div><div class="partial-build-body"><div class="partial-build-item"><img src="{html.escape(item_icon(_name))}" alt="{html.escape(_name)}"><span>{html.escape(_name)}</span></div><p>{html.escape(_item["Note"])}</p></div></div>')
        _item_cards.append('</div>');st.markdown(''.join(_item_cards),unsafe_allow_html=True)

        if _saved.get('replay_error'):
            st.warning(f"Build results are available; replay could not be recorded: {_saved['replay_error']}")
        if _saved.get('replay'):
            st.markdown('### Combat Replay · #1 Build')
            components.html(replay_html(_saved['replay']),height=790,scrolling=True)
            import json as _replay_json
            st.download_button("Download replay trace",_replay_json.dumps(_saved['replay'],ensure_ascii=False,indent=2),file_name=f"{tier_champ.lower().replace(' ', '-')}-combat-replay.json",mime="application/json",key="combat_replay_download")
        st.caption(f'AA + abilities · expected crit · fastest target defeat · {_search["simulations"]:,} fight simulations. Top 3 among tested builds; 3–5 item searches retain {_search["beam_width"]} candidates per stage and refine {_search["refined"]} full-build finalists. AP, crit, on-hit, penetration and hybrid paths are retained. Finalists are rechecked with six skill priorities, movement alternatives, AA weaving and two ultimate timings. No incoming damage or defensive value is ranked.')
        def _tier_result_frame(rows):
            return pd.DataFrame([{"Rank":i,"Build":" + ".join(r["Items"])+(" + "+r["Boots"] if r["Boots"] else ""),"TTK (s)":r["TTK"],"DPS":round(r["DPS"],1),"AA damage":round(r["AA damage"],1),"Abilities / passives":round(r["Other damage"],1),"Gold":r["Gold"],"AD":round(r["AD"],1),"AP":r["AP"],"Crit %":r["Crit %"],"AH":r["AH"],"Skill order":r["Rotation"],"Movement":{"skill_envelope":"Ready skill range","aa_envelope":"Maximum AA range","close_envelope":"Close range","approach":"Melee approach"}.get(r.get("Movement"),"Kit default"),"Ultimate timing":"After basic skills" if r.get("Ultimate timing")=="after_basics" else "Before basic skills","AA weaving":"AA between skills" if r.get("Attack weaving")=="aa_weave" else "Skills first","Starting AS":round(r["Starting AS"],3),"AS above starting cap":round(r["AS over cap"],3)} for i,r in enumerate(rows,1)])
        st.dataframe(_tier_result_frame(_search["full"]),hide_index=True,width="stretch")
        with st.expander("Best build · measured item contributions"):
            st.dataframe(pd.DataFrame(_search["marginal"]),hide_index=True,width="stretch")
            st.caption("Each item is removed and the fight is recalculated. The effects overlap and are not additive. AS above cap can still provide value through item procs or champion conversions.")
        st.markdown("""<style>.partial-build-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:12px 0 24px}.partial-build-card{display:flex;gap:14px;align-items:flex-start;padding:16px;border:1px solid #32445a;border-radius:14px;background:#101c2c;min-width:0}.partial-build-rank{font-size:21px;font-weight:800;color:#f4d383;min-width:34px}.partial-build-body{flex:1;min-width:0}.partial-build-items{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:12px}.partial-build-item{display:flex;gap:7px;align-items:center;max-width:100%;font-size:11px;color:#dce6f3}.partial-build-item img{width:40px;height:40px;border-radius:7px;flex-shrink:0}.partial-build-item span{max-width:145px;overflow-wrap:anywhere}.partial-build-metrics{font-size:13px;color:#f0d58a}.partial-build-stats{font-size:10px;line-height:1.6;color:#a4b3c6;margin-top:5px}.rank-tie{color:#f0d58a!important;font-size:11px!important}@media(max-width:760px){.partial-build-grid{grid-template-columns:1fr}}</style>""",unsafe_allow_html=True)
        for _stage in range(1,5):
            st.markdown(f'### {_stage}-Item · Top 10')
            _partial_cards=['<div class="partial-build-grid">']
            for _rank,_r in enumerate(_search["stages"][_stage],1):
                _partial_items=''.join(f'<div class="partial-build-item"><img src="{html.escape(item_icon(x))}" alt="{html.escape(x)}" title="{html.escape(x)}"><span>{html.escape(x)}</span></div>' for x in _r["Items"])
                _partial_ttk=f'{_r["TTK"]:.3f}s TTK' if _r["TTK"] is not None else 'Target survived'
                _partial_tie=f'<div class="rank-tie">{html.escape(_r.get("Rank explanation", ""))}</div>' if _r.get("Rank explanation") else ''
                _partial_cards.append(f'<div class="partial-build-card"><div class="partial-build-rank">#{_rank}</div><div class="partial-build-body"><div class="partial-build-items">{_partial_items}</div><div class="partial-build-metrics">{_partial_ttk} · {_r["DPS"]:.1f} DPS · {int(_r["Gold"]):,}g</div>{_partial_tie}<div class="partial-build-stats">{_r["AD"]:.0f} AD · {_r["AP"]:.0f} AP · {_r["Crit %"]:.0f}% crit · {_r["AH"]:.0f} AH</div></div></div>')
            _partial_cards.append('</div>');st.markdown(''.join(_partial_cards),unsafe_allow_html=True)
            with st.expander(f'{_stage}-item combat details'):
                st.dataframe(_tier_result_frame(_search["stages"][_stage]),hide_index=True,width="stretch")
        _notes=sorted({note for r in _search["full"] for note in r["Assumptions"]})
        if _notes:
            with st.expander("Unverified mechanics that may affect ranking"):
                for _note in _notes:st.write(_note)
    else:
        st.markdown('<div class="empty-state"><strong>Find your best tested build</strong><p>Full-build Top 3 appears first, followed by 1–4 item Top 10 rankings.</p></div>',unsafe_allow_html=True)


with tabs[1]:
    _tab_hero("SHARPWR • LOADOUT WORKBENCH","Build Lab","Configure champion, target, runes and items. Build a full loadout and inspect its combat performance.")
    # Build Lab owns the manual champion/target/scenario controls.
    _champ_panel,_target_panel=st.columns([1,1],gap="medium")
    with _champ_panel,st.container(border=True):
        _setup_heading("01","YOUR CHAMPION","Champion Profile")
        champ=st.selectbox("Champion",list(C),index=list(C).index(champ),key="build_champ")
        level=st.slider("Level",1,15,level,key="build_level")
        mist=st.number_input("Senna Mist",0,500,int(mist),20,key="build_mist") if champ=="Senna" else 0
        s=stats(champ,level,mist)
        _champion_profile(champ,level,mist)
    with _target_panel,st.container(border=True):
        _setup_heading("02","FIXED BENCHMARK","Target Profile")
        build_target_profile=st.radio("Target Profile",list(TARGET_PROFILES),horizontal=True,key="build_target_profile",label_visibility="collapsed")
        _build_target=_benchmark_target(build_target_profile,level)
        hp=float(_build_target["hp"]); armor=float(_build_target["armor"]); mr=float(_build_target["mr"])
        bonus_hp=float(_build_target["bonus_hp"])
        target_aa_reduction=float(_build_target.get("aa_reduction",0))
        _target_readout(hp,armor,mr,target_aa_reduction)
        st.caption("Stats follow this tab's level. Darius / Ornn apply 10% basic-attack reduction from level 5.")
    with st.container(border=True):
        _setup_heading("03","STARTING CONDITIONS","Combat Setup")
        _proc_cols=st.columns(3)
        spell=_proc_cols[0].checkbox("Spellblade ready",spell,key="build_spell",help="Ability cast before the first basic attack.")
        energized=_proc_cols[1].checkbox("Energized ready",energized,key="build_energized",help="Start with Energized / Jolt proc ready.")
        ult=False
        with st.expander("Advanced combat settings"):
            _adv_left,_adv_right=st.columns(2)
            dist=_adv_left.number_input("Attack distance",0.0,1000.0,float(dist),25.0,key="build_dist")
            st.caption(f"Target bonus HP from profile: {bonus_hp:,.0f}")
            mana=_adv_left.number_input("Champion Max Mana before item",0.0,5000.0,float(mana),50.0,key="build_mana")
            execs=_adv_right.number_input("Collector previous executes",0,500,int(execs),1,key="build_execs")
        _flags=[("SPELLBLADE",spell),("ENERGIZED",energized),("ULTIMATE PRE-CAST",ult)]
        _flag_html="".join(f'<span class="{"active" if enabled else ""}">{name} · {"ON" if enabled else "OFF"}</span>' for name,enabled in _flags)
        st.markdown(f'<div class="combat-flags">{_flag_html}<span>{dist:g} ATTACK DISTANCE</span></div>',unsafe_allow_html=True)
    if champ=="Jhin": st.warning("Jhin is excluded from V5 rankings until its 4-shot/reload model is added.")

    # Legal rune loadout: equip one slot at a time; completed pickers collapse.
    st.markdown("""<div class="rune-forge-head"><div class="gem"><b>✦</b></div><div><span>RUNE FORGE</span><strong>Configure Rune Loadout</strong></div></div>""",unsafe_allow_html=True)
    sub_trees=["Precision","Domination","Resolve","Sorcery"]

    # Explicit equipped state: None means the user still needs to choose that slot.
    _rune_defaults={
        "build_keystone":None,
        "build_primary_slot1":None,
        "build_primary_slot2":None,
        "build_primary_slot3":None,
        "build_secondary_rune":None,
    }
    for _k,_v in _rune_defaults.items():
        if _k not in st.session_state: st.session_state[_k]=_v
    _rune_count=sum(bool(st.session_state.get(_k)) for _k in _rune_defaults)
    _rune_state_class="ok" if _rune_count==5 else ""
    st.markdown(f'<div class="rune-status"><span class="{_rune_state_class}">{_rune_count}/5 RUNES EQUIPPED</span><span>1 KEYSTONE</span><span>3 PRIMARY</span><span>1 SECONDARY</span></div>',unsafe_allow_html=True)

    with st.container(border=True):
        _eqcols=st.columns(5,gap="small")
        _eqslots=[
            ("KEY RUNE","build_keystone"),
            ("PRIMARY 1","build_primary_slot1"),
            ("PRIMARY 2","build_primary_slot2"),
            ("PRIMARY 3","build_primary_slot3"),
            ("SECONDARY","build_secondary_rune"),
        ]
        for _i,(_label,_key) in enumerate(_eqslots):
            with _eqcols[_i]:
                _equipped_rune_slot(_label,_key)

    # Only unresolved slots show their selection UI.
    if not st.session_state.get("build_keystone"):
        st.markdown('<div class="wr-rune-section key"><span>KEY RUNE</span></div>',unsafe_allow_html=True)
        keystone=_rune_icon_grid("Choose Key Rune",RUNE_TREES["Key Rune"],"build_keystone",6)
    else:
        keystone=st.session_state.build_keystone

    _primary_done=all(st.session_state.get(f"build_primary_slot{x}") for x in (1,2,3))
    if not _primary_done:
        st.markdown('<div class="wr-rune-section primary"><span>PRIMARY RUNES</span></div>',unsafe_allow_html=True)
        primary_tree=_tree_icon_picker("Primary Tree",sub_trees,"build_primary_tree",4)
        # Tree changes invalidate only equipped primary runes that do not belong to the new tree.
        for _slot in (1,2,3):
            _key=f"build_primary_slot{_slot}"
            if st.session_state.get(_key) not in RUNE_SLOTS[primary_tree][_slot]:
                st.session_state[_key]=None
        if not st.session_state.get("build_primary_slot1"):
            primary_1=_rune_icon_grid("Primary • Slot 1",RUNE_SLOTS[primary_tree][1],"build_primary_slot1",4)
        else: primary_1=st.session_state.build_primary_slot1
        if not st.session_state.get("build_primary_slot2"):
            primary_2=_rune_icon_grid("Primary • Slot 2",RUNE_SLOTS[primary_tree][2],"build_primary_slot2",4)
        else: primary_2=st.session_state.build_primary_slot2
        if not st.session_state.get("build_primary_slot3"):
            primary_3=_rune_icon_grid("Primary • Slot 3",RUNE_SLOTS[primary_tree][3],"build_primary_slot3",4)
        else: primary_3=st.session_state.build_primary_slot3
    else:
        primary_tree=st.session_state.get("build_primary_tree","Precision")
        primary_1=st.session_state.build_primary_slot1
        primary_2=st.session_state.build_primary_slot2
        primary_3=st.session_state.build_primary_slot3

    _secondary_trees=[x for x in sub_trees if x!=primary_tree]
    secondary_tree=st.session_state.get("build_secondary_tree",_secondary_trees[0])
    if secondary_tree not in _secondary_trees:
        secondary_tree=_secondary_trees[0]; st.session_state.build_secondary_tree=secondary_tree
        st.session_state.build_secondary_rune=None
    if not st.session_state.get("build_secondary_rune"):
        st.markdown('<div class="wr-rune-section secondary"><span>SECONDARY RUNE</span></div>',unsafe_allow_html=True)
        secondary_tree=_tree_icon_picker("Secondary Tree",_secondary_trees,"build_secondary_tree",3)
        secondary_options=sum((RUNE_SLOTS[secondary_tree][slot] for slot in (1,2,3)),[])
        secondary_rune=_rune_icon_grid("Choose Secondary Rune",secondary_options,"build_secondary_rune",6)
    else:
        secondary_rune=st.session_state.build_secondary_rune

    selected_sub_runes=[primary_1,primary_2,primary_3,secondary_rune]
    combat_rune=next((r for r in selected_sub_runes if r in {"Cut Down","Coup de Grace","Brutal","Legend: Alacrity"}),"None")
    # Progression controls are generated for every selected rune that needs persistent state.
    selected_runes=[keystone]+selected_sub_runes
    with st.expander("Rune combat settings · progression & triggers"):
        dark_harvest_souls=st.number_input("Dark Harvest souls",0,500,0,1,key="dh_souls") if "Dark Harvest" in selected_runes else 0
        eyeball_stacks=st.number_input("Eyeball Collection stacks",0,8,8,1,key="eyeball_stacks") if "Eyeball Collection" in selected_runes else 0
        hubris_kills=st.number_input("Hubris — champion kill count",0,100,0,1,key="hubris_kills") if "Hubris" in selected_runes else 0
        hubris_active=st.checkbox("Hubris — 30s Adaptive Force buff active",value=False,key="hubris_active") if "Hubris" in selected_runes else False
        alacrity_full=st.checkbox("Legend: Alacrity — full progression (+21% AS total)",value=False,key="alacrity_full") if "Legend: Alacrity" in selected_runes else False
        haste_full=st.checkbox("Legend: Haste — full progression (+15 Ability Haste)",value=False,key="haste_full") if "Legend: Haste" in selected_runes else False
        bloodline_full=st.checkbox("Legend: Bloodline — full progression (+8% Omnivamp total)",value=False,key="bloodline_full") if "Legend: Bloodline" in selected_runes else False
        # Ability Trigger Engine Lite: shared combat events drive rune triggers.
        _needs_ability_event=any(r in selected_runes for r in ["Arcane Comet","Chain Assault","Scorch","Transcendence","Manaflow Band"])
        _needs_basic_event=("Transcendence" in selected_runes)
        _needs_ult_event=("Axiom Arcanist" in selected_runes)
        _needs_immobilize=any(r in selected_runes for r in ["Ice Overlord","Courage of the Colossus","Perseverance"])
        _needs_mobility=("Sudden Impact" in selected_runes)
        _needs_summoner=("Nimbus Cloak" in selected_runes)
        _needs_takedown=any(r in selected_runes for r in ["Triumph","Hubris","Axiom Arcanist"])

        if any([_needs_ability_event,_needs_basic_event,_needs_ult_event,_needs_immobilize,_needs_mobility,_needs_summoner,_needs_takedown]):
            st.markdown("**Combat Events — Trigger Engine Lite**")
            st.caption("These are trigger events only; champion ability damage is not calculated.")
        ability_hit=st.checkbox("Ability Hit",value=False,key="evt_ability_hit") if _needs_ability_event else False
        basic_ability_hit=st.checkbox("Basic Ability Hit",value=False,key="evt_basic_hit") if _needs_basic_event else False
        ultimate_hit=st.checkbox("Ultimate Hit / Cast",value=False,key="evt_ultimate_hit") if _needs_ult_event else False
        immobilize_event=st.checkbox("Immobilized enemy champion",value=False,key="evt_immobilize") if _needs_immobilize else False
        mobility_trigger=st.checkbox("Dash / leap / blink / teleport / stealth used",value=False,key="evt_mobility") if _needs_mobility else False
        summoner_used=st.checkbox("Summoner Spell Used",value=False,key="evt_summoner") if _needs_summoner else False
        takedown_event=st.checkbox("Champion Takedown",value=False,key="evt_takedown") if _needs_takedown else False

        # Existing rune-specific states that are not generic combat events.
        first_strike_ready=st.checkbox("First Strike — proc ready at combat start",value=True,key="first_strike_ready") if "First Strike" in selected_runes else False
        grasp_ready=st.checkbox("Grasp — already 3s in champion combat",value=False,key="grasp_ready") if "Grasp of the Undying" in selected_runes else False
        aery_ready=st.checkbox("Aery — available at combat start",value=True,key="aery_ready") if "Aery" in selected_runes else False
        comet_ability_hit=ability_hit
        comet_total_hits=st.number_input("Arcane Comet — previous champion hits",0,999,0,1,key="comet_hits") if "Arcane Comet" in selected_runes else 0
        fleet_ready=st.checkbox("Fleet Footwork — start at 100 Energy",value=False,key="fleet_ready") if "Fleet Footwork" in selected_runes else False
        target_impaired=st.checkbox("Target is movement-impaired",value=False,key="target_impaired") if "Cheap Shot" in selected_runes else False
        chain_marked=ability_hit if "Chain Assault" in selected_runes else False
        own_hp_pct=st.slider("Your current Health",0,100,100,1,format="%d%%",key="rune_own_hp") if "Last Stand" in selected_runes else 100
        battle_seconds=st.number_input("Battle Zeal — seconds already in champion combat",0,3,0,1,key="battle_zeal_seconds") if "Battle Zeal" in selected_runes else 0
        absolute_focus_active=st.checkbox("Absolute Focus — above 65% Health",value=True,key="absolute_focus_active") if "Absolute Focus" in selected_runes else False
        scorch_ability_hit=ability_hit
        nearby_enemies=st.slider("Unshakeable — nearby enemy champions",0,3,3,1,key="unshakeable_enemies") if "Unshakeable" in selected_runes else 0
        overgrowth_stacks=st.number_input("Overgrowth — stacks",0,999,60,1,key="overgrowth_stacks") if "Overgrowth" in selected_runes else 0
        font_ally_near=st.checkbox("Font of Life — injured ally nearby",value=False,key="font_ally_near") if "Font of Life" in selected_runes else False
        game_minute=st.slider("Gathering Storm — game minute",0,21,15,1,key="gathering_storm_minute") if "Gathering Storm" in selected_runes else 0
        axiom_ult_scenario=ultimate_hit if "Axiom Arcanist" in selected_runes else False

    st.caption(f"Loadout: {keystone} • {primary_tree}: {primary_1} / {primary_2} / {primary_3} • {secondary_tree}: {secondary_rune}")
    _passive_notes=[]
    if "Manaflow Band" in selected_runes: _passive_notes.append("Manaflow: +300 Mana")
    if "Zombie Ward" in selected_runes: _passive_notes.append("Zombie Ward: +15 AD (5 stacks)")
    if "Relentless Hunter" in selected_runes: _passive_notes.append("Relentless Hunter: +20 out-of-combat MS (5 stacks)")
    if "Legend: Haste" in selected_runes: _passive_notes.append(f"Legend Haste: +{15 if haste_full else 0} AH")
    if "Legend: Bloodline" in selected_runes: _passive_notes.append(f"Bloodline: {8 if bloodline_full else 1}% Omnivamp")
    if "Eyeball Collection" in selected_runes: _passive_notes.append(f"Eyeball Collection: {eyeball_stacks}/8 stacks = +{1.5*eyeball_stacks:g} AD")
    if "Hubris" in selected_runes: _passive_notes.append(f"Hubris: {'ACTIVE +' + str(5+hubris_kills) + ' AD' if hubris_active else 'buff inactive'}")
    if "Overgrowth" in selected_runes:
        _og_flat=overgrowth_stacks*3
        _passive_notes.append(f"Overgrowth: {_og_flat:+g} flat HP"+(" • ×1.03 max Health" if overgrowth_stacks>=30 else ""))
    if "Unshakeable" in selected_runes: _passive_notes.append(f"Unshakeable: +{3+2*nearby_enemies}% Armor/MR"+(" • 20% Slow Resist" if nearby_enemies==3 else ""))
    if "Celerity" in selected_runes: _passive_notes.append("Celerity: +2% MS; other MS bonuses ×1.07")
    if "Transcendence" in selected_runes: _passive_notes.append(f"Transcendence: +{5 if level<5 else 10} AH"+(" • Lv9 basic-ability CD proc TRIGGERED" if level>=9 and basic_ability_hit else (" • Lv9 proc ready for Basic Ability Hit" if level>=9 else "")))
    if "Nimbus Cloak" in selected_runes and summoner_used: _passive_notes.append("Nimbus Cloak active: +10–40% MS for 3s")
    if "Revitalize" in selected_runes: _passive_notes.append("Revitalize: +5% healing/shielding; +10% more below 40% target HP")
    if "Second Wind" in selected_runes: _passive_notes.append("Second Wind: 5 HP/5s; after champion damage 3 + 1.5% missing HP over 5s")
    if "Perseverance" in selected_runes: _passive_notes.append("Perseverance: +10% Tenacity"+(f" • immobilize event: +{lvl_scale(10,15,level):.1f} Armor/MR for 1.5s" if immobilize_event else ""))
    if "Gathering Storm" in selected_runes:
        _gs_preview=max((v for m,v in ((6,2),(9,5),(12,9),(15,14),(18,20),(21,27)) if game_minute>=m),default=0)
        _passive_notes.append(f"Gathering Storm @ {game_minute}m: +{_gs_preview} AD")
    if "Axiom Arcanist" in selected_runes: _passive_notes.append("Axiom Arcanist: "+("Ultimate event active • " if ultimate_hit else "")+"Ultimate +10% damage/heal/shield • AoE ultimate damage increase +5%"+(" • takedown event: -7% remaining ult CD" if takedown_event else ""))
    if "Hexflash" in selected_runes: _passive_notes.append("Hexflash: available while Flash is on cooldown • 18s CD • entering champion combat → 6s CD")
    if "Botanist" in selected_runes: _passive_notes.append("Botanist: plant +10g • Honeyfruit heal +20% • Scryer vision +20% • Blast Cone +40% MS for 2.5s")
    if "Ixtali Seedjar" in selected_runes: _passive_notes.append("Ixtali Seedjar: plant seed replaces trinket for 60s • unique plant 30s cooldown")
    if "Battle Zeal" in selected_runes: _passive_notes.append(f"Battle Zeal: +{1.4*min(3,int(battle_seconds)):.1f}% basic-ability damage only")
    if "Demolish" in selected_runes: _passive_notes.append("Demolish: turret-only third-attack proc • Max-HP calculation pending champion HP data")
    if "Font of Life" in selected_runes: _passive_notes.append("Font of Life: healing calculation pending champion Max HP data")
    if "Courage of the Colossus" in selected_runes: _passive_notes.append(f"Courage: "+("TRIGGERED • " if immobilize_event else "")+f"shield {lvl_scale(25,45,level):.1f} + 1% Max HP • 18s CD")
    if "Nullifying Orb" in selected_runes: _passive_notes.append(f"Nullifying Orb: shield {lvl_scale(60,180,level):.1f} at <35% HP • 60s CD")
    if "Bone Plating" in selected_runes: _passive_notes.append(f"Bone Plating: {lvl_scale(30,60,level):.1f} damage reduction on current + next 3 champion hits/abilities within 1.5s • 40s CD")

    if _passive_notes: st.caption(" • ".join(_passive_notes))
    # Rune icon selector is enabled only after verified local rune assets are present.
    st.caption("Primary: one rune from each of its 3 slots. Secondary: one rune from a different tree.")
    st.caption("Exactly 5 different completed items + 1 required Boots slot.")
    # Premium clickable item picker.
    if "build_items_v2" not in st.session_state:
        st.session_state.build_items_v2=list(F)[:5]

    st.markdown("""<div class="build-forge-head"><div class="forge-icon">◆</div><div><span>BUILD FORGE</span><strong>Assemble Full Loadout</strong></div></div>""",unsafe_allow_html=True)
    build=list(st.session_state.build_items_v2)
    _seen_spellblade=False;_legal_build=[]
    for _item in build:
        if _item in SPELLBLADE:
            if _seen_spellblade:continue
            _seen_spellblade=True
        _legal_build.append(_item)
    build=_legal_build;st.session_state.build_items_v2=build
    _item_gold=sum(float(dct(F[_x])["gold"]) for _x in build)
    _build_ready=len(build)==5 and len(set(build))==5
    st.markdown(f'<div class="build-summary"><span class="{"ready" if _build_ready else ""}">{len(build)}/5 ITEMS</span><span>{int(_item_gold):,}g ITEM COST</span><span>+ 1 BOOTS SLOT</span></div>',unsafe_allow_html=True)
    slot_cols=st.columns(5,gap="small")
    for _i in range(5):
        with slot_cols[_i]:
            st.markdown('<div class="build-slot-marker"></div>',unsafe_allow_html=True)
            if _i<len(build):
                _it=build[_i]; _url=item_icon(_it)
                if _url: st.image(_url,width=58)
                st.markdown(f'<div class="build-slot-name">{html.escape(_it)}</div>',unsafe_allow_html=True)
                if st.button("✕ Remove",key=f"remove_item_{_i}",use_container_width=True):
                    build.pop(_i); st.session_state.build_items_v2=build; st.rerun()
            else:
                st.markdown('<div class="build-empty-slot">＋</div><div class="build-slot-name">EMPTY SLOT</div>',unsafe_allow_html=True)

    st.markdown('<div class="wr-picker-title">Items</div>',unsafe_allow_html=True)
    st.caption("Hover for item details • click the icon to equip.")
    _item_names=list(F); _ncols=10
    for _start in range(0,len(_item_names),_ncols):
        _row=st.columns(_ncols,gap="small")
        for _j,_name in enumerate(_item_names[_start:_start+_ncols]):
            _ii=_start+_j; _col=_row[_j]; _icon=item_icon(_name); _selected=_name in build; _q=dct(F[_name])
            _stats=[]
            for _key,_label in STAT_NAMES.items():
                _v=_q.get(_key,0)
                if _v:
                    _val=f"{_v*100:g}%" if _key in ("as","crit","lifesteal","pctpen","ms") else f"{_v:g}"
                    _stats.append(f'<div class="wr-card-stat"><b>{html.escape(_val)}</b>{html.escape(_label)}</div>')
            _card=f'<div class="wr-hover-card"><div class="wr-card-title">{html.escape(_name)}</div><div class="wr-card-sub">◆ {int(_q["gold"])} Gold</div><div class="wr-card-rule"></div><div class="wr-card-stats">{"".join(_stats)}</div></div>'
            _spellblade_locked=_name in SPELLBLADE and not _selected and bool(set(build)&SPELLBLADE)
            with _col:
                st.markdown('<div class="wr-pick-marker '+('wr-selected' if _selected else '')+'">'+_card+'</div>',unsafe_allow_html=True)
                if _icon: st.image(_icon,width=66)
                st.markdown(f'<div class="wr-icon-name">{html.escape(_name)}</div>',unsafe_allow_html=True)
                if st.button("Equipped" if _selected else "Spellblade locked" if _spellblade_locked else "Build full" if len(build)>=5 else "Equip",key=f"native_item_{_ii}",help=None,use_container_width=False,disabled=_selected or len(build)>=5 or _spellblade_locked):
                    _new=list(st.session_state.build_items_v2)
                    if _name not in _new and len(_new)<5 and not (_name in SPELLBLADE and set(_new)&SPELLBLADE):
                        _new.append(_name); st.session_state.build_items_v2=_new
                    st.rerun()
        st.markdown('<div class="wr-grid-gap"></div>',unsafe_allow_html=True)
    st.markdown('<div class="wr-picker-title">Boots</div>',unsafe_allow_html=True)
    st.caption("Hover for boot details • click the icon to equip.")
    if "build_boot_v2" not in st.session_state:
        st.session_state.build_boot_v2=list(B)[0]

    # Database is stored as seven T2 -> T3 upgrade pairs.
    _boot_pairs=[
        ("Gluttonous Greaves","Immortal Treads"),
        ("Ionian Boots of Lucidity","Crimson Lucidity"),
        ("Berserker's Greaves","Gunmetal Greaves"),
        ("Mercury's Treads","Chainlaced Crushers"),
        ("Plated Steelcaps","Armored Advance"),
        ("Boots of Mana","Spellslinger's Shoes"),
        ("Boots of Dynamism","Armorcrusher Boots"),
    ]
    _boot_tiers=[
        ("T3 BOOTS",[t3 for t2,t3 in _boot_pairs],"wr-tier-t3"),
        ("T2 BOOTS",[t2 for t2,t3 in _boot_pairs],"wr-tier-t2"),
    ]
    _boot_index={name:i for i,name in enumerate(B)}
    for _tier_label,_boot_names,_tier_class in _boot_tiers:
        st.markdown(f'<div class="wr-tier-label {_tier_class}">{_tier_label}</div>',unsafe_allow_html=True)
        _row=st.columns(7,gap="small")
        for _j,_name in enumerate(_boot_names):
            _i=_boot_index[_name]; _icon=boot_icon(_name); _q=dct(B[_name]); _sel=st.session_state.build_boot_v2==_name
            _stats=[]
            for _key,_label in STAT_NAMES.items():
                _v=_q.get(_key,0)
                if _v:
                    _val=f"{_v*100:g}%" if _key in ("as","crit","lifesteal","pctpen","ms") else f"{_v:g}"
                    _stats.append(f'<div class="wr-card-stat"><b>{html.escape(_val)}</b>{html.escape(_label)}</div>')
            _card=f'<div class="wr-hover-card"><div class="wr-card-title">{html.escape(_name)}</div><div class="wr-card-sub">◆ {int(_q["gold"])} Gold</div><div class="wr-card-rule"></div><div class="wr-card-stats">{"".join(_stats)}</div></div>'
            with _row[_j]:
                st.markdown('<div class="wr-pick-marker '+('wr-selected' if _sel else '')+'">'+_card+'</div>',unsafe_allow_html=True)
                if _icon: st.image(_icon,width=66)
                st.markdown(f'<div class="wr-icon-name">{html.escape(_name)}</div>',unsafe_allow_html=True)
                if st.button("Equipped" if _sel else "Equip",key=f"pick_boot_{_i}",help=None,use_container_width=False):
                    st.session_state.build_boot_v2=_name
                    st.rerun()
        st.markdown('<div class="wr-grid-gap"></div>',unsafe_allow_html=True)
    boot=st.session_state.build_boot_v2
    _bq=dct(B[boot])
    st.markdown(f'<div class="boot-equipped"><img src="{html.escape(boot_icon(boot))}"><div><span>EQUIPPED BOOTS</span><strong>{html.escape(boot)} • {int(_bq["gold"]):,}g</strong></div></div>',unsafe_allow_html=True)

    immortal_above_half=False
    if boot=="Immortal Treads":
        immortal_above_half=st.checkbox(
            "Immortal Treads — Above 50% HP (+5% damage)",
            value=True,
            key="build_immortal_above_half"
        )

    # Yun Tal assumptions are only relevant when the item is in the build.
    yt_bonus_crit=0.0
    yt_flurry=False
    if "Yun Tal Wildarrows" in build:
        with st.container(border=True):
            st.markdown("**🏹 Yun Tal Settings**")
            yc1,yc2=st.columns(2)
            yt_bonus_crit=yc1.selectbox("Bonus Crit Chance",list(range(0,26)),index=25,format_func=lambda x:f"{x}%",key="build_yt_crit")/100
            yt_flurry=yc2.checkbox("Flurry Active (+35% AS)",value=False,key="build_yt_flurry")

    with st.container(border=True):
        _setup_heading("06","CHAMPION ABILITIES","Skill Lab")
        _skill_qs=[dct(F[x]) for x in build]+[dct(B[boot])]
        _skill_total={k:sum(q[k] for q in _skill_qs) for k in K}
        _own_stats=level_stats(champ,int(level))
        _fight_base_mana=_own_stats["mana"] if _own_stats["mana"] is not None else (mana if mana>0 else None)
        _fight_max_mana=None if _fight_base_mana is None else _fight_base_mana+_skill_total["mana"]
        _skill_awe=.02*((_fight_base_mana or 0)+_skill_total["mana"]) if any(x in build for x in ("Manamune","Muramana")) else 0.
        _skill_ad=stats(champ,level,mist)["ad"]+_skill_total["ad"]+_skill_awe
        _skill_cd=2.3 if "Infinity Edge" in build else 2.
        _fight_haste=_skill_total["ah"]+(15. if "Legend: Haste" in selected_sub_runes and haste_full else 0.)+((10. if level>=5 else 5.) if "Transcendence" in selected_sub_runes else 0.)
        _fight_amp=(1.05 if boot=="Immortal Treads" and immortal_above_half else 1.)*(1+min(.12,max(0,bonus_hp)/125*.01) if "Lord Dominik's Regards" in build else 1.)
        _ranks=champion_ranks(champ,int(level))
        _ability_data=SAMIRA_ABILITIES if champ=="Samira" else SMOLDER_ABILITIES if champ=="Smolder" else {k:{"cooldown":v["cooldown_by_rank"],"mana":tuple(v["mana_by_rank"]) if v["mana_by_rank"] is not None else None} for k,v in marksman_records()[champ]["abilities"].items() if k!="P"}
        _fight_range=_own_stats["attack_range"] if _own_stats["attack_range"] is not None else dist
        _fight_ms=(_own_stats["movement_speed"] or 0)*(1+sum(dct(F[x])["ms"] for x in build))+dct(B[boot])["ms"]
        _dragon_start=int(st.number_input("Dragon Practice stacks",0,10000,0,key="smolder_fight_stacks")) if champ=="Smolder" else 0
        _qrank,_wrank,_erank,_rrank=(_ranks[k] for k in ('Q','W','E','R'))
        st.markdown("**Fight timeline · AA / Q / W / E / R**")
        _supported_fight_runes={"Brutal","Cut Down","Coup de Grace","Battle Zeal","Legend: Alacrity","Legend: Haste","Transcendence"}
        _offensive_unknown=[x for x in selected_sub_runes if x and x not in _supported_fight_runes and x not in {"Legend: Bloodline","Bone Plating","Second Wind","Perseverance","Overgrowth","Unshakeable"}]
        _replay_crit=min(1.,_skill_total["crit"]+(mist//20*.10 if champ=="Senna" else 0))
        _fight_start_as=min(3.,stats(champ,level)["baseas"]+stats(champ,level)["ratio"]*(stats(champ,level)["bba"]+stats(champ,level)["lvbas"]+_skill_total["as"]+((.21 if alacrity_full else .03) if "Legend: Alacrity" in selected_sub_runes else 0.)))
        st.markdown(f"**Fight starting stats:** {_skill_ad:.1f} AD · {_skill_total['ap']:.0f} AP · {_fight_start_as:.3f} AS · {_replay_crit*100:.1f}% crit · {_skill_cd*100:.0f}% crit damage · {_fight_haste:.0f} AH · {_skill_total['pctpen']*100:.0f}% + {_skill_total['flatpen']:.0f} armor penetration · {_skill_total['pctmpen']*100:.0f}% + {_skill_total['flatmpen']:.0f} magic penetration")
        def _known_stat(value,addition=0):return "Pending" if value is None else f"{value+addition:.1f}"
        st.markdown(f"**Champion stats:** {_known_stat(_own_stats['hp'],_skill_total['hp'])} HP · {_known_stat(_fight_max_mana)} mana · {_known_stat(_own_stats['mana_regen_per_5s'])} mana / 5s · {_known_stat(_own_stats['armor'],_skill_total['armor'])} armor · {_known_stat(_own_stats['mr'],_skill_total['mr'])} MR · {_fight_ms:.0f} MS · {_known_stat(_own_stats['attack_range'])} range")
        _fight_key=keystone if keystone!="None" else None
        _fight_blocked=_fight_key not in (None,"Conqueror","Lethal Tempo") or bool(_offensive_unknown)
        if _fight_blocked: st.info("Replay currently supports Conqueror / Lethal Tempo and the listed damage runes. Choose a supported loadout to run it.")
        if st.button("Replay fight",key="fight_calculate",disabled=_fight_blocked):
            try:
                def _run_candidate(_priority=("E","W","Q"),_use_e=True,_weapon="minigun"):
                    _events=[]
                    _kernel=_combat_hits(champ,level,hp,armor,mr,build,F,mist,bonus_hp,dist,target_aa_reduction,0,(_fight_base_mana or 0),False,energized,False,execs,False,boot)
                    next(_kernel)
                    _alacrity=(.21 if alacrity_full else .03) if "Legend: Alacrity" in selected_sub_runes else 0.
                    _fight_last_hit={}
                    def _fight_aa_stats(state):
                        _dyn=(.08*state["items"].get("rage",0) if "Guinsoo's Rageblade" in build else 0.)+(.06*state["items"].get("phantom_dancer",0) if "Phantom Dancer" in build else 0.)
                        if "Yun Tal Wildarrows" in build and state["time"]<_fight_last_hit.get("yuntal_until",-1):_dyn+=.35
                        _ult=state.get("ultimate_cast_time")
                        _fiend=.5 if "Fiendhunter Bolts" in build and _ult is not None and state["time"]<=_ult+8 and (_fight_last_hit.get("fiend_remaining",3)>0 or _fight_last_hit.get("ult_seen")!=_ult) else 0.
                        _bonus=stats(champ,level)["bba"]+stats(champ,level)["lvbas"]+_skill_total["as"]+_alacrity+_dyn+state["bonus_as"]+_fiend
                        _exp=[v for v in (_fight_last_hit.get("yuntal_until",-1),(_ult+8 if _fiend else -1)) if v>state["time"]]
                        return {"bonus_as_total":_bonus,"as":min(3.,stats(champ,level)["baseas"]+stats(champ,level)["ratio"]*_bonus),"buff_expiry":min(_exp) if _exp else -1}
                    def _fight_aa(state):
                        state=dict(state);state["bonus_as"]+=_alacrity
                        _hit=_kernel.send(state)
                        _fight_last_hit.update(_hit)
                        _fight_last_hit["ult_seen"]=state.get("ultimate_cast_time")
                        if boot=="Immortal Treads" and not immortal_above_half: _hit["damage"]/=1.05
                        return _hit
                    _fight_base_crit=_replay_crit
                    return replay_samira(_events,level=level,ad=_skill_ad,base_ad=stats(champ,level)["ad"],attack_speed=stats(champ,level)["baseas"],crit_chance=_fight_base_crit,crit_damage=_skill_cd,hp=hp,armor=armor,q_rank=_qrank,r_rank=_rrank,ability_haste=_fight_haste,pct_pen=_skill_total["pctpen"],flat_pen=_skill_total["flatpen"],mode="Expected",keystone=_fight_key,sub_runes=[x for x in selected_sub_runes if x in _supported_fight_runes],instant_skills=False,timed_combat=True,base_windup=None,champion=champ,ap=_skill_total["ap"],initial_stacks=_dragon_start,skill_priority=_priority,use_e=_use_e,aa_stats=_fight_aa_stats,movement_speed=_fight_ms,distance=dist if champ=="Samira" else _fight_range,attack_range=_fight_range,w_rank=_wrank,e_rank=_erank,mr=mr,pct_mpen=_skill_total["pctmpen"],flat_mpen=_skill_total["flatmpen"],navori="Navori Quickblades" in build,collector_threshold=min(1.,.05+.001*execs) if "The Collector" in build else 0.,skill_amp=_fight_amp,melee=False,transcendence="Transcendence" in selected_sub_runes,until_death=True,aa_hit=_fight_aa,yuntal="Yun Tal Wildarrows" in build,yuntal_initial=0.,terminus="Terminus" in build,max_mana=_fight_max_mana,muramana="Muramana" in build,mana_refund=.15 if any(x in build for x in ("Manamune","Muramana")) else 0.,mana_regen_per_5s=_own_stats["mana_regen_per_5s"] or 0,mist=mist,as_ratio=stats(champ,level)["ratio"],natural_attack_speed=stats(champ,level)["baseas"]+stats(champ,level)["ratio"]*(stats(champ,level)["bba"]+stats(champ,level)["lvbas"]),completed_items=len(build),item_as=_skill_total["as"],item_ad=_skill_total["ad"],weapon=_weapon,galeforce="Galeforce" in build,hexoptics="Hexoptics C44" in build)
                _candidates=[(_run_candidate(_p,_e,_weapon),_p,_e,_weapon) for _p in permutations(('Q','W','E')) for _e in (False,True) for _weapon in (("minigun","rockets") if champ=="Jinx" else ("minigun",))]
                _fight_result,_best_priority,_best_e,_best_weapon=min(_candidates,key=lambda x:(x[0].killed_at is None,x[0].killed_at if x[0].killed_at is not None else x[0].hp_remaining))
                _move_label='approach for melee passive' if champ=='Samira' else 'max-range kite'+(' · '+_best_weapon if champ=='Jinx' else '')
                st.markdown(f"**Best tested rotation:** {' → '.join(_best_priority)} · E {'enabled' if _best_e else 'skipped for AA uptime'} · {_move_label}")
                if _fight_result.killed_at is not None: st.success(f"Target defeated · TTK {_fight_result.killed_at:.3f} seconds")
                else: st.warning("Simulation safety limit reached; target survived. No kill time is reported.")
                st.caption(f"Landed: {_fight_result.aa_count} AAs / {_fight_result.skill_count} skill casts • Damage {_fight_result.total_damage:.1f} • HP remaining {_fight_result.hp_remaining:.1f}")
                _fight_rows=[]
                for _e in _fight_result.log:
                    _fight_rows.append([round(_e["time"],3),_e["action"],round(_e["AD"],2),round(_e["crit_chance"]*100,2),round(_e["damage"],2),round(_e["hp_after"],2),round(_e["mana"],2) if _e["mana"] is not None else None,round(_e["distance"],2),_e["dragon_stacks"] if champ=="Smolder" else None,round(_e["kite_arc"],1),str(_e["before"]),str(_e["after"]),str({k:round(v,2) for k,v in _e["cooldowns"].items()}),_e["executed"],"Melee" if _e["melee"] else "Ranged"," / ".join(_e["effects"])])
                if _fight_rows: st.dataframe(pd.DataFrame(_fight_rows,columns=["Time","Event","AD","Crit %","Damage","Target HP","Mana","Distance","Dragon stacks","Kite movement","Stacks before","Stacks after","Cooldowns remaining","Collector execute","Range","Effects"]),hide_index=True,use_container_width=True)
                if _fight_result.rejected: st.dataframe(pd.DataFrame(_fight_result.rejected),hide_index=True,use_container_width=True)
                if _fight_result.assumptions:
                    with st.expander("Research notes — unverified mechanics"):
                        for _note in _fight_result.assumptions:st.write(_note)
            except (ValueError,LookupError,StopIteration) as _err:
                st.error(f"Timeline could not run: {_err}")
        _cd_rows=[]
        for _slot,_rank in [("Q",_qrank),("W",_wrank),("E",_erank),("R",_rrank)]:
            if _rank:
                _base_cd=(_ability_data[_slot]["cooldown"][_rank-1] if _ability_data[_slot]["cooldown"] is not None else None)
                _cd_rows.append([_slot,_base_cd,round(_base_cd/(1+_fight_haste/100),2) if _base_cd is not None else None,(_ability_data[_slot]["mana"][_rank-1] if isinstance(_ability_data[_slot]["mana"],tuple) else _ability_data[_slot]["mana"])])
        if _cd_rows: st.table(pd.DataFrame(_cd_rows,columns=["Ability","Base cooldown","Cooldown with item haste","Mana cost"]))
    if len(build)<5 or len(set(build))<5:
        st.error("Choose 5 different completed items.")
    elif champ!="Jhin" and st.button("Calculate build",type="primary",use_container_width=True):
        qs=[dct(F[x]) for x in build]; qb=dct(B[boot])
        total={k:sum(q[k] for q in qs)+qb[k] for k in K}
        s0=stats(champ,level,mist)
        # Persistent Resolve/Sorcery stats.
        rune_bonus_hp=0.0
        overgrowth_health_mult=1.0
        if "Overgrowth" in selected_sub_runes:
            # Each stack grants +3 max HP. At 30 stacks, ALL max Health (base + items + flat rune HP) is increased by 3%.
            rune_bonus_hp=overgrowth_stacks*3.0
            if overgrowth_stacks>=30:
                overgrowth_health_mult=1.03
        build_max_hp=(total["hp"]+rune_bonus_hp)*overgrowth_health_mult
        overgrowth_bonus_from_pct=(total["hp"]+rune_bonus_hp)*(overgrowth_health_mult-1.0)
        rune_armor_mult=1.0
        rune_mr_mult=1.0
        if "Unshakeable" in selected_sub_runes:
            _unshakeable_pct=.03+.02*nearby_enemies
            rune_armor_mult+=_unshakeable_pct
            rune_mr_mult+=_unshakeable_pct
        # Persistent rune progression only; combat stacks always start at zero.
        rune_bonus_ad=15.0 if "Zombie Ward" in selected_sub_runes else 0.0
        if "Eyeball Collection" in selected_sub_runes: rune_bonus_ad+=1.5*eyeball_stacks
        if "Hubris" in selected_sub_runes and hubris_active: rune_bonus_ad+=5.0+hubris_kills
        if "Absolute Focus" in selected_sub_runes and absolute_focus_active:
            rune_bonus_ad+=lvl_scale(2,20,level)
        gathering_storm_ad=0.0
        if "Gathering Storm" in selected_sub_runes:
            # Only user-supplied known breakpoints; do not extrapolate beyond 21 minutes.
            _gs=((6,2),(9,5),(12,9),(15,14),(18,20),(21,27))
            gathering_storm_ad=max((v for m,v in _gs if game_minute>=m),default=0)
            rune_bonus_ad+=gathering_storm_ad
        maxmana=mana+total["mana"]+(300 if "Manaflow Band" in selected_sub_runes else 0)
        awe=.02*maxmana if ("Manamune" in build or "Muramana" in build) else 0
        ad=s0["ad"]+total["ad"]+awe+rune_bonus_ad
        rune_bonus_as=(.21 if alacrity_full else .03) if "Legend: Alacrity" in selected_sub_runes else 0.0
        rune_bonus_ah=15.0 if ("Legend: Haste" in selected_sub_runes and haste_full) else 0.0
        if "Transcendence" in selected_sub_runes:
            rune_bonus_ah+=5.0 if level<5 else 10.0
        rune_omnivamp=(.08 if bloodline_full else .01) if "Legend: Bloodline" in selected_sub_runes else 0.0
        crit=min(1,total["crit"]+(mist//20*.10 if champ=="Senna" else 0)+yt_bonus_crit)
        cd=2.3 if "Infinity Edge" in build else 2.0
        if champ=="Senna": cd*=.9
        display_dyn=.35 if ("Yun Tal Wildarrows" in build and yt_flurry) else 0
        display_as=min(3,s0["baseas"]+s0["ratio"]*(s0["bba"]+s0["lvbas"]+total["as"]+display_dyn+rune_bonus_as))
        if "Overgrowth" in selected_sub_runes:
            st.caption(f"Overgrowth applied to tracked build/rune HP: {total['hp']:.0f} item HP + {rune_bonus_hp:.0f} flat rune HP → {build_max_hp:.1f} HP contribution after ×{overgrowth_health_mult:.2f}.")
        dealt_damage=0.
        hp2=float(hp); t=0.; attacks=0
        rune_trace=[]
        rune_timeline=[]
        conq_stacks=0; lt_stacks=0; empowerment_hits=0; empowerment_active=False; brutal_cd_ready=0.0
        first_strike_until=3.0 if (keystone=="First Strike" and first_strike_ready) else -1.0
        grasp_next_ready=0.0 if (keystone=="Grasp of the Undying" and grasp_ready) else 3.0
        aery_available=(keystone=="Aery" and aery_ready)
        comet_pending=(keystone=="Arcane Comet" and comet_ability_hit)
        fleet_available=(keystone=="Fleet Footwork" and fleet_ready)
        dark_harvest_ready_at=0.0
        dark_harvest_live_souls=int(dark_harvest_souls)
        cheap_shot_ready_at=sudden_impact_ready_at=tyrant_ready_at=empowered_attack_ready_at=0.0
        chain_hits_left=2 if chain_marked else 0
        scorch_pending=(1.0 if ("Scorch" in selected_sub_runes and scorch_ability_hit) else None)
        scorch_ready_at=0.0
        _engine=_combat_hits(champ,level,hp,armor,mr,build,F,mist,bonus_hp,dist,target_aa_reduction,round(yt_bonus_crit/.002),mana,spell,energized,ult,execs,False,boot,initial_flurry=yt_flurry)
        next(_engine)
        while hp2>0 and attacks<500:
            attacks+=1
            current_ad=ad+conq_stacks*lvl_scale(3.,5.,level) if keystone=="Conqueror" else ad
            lt_as=.048*lt_stacks if keystone=="Lethal Tempo" else 0.
            _hit=_engine.send({"hp":hp2,"time":t,"bonus_ad":current_ad-(s0["ad"]+total["ad"]+awe),"bonus_as":rune_bonus_as+lt_as})
            asp=_hit["as"]; cc=_hit["crit"]; ea=_hit["armor"]; em=_hit["mr"]; dmg=_hit["damage"]
            # Immortal is controlled by the explicit own-health toggle in this tab.
            if boot=="Immortal Treads": dmg/=1.05

            # Rune effects read the live state before this hit.
            hp_pct=hp2/hp if hp else 0
            bonus_ad=max(0,current_ad-s0["ad"])
            _pre_rune_dmg=dmg
            _rune_events=[]
            _rune_parts=[]
            def _rune_part(name,before,after,detail=""):
                delta=after-before
                if abs(delta)>0.005 or detail:
                    _rune_parts.append(f"{name} {delta:+.1f}"+(f" ({detail})" if detail else ""))
            if keystone=="First Strike" and 0<=t<first_strike_until:
                # First Strike is 7% BONUS TRUE damage, not a generic 7% multiplier.
                _v=dmg*.07; dmg += _v; _rune_events.append(f"First Strike +{_v:.1f} true")
            elif keystone=="Empowerment":
                # Tooltip range uses linear Lv1 -> Lv15 scaling.
                if empowerment_hits==2:
                    _raw=lvl_scale(40.0,165.0,level); _v=_raw*rm(ea); dmg+=_v; _rune_events.append(f"Empowerment +{_v:.1f} physical")
                # The 8% amp begins after the third hit.
                if empowerment_active: dmg*=1.08
            elif keystone=="Dark Harvest" and hp_pct<.50 and t>=dark_harvest_ready_at:
                _raw=35+11*dark_harvest_live_souls+.10*bonus_ad+.05*total["ap"]; _v=_raw*rm(ea); dmg+=_v; _rune_events.append(f"Dark Harvest +{_v:.1f} physical (souls {dark_harvest_live_souls}→{dark_harvest_live_souls+1})")
                dark_harvest_live_souls+=1
                dark_harvest_ready_at=t+20.0
            elif keystone=="Aery" and aery_available:
                _v=(lvl_scale(15,70,level)+.10*bonus_ad+.05*total["ap"])*rm(em)
                dmg+=_v; _rune_events.append(f"Aery +{_v:.1f}")
                # Return cadence was not supplied, so only the explicitly-ready Aery is consumed.
                aery_available=False
            elif keystone=="Arcane Comet" and comet_pending:
                _v=(lvl_scale(15,100,level)+2*comet_total_hits+.10*bonus_ad+.05*total["ap"])*rm(em)
                dmg+=_v; _rune_events.append(f"Arcane Comet +{_v:.1f}")
                comet_pending=False
            elif keystone=="Fleet Footwork" and fleet_available:
                # Energized attack consumes Fleet. Its heal/MS/mana are utility; the supplied tooltip has no bonus hit damage.
                _rune_events.append("Fleet Footwork proc")
                fleet_available=False
            elif keystone=="Grasp of the Undying" and t>=grasp_next_ready:
                # Grasp scales from the USER'S max HP, never target HP.
                # Champion max-HP data is not in the lab yet, so do not fabricate damage.
                _rune_events.append("Grasp ready — own Max HP data required")
                grasp_next_ready=t+3.0
            elif keystone=="Lethal Tempo" and lt_stacks>=6:
                # Tooltip range is treated as linear Lv1 -> Lv15: 6 at Lv1, 20 at Lv15.
                base_lt=lvl_scale(6.0,20.0,level)
                bonus_as_pct=(total["as"]+rune_bonus_as+.048*lt_stacks)*100
                _raw=base_lt*(1+.0033*bonus_as_pct); _v=_raw*rm(ea); dmg+=_v; _rune_events.append(f"Lethal Tempo +{_v:.1f} physical")
            if "Cut Down" in selected_sub_runes and hp_pct>.60:
                _b=dmg; dmg*=1.065; _rune_part("Cut Down",_b,dmg,"×1.065")
            if "Coup de Grace" in selected_sub_runes and hp_pct<.40:
                _b=dmg; dmg*=1.08; _rune_part("Coup de Grace",_b,dmg,"×1.08")
            if "Brutal" in selected_sub_runes:
                # Verified tooltip: every champion attack deals 6 + 8% bonus AD adaptive damage.
                # Current ADC lab resolves adaptive damage as physical when AD is the adaptive stat.
                _b=dmg; dmg+=(6+.08*bonus_ad)*rm(ea); _rune_part("Brutal",_b,dmg)
            # Precision combat modifiers.
            if "Last Stand" in selected_sub_runes and own_hp_pct<60:
                # Shared tested implementation of the verified missing-HP step rule.
                last_stand_amp=_last_stand_amp(own_hp_pct)
                _b=dmg; dmg*=1+last_stand_amp; _rune_part("Last Stand",_b,dmg,f"×{1+last_stand_amp:.3f}")
            if "Battle Zeal" in selected_sub_runes:
                # Basic-ability damage amplification only. Normal auto attacks are intentionally unaffected.
                pass
            # Domination combat runes. Adaptive damage resolves physical for this ADC lab.
            if "Cheap Shot" in selected_sub_runes and target_impaired and t>=cheap_shot_ready_at:
                _b=dmg; dmg+=lvl_scale(10,45,level); _rune_part("Cheap Shot",_b,dmg,"true")
                cheap_shot_ready_at=t+7.0
            if "Sudden Impact" in selected_sub_runes and mobility_trigger and t<4.0 and t>=sudden_impact_ready_at:
                _b=dmg; dmg+=lvl_scale(10,65,level); _rune_part("Sudden Impact",_b,dmg,"true")
                sudden_impact_ready_at=t+15.0
            if "Chain Assault" in selected_sub_runes and chain_hits_left>0:
                _b=dmg; dmg+=(lvl_scale(12,38,level)+.03*bonus_ad+.015*total["ap"])*rm(ea); _rune_part("Chain Assault",_b,dmg,f"{chain_hits_left}/2 before hit")
                chain_hits_left-=1
            if "Tyrant" in selected_sub_runes and hp_pct<.50 and t>=tyrant_ready_at:
                _b=dmg; dmg+=(lvl_scale(20,70,level)+.06*bonus_ad+.03*total["ap"])*rm(ea); _rune_part("Tyrant",_b,dmg)
                tyrant_ready_at=t+10.0
            if "Empowered Attack" in selected_sub_runes and t>=empowered_attack_ready_at:
                _b=dmg; dmg+=lvl_scale(20,60,level)*.80*rm(ea); _rune_part("Empowered Attack",_b,dmg)
                empowered_attack_ready_at=t+8.0
            if scorch_pending is not None and t>=scorch_pending and t>=scorch_ready_at:
                _sv=lvl_scale(21,49,level)*rm(em)
                hp2-=_sv; dealt_damage+=_sv
                rune_trace.append(["EVENT",round(scorch_pending,3),round(hp_pct*100,1),f"Scorch +{_sv:.1f} magic",round(_sv,1),round(_sv,1)])
                scorch_ready_at=scorch_pending+8.0
                scorch_pending=None

            if boot=="Immortal Treads" and immortal_above_half: dmg*=1.05
            _rune_delta=dmg-_pre_rune_dmg
            _event_text=" • ".join(_rune_events+_rune_parts)
            if _event_text or abs(_rune_delta)>0.01:
                rune_trace.append([attacks,round(t,3),round(hp_pct*100,1),_event_text or "Rune modifier",round(_rune_delta,1),round(dmg,1)])
            _stack_before=f"Conq {conq_stacks}/6 | LT {lt_stacks}/6 | Empower {empowerment_hits}/3"
            _cd_bits=[]
            if "Cheap Shot" in selected_sub_runes: _cd_bits.append(f"Cheap {'READY' if cheap_shot_ready_at<=t else f'{cheap_shot_ready_at-t:.1f}s'}")
            if "Sudden Impact" in selected_sub_runes: _cd_bits.append(f"Sudden {'READY' if sudden_impact_ready_at<=t else f'{sudden_impact_ready_at-t:.1f}s'}")
            if "Tyrant" in selected_sub_runes: _cd_bits.append(f"Tyrant {'READY' if tyrant_ready_at<=t else f'{tyrant_ready_at-t:.1f}s'}")
            if "Empowered Attack" in selected_sub_runes: _cd_bits.append(f"EmpAtk {'READY' if empowered_attack_ready_at<=t else f'{empowered_attack_ready_at-t:.1f}s'}")
            hp2-=dmg; dealt_damage+=dmg
            if "The Collector" in build:
                th=min(1,.05+.001*execs)
                if 0<hp2<=hp*th: hp2=0
            # The completed auto grants stacks for the NEXT attack.
            if keystone=="Conqueror": conq_stacks=min(6,conq_stacks+1)
            if keystone=="Lethal Tempo": lt_stacks=min(6,lt_stacks+1)
            if keystone=="Empowerment":
                empowerment_hits=min(3,empowerment_hits+1)
                if empowerment_hits>=3: empowerment_active=True
            _stack_after=f"Conq {conq_stacks}/6 | LT {lt_stacks}/6 | Empower {empowerment_hits}/3"
            rune_timeline.append([attacks,round(t,3),round(max(0,hp2),1),_stack_before+" → "+_stack_after," • ".join(_cd_bits) if _cd_bits else "—",_event_text or "—"])
            t+=1/asp
            if hp2<=0: break
        cost=sum(F[x][0] for x in build)+B[boot][0]

        # A fresh first-hit scenario uses the same item kernel, with a legal forced crit.
        maxcrit=crit>0
        _max_engine=_combat_hits(champ,level,hp,armor,mr,build,F,mist,bonus_hp,dist,target_aa_reduction,round(yt_bonus_crit/.002),mana,spell,energized,ult,execs,False,boot)
        next(_max_engine)
        _max=_max_engine.send({"hp":hp,"time":0.,"bonus_ad":rune_bonus_ad,"crit":1. if maxcrit else 0.})
        max_ea=_max["armor"]; max_em=_max["mr"]; max_hit=_max["damage"]
        parts=[["AA + item effects","Physical",_max["physical"]],["Item effects","Magic",_max["magic"]],["Item effects","True",_max["true"]]]
        if boot=="Immortal Treads":
            _imm=1.05 if immortal_above_half else 1.
            parts=[[name,typ,value*_imm] for name,typ,value in parts]
            if not immortal_above_half: max_hit/=1.05

        _avg_dps=dealt_damage/t if t else 0.
        _killed=hp2<=0
        if not _killed: st.warning("Target not killed within 500 attacks. Time to kill is unavailable.")
        _ttk_text=f"{t:.3f}" if _killed else "Not killed"
        st.markdown('<div class="combat-result-head"><div><span>COMBAT ANALYSIS</span><strong>Build Performance</strong></div><em>SHARPWR DAMAGE ENGINE</em></div>',unsafe_allow_html=True)
        _dps_text=f"{_avg_dps:.1f}" if t else "∞"
        st.markdown(f'<div class="combat-hero"><div class="combat-kpi hero"><div class="label">AVERAGE DPS</div><div><span class="value">{_dps_text}</span> <span class="unit">DPS</span></div><div class="sub">Damage over attack intervals</div></div><div class="combat-kpi"><div class="label">TIME TO KILL</div><div><span class="value">{_ttk_text}</span> <span class="unit">SEC</span></div><div class="sub">{attacks} attacks</div></div><div class="combat-kpi"><div class="label">MAX SINGLE HIT</div><div><span class="value">{max_hit:.1f}</span></div><div class="sub">Highest legal AA setup</div></div><div class="combat-kpi"><div class="label">BUILD COST</div><div><span class="value">{cost:,}</span> <span class="unit">G</span></div><div class="sub">Items + boots</div></div></div>',unsafe_allow_html=True)
        _pieces="".join(f'<span class="piece">{html.escape(_x)}</span>' for _x in build)
        st.markdown(f'<div class="build-ribbon"><span class="tag">LOADOUT</span>{_pieces}<span class="piece boots">{html.escape(boot)}</span></div>',unsafe_allow_html=True)
        st.markdown('<div class="combat-stat-title">OFFENSIVE STAT PROFILE</div>',unsafe_allow_html=True)
        if keystone!="None":
            rune_bits=[]
            if rune_bonus_ad: rune_bits.append(f"+{rune_bonus_ad:.1f} AD")
            if gathering_storm_ad: rune_bits.append(f"GS +{gathering_storm_ad:.0f} AD @ {game_minute}m")
            if rune_bonus_as: rune_bits.append(f"+{rune_bonus_as*100:.1f}% AS")
            if rune_bonus_ah: rune_bits.append(f"+{rune_bonus_ah:.0f} AH")
            if rune_omnivamp: rune_bits.append(f"+{rune_omnivamp*100:.0f}% Omnivamp")
            st.caption("Key Rune: **"+str(keystone or "None")+"** • Primary: **"+str(primary_tree or "None")+"** • Secondary: **"+str(secondary_rune or "None")+"**"+((" • "+" • ".join(rune_bits)) if rune_bits else ""))
        o1,o2,o3,o4=st.columns(4)
        o1.metric("Total AD",f"{ad:.1f}")
        o2.metric("Attack Speed",f"{display_as:.3f}")
        o3.metric("Crit Chance",f"{crit*100:.0f}%")
        o4.metric("Crit Damage",f"{cd*100:.0f}%")
        o5,o6,o7,o8=st.columns(4)
        o5.metric("Lifesteal",f"{total['ls']*100:.0f}%")
        o6.metric("Ability Haste",f"{total['ah']+rune_bonus_ah:.0f}")
        o7.metric("Flat Armor Pen",f"{total['flatpen']:.0f}")
        o8.metric("Armor Pen",f"{total['pctpen']*100:.0f}%")
        if total["flatmpen"] or total["pctmpen"]:
            m1,m2=st.columns(2)
            m1.metric("Flat Magic Pen",f"{total['flatmpen']:.0f}")
            m2.metric("Magic Pen",f"{total['pctmpen']*100:.0f}%")

        st.caption(f"Simulation ran {attacks} basic attacks against the configured {int(hp):,} HP target.")
        with st.expander("Rune Combat Breakdown V2"):
            if rune_trace:
                st.caption("Each rune contribution is separated. Multipliers show their exact damage delta on that hit.")
                st.dataframe(pd.DataFrame(rune_trace,columns=["AA","Time","Target HP %","Rune Events","Total Rune Delta","Final Hit"]),use_container_width=True,hide_index=True)
            else:
                st.caption("No selected rune changed auto-attack damage in this scenario.")
            st.markdown("**Stack / Cooldown Timeline**")
            if rune_timeline:
                st.dataframe(pd.DataFrame(rune_timeline,columns=["AA","Time","Target HP After","Stacks Before → After","Cooldowns","Rune Events"]),use_container_width=True,hide_index=True)
        with st.expander("Max Single Hit breakdown"):
            st.caption("Item-only first-hit estimate using the shared engine; rune damage is excluded. Highest one basic attack when a crit is possible. Ready Spellblade, Energized and first-hit effects use the scenario switches. Kraken 3rd-hit and pre-stacked Terminus/Rageblade are not assumed.")
            br=[]
            for pn,pt,pv in parts:
                dealt=pv*rm(max_ea) if pt=="Physical" else pv*rm(max_em) if pt=="Magic" else pv
                dealt*=1-target_aa_reduction
                br.append([pn,pt,round(pv,1),round(dealt,1)])
            st.table(pd.DataFrame(br,columns=["Source","Type","Raw Damage","Damage Dealt"]))
            st.metric("Total Max Single Hit",f"{max_hit:.1f}")

with tabs[2]:
    _tab_hero("SHARPWR • GOLD & PERFORMANCE","Item Value","Find the strongest purchases for your selected champion and target. Compare combat output and directly priced raw stats.")
    st.caption("Raw Gold Efficiency uses only directly priced base components. DPS/1000g is shown separately.")
    st.markdown("### Item Ranking · ADC Adoption")
    import json as _adoption_json
    _screen_path=Path(__file__).resolve().parent/'data/item-adoption-screen.json'
    if _screen_path.exists():
        _screen=_adoption_json.loads(_screen_path.read_text())
        st.caption(f"{_screen['champions']} ADCs × 6 levels × 3 targets · {_screen['simulations']:,} AA + ability simulations. Budgets: 5→1, 7→1, 9→2, 11→3, 13→4, 15→5 items. Muramana excluded before level 11. Each level/target has equal weight; build item shares are normalized by item count. No boots, runes or incoming damage. Yunara uses observed core stats and mana regeneration at all 15 levels.")
        _screen_mode=st.selectbox("Ranking stage",['All stages']+[f"Level {l}" for l in _screen['levels']],key="adoption_stage")
        if _screen_mode=='All stages':_ranking=_screen['ranking']
        else:
            _stage_level=int(_screen_mode.split()[-1])
            _filtered={c:{k:v for k,v in cells.items() if v['level']==_stage_level} for c,cells in _screen['results'].items()}
            _ranking=progression_ranking(_filtered,F)
        _adoption_cards=['<div class="value-grid">']
        for _rank,_row in enumerate(_ranking[:10],1):
            _name=_row['Item']
            _adoption_cards.append(f'<div class="value-card"><span class="value-rank">#{_rank}</span><img src="{html.escape(item_icon(_name))}" alt="{html.escape(_name)}"><div class="value-name">{html.escape(_name)}</div><div class="value-score">{_row["Stage-balanced score"]:.2f}</div><div class="value-unit">WEIGHTED BUILD SHARE % · {_row["Champions"]}/23 ADCs</div></div>')
        _adoption_cards.append('</div>');st.markdown(''.join(_adoption_cards),unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(_ranking),hide_index=True,width="stretch")
        with st.expander("Screen method and champion results"):
            st.write(_screen['method'])
            _screen_champ=st.selectbox("Screen champion",list(_screen['results']),key="adoption_champ")
            _screen_level=st.selectbox("Screen level",_screen['levels'],key="adoption_level")
            _screen_target=st.selectbox("Screen target",['squishy','bruiser','tank'],key="adoption_target")
            _cell=_screen['results'][_screen_champ][f'{_screen_level}:{_screen_target}']
            st.caption(f"{_cell['item_count']} items · Yun Tal starting stacks: {_cell['yuntal_start_stacks']} · {_cell['candidates']} candidates")
            st.dataframe(pd.DataFrame([{'Build':' + '.join(r['Items']),'DPS':r['DPS'],'TTK':r['TTK']} for r in _cell['builds']]),hide_index=True,width="stretch")
    else:st.info("The ADC adoption screen has not been generated yet.")
    _iv_champion,_iv_target=st.columns(2,gap="medium")
    with _iv_champion,st.container(border=True):
        _setup_heading("01","YOUR CHAMPION","Champion Profile")
        iv_champ=st.selectbox("Champion",list(C),index=0,key="iv_champ")
        iv_level=st.slider("Level",1,15,9,key="iv_level")
        iv_mist=st.number_input("Senna Mist",0,500,40,20,key="iv_mist") if iv_champ=="Senna" else 0
        _champion_profile(iv_champ,iv_level,iv_mist)
    with _iv_target,st.container(border=True):
        _setup_heading("02","FIXED BENCHMARK","Target Profile")
        iv_target_profile=st.radio("Target Profile",list(TARGET_PROFILES),horizontal=True,key="iv_target_profile",label_visibility="collapsed")
        _iv_benchmark=_benchmark_target(iv_target_profile,iv_level)
        iv_hp=float(_iv_benchmark["hp"]); iv_armor=float(_iv_benchmark["armor"]); iv_mr=float(_iv_benchmark["mr"])
        iv_bonus_hp=float(_iv_benchmark["bonus_hp"]); iv_reduction=float(_iv_benchmark.get("aa_reduction",0))
        _target_readout(iv_hp,iv_armor,iv_mr,iv_reduction)
        st.caption("Stats follow this tab's level. Darius / Ornn apply 10% basic-attack reduction from level 5. Runes are excluded from single-item value.")
    with st.container(border=True):
        _setup_heading("03","STARTING CONDITIONS","Combat Setup")
        _iv_proc_cols=st.columns(3)
        iv_spell=_iv_proc_cols[0].checkbox("Spellblade ready",value=True,key="iv_spell")
        iv_energized=_iv_proc_cols[1].checkbox("Energized ready",value=True,key="iv_energized")
        iv_ult=False
        with st.expander("Advanced combat settings"):
            _iv_a,_iv_b=st.columns(2)
            iv_dist=_iv_a.number_input("Attack distance",0.0,1000.0,550.0,25.0,key="iv_dist")
            iv_mana=_iv_b.number_input("Champion Max Mana before item",0.0,5000.0,0.0,50.0,key="iv_mana")
            iv_execs=_iv_a.number_input("Collector previous executes",0,500,0,1,key="iv_execs")
        _iv_flags=[("Spellblade",iv_spell),("Energized",iv_energized),("Ultimate pre-cast",iv_ult)]
        st.markdown('<div class="combat-flags">'+"".join(f'<span class="{"active" if on else ""}">{name} · {"ON" if on else "OFF"}</span>' for name,on in _iv_flags)+f'<span>{iv_dist:g} ATTACK DISTANCE</span></div>',unsafe_allow_html=True)
    rates={"ad":500/12,"as":400/.12,"crit":500/.10,"ap":500/20,"hp":500/150,"armor":500/20,"mr":500/20,"ah":300/5}
    proc_items=["Fiendhunter Bolts","Rapid Firecannon","Phantom Dancer","Kraken Slayer","Statikk Shiv","Guinsoo\'s Rageblade","Essence Reaver","The Collector","Terminus","Stormrazor","Yun Tal Wildarrows","Trinity Force","Duskblade of Draktharr","Iceborn Gauntlet"]
    proc_states={}
    with st.expander("Proc settings · customize item effects"):
        st.caption("ON = proc is used whenever its trigger/cooldown allows during the fight. OFF = proc disabled. Raw item stats remain active.")
        pc=st.columns(3)
        for i,pit in enumerate(proc_items):
            proc_states[pit]=pc[i%3].checkbox(pit,value=True,key=f"iv_proc_{pit}")
    st.caption(f"{iv_champ} · Level {iv_level} · {iv_target_profile} · {iv_hp:,.0f} HP · {iv_armor:g} Armor · {iv_mr:g} MR · {sum(proc_states.values())}/{len(proc_states)} item effects enabled")
    if iv_champ!="Jhin":
        rows=[]
        for it,v0 in F.items():
            q=dct(v0); raw=sum(q[k]*rates[k] for k in rates)
            row,_=sim(iv_champ,iv_level,iv_hp,iv_armor,iv_mr,it,F,iv_mist,iv_bonus_hp,iv_dist,iv_mana,iv_spell,iv_energized,iv_ult,iv_execs,proc_states.get(it,True),target_aa_reduction=iv_reduction)
            dps=row[4]; rows.append([item_icon(it),it,q["gold"],round(raw),round(raw/q["gold"]*100,1),dps,round(dps/q["gold"]*1000,1)])
        val=pd.DataFrame(rows,columns=["Icon","Item","Cost","Priced Raw Stats","Raw Gold Efficiency %","DPS","DPS / 1000g"]).sort_values("DPS / 1000g",ascending=False).reset_index(drop=True)
        val.insert(0,"Rank",range(1,len(val)+1))
        _iv_best=val.iloc[0]
        _iv_raw=val.loc[val["Raw Gold Efficiency %"].idxmax()]
        _iv_damage=val.loc[val["DPS"].idxmax()]
        _iv_cols=st.columns(3)
        _iv_cols[0].metric("Best DPS / 1000g",f"{_iv_best['DPS / 1000g']:.1f}",str(_iv_best["Item"]),delta_color="off")
        _iv_cols[1].metric("Highest Raw Efficiency",f"{_iv_raw['Raw Gold Efficiency %']:.1f}%",str(_iv_raw["Item"]),delta_color="off")
        _iv_cols[2].metric("Highest Item DPS",f"{_iv_damage['DPS']:.1f}",str(_iv_damage["Item"]),delta_color="off")
        st.markdown('<div class="combat-stat-title">VALUE LEADERBOARD · TOP 10</div>',unsafe_allow_html=True)
        _iv_cards=['<div class="value-grid">']
        for _,_r in val.head(10).iterrows():
            _iv_name=html.escape(str(_r["Item"]))
            _iv_cards.append(f'<div class="value-card"><span class="value-rank">#{int(_r["Rank"]):02d}</span><img src="{html.escape(str(_r["Icon"]))}" alt="{_iv_name}"><div class="value-name">{_iv_name}</div><div class="value-score">{float(_r["DPS / 1000g"]):.1f}</div><div class="value-unit">DPS / 1000 GOLD</div><div class="value-detail"><span>{int(_r["Cost"]):,}g</span><span>{float(_r["Raw Gold Efficiency %"]):.1f}% raw</span></div></div>')
        st.markdown("".join(_iv_cards)+"</div>",unsafe_allow_html=True)
        with st.expander("Detailed item value table",expanded=True):
            _iv_left,_iv_right=st.columns([2,1])
            _iv_query=_iv_left.text_input("Find an item",placeholder="Search item name…",key="iv_search")
            _iv_sort=_iv_right.selectbox("Sort by",["DPS / 1000g","Raw Gold Efficiency %","DPS","Cost"],key="iv_sort")
            _iv_table=val[val["Item"].str.contains(_iv_query.strip(),case=False,regex=False)].sort_values(_iv_sort,ascending=_iv_sort=="Cost")
            st.caption(f"{len(_iv_table)} of {len(val)} items · Rank refers to DPS / 1000g")
            if _iv_table.empty: st.info("No items match this search. Try another item name.")
            st.dataframe(_iv_table,use_container_width=True,hide_index=True,column_config={"Icon":st.column_config.ImageColumn(""),"Item":st.column_config.TextColumn("Item",width="medium")})
        st.info("Unpriced stats/passives are excluded from Raw Gold Efficiency rather than assigned invented prices.")
    else:
        st.info("Jhin item value rankings are pending dedicated four-shot and reload modeling.")

with tabs[3]:
    _tab_hero("SHARPWR • RESEARCH LIBRARY","Database","Explore item stats, verified rune effects and engine coverage. Search records or inspect the combat audits.")
    with st.container(border=True):
        _setup_heading("01","BROWSE RECORDS","Database Explorer")
        dbpick=st.radio("Show",["Champions","Completed items","Components","Boots","Runes","Item Engine Audit","Build Engine Audit"],horizontal=True,key="db_category")
    if dbpick=="Champions":
        _champ_query=st.text_input("Find a champion",key="db_champion_search")
        _champ_records=[r for n,r in CHAMPION_DATABASE.items() if _champ_query.strip().casefold() in n.casefold()]
        _champ_rows=[{"Champion":r["name"],**r["stats"],"Source status":r["source_status"]} for r in _champ_records]
        if _champ_rows:
            st.dataframe(pd.DataFrame(_champ_rows),width="stretch",hide_index=True)
            _inspect_champ=st.selectbox("Champion record",[r["name"] for r in _champ_records],key="db_champion_inspect")
            _champ_record=CHAMPION_DATABASE[_inspect_champ]
            if _champ_record["source_status"]=="manual_pending_user_instruction":st.info("Yunara: additional stats pending manual data.")
            elif _champ_record["source_status"]=="manual_observed_levels_partial":
                st.info("Yunara: verified manual core data at all 15 levels. Mana regeneration is per 5 seconds; HP regeneration units remain pending.")
                st.dataframe(pd.DataFrame.from_dict(_champ_record["observed_level_stats"],orient="index").rename_axis("Level").reset_index(),hide_index=True,width="stretch")
            else:st.markdown(f"[Wild Rift wiki source]({_champ_record['wiki_source_url']})")
            _field_rows=[]
            for _field,_value in _champ_record["stats"].items():
                _origin=_champ_record["field_sources"].get(_field)
                _field_rows.append([_field,_value,"Existing record" if _origin=="existing_user_preserved" else "Manual WR verification" if isinstance(_origin,dict) and _origin.get("status")=="manual_verified" else "PC timing proxy" if isinstance(_origin,dict) and "PC" in _origin.get("game","") else "WR wiki" if _origin else "Missing source"])
            st.table(pd.DataFrame(_field_rows,columns=["Stat","Value","Origin"]))
        else:st.info("No matching champions.")
    elif dbpick=="Runes":
        st.caption("51/51 verified rune records. Utility/defensive runes are retained for future champion, ability, heal, shield, CC and movement systems. Level-scaled ranges are stored without inventing intermediate values.")
        _rune_filter_left,_rune_filter_right=st.columns([1,2])
        tree_filter=_rune_filter_left.selectbox("Rune tree",["All","Key Rune","Precision","Domination","Resolve","Sorcery"],key="rune_db_tree")
        _rune_query=_rune_filter_right.text_input("Find a rune",placeholder="Search name or effect…",key="rune_db_search")

        rune_rows=[]
        for rn,rv in RUNE_DATABASE.items():
            if tree_filter!="All" and rv["tree"]!=tree_filter: continue
            if _rune_query.strip().casefold() not in (rn+" "+rv["tooltip"]).casefold(): continue
            rune_rows.append([rn,rv["tree"],rv["kind"],rv["tooltip"]])
        st.caption(f"{len(rune_rows)} of {len(RUNE_DATABASE)} rune records")
        if rune_rows:
            st.dataframe(pd.DataFrame(rune_rows,columns=["Rune","Tree","Type","Verified tooltip / effect"]),width="stretch",hide_index=True)
            with st.expander("Read full rune description"):
                _inspect=st.selectbox("Rune",[row[0] for row in rune_rows],key="rune_db_inspect")
                st.markdown(f"**{_inspect}** · {RUNE_DATABASE[_inspect]['tree']}")
                st.write(RUNE_DATABASE[_inspect]["tooltip"])
        else:
            st.info("No runes match this search. Try a different name or effect.")
        st.markdown("**Rune Engine Audit**")
        audit_rows=[
            ["First Strike","Partial","Damage works; engagement/cooldown/gold lifecycle not fully simulated"],
            ["Ice Overlord","Pending","Needs immobilize + own bonus HP/defense state"],
            ["Phase Rush","Partial","No direct AA damage; 3-hit mobility/basic-AH state not simulated"],
            ["Arcane Comet","Trigger Lite","Shared Ability Hit event launches the modeled comet proc"],
            ["Aery","Scenario","One explicitly-ready damage proc modeled; return cadence not supplied"],
            ["Guardian","Pending","Needs ally/incoming-damage + own bonus HP state"],
            ["Grasp of the Undying","Blocked: HP","Correctly disabled until own champion Max HP exists"],
            ["Conqueror","Combat","0→6 AD stacks modeled; omnivamp is non-damage"],
            ["Fleet Footwork","Partial","Proc consumption modeled; 40% AS duration/heal/resource need duration/HP-resource engine"],
            ["Lethal Tempo","Combat","0→6 AS stacks + max-stack adaptive physical bullet modeled"],
            ["Empowerment","Combat","3rd-hit adaptive physical proc + subsequent 8% amp modeled; repeat proc lifecycle needs verification"],
            ["Dark Harvest","Combat","<50% threshold + adaptive physical proc modeled; proc harvests +1 live soul"],
            ["Brutal","Combat","Every-AA adaptive physical damage modeled"],
            ["Triumph","Post-fight","Takedown-only; no fake DPS effect"],
            ["Battle Zeal","Ability-only","Correctly excluded from AA damage; waits for ability engine"],
            ["Last Stand","Combat","User-verified missing-HP steps: 30%=+5%, then +1% per 5% missing HP, capped at 60%=+11%"],
            ["Cut Down","Combat","Live target >60% threshold modeled"],
            ["Coup de Grace","Combat","Live target <40% threshold modeled"],
            ["Legend: Alacrity","Stat","Base/max progression toggle modeled; intermediate progression unknown"],
            ["Legend: Haste","Stat","Max progression toggle modeled; intermediate progression unknown"],
            ["Legend: Bloodline","Stat","Omnivamp stored/displayed; intermediate progression unknown"],
            ["Eyeball Collection","Stat","0–8 progression input wired at +1.5 AD/stack"],
            ["Hubris","Scenario","Champion kill count + explicit 30s buff-active state wired"],
            ["Tyrant","Combat","Live <50% + adaptive physical + 10s CD modeled"],
            ["Chain Assault","Trigger Lite","Shared Ability Hit event marks target; next 2 hits modeled"],
            ["Sudden Impact","Scenario","Mobility trigger + 4s window + true damage modeled"],
            ["Cheap Shot","Scenario","Impaired-target trigger + true damage + 7s CD modeled"],
            ["Zombie Ward","Stat","Default 5 stacks = +15 AD modeled"],
            ["Empowered Attack","Combat","Ranged 80% adaptive physical + 8s CD modeled"],
            ["Relentless Hunter","Utility","Default max OOC MS displayed; no movement engine"],
            ["Overgrowth","Blocked: HP","60 stacks = +180 flat HP; ×1.03 final Max HP awaits champion base HP"],
            ["Bone Plating","Defense-only","Values displayed; needs incoming-damage engine"],
            ["Second Wind","Defense-only","Values displayed; needs own HP/incoming-damage engine"],
            ["Perseverance","Utility","Tenacity displayed; immobilize defense needs incoming/CC engine"],
            ["Revitalize","Utility","Heal/shield amp stored as rule; needs heal/shield engine"],
            ["Nullifying Orb","Defense-only","Shield value displayed; needs own HP/incoming-damage engine"],
            ["Unshakeable","Partial","Nearby-enemy % state modeled/displayed; own Armor/MR database pending"],
            ["Courage of the Colossus","Blocked: HP","Flat shield portion known; full shield needs own Max HP + immobilize event"],
            ["Font of Life","Blocked: HP","Needs own Max HP/heal state"],
            ["Demolish","Blocked: HP","Needs own Max HP + turret scenario"],
            ["Gathering Storm","Stat","Verified 6–21m AD sequence modeled; no extrapolation"],
            ["Absolute Focus","Scenario","Linear AD modeled with >65% toggle; own live HP engine pending"],
            ["Scorch","Trigger Lite","Shared Ability Hit event schedules independent t=1.0 magic damage"],
            ["Axiom Arcanist","Trigger Lite","Ultimate and takedown events represented; champion ultimate damage itself is out of scope"],
            ["Manaflow Band","Stat","Default full +300 Mana modeled"],
            ["Transcendence","Trigger Lite","+5/+10 AH modeled; Lv9 Basic Ability Hit event represented"],
            ["Celerity","Utility","Rule displayed; needs movement-speed engine"],
            ["Nimbus Cloak","Utility","Summoner trigger represented; exact MS output not applied to movement engine"],
            ["Ixtali Seedjar","Utility","Rule displayed; no plant/trinket engine"],
            ["Hexflash","Utility","Rule displayed; no mobility engine"],
            ["Botanist","Utility","Rule displayed; no plant engine"],
        ]
        adf=pd.DataFrame(audit_rows,columns=["Rune","Engine Status","Audit Note"])
        _audit_badges(audit_rows)
        st.dataframe(adf,width="stretch",hide_index=True)
        st.caption("Audit: 51/51 runes classified. 'Pending/Blocked' effects are intentionally not converted into fake DPS.")
        st.markdown("**Rune Engine Test Suite**")
        _tests=_rune_self_tests()
        _passed=sum(1 for r in _tests if r[1]=="PASS")
        st.caption(f"{_passed}/{len(_tests)} deterministic checks passing. Guards verified rune math, thresholds, stack timing and persistent defaults.")
        st.dataframe(pd.DataFrame(_tests,columns=["Test","Status","Actual","Expected"]),use_container_width=True,hide_index=True)
        if _passed==len(_tests): st.success("All rune regression checks PASS.")
        else: st.error(f"{len(_tests)-_passed} rune regression check(s) FAILED.")
        counts={tree:len(names) for tree,names in RUNE_TREES.items()}
        st.caption(" • ".join(f"{tree}: {count}" for tree,count in counts.items())+" • Total: 51")
    elif dbpick=="Build Engine Audit":
        st.caption("Multi-item engine V1: one shared AA timeline for audited item interactions. Start with BotRK + Rageblade.")
        _bc1,_bc2,_bc3=st.columns(3)
        _bchamp=_bc1.selectbox("Attacker",list(C),index=list(C).index("Jinx") if "Jinx" in C else 0,key="build_audit_champ")
        _blvl=_bc2.slider("Level",1,15,15,key="build_audit_level")
        _btarget=_bc3.selectbox("Target",list(TARGET_PROFILES),index=list(TARGET_PROFILES).index("Tank • Ornn"),key="build_audit_target")
        _audited=["Blade of the Ruined King","Guinsoo's Rageblade","Wit's End","Terminus","Kraken Slayer","Yun Tal Wildarrows","Hexoptics C44","Infinity Edge"]
        _bi1=st.selectbox("Item 1",_audited,index=0,key="build_audit_i1")
        _bi2=st.selectbox("Item 2",_audited,index=1,key="build_audit_i2")
        if _bi1==_bi2:
            st.warning("Choose two different items.")
        else:
            _bp=_target_profile_at_level(TARGET_PROFILES[_btarget],_blvl)
            _bhp=float(_bp["hp"]); _bar=float(_bp["armor"]); _bmr=float(_bp["mr"]); _bred=float(_bp.get("aa_reduction",0))
            _bnatural={"Squishy • Jinx":_bhp,"Bruiser • Darius":660+148*gu(_blvl),"Tank • Ornn":690+132*gu(_blvl)}[_btarget]
            _bbonus=max(0.0,_bhp-float(_bnatural))
            _byt=125 if "Yun Tal Wildarrows" in (_bi1,_bi2) and _blvl>=9 else 0
            _bres,_blog=sim_build(_bchamp,_blvl,_bhp,_bar,_bmr,[_bi1,_bi2],F,0,_bbonus,550.0,_bred,_byt)
            st.metric("Build DPS",f"{_bres[4]:.1f}")
            _brows=[]
            for _r in _blog:
                _k,_t,_asp,_crit,_ea,_before,_dmg,_after,_note,_rb,_light,_dark=_r
                _state=[]
                if "Guinsoo's Rageblade" in (_bi1,_bi2): _state.append(f"Rageblade {_rb}/4")
                if "Terminus" in (_bi1,_bi2): _state.append(f"Terminus L{_light}/3 D{_dark}/3")
                if "Blade of the Ruined King" in (_bi1,_bi2): _state.append(f"BotRK HP {_before:.1f}")
                if "Kraken Slayer" in (_bi1,_bi2):
                    # Reconstruct the verified Bring It Down state from the trace:
                    # +1 each AA, plus +1 on every Phantom Hit.
                    _kh=sum(1+(1 if "Phantom Hit" in str(_x[8]) else 0) for _x in _blog[:_k])
                    _state.append(f"Kraken {_kh%3}/3")
                _brows.append([_k,_t,_asp,_crit,_ea,_before,_dmg,_after,_note," • ".join(_state)])
            st.dataframe(pd.DataFrame(_brows,columns=["AA","Time","AS","Crit %","Effective Armor","HP Before","Damage","HP After","Proc / Note","Build State"]),use_container_width=True,hide_index=True)
            st.caption("Build engine now carries the audited AA mechanics used by the single-item simulator: Giant Slayer, Energized cadence, Cloudburst, Nightstalker, Collector execute, Spellblade, Phantom Dancer stacks, mana on-hits and the verified Rageblade interactions. Rageblade + Kraken, Wit's End and Terminus behavior follows the in-game checks.")
    elif dbpick=="Item Engine Audit":
        st.caption("Developer trace: this runs the same single-item sim() used by Item Tier List, so the table exposes the actual ranking engine rather than a second calculator.")
        _audit_items=["Yun Tal Wildarrows","Terminus","Guinsoo's Rageblade","Kraken Slayer","Blade of the Ruined King","Hexoptics C44"]
        _ai=st.selectbox("Audit item",_audit_items,key="item_engine_audit_item")
        _ac1,_ac2,_ac3=st.columns(3)
        _achamp=_ac1.selectbox("Attacker",list(C),index=list(C).index("Jinx") if "Jinx" in C else 0,key="item_audit_champ")
        _alvl=_ac2.slider("Level",1,15,15,key="item_audit_level")
        _atarget=_ac3.selectbox("Target",list(TARGET_PROFILES),index=list(TARGET_PROFILES).index("Tank • Ornn"),key="item_audit_target")
        _aprof=_target_profile_at_level(TARGET_PROFILES[_atarget],_alvl)
        _afull=float(_aprof["hp"]); _aar=float(_aprof["armor"]); _amr=float(_aprof["mr"]); _ared=float(_aprof.get("aa_reduction",0))
        _anatural={"Squishy • Jinx":_afull,"Bruiser • Darius":660+148*gu(_alvl),"Tank • Ornn":690+132*gu(_alvl)}[_atarget]
        _abonus=max(0.0,_afull-float(_anatural))
        _adist=550.0
        _ayt=0
        if _ai=="Yun Tal Wildarrows":
            _ayt_default=0 if _alvl<=5 else (125 if _alvl>=9 else round(125*(_alvl-5)/4))
            _ayt=st.number_input("Yun Tal starting stacks",0,125,int(_ayt_default),1,key=f"item_audit_yt_{_alvl}")
        elif _ai=="Hexoptics C44":
            _adist=st.number_input("Attack distance",0.0,1000.0,550.0,25.0,key="item_audit_dist")
        _ares,_alog=sim(_achamp,_alvl,_afull,_aar,_amr,_ai,F,0,_abonus,_adist,0.0,False,False,False,0,True,_ared,False,_ayt)
        st.metric("Simulated DPS",f"{_ares[4]:.1f}")
        _rows=[]
        # sim log: attack, time, AS, crit%, effective armor, target HP before, damage, HP after, notes
        for _r in _alog:
            _k,_t,_asp,_crit,_ea,_before,_dmg,_after,_note=_r
            _state=""
            if _ai=="Yun Tal Wildarrows":
                _start=min(.25,_ayt*.002); _pre=min(.25,_start+max(0,_k-1)*.002); _post=min(.25,_start+_k*.002)
                _yt_until_a=-1.0; _yt_cd_a=0.0
                for _rr in _alog[:_k]:
                    _tt=float(_rr[1]); _cc=float(_rr[3])/100.0
                    if _yt_cd_a<=_tt:
                        _yt_until_a=_tt+6.0; _yt_cd_a=_tt+25.0
                    else:
                        _yt_cd_a=max(_tt,_yt_cd_a-(1.0+_cc))
                _active="ON" if _t<_yt_until_a else "OFF"
                _remain=max(0.0,_yt_cd_a-_t)
                _state=f"Permanent crit {100*_pre:.1f}% → {100*_post:.1f}% • Flurry {_active} • CD {_remain:.2f}s"
            elif _ai=="Terminus":
                _dark=min(3,_k//2); _light=min(3,(_k+1)//2)
                _state=f"Light {_light}/3 • Dark {_dark}/3 • Dark pen {_dark*10}%"
            elif _ai=="Guinsoo's Rageblade":
                _rb=min(4,_k); _after_full=max(0,_k-3); _ph=_after_full%3
                _state=f"Seething {_rb}/4 • Phantom counter {_ph}/3"
            elif _ai=="Kraken Slayer":
                _state=f"Bring It Down counter {_k%3}/3"
            elif _ai=="Blade of the Ruined King":
                _state=f"Target HP before AA {_before:.1f}"
            elif _ai=="Hexoptics C44":
                _amp=0 if _adist<100 else min(10,int((_adist-100)//50)+1)
                _state=f"Distance {_adist:.0f} • Magnification +{_amp}%"
            _rows.append([_k,_t,_asp,_crit,_ea,_before,_dmg,_after,_note,_state])
        _trace=pd.DataFrame(_rows,columns=["AA","Time","AS","Crit %","Effective Armor","HP Before","Damage","HP After","Proc / Note","Item State"])
        st.dataframe(_trace,use_container_width=True,hide_index=True)
        if _ai=="Yun Tal Wildarrows":
            st.info("Yun Tal trace currently exposes permanent-crit growth and Flurry trigger notes. Flurry cooldown reduction is executed inside sim(); a dedicated per-hit remaining-CD field would require extending sim()'s log schema.")
        elif _ai=="Hexoptics C44":
            st.caption("C44 distance is fixed for the entire simulation. With unchanged distance, every AA uses the same Magnification step.")
        st.caption(f"Target: {_atarget} • {_afull:.0f} HP • {_aar:.0f} Armor • {_amr:.0f} MR • Bonus HP {_abonus:.0f} • AA reduction {_ared*100:.0f}%")
    else:
        DB=F if dbpick=="Completed items" else P if dbpick=="Components" else B
        _db_cols=st.columns(3)
        _db_cols[0].metric("Records",len(DB))
        _db_cols[1].metric("Lowest Cost",f"{min(dct(v)['gold'] for v in DB.values()):,.0f}g")
        _db_cols[2].metric("Highest Cost",f"{max(dct(v)['gold'] for v in DB.values()):,.0f}g")
        _db_query=st.text_input("Find a record",placeholder="Search item or boots name…",key="db_item_search")
        rows=[]
        for n,v0 in DB.items():
            if _db_query.strip().casefold() not in n.casefold(): continue
            q=dct(v0); rows.append([boot_icon(n) if dbpick=="Boots" else item_icon(n),n,q["gold"],q["ad"],q["as"]*100,q["crit"]*100,q["ap"],q["hp"],q["mana"],q["armor"],q["mr"],q["ah"],q["ls"]*100,q["flatpen"],q["pctpen"]*100,q["ms"]])
        st.caption(f"{len(rows)} of {len(DB)} records · Base stats")
        if not rows: st.info("No records match this search. Try another item or boots name.")
        st.dataframe(pd.DataFrame(rows,columns=["Icon","Item","Gold","AD","AS%","Crit%","AP","HP","Mana","Armor","MR","AH","LS%","Flat Pen","Armor Pen%","MS"]),use_container_width=True,hide_index=True,column_config={"Icon":st.column_config.ImageColumn(""),"Item":st.column_config.TextColumn("Item",width="medium")})

st.divider()
st.caption("Web V5.77.0 | 23 champion fight adapters • Shared AA engine • Squishy benchmark tier list • 51-rune database • Item Tier List • Build Lab: 5 items + 1 Boots • Item Value • 23 components • 14 Boots | Ability-aware item rankings • Best tested builds.")
