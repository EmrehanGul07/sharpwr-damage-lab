
import streamlit as st, math, pandas as pd
st.set_page_config(page_title="SharpWR Calculator v2", page_icon="⚔️", layout="wide")
st.title("⚔️ SharpWR Damage Lab")

# baseAD, AD/lvl, AS ratio, baseAS, base bonus AS, AS/lvl
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
I={
"Stormrazor":(3000,50,.20,.25),"Blade of the Ruined King":(3100,40,.30,0),
"Bloodthirster":(3200,75,0,0),"Infinity Edge":(3400,75,0,.25),
"The Collector":(3000,50,0,.25),"Essence Reaver":(3000,50,0,.25),
"Kraken Slayer":(2900,45,.35,0),"Yun Tal Wildarrows":(3100,50,.25,0),
"Hexoptics C44":(2900,55,0,.25)}
ERI={"Ezreal":2,"Lucian":3,"Vayne":4,"Kai'Sa":5,"Xayah":8}

def gu(l):
    n=l-1
    return n*(.7025+.0175*n)
def stats(n,l,mist=0):
    ba,g,r,b,bba,asg=C[n]; u=gu(l)
    ad=ba+g*u+(mist*1.25 if n=="Senna" else 0)
    return dict(basead=ba,ad=ad,ratio=r,baseas=b,bba=bba,asg=asg,lvbas=asg*u)
def rm(x): return 100/(100+max(0,x))
def sim(n,l,hp0,arm,mr,it,mist):
    s=stats(n,l,mist); gold,iad,ias,ic=I[it]
    ad=s["ad"]+10+iad; hp=float(hp0); t=0.; k=0; yt=0.; buff=-1.; er=0.; log=[]
    while hp>0 and k<500:
        k+=1
        steroid=.25 if it=="Yun Tal Wildarrows" and t<buff else 0
        asp=min(3,s["baseas"]+s["ratio"]*(s["bba"]+s["lvbas"]+.25+ias+steroid))
        crit=ic+(mist//20*.10 if n=="Senna" else 0)
        if it=="Yun Tal Wildarrows": crit=yt+(mist//20*.10 if n=="Senna" else 0)
        crit=min(1,crit); cd=2.3 if it=="Infinity Edge" else 2
        if n=="Senna": cd*=.9
        phy=ad*(1+crit*(cd-1)); mag=0; note=[]
        if it=="Hexoptics C44": phy*=1.10; note+=["C44"]
        if it=="Stormrazor" and k%6==0: mag+=120; note+=["Storm"]
        if it=="Blade of the Ruined King": phy+=max(15,.07*hp); note+=["BotRK"]
        if it=="Kraken Slayer" and k%3==0:
            base=120+(l-1)/14*48; miss=(hp0-hp)/hp0
            phy+=base*(1+min(.75,.75*miss)); note+=["Kraken"]
        if it=="Essence Reaver" and t+1e-9>=er:
            iv=ERI.get(n,10); phy+=1.35*s["ad"]+20; er=t+iv; note+=["ER"]
        dmg=phy*rm(arm)+mag*rm(mr); before=hp; hp-=dmg
        if it=="The Collector" and 0<hp<=hp0*.05: hp=0; note+=["Execute"]
        if it=="Yun Tal Wildarrows":
            if k==1: buff=t+6; note+=["YT steroid"]
            yt=min(.25,yt+.002)
        log.append([k,round(t,3),round(asp,4),round(crit*100,2),round(before,1),round(dmg,1),round(max(hp,0),1),", ".join(note)])
        if hp<=0: break
        t+=1/asp
    return [it,gold,round(t,3),k,round(hp0/t,1) if t else float("inf")],log

champ=st.selectbox("Champion",list(C))
level=st.slider("Level",1,15,9)
mist=st.number_input("Senna Mist",0,500,40,20) if champ=="Senna" else 0
s=stats(champ,level,mist)
a,b=st.columns(2)
a.metric("Automatic raw AD",f"{s['ad']:.2f}")
b.metric("Naked AS",f"{s['baseas']+s['ratio']*(s['bba']+s['lvbas']):.4f}")
if champ=="Jhin":
    # Patch 7.3 Whisper conversion ratio supplied/verified for this project:
    # bonus AS * 30% + crit rate * 40% + level * 3%.
    # Naked preview uses champion innate bonus AS and 0% item crit.
    jhin_bonus_as = s["bba"] + s["lvbas"]
    jhin_conversion = jhin_bonus_as*0.30 + 0.0*0.40 + level*0.03
    jhin_display_ad = s["ad"] * (1 + jhin_conversion)
    st.metric("Jhin Whisper AD (naked preview)", f"{jhin_display_ad:.2f}",
              help="v3 formula: Bonus AS × 30% + Crit Rate × 40% + Level × 3%. Item-specific Jhin combat modeling is still marked experimental.")
with st.expander("Master stats"): st.write({"Base AD":s["basead"],"AD/Lvl":C[champ][1],"AS Ratio":s["ratio"],"Base AS":s["baseas"],"Base Bonus AS":s["bba"],"AS/Lvl":s["asg"]})
x,y,z=st.columns(3); hp=x.number_input("Target HP",100,20000,2500,100); armor=y.number_input("Armor",0.,1000.,0.,5.); mr=z.number_input("MR",0.,1000.,0.,5.)
items=st.multiselect("Items",list(I),default=list(I))
if st.button("⚔️ CALCULATE",type="primary",use_container_width=True):
    rows=[]; logs={}
    for it in items:
        row,lg=sim(champ,level,hp,armor,mr,it,mist); rows.append(row); logs[it]=lg
    df=pd.DataFrame(rows,columns=["Item","Gold","TTK","Attacks","Avg DPS"]).sort_values(["TTK","Attacks"]).reset_index(drop=True)
    df.insert(0,"Rank",range(1,len(df)+1)); st.dataframe(df,use_container_width=True,hide_index=True)
    if len(df): st.success(f"Fastest: {df.iloc[0]['Item']} — {df.iloc[0]['TTK']}s")
    pick=st.selectbox("Attack log",df["Item"].tolist())
    st.dataframe(pd.DataFrame(logs[pick],columns=["AA","Time","AS","Crit %","HP before","Damage","HP after","Proc"]),use_container_width=True,hide_index=True)
    st.download_button("CSV indir",df.to_csv(index=False).encode(),"sharpwr_v2_results.csv","text/csv")
st.divider()
st.caption("Web v4 |  Jhin Whisper conversion = Bonus AS × 30% + Crit Rate × 40% + Level × 3%. |  Lv1–15 AD/AS automatic scaling. Xayah AS/Lvl .034; Yunara 58 + 3 AD/Lvl. Jhin/Zeri special mechanics are not authoritative in generic AA mode. C44 assumes max +10%. Yun Tal starts at 0 item crit.")
