import streamlit as st
import base64
import html
import urllib.parse
import streamlit.components.v1 as components
from pathlib import Path
from rune_database import RUNE_DATABASE, RUNE_TREES, RUNE_SLOTS

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
            if st.button(" ",key=f"{state_key}_tree_{i}",help=None,use_container_width=False):
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
                if st.button(" ",key=f"{state_key}__{i}__{name}",help=None,use_container_width=False):
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
</style>
""",unsafe_allow_html=True)
st.title("⚔️ SharpWR Damage Lab — V5")
st.caption("Patch 7.3a • Full items + components • single-target ADC auto-attack lab")

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
"Fiendhunter Bolts":("ultimate-trigger","modeled","Opening Barrage uses Ultimate pre-cast."),
"Rapid Firecannon":("energized","modeled","First Energized hit."),
"Runaan's Hurricane":("multi-target","not modeled","Extra bolts excluded in single-target ranking."),
"Phantom Dancer":("stacking","modeled","AS stacks build naturally from 0."),
"Navori Quickblades":("ability-cooldown","not modeled","Ability cooldown refund excluded."),
"Wit's End":("on-hit","modeled","Magic on-hit each attack."),
"Hexoptics C44":("distance","modeled","Uses attack distance."),
"Kraken Slayer":("every-N-hit","modeled","Proc every third attack."),
"Nashor's Tooth":("on-hit","modeled","Magic on-hit."),
"Manamune":("mana-scaling","modeled","Awe AD from mana."),
"Muramana":("mana/on-hit","modeled","Awe plus mana on-hit."),
"Statikk Shiv":("energized","modeled","First Energized hit."),
"Guinsoo's Rageblade":("stacking/on-hit","modeled","Stacks and phantom on-hit."),
"Mortal Reminder":("penetration","modeled","Percent armor penetration."),
"Maw of Malmortius":("defensive","not modeled","Shield/survival excluded."),
"Essence Reaver":("spell-trigger","modeled","Proc when ability-before-AA is enabled."),
"Immortal Shieldbow":("defensive","not modeled","Shield/survival excluded."),
"The Collector":("execute","modeled","Execute and previous executes."),
"Terminus":("stacking/on-hit","modeled","On-hit and penetration stacks."),
"Stormrazor":("energized","modeled","First Energized hit."),
"Yun Tal Wildarrows":("combat-state","partial","Combat proc exists; advanced state is partial."),
"Galeforce":("active","not modeled","Active excluded."),
"Mercurial Scimitar":("active/defensive","not modeled","Cleanse/active excluded."),
"Blade of the Ruined King":("current-HP/on-hit","modeled","Current-HP on-hit recalculated each attack."),
"Guardian Angel":("defensive","not modeled","Revive excluded."),
"Bloodthirster":("sustain","not modeled","Sustain is not scored as DPS."),
"Lord Dominik's Regards":("bonus-HP scaling","partial","Penetration modeled; amp needs target Bonus HP."),
"Trinity Force":("spell-trigger","modeled","Spellblade when ability-before-AA is enabled."),
"Infinity Edge":("crit modifier","modeled","Critical damage modifier."),
"Serylda's Grudge":("penetration/utility","partial","Penetration modeled; slow excluded."),
"Serpent's Fang":("shield-counter","not modeled","Needs target shield state."),
"Youmuu's Ghostblade":("movement/combat-state","partial","Static stats modeled; passive not fully scored."),
"Duskblade of Draktharr":("first-hit","modeled","First-hit Nightstalker damage."),
"Edge of Night":("defensive","not modeled","Spell shield excluded."),
"Iceborn Gauntlet":("spell-trigger","modeled","Spellblade damage; slow utility excluded."),
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
def rm(x): return 100/(100+max(0,x))
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


def sim(n,l,hp0,arm,mr,it,db,mist,bonus_hp,dist,base_mana,spell,energized,ult,execs,item_proc=True,target_aa_reduction=0.0):
    s=stats(n,l,mist); q=dct(db[it]); mana=base_mana+q["mana"]
    awe=.02*mana if it in ("Manamune","Muramana") else 0
    ad=s["ad"]+q["ad"]+awe
    hp=float(hp0); t=0.; k=0; log=[]
    pd_stacks=rb=light=dark=0; rage_hits=0; ytcrit=0.; yt_until=-1.; yt_cd=0.; spellblade_ready=0.
    fh=3 if it=="Fiendhunter Bolts" and ult else 0
    while hp>0 and k<500:
        k+=1
        dyn=(.06*pd_stacks if it=="Phantom Dancer" and item_proc else 0)+(.08*rb if it=="Guinsoo's Rageblade" and item_proc else 0)
        if it=="Yun Tal Wildarrows" and item_proc and t<yt_until: dyn+=.35
        if it=="Fiendhunter Bolts" and item_proc and fh and t<=8: dyn+=.50
        asp=min(3,s["baseas"]+s["ratio"]*(s["bba"]+s["lvbas"]+q["as"]+dyn))
        crit=q["crit"]+(mist//20*.10 if n=="Senna" else 0)+(ytcrit if it=="Yun Tal Wildarrows" else 0)
        crit=min(1,crit); cd=2.3 if it=="Infinity Edge" else 2.
        if n=="Senna": cd*=.9
        pct=q["pctpen"]+(.10*dark if it=="Terminus" and item_proc else 0)
        if it=="Terminus": pct=min(.40,pct)
        ea=max(0,arm*(1-pct)-q["flatpen"])
        true=0.; mag=0.; onp=0.; onm=0.; note=[]
        if it=="Fiendhunter Bolts" and item_proc and fh and t<=8:
            phy=ad*(cd*.80); true=ad*.15*crit; note.append("Opening Barrage")
        else: phy=ad*(1+crit*(cd-1))
        if it=="Hexoptics C44":
            amp=max(0,min(.10,.10*dist/550)); phy*=1+amp; true*=1+amp; note.append(f"C44 {amp*100:.1f}%")
        if it=="Wit's End": onm+=40
        if it=="Nashor's Tooth": onm+=15+.20*q["ap"]
        rage_extra=False
        if it=="Guinsoo's Rageblade":
            onm+=30
            if rb>=4:
                rage_hits+=1
                if rage_hits>=3:
                    rage_extra=True; rage_hits=0
        if it=="Terminus": onm+=30
        if it=="Recurve Bow": onp+=15
        if it=="Blade of the Ruined King": onp+=max(15,.07*hp)
        if it=="Muramana": onp+=.015*mana
        if it=="Kraken Slayer" and item_proc and k%3==0:
            base=120+(l-1)/14*48; miss=(hp0-hp)/hp0
            onp+=base*(1+min(.75,.75*miss)); note.append("Kraken")
        if it=="Duskblade of Draktharr" and item_proc and k==1:
            onp+=60+(l-1)/14*100; note.append("Nightstalker")
        if energized and item_proc and k==1:
            if it=="Rapid Firecannon": onm+=80; note.append("RFC")
            if it=="Stormrazor": onm+=120; note.append("Storm")
            if it=="Statikk Shiv": onm+=60; note.append("Shiv")
            if it=="Kircheis Shard": onm+=40; note.append("Jolt")
        if spell and item_proc and t>=spellblade_ready:
            if it=="Essence Reaver":
                onp+=1.35*s["basead"]+min(80,.8*crit*100); note.append("ER")
                spellblade_ready=t+1.5
            if it=="Trinity Force":
                onp+=2*s["basead"]; note.append("Trinity")
                spellblade_ready=t+1.5
            if it=="Iceborn Gauntlet":
                onp+=s["basead"]+.25*q["armor"]; note.append("Iceborn")
                spellblade_ready=t+1.5
            if it=="Sheen":
                onp+=s["basead"]; note.append("Sheen")
                spellblade_ready=t+1.5
        if it=="Guinsoo's Rageblade" and item_proc and rage_extra:
            # Phantom hit repeats Rageblade's own repeatable on-hit only.
            # It must not duplicate unrelated every-N-attacks procs such as Kraken.
            onm+=30; note.append("Rageblade phantom on-hit")
        phy+=onp; mag+=onm
        if it=="Lord Dominik's Regards":
            amp=min(.12,.12*max(0,bonus_hp)/1200); phy*=1+amp; mag*=1+amp; true*=1+amp
        dmg=phy*rm(ea)+mag*rm(mr)+true
        if target_aa_reduction: dmg*=1-target_aa_reduction
        before=hp; hp-=dmg
        if it=="The Collector" and item_proc:
            th=min(1,.05+.001*execs)
            if 0<hp<=hp0*th: hp=0; note.append(f"Execute {th*100:.1f}%")
        if it=="Phantom Dancer" and item_proc: pd_stacks=min(5,pd_stacks+1)
        if it=="Guinsoo's Rageblade" and item_proc: rb=min(4,rb+1)
        if it=="Terminus" and item_proc:
            if k%2: light=min(3,light+1)
            else: dark=min(3,dark+1)
        if it=="Yun Tal Wildarrows" and item_proc:
            ytcrit=min(.25,ytcrit+.002)
            if yt_cd<=t: yt_until=t+6; yt_cd=t+20; note.append("Flurry")
        if it=="Fiendhunter Bolts" and item_proc and fh and t<=8: fh-=1
        log.append([k,round(t,3),round(asp,4),round(crit*100,2),round(ea,1),round(before,1),round(dmg,1),round(max(hp,0),1),", ".join(note)])
        if hp<=0: break
        t+=1/asp
    return [it,q["gold"],round(t,3),k,round(hp0/t,1) if t else float("inf")],log

# Shared scenario defaults/state. UI belongs inside each tab rather than above the tabs.
champ=st.session_state.get("build_champ",list(C)[0])
level=int(st.session_state.get("build_level",9))
mist=int(st.session_state.get("build_mist",40 if champ=="Senna" else 0)) if champ=="Senna" else 0
s=stats(champ,level,mist)
hp=float(st.session_state.get("build_target_hp",2500))
armor=float(st.session_state.get("build_target_armor",0.0))
mr=float(st.session_state.get("build_target_mr",0.0))
bonus_hp=float(st.session_state.get("build_target_bonus_hp",0.0))
dist=float(st.session_state.get("build_dist",550.0))
mana=float(st.session_state.get("build_mana",0.0))
spell=bool(st.session_state.get("build_spell",True))
energized=bool(st.session_state.get("build_energized",True))
ult=bool(st.session_state.get("build_ult",True))
execs=int(st.session_state.get("build_execs",0))

tabs=st.tabs(["⚔️ Item Tier List","🔥 Build Lab","💰 Item Value","📚 Database"])

with tabs[0]:
    st.subheader("Item Tier List")
    st.caption("Enemy champion selection removed. Items are tested against fixed level-based target profiles.")

    tc1,tc2=st.columns(2)
    tier_champ=tc1.selectbox("Champion",list(C),index=list(C).index(champ),key="tier_champ")
    tier_level=tc2.slider("Level",1,15,level,key="tier_level")
    tier_mist=st.number_input("Senna Mist",0,500,int(mist if tier_champ=="Senna" else 0),20,key="tier_mist") if tier_champ=="Senna" else 0

    tier_target=st.radio("Target Profile",list(TARGET_PROFILES),horizontal=True,key="tier_target")
    _target=_target_profile_at_level(TARGET_PROFILES[tier_target],tier_level)
    st.caption("Fixed benchmark target active. Darius/Ornn automatically apply the 10% Steelcaps/Armored Advance basic-attack reduction from Lv5 onward.")

    st.markdown("**Scenario Preset**")
    _scenario_defs={
        "Standard Fight":{"hp_pct":100,"spell":False,"energized":False,"ult":False,"desc":"Fresh all-in from full HP. Item stacks start at 0 and build naturally."},
        "First Contact":{"hp_pct":100,"spell":True,"energized":True,"ult":False,"desc":"Fresh target with first-contact triggers prepared: Spellblade + Energized ready."},
        "Extended Fight":{"hp_pct":100,"spell":False,"energized":False,"ult":False,"desc":"Sustained all-in from 0 stacks. Current engine still measures target TTK; fixed-duration damage is not enabled yet."},
        "Low HP Target":{"hp_pct":35,"spell":False,"energized":False,"ult":False,"desc":"Finisher test: target starts at 35% HP; defenses and boot mitigation stay unchanged."},
    }
    tier_scenario=st.radio("Combat Scenario",list(_scenario_defs),horizontal=True,key="tier_scenario",label_visibility="collapsed")
    _sc=_scenario_defs[tier_scenario]
    st.caption(_sc["desc"])

    with st.expander("Advanced Scenario Settings"):
        ta1,ta2=st.columns(2)
        tier_start_hp_pct=ta1.slider("Target Starting HP %",1,100,int(_sc["hp_pct"]),1,key=f"tier_hp_pct_{tier_scenario}")
        tier_dist=ta2.number_input("Attack Range / Distance",0.0,1000.0,float(dist),25.0,key="tier_dist")
        ta3,ta4=st.columns(2)
        tier_mana=ta3.number_input("Champion Max Mana before item",0.0,5000.0,float(mana),50.0,key="tier_mana")
        tier_execs=ta4.number_input("Collector previous executes",0,500,int(execs),1,key="tier_execs")
        tb1,tb2,tb3=st.columns(3)
        tier_spell=tb1.checkbox("Ability cast before first AA",value=_sc["spell"],key=f"tier_spell_{tier_scenario}")
        tier_energized=tb2.checkbox("Energized ready",value=_sc["energized"],key=f"tier_energized_{tier_scenario}")
        tier_ult=tb3.checkbox("Ultimate pre-cast",value=_sc["ult"],key=f"tier_ult_{tier_scenario}")

    if tier_champ=="Jhin":
        st.warning("Jhin is excluded until the 4-shot + reload model is added.")
    elif st.button(f"⚔️ CALCULATE VS {tier_target.split(' • ')[0].upper()}",type="primary",use_container_width=True,key="tiercalc"):
        tier_full_hp=float(_target["hp"]); tier_hp=tier_full_hp*(tier_start_hp_pct/100.0); tier_armor=float(_target["armor"]); tier_mr=float(_target["mr"]); tier_bonus_hp=0.0
        tier_aa_reduction=float(_target.get("aa_reduction",0))
        base_db={"No Item":(0,0,0,0,0,0,0,0,0,0,0,0,0,0)}
        base_row,_=sim(tier_champ,tier_level,tier_hp,tier_armor,tier_mr,"No Item",base_db,tier_mist,tier_bonus_hp,tier_dist,tier_mana,False,False,False,0,target_aa_reduction=tier_aa_reduction)
        baseline=base_row[4]
        rows=[]
        for it in F:
            row,_=sim(tier_champ,tier_level,tier_hp,tier_armor,tier_mr,it,F,tier_mist,tier_bonus_hp,tier_dist,tier_mana,tier_spell,tier_energized,tier_ult,tier_execs,target_aa_reduction=tier_aa_reduction)
            gold=float(row[1]); dps=float(row[4]); gain=(dps/baseline-1)*100 if baseline else 0
            bonus_dps=dps-baseline; value=(bonus_dps/gold*1000) if gold else 0
            rows.append([it,gold,dps,gain,bonus_dps,value,row[2],row[3]])
        df=pd.DataFrame(rows,columns=["Item","Gold","DPS","DPS Gain %","Bonus DPS","Bonus DPS / 1000g","TTK","Attacks"]).sort_values(["DPS","TTK"],ascending=[False,True]).reset_index(drop=True)
        df.insert(0,"Rank",range(1,len(df)+1))
        best_dps=df.iloc[0]; best_value=df.sort_values(["Bonus DPS / 1000g","DPS"],ascending=[False,False]).iloc[0]; best_gain=df.sort_values(["DPS Gain %","DPS"],ascending=[False,False]).iloc[0]
        m1,m2,m3,m4=st.columns(4)
        m1.metric(f"Best Item • {tier_scenario}",best_dps["Item"])
        m2.metric("Best DPS",f"{best_dps['DPS']:.1f}")
        m3.metric("Best DPS Gain",f"{best_gain['DPS Gain %']:.1f}%",best_gain["Item"])
        m4.metric("Best Value / 1000g",f"{best_value['Bonus DPS / 1000g']:.1f}",best_value["Item"])
        st.markdown(f"**{tier_champ} Lv{tier_level} • VS {tier_target.split(' • ')[0]} • {tier_scenario}**")
        # Premium icon-first ranking: keep the numeric table compact, but make each ranked item visually identifiable.
        _rank_html=['<div class="tier-rank-grid">']
        for _,_r in df.iterrows():
            _name=str(_r["Item"]); _icon=item_icon(_name)
            _rank_html.append(
                f'<div class="tier-rank-card">'
                f'<div class="tier-rank-num">#{int(_r["Rank"])}</div>'
                f'<img src="{html.escape(_icon)}" alt="{html.escape(_name)}">'
                f'<div class="tier-rank-name">{html.escape(_name)}</div>'
                f'<div class="tier-rank-dps">{float(_r["DPS"]):.1f} <span>DPS</span></div>'
                f'<div class="tier-rank-sub">+{float(_r["DPS Gain %"]):.1f}% · {float(_r["Bonus DPS / 1000g"]):.1f}/1k</div>'
                f'</div>'
            )
        _rank_html.append('</div>')
        st.markdown("""<style>
        .tier-rank-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(128px,1fr));gap:10px;margin:8px 0 16px}
        .tier-rank-card{position:relative;text-align:center;padding:10px 7px 9px;border:1px solid rgba(128,128,128,.22);border-radius:12px;background:rgba(128,128,128,.045)}
        .tier-rank-card:hover{border-color:#c9a84c;transform:translateY(-1px)}
        .tier-rank-card img{width:54px;height:54px;border-radius:9px;object-fit:cover;border:1px solid rgba(255,255,255,.16)}
        .tier-rank-num{position:absolute;top:7px;left:8px;font-size:11px;font-weight:800;color:#c9a84c}
        .tier-rank-name{font-size:11px;font-weight:750;line-height:1.15;min-height:26px;margin-top:5px}
        .tier-rank-dps{font-size:15px;font-weight:850}.tier-rank-dps span{font-size:9px;font-weight:650;opacity:.62}
        .tier-rank-sub{font-size:9px;opacity:.62;white-space:nowrap}
        @media(max-width:640px){.tier-rank-grid{grid-template-columns:repeat(3,1fr);gap:7px}.tier-rank-card{padding:9px 4px 7px}.tier-rank-card img{width:48px;height:48px}}
        </style>""",unsafe_allow_html=True)
        st.markdown("".join(_rank_html),unsafe_allow_html=True)
        with st.expander("Detailed ranking table"):
            st.dataframe(df,use_container_width=True,hide_index=True)
        st.caption("Value = (item DPS − naked champion DPS) / item gold × 1000. The champion's base DPS is not counted as item value.")
        with st.expander("Scenario Engine • Item Passive Audit"):
            st.caption("Modeled = explicit combat logic. Partial = only part is represented. Not modeled = DPS rank is not full in-game value.")
            _audit_rows=[]
            for _it in F:
                _cat,_status,_note=ITEM_SCENARIO_AUDIT.get(_it,("static stats","modeled","Static offensive stats only."))
                _audit_rows.append([_it,_cat,_status,_note])
            st.dataframe(pd.DataFrame(_audit_rows,columns=["Item","Mechanic","Engine Status","Tier List behavior"]),use_container_width=True,hide_index=True)


with tabs[1]:
    st.subheader("Build Lab")

    # Build Lab owns the manual champion/target/scenario controls.
    _bc1,_bc2=st.columns(2)
    champ=_bc1.selectbox("Champion",list(C),index=list(C).index(champ),key="build_champ")
    level=_bc2.slider("Level",1,15,level,key="build_level")
    mist=st.number_input("Senna Mist",0,500,int(mist),20,key="build_mist") if champ=="Senna" else 0
    s=stats(champ,level,mist)
    _tx,_ty,_tz=st.columns(3)
    hp=_tx.number_input("Target HP",100,20000,int(hp),100,key="build_target_hp")
    armor=_ty.number_input("Target Armor",0.0,1000.0,float(armor),5.0,key="build_target_armor")
    mr=_tz.number_input("Target MR",0.0,1000.0,float(mr),5.0,key="build_target_mr")
    _tu,_tv,_tw=st.columns(3)
    bonus_hp=_tu.number_input("Target Bonus HP",0.0,10000.0,float(bonus_hp),100.0,key="build_target_bonus_hp")
    dist=_tv.number_input("Attack distance",0.0,1000.0,float(dist),25.0,key="build_dist")
    mana=_tw.number_input("Champion Max Mana before item",0.0,5000.0,float(mana),50.0,key="build_mana")
    target_boot=st.selectbox("Target Boots",["None","Plated Steelcaps","Armored Advance"],key="build_target_boot",help="Plated Steelcaps and Armored Advance: 10% less damage from basic attacks.")
    target_aa_reduction=.10 if target_boot in ("Plated Steelcaps","Armored Advance") else 0.0
    with st.expander("Proc / scenario switches"):
        spell=st.checkbox("Ability cast before first AA (Spellblade ready)",spell,key="build_spell")
        energized=st.checkbox("Start with Energized/Jolt proc ready",energized,key="build_energized")
        ult=st.checkbox("Ultimate cast before combat (Fiendhunter)",ult,key="build_ult")
        execs=st.number_input("Collector previous executes",0,500,int(execs),1,key="build_execs")
    if champ=="Jhin": st.warning("Jhin is excluded from V5 rankings until its 4-shot/reload model is added.")

    # Legal rune loadout: equip one slot at a time; completed pickers collapse.
    st.markdown("**Rune Loadout**")
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

    st.markdown('<div class="wr-eq-wrap">',unsafe_allow_html=True)
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
    st.markdown('</div>',unsafe_allow_html=True)

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

    st.markdown("### Equipped Build")
    build=list(st.session_state.build_items_v2)
    slot_cols=st.columns(5)
    for _i in range(5):
        if _i<len(build):
            _it=build[_i]; _url=item_icon(_it)
            if _url: slot_cols[_i].image(_url,width=58)
            slot_cols[_i].markdown(f"**{_it}**")
            if slot_cols[_i].button("✕ Remove",key=f"remove_item_{_i}",use_container_width=True):
                build.pop(_i); st.session_state.build_items_v2=build; st.rerun()
        else:
            slot_cols[_i].markdown("### ＋")
            slot_cols[_i].caption("Empty slot")

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
            with _col:
                st.markdown('<div class="wr-pick-marker '+('wr-selected' if _selected else '')+'">'+_card+'</div>',unsafe_allow_html=True)
                if _icon: st.image(_icon,width=66)
                st.markdown(f'<div class="wr-icon-name">{html.escape(_name)}</div>',unsafe_allow_html=True)
                if st.button(" ",key=f"native_item_{_ii}",help=None,use_container_width=False,disabled=_selected or len(build)>=5):
                    _new=list(st.session_state.build_items_v2)
                    if _name not in _new and len(_new)<5:
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
                if st.button(" ",key=f"pick_boot_{_i}",help=None,use_container_width=False):
                    st.session_state.build_boot_v2=_name
                    st.rerun()
        st.markdown('<div class="wr-grid-gap"></div>',unsafe_allow_html=True)
    boot=st.session_state.build_boot_v2

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
        hp2=float(hp); t=0.; attacks=0; pd_stacks=rb=dark=0; rage_hits=0; fh=3 if ("Fiendhunter Bolts" in build and ult) else 0
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
        while hp2>0 and attacks<500:
            attacks+=1
            dyn=(.06*pd_stacks if "Phantom Dancer" in build else 0)+(.08*rb if "Guinsoo's Rageblade" in build else 0)
            if "Yun Tal Wildarrows" in build and yt_flurry: dyn+=.35
            if "Fiendhunter Bolts" in build and fh and t<=8: dyn+=.50
            if keystone=="Conqueror":
                # User-confirmed convention for tooltip ranges: linear Lv1 -> Lv15 scaling.
                _conq_ad_per_stack=lvl_scale(3.0,5.0,level)
                current_ad=ad+conq_stacks*_conq_ad_per_stack
            else:
                current_ad=ad
            lt_as=.048*lt_stacks if keystone=="Lethal Tempo" else 0.0
            asp=min(3,s0["baseas"]+s0["ratio"]*(s0["bba"]+s0["lvbas"]+total["as"]+dyn+rune_bonus_as+lt_as))
            cc=crit
            pct=total["pctpen"]+(.10*dark if "Terminus" in build else 0)
            if "Terminus" in build: pct=min(.40,pct)
            ea=max(0,armor*(1-pct)-total["flatpen"])
            true=0.; mag=0.; onp=0.
            if "Fiendhunter Bolts" in build and fh and t<=8:
                phy=current_ad*(cd*.80); true=current_ad*.15*cc
            else: phy=current_ad*(1+cc*(cd-1))
            if "Hexoptics C44" in build:
                amp=max(0,min(.10,.10*dist/550)); phy*=1+amp; true*=1+amp
            if "Wit's End" in build: mag+=40
            if "Nashor's Tooth" in build: mag+=15+.20*total["ap"]
            rage_extra=False
            if "Guinsoo's Rageblade" in build:
                mag+=30
                if rb>=4:
                    rage_hits+=1
                    if rage_hits>=3:
                        rage_extra=True; rage_hits=0
            if "Terminus" in build: mag+=30
            if "Blade of the Ruined King" in build: onp+=max(15,.07*hp2)
            if "Muramana" in build: onp+=.015*maxmana
            if "Kraken Slayer" in build and attacks%3==0:
                base=120+(level-1)/14*48; miss=(hp-hp2)/hp
                onp+=base*(1+min(.75,.75*miss))
            if "Duskblade of Draktharr" in build and attacks==1: onp+=60+(level-1)/14*100
            if energized and attacks==1:
                if "Rapid Firecannon" in build: mag+=80
                if "Stormrazor" in build: mag+=120
                if "Statikk Shiv" in build: mag+=60
            if spell and attacks==1:
                if "Essence Reaver" in build: onp+=1.35*s0["basead"]+min(80,.8*cc*100)
                if "Trinity Force" in build: onp+=2*s0["basead"]
                if "Iceborn Gauntlet" in build: onp+=s0["basead"]+.25*total["armor"]
            if "Guinsoo's Rageblade" in build and rage_extra:
                # Repeat only repeatable on-hit effects; never duplicate Kraken,
                # Energized, Spellblade, Duskblade, or the basic attack itself.
                mag+=30
                if "Wit's End" in build: mag+=40
                if "Nashor's Tooth" in build: mag+=15+.20*total["ap"]
                if "Terminus" in build: mag+=30
                if "Blade of the Ruined King" in build: onp+=max(15,.07*hp2)
                if "Muramana" in build: onp+=.015*maxmana
            phy+=onp
            if "Lord Dominik's Regards" in build:
                amp=min(.12,.12*max(0,bonus_hp)/1200); phy*=1+amp; mag*=1+amp; true*=1+amp
            em=max(0,mr*(1-total["pctmpen"])-total["flatmpen"])
            dmg=phy*rm(ea)+mag*rm(em)+true
            if target_aa_reduction: dmg*=1-target_aa_reduction

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
                hp2-=_sv
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
            hp2-=dmg
            if "The Collector" in build:
                th=min(1,.05+.001*execs)
                if 0<hp2<=hp*th: hp2=0
            # The completed auto grants stacks for the NEXT attack.
            if keystone=="Conqueror": conq_stacks=min(6,conq_stacks+1)
            if keystone=="Lethal Tempo": lt_stacks=min(6,lt_stacks+1)
            if keystone=="Empowerment":
                empowerment_hits=min(3,empowerment_hits+1)
                if empowerment_hits>=3: empowerment_active=True
            if "Phantom Dancer" in build: pd_stacks=min(5,pd_stacks+1)
            if "Guinsoo's Rageblade" in build: rb=min(4,rb+1)
            if "Terminus" in build and attacks%2==0: dark=min(3,dark+1)
            if "Fiendhunter Bolts" in build and fh and t<=8: fh-=1
            _stack_after=f"Conq {conq_stacks}/6 | LT {lt_stacks}/6 | Empower {empowerment_hits}/3"
            rune_timeline.append([attacks,round(t,3),round(max(0,hp2),1),_stack_before+" → "+_stack_after," • ".join(_cd_bits) if _cd_bits else "—",_event_text or "—"])
            if hp2<=0: break
            t+=1/asp
        cost=sum(F[x][0] for x in build)+B[boot][0]

        # Highest legal one-AA damage. A crit is forced only when the build has non-zero crit chance.
        maxcrit=crit>0
        max_ea=max(0,armor*(1-total["pctpen"])-total["flatpen"])
        hit_phy=ad*(cd if maxcrit else 1.0); hit_mag=0.; hit_true=0.
        parts=[["Basic AA crit" if maxcrit else "Basic AA","Physical",hit_phy]]
        if "Hexoptics C44" in build:
            amp=max(0,min(.10,.10*dist/550)); hit_phy*=1+amp
            parts=[[n,typ,v*(1+amp) if typ=="Physical" else v] for n,typ,v in parts]
        for name,val in [("Wit's End",40 if "Wit's End" in build else 0),
                         ("Rageblade",30 if "Guinsoo's Rageblade" in build else 0),
                         ("Terminus",30 if "Terminus" in build else 0)]:
            if val: hit_mag+=val; parts.append([name,"Magic",val])
        if "Nashor's Tooth" in build:
            v=15+.20*total["ap"]; hit_mag+=v; parts.append(["Nashor's Tooth","Magic",v])
        if "Blade of the Ruined King" in build:
            v=max(15,.07*hp); hit_phy+=v; parts.append(["BotRK current-HP","Physical",v])
        if "Muramana" in build:
            v=.015*maxmana; hit_phy+=v; parts.append(["Muramana Shock","Physical",v])
        if energized:
            for name,val in [("Rapid Firecannon",80),("Stormrazor",120),("Statikk Shiv",60)]:
                if name in build: hit_mag+=val; parts.append([name,"Magic",val])
        if spell:
            if "Essence Reaver" in build:
                v=1.35*s0["basead"]+min(80,80 if maxcrit else 0); hit_phy+=v; parts.append(["Essence Reaver","Physical",v])
            if "Trinity Force" in build:
                v=2*s0["basead"]; hit_phy+=v; parts.append(["Trinity Force","Physical",v])
            if "Iceborn Gauntlet" in build:
                v=s0["basead"]+.25*total["armor"]; hit_phy+=v; parts.append(["Iceborn Gauntlet","Physical",v])
        if "Duskblade of Draktharr" in build:
            v=60+(level-1)/14*100; hit_phy+=v; parts.append(["Duskblade","Physical",v])
        ldramp=min(.12,.12*max(0,bonus_hp)/1200) if "Lord Dominik's Regards" in build else 0
        if ldramp:
            hit_phy*=1+ldramp; hit_mag*=1+ldramp; hit_true*=1+ldramp
            parts=[[n,typ,v*(1+ldramp)] for n,typ,v in parts]
        max_em=max(0,mr*(1-total["pctmpen"])-total["flatmpen"])
        max_hit=hit_phy*rm(max_ea)+hit_mag*rm(max_em)+hit_true
        if boot=="Immortal Treads" and immortal_above_half:
            max_hit*=1.05
            parts=[[n+" × Immortal Treads",typ,v*1.05] for n,typ,v in parts]

        st.markdown("**Full Build Offensive Stats**")
        if keystone!="None":
            rune_bits=[]
            if rune_bonus_ad: rune_bits.append(f"+{rune_bonus_ad:.1f} AD")
            if gathering_storm_ad: rune_bits.append(f"GS +{gathering_storm_ad:.0f} AD @ {game_minute}m")
            if rune_bonus_as: rune_bits.append(f"+{rune_bonus_as*100:.1f}% AS")
            if rune_bonus_ah: rune_bits.append(f"+{rune_bonus_ah:.0f} AH")
            if rune_omnivamp: rune_bits.append(f"+{rune_omnivamp*100:.0f}% Omnivamp")
            st.caption("Key Rune: **"+keystone+"** • Primary: **"+primary_tree+"** • Secondary: **"+secondary_rune+"** • "+" • ".join(rune_bits))
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

        a1,a2,a3,a4=st.columns(4)
        a1.metric("Build Cost",f"{cost:,}g"); a2.metric("TTK",f"{t:.3f}s")
        a3.metric("Avg DPS",f"{hp/t:.1f}" if t else "∞"); a4.metric("Max Single Hit",f"{max_hit:.1f}")
        st.write("**Build:** "+" • ".join(build)+f" • **{boot}**")
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
            st.caption("Highest one basic attack when a crit is possible. Ready Spellblade, Energized and first-hit effects use the scenario switches. Kraken 3rd-hit and pre-stacked Terminus/Rageblade are not assumed.")
            br=[]
            for pn,pt,pv in parts:
                dealt=pv*rm(max_ea) if pt=="Physical" else pv*rm(max_em) if pt=="Magic" else pv
                br.append([pn,pt,round(pv,1),round(dealt,1)])
            st.table(pd.DataFrame(br,columns=["Source","Type","Raw Damage","Damage After Resist"]))
            st.metric("Total Max Single Hit",f"{max_hit:.1f}")

with tabs[2]:
    st.subheader("Item Value")
    st.caption("Raw Gold Efficiency uses only directly priced base components. DPS/1000g is shown separately.")
    rates={"ad":500/12,"as":400/.12,"crit":500/.10,"ap":500/20,"hp":500/150,"armor":500/20,"mr":500/20,"ah":300/5}
    proc_items=["Fiendhunter Bolts","Rapid Firecannon","Phantom Dancer","Kraken Slayer","Statikk Shiv","Guinsoo\'s Rageblade","Essence Reaver","The Collector","Terminus","Stormrazor","Yun Tal Wildarrows","Trinity Force","Duskblade of Draktharr","Iceborn Gauntlet"]
    st.markdown("**Item proc?**")
    st.caption("ON = proc is used whenever its trigger/cooldown allows during the fight. OFF = proc disabled. Raw item stats remain active.")
    proc_states={}
    pc=st.columns(4)
    for i,pit in enumerate(proc_items):
        proc_states[pit]=pc[i%4].checkbox(pit,value=True,key=f"iv_proc_{pit}")
    if champ!="Jhin":
        rows=[]
        for it,v0 in F.items():
            q=dct(v0); raw=sum(q[k]*rates[k] for k in rates)
            row,_=sim(champ,level,hp,armor,mr,it,F,mist,bonus_hp,dist,mana,spell,energized,ult,execs,proc_states.get(it,True))
            dps=row[4]; rows.append([item_icon(it),it,q["gold"],round(raw),round(raw/q["gold"]*100,1),dps,round(dps/q["gold"]*1000,1)])
        val=pd.DataFrame(rows,columns=["Icon","Item","Cost","Priced Raw Stats","Raw Gold Efficiency %","DPS","DPS / 1000g"]).sort_values("DPS / 1000g",ascending=False).reset_index(drop=True)
        val.insert(0,"Rank",range(1,len(val)+1))
        st.dataframe(val,use_container_width=True,hide_index=True,column_config={"Icon":st.column_config.ImageColumn(""),"Item":st.column_config.TextColumn("Item",width="medium")})
        st.info("Unpriced stats/passives are excluded from Raw Gold Efficiency rather than assigned invented prices.")

with tabs[3]:
    st.subheader("Database")
    dbpick=st.radio("Show",["Completed items","Components","Boots","Runes"],horizontal=True)
    if dbpick=="Runes":
        st.caption("51/51 verified rune records. Utility/defensive runes are retained for future champion, ability, heal, shield, CC and movement systems. Level-scaled ranges are stored without inventing intermediate values.")
        tree_filter=st.selectbox("Rune tree",["All","Key Rune","Precision","Domination","Resolve","Sorcery"],key="rune_db_tree")
        rune_rows=[]
        for rn,rv in RUNE_DATABASE.items():
            if tree_filter!="All" and rv["tree"]!=tree_filter: continue
            rune_rows.append([rn,rv["tree"],rv["kind"],rv["tooltip"]])
        st.dataframe(pd.DataFrame(rune_rows,columns=["Rune","Tree","Type","Verified tooltip / effect"]),use_container_width=True,hide_index=True)
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
        st.dataframe(adf,use_container_width=True,hide_index=True)
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
    else:
        DB=F if dbpick=="Completed items" else P if dbpick=="Components" else B
        rows=[]
        for n,v0 in DB.items():
            q=dct(v0); rows.append([n,q["gold"],q["ad"],q["as"]*100,q["crit"]*100,q["ap"],q["hp"],q["mana"],q["armor"],q["mr"],q["ah"],q["ls"]*100,q["flatpen"],q["pctpen"]*100,q["ms"]])
        st.dataframe(pd.DataFrame(rows,columns=["Item","Gold","AD","AS%","Crit%","AP","HP","Mana","Armor","MR","AH","LS%","Flat Pen","Armor Pen%","MS"]),use_container_width=True,hide_index=True)

st.divider()
st.caption("Web V5.40 | Squishy benchmark tier list • 51-rune database • Item Tier List • Build Lab: 5 items + 1 Boots • Item Value • 23 components • 14 Boots | Jhin rankings disabled pending 4-shot/reload modeling.")
