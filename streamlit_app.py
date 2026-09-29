import streamlit as st
import base64
import html
import urllib.parse
import streamlit.components.v1 as components
from pathlib import Path
from rune_database import RUNE_DATABASE, RUNE_TREES, RUNE_SLOTS

CD_ITEM_ICON_BASE="https://raw.communitydragon.org/latest/game/assets/items/icons2d/"
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
        tiles.append(f'''<a class="tile{sel}{edge}" href="{href}" target="_top">
          <img src="{html.escape(icon)}" alt="{html.escape(name)}">
          <div class="card"><header><img src="{html.escape(icon)}"><div><strong>{html.escape(name)}</strong><em>◆ {int(q["gold"])} Gold</em></div></header>
          <section>{"".join(rows)}</section><footer>Click to add to build</footer></div></a>''')
    doc='''<!doctype html><html><head><style>
    *{box-sizing:border-box}body{margin:0;background:transparent;font-family:Inter,system-ui,sans-serif;color:#e9edf3;overflow:visible}
    .grid{display:grid;grid-template-columns:repeat(10,minmax(58px,1fr));gap:10px;padding:18px 4px 230px}
    .tile{position:relative;display:flex;justify-content:center;align-items:center;height:68px;border:1px solid #343e4e;border-radius:11px;
      background:linear-gradient(145deg,#171e29,#0a0f16);text-decoration:none;transition:.15s;z-index:1}
    .tile>img{width:56px;height:56px;object-fit:cover;border-radius:8px}
    .tile:hover{border-color:#d1ae55;transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.35);z-index:20}
    .tile.selected{border-color:#d1ae55;box-shadow:inset 0 0 0 1px rgba(209,174,85,.45)}
    .card{pointer-events:none;visibility:hidden;opacity:0;position:absolute;z-index:100;left:50%;bottom:76px;transform:translateX(-50%) translateY(5px);
      width:360px;min-height:150px;padding:14px;border:1px solid #526078;border-radius:13px;background:linear-gradient(150deg,#151d29,#080d14 75%);
      box-shadow:0 18px 45px rgba(0,0,0,.62);transition:opacity .14s .32s,transform .14s .32s}
    .tile:hover .card{visibility:visible;opacity:1;transform:translateX(-50%) translateY(0)}
    .tile:nth-child(-n+20) .card{bottom:auto;top:76px;transform:translateX(-50%) translateY(-5px)}
    .tile.edge-left .card{left:0;right:auto;transform:translateX(0) translateY(5px)}
    .tile.edge-right .card{left:auto;right:0;transform:translateX(0) translateY(5px)}
    .tile:nth-child(-n+20).edge-left .card,.tile:nth-child(-n+20).edge-right .card{transform:translateX(0) translateY(-5px)}
    .tile:nth-child(-n+20):hover .card{transform:translateX(-50%) translateY(0)}
    .tile.edge-left:hover .card,.tile.edge-right:hover .card,
    .tile:nth-child(-n+20).edge-left:hover .card,.tile:nth-child(-n+20).edge-right:hover .card{transform:translateX(0) translateY(0)}
    header{display:flex;gap:11px;align-items:center;padding-bottom:10px;border-bottom:1px solid #2d3746}
    header img{width:52px;height:52px;border-radius:8px;border:1px solid #b8994d}strong{display:block;color:#f1d37b;font-size:16px}
    em{display:block;color:#d5b45b;font-size:12px;font-style:normal;margin-top:3px}
    section{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 14px;padding-top:11px;align-items:start}.s{display:flex;gap:7px;align-items:flex-start;min-width:0}.s i{font-style:normal;width:22px;height:22px;border-radius:6px;display:flex;align-items:center;justify-content:center;background:#202a38;border:1px solid #3a485d;color:#a8c8ee}
    .s b{font-size:12px;white-space:nowrap}.s span{min-width:0}.s small{display:block;color:#8f9cac;font-size:9px;line-height:1.15;white-space:normal;overflow-wrap:anywhere}footer{margin-top:10px;padding-top:8px;border-top:1px solid #28313e;color:#718096;font-size:9px}
    @media(max-width:900px){.grid{grid-template-columns:repeat(6,minmax(54px,1fr))}}
    </style></head><body><div class="grid">'''+''.join(tiles)+'''</div></body></html>'''
    rows=(len(items)+9)//10
    components.html(doc,height=250+rows*78,scrolling=False)


import pandas as pd

st.set_page_config(page_title="SharpWR Damage Lab V5", page_icon="⚔️", layout="wide")
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

def sim(n,l,hp0,arm,mr,it,db,mist,bonus_hp,dist,base_mana,spell,energized,ult,execs,item_proc=True):
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
        dmg=phy*rm(ea)+mag*rm(mr)+true; before=hp; hp-=dmg
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

champ=st.selectbox("Champion",list(C)); level=st.slider("Level",1,15,9)
mist=st.number_input("Senna Mist",0,500,40,20) if champ=="Senna" else 0
s=stats(champ,level,mist)
a,b=st.columns(2); a.metric("Automatic raw AD",f"{s['ad']:.2f}"); b.metric("Naked AS",f"{s['baseas']+s['ratio']*(s['bba']+s['lvbas']):.4f}")
if champ=="Jhin":
    conv=(s["bba"]+s["lvbas"])*.30+level*.03
    st.metric("Jhin Whisper AD (naked preview)",f"{s['ad']*(1+conv):.2f}",help="Bonus AS ×30% + Crit ×40% + Level ×3%; generic combat remains experimental.")

x,y,z=st.columns(3)
hp=x.number_input("Target HP",100,20000,2500,100); armor=y.number_input("Target Armor",0.,1000.,0.,5.); mr=z.number_input("Target MR",0.,1000.,0.,5.)
u,v,w=st.columns(3)
bonus_hp=u.number_input("Target Bonus HP",0.0,10000.0,0.0,100.0); dist=v.number_input("Attack distance",0.0,1000.0,550.0,25.0); mana=w.number_input("Champion Max Mana before item",0.0,5000.0,0.0,50.0)
with st.expander("Proc / scenario switches"):
    spell=st.checkbox("Ability cast before first AA (Spellblade ready)",True)
    energized=st.checkbox("Start with Energized/Jolt proc ready",True)
    ult=st.checkbox("Ultimate cast before combat (Fiendhunter)",True)
    execs=st.number_input("Collector previous executes",0,500,0,1)

if champ=="Jhin":
    st.warning("Jhin is excluded from V5 rankings until its 4-shot/reload model is added.")

tabs=st.tabs(["⚔️ Item Tier List","🔥 Build Lab","💰 Item Value","📚 Database"])

with tabs[0]:
    st.subheader("Item Tier List")
    st.caption("Pick the champion and target here, then every completed item is tested alone. Boots are excluded.")

    tc1,tc2=st.columns(2)
    tier_champ=tc1.selectbox("Champion",list(C),index=list(C).index(champ),key="tier_champ")
    tier_level=tc2.slider("Level",1,15,level,key="tier_level")
    tier_mist=st.number_input("Senna Mist",0,500,int(mist if tier_champ=="Senna" else 0),20,key="tier_mist") if tier_champ=="Senna" else 0

    te1,te2,te3=st.columns(3)
    tier_hp=te1.number_input("Enemy HP",100,20000,int(hp),100,key="tier_hp")
    tier_armor=te2.number_input("Enemy Armor",0.0,1000.0,float(armor),5.0,key="tier_armor")
    tier_mr=te3.number_input("Enemy MR",0.0,1000.0,float(mr),5.0,key="tier_mr")
    te4,te5,te6=st.columns(3)
    tier_bonus_hp=te4.number_input("Enemy Bonus HP",0.0,10000.0,float(bonus_hp),100.0,key="tier_bonus_hp")
    tier_dist=te5.number_input("Attack Range / Distance",0.0,1000.0,float(dist),25.0,key="tier_dist")
    tier_mana=te6.number_input("Champion Max Mana before item",0.0,5000.0,float(mana),50.0,key="tier_mana")

    st.markdown("**Scenario assumptions**")
    ts1,ts2,ts3=st.columns(3)
    tier_spell=ts1.checkbox("Spellblade ready",value=spell,key="tier_spell")
    tier_energized=ts2.checkbox("Energized proc ready",value=energized,key="tier_energized")
    tier_ult=ts3.checkbox("Ultimate cast before combat",value=ult,key="tier_ult")
    tier_execs=st.number_input("Collector previous executes",0,500,int(execs),1,key="tier_execs")

    if tier_champ=="Jhin":
        st.warning("Jhin is excluded until the 4-shot + reload model is added.")
    elif st.button("⚔️ CALCULATE ITEM TIER LIST",type="primary",use_container_width=True,key="tiercalc"):
        # Naked baseline uses the same engine with a zero-stat pseudo item.
        base_db={"No Item":(0,0,0,0,0,0,0,0,0,0,0,0,0,0)}
        base_row,_=sim(tier_champ,tier_level,tier_hp,tier_armor,tier_mr,"No Item",base_db,tier_mist,tier_bonus_hp,tier_dist,tier_mana,False,False,False,0)
        baseline=base_row[4]
        rows=[]
        for it in F:
            row,_=sim(tier_champ,tier_level,tier_hp,tier_armor,tier_mr,it,F,tier_mist,tier_bonus_hp,tier_dist,tier_mana,tier_spell,tier_energized,tier_ult,tier_execs)
            gain=(row[4]/baseline-1)*100 if baseline else 0
            rows.append([it,row[1],row[4],gain,row[2],row[3]])
        df=pd.DataFrame(rows,columns=["Item","Gold","DPS","DPS Gain %","TTK","Attacks"]).sort_values(["DPS","TTK"],ascending=[False,True]).reset_index(drop=True)
        df.insert(0,"Rank",range(1,len(df)+1))
        m1,m2,m3=st.columns(3)
        m1.metric("No-item DPS",f"{baseline:.1f}")
        m2.metric("Highest DPS",f"{df.iloc[0]['DPS']:.1f}")
        m3.metric("Top item",df.iloc[0]["Item"])
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.caption("DPS Gain % = improvement over the same champion with no item against this exact target. Item passives use the scenario switches above.")

with tabs[1]:
    st.subheader("Build Lab")

    # Legal rune loadout: 1 key + 3 runes from one primary tree + 1 from another tree.
    st.markdown("**Rune Loadout**")
    keystone=st.selectbox("Key Rune",["None"]+RUNE_TREES["Key Rune"],key="build_keystone")
    sub_trees=["Precision","Domination","Resolve","Sorcery"]
    primary_tree=st.selectbox("Primary Tree",sub_trees,key="build_primary_tree")
    pr1,pr2,pr3=st.columns(3)
    primary_1=pr1.selectbox("Primary • Slot 1",RUNE_SLOTS[primary_tree][1],key="build_primary_slot1")
    primary_2=pr2.selectbox("Primary • Slot 2",RUNE_SLOTS[primary_tree][2],key="build_primary_slot2")
    primary_3=pr3.selectbox("Primary • Slot 3",RUNE_SLOTS[primary_tree][3],key="build_primary_slot3")
    secondary_tree=st.selectbox("Secondary Tree",[x for x in sub_trees if x!=primary_tree],key="build_secondary_tree")
    secondary_options=sum((RUNE_SLOTS[secondary_tree][slot] for slot in (1,2,3)),[])
    secondary_rune=st.selectbox("Secondary Rune",secondary_options,key="build_secondary_rune")
    selected_sub_runes=[primary_1,primary_2,primary_3,secondary_rune]
    combat_rune=next((r for r in selected_sub_runes if r in {"Cut Down","Coup de Grace","Brutal","Legend: Alacrity"}),"None")
    # Progression controls are generated for every selected rune that needs persistent state.
    selected_runes=[keystone]+selected_sub_runes
    dark_harvest_souls=st.number_input("Dark Harvest souls",0,500,0,1,key="dh_souls") if "Dark Harvest" in selected_runes else 0
    alacrity_full=st.checkbox("Legend: Alacrity — full progression (+21% AS total)",value=False,key="alacrity_full") if "Legend: Alacrity" in selected_runes else False
    haste_full=st.checkbox("Legend: Haste — full progression (+15 Ability Haste)",value=False,key="haste_full") if "Legend: Haste" in selected_runes else False
    bloodline_full=st.checkbox("Legend: Bloodline — full progression (+8% Omnivamp total)",value=False,key="bloodline_full") if "Legend: Bloodline" in selected_runes else False
    st.caption(f"Loadout: {keystone} • {primary_tree}: {primary_1} / {primary_2} / {primary_3} • {secondary_tree}: {secondary_rune}")
    st.caption("Primary: one rune from each of its 3 slots. Secondary: one rune from a different tree.")
    st.caption("Exactly 5 different completed items + 1 required Boots slot.")
    # Premium clickable item picker.
    if "build_items_v2" not in st.session_state:
        st.session_state.build_items_v2=list(F)[:5]

    picked=st.query_params.get("item_pick")
    if picked:
        picked=urllib.parse.unquote(picked)
        cur=list(st.session_state.build_items_v2)
        if picked in F:
            st.session_state.preview_item=picked
            if picked not in cur and len(cur)<5:
                cur.append(picked)
                st.session_state.build_items_v2=cur
        st.query_params.clear()
        st.rerun()

    st.markdown("**Selected Build**")
    build=list(st.session_state.build_items_v2)
    slot_cols=st.columns(5)
    for _i in range(5):
        if _i<len(build):
            _it=build[_i]; _url=item_icon(_it)
            if _url: slot_cols[_i].image(_url,width=58)
            slot_cols[_i].caption(_it)
            if slot_cols[_i].button("Remove",key=f"remove_item_{_i}",use_container_width=True):
                build.pop(_i); st.session_state.build_items_v2=build; st.rerun()
        else:
            slot_cols[_i].markdown("### ＋")
            slot_cols[_i].caption("Empty slot")

    st.markdown("**Items**")
    _premium_item_grid(list(F),build)
    st.markdown("**Boots**")
    if "build_boot_v2" not in st.session_state:
        st.session_state.build_boot_v2=list(B)[0]
    boot_cols=st.columns(7)
    for _i,_name in enumerate(B):
        _col=boot_cols[_i%7]
        _icon=boot_icon(_name)
        if _icon: _col.image(_icon,width=56)
        _q=dct(B[_name])
        _parts=[f"{int(_q['gold'])}g"]
        for _key,_label in STAT_LABELS:
            _v=_q.get(_key,0)
            if not _v: continue
            _parts.append(f"{_label} +{_v*100:g}%" if _key in ("as","crit","lifesteal","pctpen","ms") else f"{_label} +{_v:g}")
        if _col.button("✓" if st.session_state.build_boot_v2==_name else "＋",key=f"pick_boot_{_i}",
                       help="Select / preview "+_name+" • "+" • ".join(_parts),use_container_width=True,
                       disabled=False):
            st.session_state.build_boot_v2=_name
            st.session_state.preview_boot=_name
            st.rerun()
    boot=st.session_state.build_boot_v2
    _bq=dct(B[boot]); _bicon=boot_icon(boot)
    _brows=[]
    for _key,_label in STAT_NAMES.items():
        _v=_bq.get(_key,0)
        if not _v: continue
        _val=f"{_v*100:g}%" if _key in ("as","crit","lifesteal","pctpen","ms") else f"{_v:g}"
        _brows.append(f'<div class="wr-stat"><span class="wr-stat-i">{STAT_GLYPHS[_key]}</span><span><b>{_val}</b><span class="wr-stat-name">{_label}</span></span></div>')
    _bcard=f"""<div class="wr-card"><div class="wr-card-head"><img src="{html.escape(_bicon)}"><div>
      <div class="wr-card-name">{html.escape(boot)}</div><div class="wr-card-gold">◆ {int(_bq['gold'])} Gold</div>
      </div></div><div class="wr-stats">{''.join(_brows)}</div></div>"""
    st.markdown(_bcard,unsafe_allow_html=True)

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
        s0=stats(champ,level,mist); maxmana=mana+total["mana"]
        awe=.02*maxmana if ("Manamune" in build or "Muramana" in build) else 0
        ad=s0["ad"]+total["ad"]+awe
        # Persistent rune progression only; combat stacks always start at zero.
        rune_bonus_ad=0.0
        rune_bonus_as=(.21 if alacrity_full else .03) if "Legend: Alacrity" in selected_sub_runes else 0.0
        rune_bonus_ah=15.0 if ("Legend: Haste" in selected_sub_runes and haste_full) else 0.0
        rune_omnivamp=(.08 if bloodline_full else .01) if "Legend: Bloodline" in selected_sub_runes else 0.0
        crit=min(1,total["crit"]+(mist//20*.10 if champ=="Senna" else 0)+yt_bonus_crit)
        cd=2.3 if "Infinity Edge" in build else 2.0
        if champ=="Senna": cd*=.9
        display_dyn=.35 if ("Yun Tal Wildarrows" in build and yt_flurry) else 0
        display_as=min(3,s0["baseas"]+s0["ratio"]*(s0["bba"]+s0["lvbas"]+total["as"]+display_dyn+rune_bonus_as))
        hp2=float(hp); t=0.; attacks=0; pd_stacks=rb=dark=0; rage_hits=0; fh=3 if ("Fiendhunter Bolts" in build and ult) else 0
        conq_stacks=0; lt_stacks=0; empowerment_hits=0; empowerment_active=False; brutal_cd_ready=0.0
        while hp2>0 and attacks<500:
            attacks+=1
            dyn=(.06*pd_stacks if "Phantom Dancer" in build else 0)+(.08*rb if "Guinsoo's Rageblade" in build else 0)
            if "Yun Tal Wildarrows" in build and yt_flurry: dyn+=.35
            if "Fiendhunter Bolts" in build and fh and t<=8: dyn+=.50
            current_ad=ad+(conq_stacks*(3+(level-1)/14*2) if keystone=="Conqueror" else 0)
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

            # Rune effects read the live state before this hit.
            hp_pct=hp2/hp if hp else 0
            bonus_ad=max(0,current_ad-s0["ad"])
            if keystone=="First Strike":
                dmg*=1.07
            elif keystone=="Empowerment":
                if empowerment_hits==2: dmg+=40+(level-1)/14*125
                if empowerment_active: dmg*=1.08
            elif keystone=="Dark Harvest" and hp_pct<.50:
                dmg+=35+11*dark_harvest_souls+.10*bonus_ad+.05*total["ap"]
                # One proc in this single-target fight; 20s cooldown is longer than typical test.
                dark_harvest_souls=-999999
            elif keystone=="Arcane Comet" and attacks==1:
                dmg+=15+(level-1)/14*85+.10*bonus_ad+.05*total["ap"]
            elif keystone=="Aery" and attacks==1:
                dmg+=15+(level-1)/14*55+.10*bonus_ad+.05*total["ap"]
            elif keystone=="Grasp of the Undying" and attacks==1:
                dmg+=.033*hp*.40
            elif keystone=="Lethal Tempo" and lt_stacks>=6:
                base_lt=6+(level-1)/14*14
                bonus_as_pct=(total["as"]+rune_bonus_as+.048*lt_stacks)*100
                dmg+=base_lt*(1+.0033*bonus_as_pct)
            if "Cut Down" in selected_sub_runes and hp_pct>.60: dmg*=1.065
            if "Coup de Grace" in selected_sub_runes and hp_pct<.40: dmg*=1.08
            if "Brutal" in selected_sub_runes:
                # Verified tooltip: every champion attack deals 6 + 8% bonus AD adaptive damage.
                # Current ADC lab resolves adaptive damage as physical when AD is the adaptive stat.
                dmg+=(6+.08*bonus_ad)*rm(ea)
            if boot=="Immortal Treads" and immortal_above_half: dmg*=1.05
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
        counts={tree:len(names) for tree,names in RUNE_TREES.items()}
        st.caption(" • ".join(f"{tree}: {count}" for tree,count in counts.items())+" • Total: 51")
    else:
        DB=F if dbpick=="Completed items" else P if dbpick=="Components" else B
        rows=[]
        for n,v0 in DB.items():
            q=dct(v0); rows.append([n,q["gold"],q["ad"],q["as"]*100,q["crit"]*100,q["ap"],q["hp"],q["mana"],q["armor"],q["mr"],q["ah"],q["ls"]*100,q["flatpen"],q["pctpen"]*100,q["ms"]])
        st.dataframe(pd.DataFrame(rows,columns=["Item","Gold","AD","AS%","Crit%","AP","HP","Mana","Armor","MR","AH","LS%","Flat Pen","Armor Pen%","MS"]),use_container_width=True,hide_index=True)

st.divider()
st.caption("Web V5.7.3 | Fixed edge & stat layout • 51-rune database • Item Tier List • Build Lab: 5 items + 1 Boots • Item Value • 23 components • 14 Boots | Jhin rankings disabled pending 4-shot/reload modeling.")
