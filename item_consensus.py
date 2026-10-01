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
