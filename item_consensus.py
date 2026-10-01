"""Equal-target item coverage from completed champion build searches."""
from collections import defaultdict

def consensus(searches):
    scores=defaultdict(float);coverage=defaultdict(set)
    for target,search in searches.items():
        per=defaultdict(float)
        for rank,row in enumerate(search['full'],1):
            for item in row['Items']:per[item]+=1/rank
        for item,value in per.items():
            scores[item]+=value/(1+1/2+1/3);coverage[item].add(target)
    n=len(searches)
    return [{'Item':i,'Target coverage':len(coverage[i]),'Targets tested':n,'Top-3 score':round(100*v/max(1,n),2)} for i,v in sorted(scores.items(),key=lambda x:(-len(coverage[x[0]]),-x[1],x[0]))]

def adopters(history):
    found=defaultdict(set);targets=defaultdict(int)
    for champion,searches in history.items():
        for row in consensus(searches):
            found[row['Item']].add(champion);targets[row['Item']]+=row['Target coverage']
    return [{'Item':item,'Champions':len(names),'Champion names':', '.join(sorted(names)),'Target appearances':targets[item]} for item,names in sorted(found.items(),key=lambda x:(-len(x[1]),-targets[x[0]],x[0]))]

NOTES={"Lord Dominik's Regards":"Tank answer · armor penetration and bonus-health damage",'The Collector':'Squishy finisher · flat penetration and execute','Muramana':'Mana scaling · attacks and damaging casts trigger Shock','Yun Tal Wildarrows':'Scaling crit · value depends on permanent stacks','Infinity Edge':'Crit damage payoff · pair with crit chance',"Guinsoo's Rageblade":'On-hit synergy · benefits from repeated attacks','Kraken Slayer':'Repeated-hit damage · sustained fights','Phantom Dancer':'Attack-speed ramp · check the champion AS cap',"Blade of the Ruined King":'Current-health on-hit · high-HP targets','Galeforce':'Active burst · contributes independently of attacks',"Mortal Reminder":'Armor penetration + anti-heal · healing is not simulated',"Serylda's Grudge":'Armor penetration · ability-oriented utility'}

def champion_items(search):
    scores=defaultdict(float)
    for rank,row in enumerate(search['full'],1):
        for item in row['Items']:scores[item]+=5/rank
    for stage,rows in search['stages'].items():
        for rank,row in enumerate(rows,1):
            for item in row['Items']:scores[item]+=1/(rank*int(stage))
    return [{'Item':i,'Score':round(v,3),'Note':NOTES.get(i,'Kit-dependent value · compare the tested builds')} for i,v in sorted(scores.items(),key=lambda x:(-x[1],x[0]))[:10]]

def progression_ranking(results,pool):
    scores=defaultdict(float);champions=defaultdict(set);appearances=defaultdict(int)
    for champion,cells in results.items():
        for cell in cells.values():
            rows=cell['builds'];normal=sum(1/r for r in range(1,len(rows)+1));seen=set()
            for rank,row in enumerate(rows,1):
                for item in row['Items']:
                    scores[item]+=1/rank/max(1,normal)/cell['item_count']/len(cells)/len(results)
                    champions[item].add(champion);seen.add(item)
            for item in seen:appearances[item]+=1
    return [{'Item':i,'Stage-balanced score':round(100*scores[i],4),'Champions':len(champions[i]),'Champion names':', '.join(sorted(champions[i])),'Level-target appearances':appearances[i]} for i in sorted(pool,key=lambda i:(-scores[i],-len(champions[i]),i))]
