import streamlit as st
import pandas as pd

st.set_page_config(page_title="SharpWR Damage Lab V5", page_icon="⚔️", layout="wide")
st.title("⚔️ SharpWR Damage Lab — V5")
st.caption("Patch 7.3 • Full items + components • single-target ADC auto-attack lab")

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
"Caitlyn":(60,4.2,.625,.625,.28,.040),"Jinx":(58,4,.625,.625,.30,.020),
"Ezreal":(60,4.5,.625,.625,.28,.022),"Zeri":(58,4,.625,.625,.28,.024),
"Jhin":(60,5,.625,.625,.06,.032),"Sivir":(60,4,.625,.625,.30,.010),
"Senna":(50,0,.400,.400,.60,.050)}

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
"Yun Tal Wildarrows":(3100,50,.25,0,0,0,0,0,0,0,0,0,0,0),
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
"Spellslinger's Shoes":(2200,0,0,0,35,0,0,0,0,0,0,0,0,45),
"Boots of Dynamism":(1200,15,0,0,0,0,0,0,0,0,0,10,0,45),
"Armorcrusher Boots":(2200,20,0,0,0,0,0,0,0,0,0,10,.06,45)}
K=["gold","ad","as","crit","ap","hp","mana","armor","mr","ah","ls","flatpen","pctpen","ms"]
def dct(v): return dict(zip(K,v))
def gu(l):
    n=l-1
    return n*(.7025+.0175*n)
def stats(n,l,mist=0):
    ba,g,r,b,bba,asg=C[n]; u=gu(l)
    return {"basead":ba,"ad":ba+g*u+(mist*1.25 if n=="Senna" else 0),
            "ratio":r,"baseas":b,"bba":bba,"lvbas":asg*u}
def rm(x): return 100/(100+max(0,x))

def sim(n,l,hp0,arm,mr,it,db,mist,bonus_hp,dist,base_mana,spell,energized,ult,execs):
    s=stats(n,l,mist); q=dct(db[it]); mana=base_mana+q["mana"]
    awe=.02*mana if it in ("Manamune","Muramana") else 0
    ad=s["ad"]+q["ad"]+awe
    hp=float(hp0); t=0.; k=0; log=[]
    pd_stacks=rb=light=dark=0; ytcrit=0.; yt_until=-1.; yt_cd=0.
    fh=3 if it=="Fiendhunter Bolts" and ult else 0
    while hp>0 and k<500:
        k+=1
        dyn=(.06*pd_stacks if it=="Phantom Dancer" else 0)+(.08*rb if it=="Guinsoo's Rageblade" else 0)
        if it=="Yun Tal Wildarrows" and t<yt_until: dyn+=.25
        if it=="Fiendhunter Bolts" and fh and t<=8: dyn+=.50
        asp=min(3,s["baseas"]+s["ratio"]*(s["bba"]+s["lvbas"]+q["as"]+dyn))
        crit=q["crit"]+(mist//20*.10 if n=="Senna" else 0)+(ytcrit if it=="Yun Tal Wildarrows" else 0)
        crit=min(1,crit); cd=2.3 if it=="Infinity Edge" else 2.
        if n=="Senna": cd*=.9
        pct=q["pctpen"]+(.10*dark if it=="Terminus" else 0)
        if it=="Terminus": pct=min(.40,pct)
        ea=max(0,arm*(1-pct)-q["flatpen"])
        true=0.; mag=0.; onp=0.; onm=0.; note=[]
        if it=="Fiendhunter Bolts" and fh and t<=8:
            phy=ad*(cd*.80); true=ad*.15*crit; note.append("Opening Barrage")
        else: phy=ad*(1+crit*(cd-1))
        if it=="Hexoptics C44":
            amp=max(0,min(.10,.10*dist/550)); phy*=1+amp; true*=1+amp; note.append(f"C44 {amp*100:.1f}%")
        if it=="Wit's End": onm+=40
        if it=="Nashor's Tooth": onm+=15+.20*q["ap"]
        if it=="Guinsoo's Rageblade": onm+=30
        if it=="Terminus": onm+=30
        if it=="Recurve Bow": onp+=15
        if it=="Blade of the Ruined King": onp+=max(15,.07*hp)
        if it=="Muramana": onp+=.015*mana
        if it=="Kraken Slayer" and k%3==0:
            base=120+(l-1)/14*48; miss=(hp0-hp)/hp0
            onp+=base*(1+min(.75,.75*miss)); note.append("Kraken")
        if it=="Duskblade of Draktharr" and k==1:
            onp+=60+(l-1)/14*100; note.append("Nightstalker")
        if energized and k==1:
            if it=="Rapid Firecannon": onm+=80; note.append("RFC")
            if it=="Stormrazor": onm+=120; note.append("Storm")
            if it=="Statikk Shiv": onm+=60; note.append("Shiv")
            if it=="Kircheis Shard": onm+=40; note.append("Jolt")
        if spell and k==1:
            if it=="Essence Reaver": onp+=1.35*s["basead"]+min(80,.8*crit*100); note.append("ER")
            if it=="Trinity Force": onp+=2*s["basead"]; note.append("Trinity")
            if it=="Iceborn Gauntlet": onp+=s["basead"]+.25*q["armor"]; note.append("Iceborn")
            if it=="Sheen": onp+=s["basead"]; note.append("Sheen")
        if it=="Guinsoo's Rageblade" and rb>=4 and k%3==0:
            onp*=2; onm*=2; note.append("Double on-hit")
        phy+=onp; mag+=onm
        if it=="Lord Dominik's Regards":
            amp=min(.12,.12*max(0,bonus_hp)/1200); phy*=1+amp; mag*=1+amp; true*=1+amp
        dmg=phy*rm(ea)+mag*rm(mr)+true; before=hp; hp-=dmg
        if it=="The Collector":
            th=min(1,.05+.001*execs)
            if 0<hp<=hp0*th: hp=0; note.append(f"Execute {th*100:.1f}%")
        if it=="Phantom Dancer": pd_stacks=min(5,pd_stacks+1)
        if it=="Guinsoo's Rageblade": rb=min(4,rb+1)
        if it=="Terminus":
            if k%2: light=min(3,light+1)
            else: dark=min(3,dark+1)
        if it=="Yun Tal Wildarrows":
            ytcrit=min(.25,ytcrit+.002)
            if yt_cd<=t: yt_until=t+6; yt_cd=t+20; note.append("Flurry")
        if it=="Fiendhunter Bolts" and fh and t<=8: fh-=1
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
    st.caption("Exactly 5 different completed items + 1 required Boots slot.")
    cols=st.columns(5)
    build=[cols[i].selectbox(f"Item {i+1}",list(F),index=i,key=f"bi{i}") for i in range(5)]
    boot=st.selectbox("Boots (required)",list(B))
    if len(set(build))<5:
        st.error("Choose 5 different completed items.")
    elif champ!="Jhin" and st.button("Calculate build",type="primary",use_container_width=True):
        qs=[dct(F[x]) for x in build]; qb=dct(B[boot])
        total={k:sum(q[k] for q in qs)+qb[k] for k in K}
        s0=stats(champ,level,mist); maxmana=mana+total["mana"]
        awe=.02*maxmana if ("Manamune" in build or "Muramana" in build) else 0
        ad=s0["ad"]+total["ad"]+awe
        crit=min(1,total["crit"]+(mist//20*.10 if champ=="Senna" else 0))
        cd=2.3 if "Infinity Edge" in build else 2.0
        if champ=="Senna": cd*=.9
        hp2=float(hp); t=0.; attacks=0; pd_stacks=rb=dark=0; ytcrit=0.; yt_until=-1.; fh=3 if ("Fiendhunter Bolts" in build and ult) else 0
        while hp2>0 and attacks<500:
            attacks+=1
            dyn=(.06*pd_stacks if "Phantom Dancer" in build else 0)+(.08*rb if "Guinsoo's Rageblade" in build else 0)
            if "Yun Tal Wildarrows" in build and t<yt_until: dyn+=.25
            if "Fiendhunter Bolts" in build and fh and t<=8: dyn+=.50
            asp=min(3,s0["baseas"]+s0["ratio"]*(s0["bba"]+s0["lvbas"]+total["as"]+dyn))
            cc=min(1,crit+(ytcrit if "Yun Tal Wildarrows" in build else 0))
            pct=total["pctpen"]+(.10*dark if "Terminus" in build else 0)
            if "Terminus" in build: pct=min(.40,pct)
            ea=max(0,armor*(1-pct)-total["flatpen"])
            true=0.; mag=0.; onp=0.
            if "Fiendhunter Bolts" in build and fh and t<=8:
                phy=ad*(cd*.80); true=ad*.15*cc
            else: phy=ad*(1+cc*(cd-1))
            if "Hexoptics C44" in build:
                amp=max(0,min(.10,.10*dist/550)); phy*=1+amp; true*=1+amp
            if "Wit's End" in build: mag+=40
            if "Nashor's Tooth" in build: mag+=15+.20*total["ap"]
            if "Guinsoo's Rageblade" in build: mag+=30
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
            if "Guinsoo's Rageblade" in build and rb>=4 and attacks%3==0:
                onp*=2; mag*=2
            phy+=onp
            if "Lord Dominik's Regards" in build:
                amp=min(.12,.12*max(0,bonus_hp)/1200); phy*=1+amp; mag*=1+amp; true*=1+amp
            dmg=phy*rm(ea)+mag*rm(mr)+true; hp2-=dmg
            if "The Collector" in build:
                th=min(1,.05+.001*execs)
                if 0<hp2<=hp*th: hp2=0
            if "Phantom Dancer" in build: pd_stacks=min(5,pd_stacks+1)
            if "Guinsoo's Rageblade" in build: rb=min(4,rb+1)
            if "Terminus" in build and attacks%2==0: dark=min(3,dark+1)
            if "Yun Tal Wildarrows" in build:
                ytcrit=min(.25,ytcrit+.002)
                if attacks==1: yt_until=t+6
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
        max_hit=hit_phy*rm(max_ea)+hit_mag*rm(mr)+hit_true

        a1,a2,a3,a4,a5,a6=st.columns(6)
        a1.metric("Build Cost",f"{cost:,}g"); a2.metric("Total AD",f"{ad:.1f}"); a3.metric("Crit",f"{crit*100:.0f}%")
        a4.metric("TTK",f"{t:.3f}s"); a5.metric("Avg DPS",f"{hp/t:.1f}" if t else "∞"); a6.metric("Max Single Hit",f"{max_hit:.1f}")
        st.write("**Build:** "+" • ".join(build)+f" • **{boot}**")
        with st.expander("Max Single Hit breakdown"):
            st.caption("Highest one basic attack when a crit is possible. Ready Spellblade, Energized and first-hit effects use the scenario switches. Kraken 3rd-hit and pre-stacked Terminus/Rageblade are not assumed.")
            br=[]
            for pn,pt,pv in parts:
                dealt=pv*rm(max_ea) if pt=="Physical" else pv*rm(mr) if pt=="Magic" else pv
                br.append([pn,pt,round(pv,1),round(dealt,1)])
            st.table(pd.DataFrame(br,columns=["Source","Type","Raw Damage","Damage After Resist"]))
            st.metric("Total Max Single Hit",f"{max_hit:.1f}")

with tabs[2]:
    st.subheader("Item Value")
    st.caption("Raw Gold Efficiency uses only directly priced base components. DPS/1000g is shown separately.")
    rates={"ad":500/12,"as":400/.12,"crit":500/.10,"ap":500/20,"hp":500/150,"armor":500/20,"mr":500/20,"ah":300/5}
    if champ!="Jhin":
        rows=[]
        for it,v0 in F.items():
            q=dct(v0); raw=sum(q[k]*rates[k] for k in rates)
            row,_=sim(champ,level,hp,armor,mr,it,F,mist,bonus_hp,dist,mana,spell,energized,ult,execs)
            dps=row[4]; rows.append([it,q["gold"],round(raw),round(raw/q["gold"]*100,1),dps,round(dps/q["gold"]*1000,1)])
        val=pd.DataFrame(rows,columns=["Item","Cost","Priced Raw Stats","Raw Gold Efficiency %","DPS","DPS / 1000g"]).sort_values("DPS / 1000g",ascending=False).reset_index(drop=True)
        val.insert(0,"Rank",range(1,len(val)+1)); st.dataframe(val,use_container_width=True,hide_index=True)
        st.info("Unpriced stats/passives are excluded from Raw Gold Efficiency rather than assigned invented prices.")

with tabs[3]:
    st.subheader("Database")
    dbpick=st.radio("Show",["Completed items","Components","Boots"],horizontal=True)
    DB=F if dbpick=="Completed items" else P if dbpick=="Components" else B
    rows=[]
    for n,v0 in DB.items():
        q=dct(v0); rows.append([n,q["gold"],q["ad"],q["as"]*100,q["crit"]*100,q["ap"],q["hp"],q["mana"],q["armor"],q["mr"],q["ah"],q["ls"]*100,q["flatpen"],q["pctpen"]*100,q["ms"]])
    st.dataframe(pd.DataFrame(rows,columns=["Item","Gold","AD","AS%","Crit%","AP","HP","Mana","Armor","MR","AH","LS%","Flat Pen","Armor Pen%","MS"]),use_container_width=True,hide_index=True)

st.divider()
st.caption("Web V5.1 | Item Tier List • Build Lab: 5 items + 1 Boots • Item Value • 23 components • 14 Boots | Jhin rankings disabled pending 4-shot/reload modeling.")
