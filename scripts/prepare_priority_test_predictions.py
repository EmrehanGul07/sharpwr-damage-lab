"""Export testable current-engine hypotheses, never mark them as game measurements.

Run from repository root. Optional --ad/--ap replace the hypothetical database
stats with the user's displayed stats for all AA samples. Runes are excluded:
record the practice tool's fixed runes rather than requiring a different page.
"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT)]
from sharpwr import engine_namespace
from sharpwr.marksman_damage_components import damage_component,xayah_feather_multiplier


def predictions(ad=None,ap=None,armor=100,mr=100,hp=10000):
    ns=engine_namespace();champ='Ezreal';level=15
    def sequence(items,distance=550,count=18,health_fraction=1):
        kernel=ns['combat_hits'](champ,level,hp,armor,mr,items,ns['F'],dist=distance,active_ready=False)
        next(kernel);out=[]
        native_ad=ns['stats'](champ,level)['ad']+sum(ns['dct'](ns['F'][x])['ad'] for x in items)
        for i in range(count):
            state={'hp':hp*health_fraction,'time':i,'crit':0.,'event_driven':True,'distance':distance}
            if ad is not None:state['bonus_ad']=ad-native_ad
            h=kernel.send(state)
            out.append({'AA':i+1,'AD':h['ad'],'physical_after_armor':h['physical']*ns['rm'](h['armor']),'magic_after_MR':h['magic']*ns['rm'](h['mr']),'damage':h['damage'],'AS_before_hit':h['as'],'armor_before_hit':h['armor'],'MR_before_hit':h['mr'],'rage_after_hit':h['rage'],'light_after_hit':h['light'],'dark_after_hit':h['dark'],'kraken_counter_after_hit':h['kraken'],'effects':h['notes']})
        return out
    distances=(0,99,100,149,150,199,200,499,500,549,550,600)
    hex_rows=[]
    for d in distances:
        h=sequence(['Hexoptics C44'],d,1)[0]
        hex_rows.append({'distance':d,'model_amplification':0 if d<100 else min(.1,(int((d-100)//50)+1)*.01),**h})
    combinations=[['Kraken Slayer'],["Guinsoo's Rageblade"],['Terminus'],["Guinsoo's Rageblade",'Kraken Slayer'],["Guinsoo's Rageblade",'Terminus'],["Guinsoo's Rageblade",'Kraken Slayer','Terminus']]
    combos={' + '.join(items):sequence(items) for items in combinations}
    fractions={str(f):sequence(['Kraken Slayer'],count=3,health_fraction=f)[2] for f in (1,.5,.25)}
    # Per-feather damage intentionally normalized: measured bonus AD / crit differ
    # between setups. Compare E(3)/E(1), not raw values across different builds.
    feathers=[{'hits':n,'multiplier_of_single_feather':xayah_feather_multiplier(n)} for n in (1,2,3,5,7,10,12)]
    return {'status':'current_engine_hypotheses_NOT_in_game_verified','version':'5.61.0','setup':{'champion':champ,'level':level,'target_hp':hp,'armor':armor,'MR':mr,'crit_override_for_samples':0,'AD_override':ad,'AP_override':ap,'runes':'excluded; game comparison must record fixed runes','health_mode':'frozen pre-hit HP for isolated counter tests; not a kill-time simulation','time_mode':'one-second sample spacing; not an AS/DPS measurement','range_mode':'synthetic exact distances; game distances may not be measurable'},'hexoptics':hex_rows,'AA_combinations':combos,'kraken_missing_health':fractions,'xayah_recall':feathers,'unverified':['Hexoptics ability/passive/on-hit/true damage applicability and actual breakpoints','Rageblade phantom counting towards Kraken and Terminus','Terminus stack grant ordering / light versus dark first','Xayah lateral and fan feather collision geometry']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--ad',type=float);p.add_argument('--ap',type=float);p.add_argument('--armor',type=float,default=100);p.add_argument('--mr',type=float,default=100);p.add_argument('--hp',type=float,default=10000);p.add_argument('--output',default=str(ROOT/'data/priority-test-predictions.json'));args=p.parse_args()
    # AP is accepted for metadata only: these three items have no AP scaling.
    result=predictions(args.ad,args.ap,args.armor,args.mr,args.hp)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(f'Prepared hypotheses: {args.output}')
if __name__=='__main__':main()
