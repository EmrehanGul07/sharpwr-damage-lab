/** FirstContact/DamageProcs from sharpwr/rune_runtime.py; same provisional ADC damage model. */
export class ArenaRunes {
  private ready: Record<string, number> = {};
  private hits = 0;
  private last = -Infinity;
  private empowered = false;
  private souls = 0;
  private first: number | null = null;
  private stacks=0;
  private until=0;
  private phase: number[]=[];
  bonusAs(time: number) { return this.keystone==='Lethal Tempo' && time<this.until ? .048*this.stacks : 0; }
  bonusAd(time: number) { return this.keystone==='Conqueror' && time<this.until ? this.stacks*(3+(this.level-1)*2/14) : 0; }
  constructor(private level: number, private keystone: string, private selected: string[]) {}
  apply(time: number, attack: boolean, fraction: number, bonusAd: number, ap: number, armorMultiplier: number) {
    const scale = (a: number, b: number) => a+(b-a)*(this.level-1)/14;
    let physical=0, trueDamage=0;
    const proc=(name: string, raw: number, cd: number, condition: boolean) => {
      if(condition && time >= (this.ready[name] || 0)) { physical += raw*armorMultiplier; this.ready[name]=time+cd; }
    };
    if(this.keystone==='Dark Harvest' && fraction<.5 && time >= (this.ready['Dark Harvest']||0)) {
      proc('Dark Harvest',35+11*this.souls+.1*bonusAd+.05*ap,20,true); this.souls++;
    }
    proc('Tyrant',scale(20,70)+.06*bonusAd+.03*ap,10,this.selected.includes('Tyrant')&&fraction<.5);
    proc('Empowered Attack',scale(20,60)*.8,8,this.selected.includes('Empowered Attack')&&attack);
    const multiplier=this.empowered?1.08:1;
    if(attack && this.selected.includes('Brutal'))physical+=(6+.08*bonusAd)*armorMultiplier;
    if(attack && this.keystone==='Lethal Tempo' && time<this.until && this.stacks>=6)physical+=(6+this.level-1)*(1+.33*this.bonusAs(time))*armorMultiplier;
    if(time>=this.until)this.stacks=0;
    if(this.keystone==='Conqueror'||attack&&this.keystone==='Lethal Tempo'){this.stacks=Math.min(6,this.stacks+1);this.until=time+6;}
    let phaseRush=false;
    if(this.keystone==='Phase Rush'){
      this.phase=this.phase.filter(t=>time-t<=4);this.phase.push(time);
      if(this.phase.length>=3&&time>=(this.ready.PhaseRush||0)){phaseRush=true;this.phase=[];this.ready.PhaseRush=time+21-(this.level-1);}
    }
    if(this.keystone==='Empowerment') {
      if(time-this.last>4)this.hits=0; this.last=time; this.hits++;
      if(this.hits>=3&&time>=(this.ready.Empowerment||0)){proc('Empowerment',scale(40,165),4,true);this.hits=0;this.empowered=true;}
    }
    if(this.keystone==='First Strike' && this.first===null)this.first=time;
    return { physical:physical*multiplier, true:trueDamage, multiplier, phaseRush, firstStrike:this.first!==null&&time<this.first+3 };
  }
}
