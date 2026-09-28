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
"Brawler's Gloves":(500,0,0,.10,0,0,0,0,0,0,0,0,0,0)}

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
    pd=rb=light=dark=0; ytcrit=0.; yt_until=-1.; yt_cd=0.
    fh=3 if it=="Fiendhunter Bolts" and ult else 0
    while hp>0 and k<500:
        k+=1
        dyn=(.06*pd if it=="Phantom Dancer" else 0)+(.08*rb if it=="Guinsoo's Rageblade" else 0)
        if it=="Yun Tal Wildarrows" and t<yt_until: dyn+=.25
        if it=="Fiendhunter Bolts" and fh and t<=8: dyn+=.50
        asp=min(3,s["baseas"]+s["ratio"]*(s["bba"]+s["lvbas"]+.25+q["as"]+dyn))
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
        if it=="Phantom Dancer": pd=min(5,pd+1)
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
bonus_hp=u.number_input("Target Bonus HP",0.,10000.,0.,100); dist=v.number_input("Attack distance",0.,1000.,550.,25.); mana=w.number_input("Champion Max Mana before item",0.,5000.,0.,50.)
with st.expander("Proc / scenario switches"):
    spell=st.checkbox("Ability cast before first AA (Spellblade ready)",True)
    energized=st.checkbox("Start with Energized/Jolt proc ready",True)
    ult=st.checkbox("Ultimate cast before combat (Fiendhunter)",True)
    execs=st.number_input("Collector previous executes",0,500,0,1)

pool=st.radio("Item pool",["Full items","Components"],horizontal=True); DB=F if pool=="Full items" else P
items=st.multiselect("Items",list(DB),default=list(DB))
with st.expander("V5 item database"):
    rows=[]
    for n,v0 in DB.items():
        q=dct(v0); rows.append([n,q["gold"],q["ad"],q["as"]*100,q["crit"]*100,q["ap"],q["hp"],q["mana"],q["armor"],q["mr"],q["ah"],q["ls"]*100,q["flatpen"],q["pctpen"]*100,q["ms"]*100])
    st.dataframe(pd.DataFrame(rows,columns=["Item","Gold","AD","AS%","Crit%","AP","HP","Mana","Armor","MR","AH","LS%","Flat Pen","Armor Pen%","MS%"]),use_container_width=True,hide_index=True)

if st.button("⚔️ CALCULATE",type="primary",use_container_width=True):
    rows=[]; logs={}
    for it in items:
        row,lg=sim(champ,level,hp,armor,mr,it,DB,mist,bonus_hp,dist,mana,spell,energized,ult,execs)
        rows.append(row); logs[it]=lg
    if rows:
        df=pd.DataFrame(rows,columns=["Item","Gold","TTK","Attacks","Avg DPS"]).sort_values(["TTK","Attacks"]).reset_index(drop=True)
        df.insert(0,"Rank",range(1,len(df)+1)); st.dataframe(df,use_container_width=True,hide_index=True)
        st.success(f"Fastest: {df.iloc[0]['Item']} — {df.iloc[0]['TTK']}s")
        pick=st.selectbox("Attack log",df["Item"].tolist())
        st.dataframe(pd.DataFrame(logs[pick],columns=["AA","Time","AS","Crit%","Effective Armor","HP before","Damage","HP after","Proc"]),use_container_width=True,hide_index=True)
        st.download_button("CSV indir",df.to_csv(index=False).encode(),"sharpwr_v5_results.csv","text/csv")

st.divider()
st.caption("Web V5 | 35 completed items + Muramana transformed state + 17 components | QSS 60s | Flat and % armor penetration separated | Runaan secondary bolts excluded from single-target TTK | Utility/defensive passives stored conceptually but do not inflate offensive DPS.")
