import sys; sys.path.insert(0,'/tmp/claude-0/work')
from lib import *
from concurrent.futures import ProcessPoolExecutor
import re, sumolib
sys.path.append(H28+'/tools')
SEEDS=range(1,11)
# ---------- vtypes for AV experiment
def vt_files():
    for pen in [0,10,30,50]:
        h=1-pen/100
        x='<additional>\n'
        x+='<vType id="compact" length="4.2" accel="3.0" decel="4.5" tau="1.0" minGap="2.5" sigma="0.5" emissionClass="HBEFA4/PC_petrol_Euro-4"/>\n'
        x+='<vType id="sedan" length="4.8" accel="2.6" decel="4.5" tau="1.0" minGap="2.5" sigma="0.5" emissionClass="HBEFA4/PC_petrol_Euro-4"/>\n'
        x+='<vType id="suv" length="5.3" accel="2.2" decel="4.0" tau="1.1" minGap="2.5" sigma="0.5" emissionClass="HBEFA4/PC_petrol_Euro-4"/>\n'
        x+='<vType id="av" length="4.8" accel="2.6" decel="4.5" tau="0.5" minGap="1.5" sigma="0.1" emissionClass="HBEFA4/PC_petrol_Euro-4" color="0,200,120"/>\n'
        x+=f'<vTypeDistribution id="mix">\n'
        for n,w in [('compact',.4*h),('sedan',.4*h),('suv',.2*h),('av',pen/100)]:
            if w>0: x+=f'  <vType id="{n}" probability="{w:.4f}"/>\n'
        x+='</vTypeDistribution>\n</additional>'
        open(f'exp/vt_av{pen}.add.xml','w').write(x)
def vt_fix(pen):
    # distribution refs: SUMO needs vTypes referenced via vTypes attr instead -> use vTypes/probabilities form
    h=1-pen/100; names=['compact','sedan','suv','av']; ps=[.4*h,.4*h,.2*h,pen/100]
    keep=[(n,p) for n,p in zip(names,ps) if p>0]
    x=open(f'exp/vt_av{pen}.add.xml').read()
    x=re.sub(r'<vTypeDistribution.*</vTypeDistribution>',f'<vTypeDistribution id="mix" vTypes="{" ".join(n for n,_ in keep)}" probabilities="{" ".join(f"{p:.4f}" for _,p in keep)}"/>',x,flags=re.S)
    open(f'exp/vt_av{pen}.add.xml','w').write(x)
def job_gen(a):
    tag,p,ff,seed=a; return gen(tag,p,ff,seed)
def job_sens(a):
    tag,p,ff,seed=a; rou=f'exp/{tag}.rou.xml'
    d=sim(tag,rou,seed); r=agg(ti(d),kind='sens',p=p,ff=ff,seed=seed,maxrun=summ(d)); return r
def job_av(a):
    p,pen,seed=a; rou=f'exp/p{p}_s{seed}.rou.xml'
    s=open(rou).read(); mr=f'exp/avrou_p{p}_a{pen}_s{seed}.rou.xml'
    open(mr,'w').write(s.replace('<vehicle ','<vehicle type="mix" '))
    d=sim(f'av_p{p}_a{pen}_s{seed}',mr,seed,add=f'exp/vt_av{pen}.add.xml',emis=True)
    df=ti(d); r=agg(df,kind='av',p=p,pen=pen,seed=seed,maxrun=summ(d))
    if pen>0:
        a=df[df.vtype=='av']; h=df[df.vtype!='av']; r.update(av_dur=a.dur.mean(),h_dur=h.dur.mean(),av_co2=a.co2.sum()/a.rl.sum()*1000/1000, h_co2=h.co2.sum()/h.rl.sum())
    return r
def job_tls(a):
    var,p,seed=a; net={'none':'osm.net.xml.gz','hot5':'exp/net_hot5.net.xml.gz','all':'exp/net_all.net.xml.gz'}[var]
    d=sim(f'tls_{var}_p{p}_s{seed}',f'exp/p{p}_s{seed}.rou.xml',seed,net=net); df=ti(d); return agg(df,kind='tls',var=var,p=p,seed=seed,maxrun=summ(d))
if __name__=='__main__':
    ex=ProcessPoolExecutor(2)
    # generate demand: p in 1,1.5,2,3,5,10 ; ff 1,5,20 at p=2 ; seeds 1..10
    gens=[(f'p{p}_s{s}',p,10,s) for p in [1,1.5,2,3,5,10] for s in SEEDS]+[(f'ff{f}_s{s}',2,f,s) for f in [1,5,20] for s in SEEDS]
    list(ex.map(job_gen,gens)); print('gen done',flush=True)
    res=[]
    sens=[(f'p{p}_s{s}',p,10,s) for p in [1,1.5,2,3,5,10] for s in SEEDS]+[(f'ff{f}_s{s}',2,f,s) for f in [1,5,20] for s in SEEDS]
    res+=list(ex.map(job_sens,sens)); json.dump(res,open('exp/res_sens.json','w'),default=float); print('sens done',flush=True)
    # networks with signals
    net=sumolib.net.readNet('osm.net.xml.gz'); hot=['-1095828493#0','-278305873#2','278305900','278305878#1','-889249672']
    nodes=sorted({net.getEdge(e).getToNode().getID() for e in hot}); print('hot nodes',nodes)
    allp=[n.getID() for n in net.getNodes() if n.getType() in('priority','right_before_left') and len([e for e in n.getIncoming() if e.allows('passenger')])>=3]
    print('all nodes',len(allp))
    for nm,ids in [('hot5',nodes),('all',allp)]:
        r=subprocess.run([H28+'/bin/netconvert','-s','osm.net.xml.gz','--tls.set',','.join(ids),'--tls.default-type','static','-o',f'exp/net_{nm}.net.xml.gz','--no-warnings'],capture_output=True,text=True); print(nm,r.returncode,r.stderr[-200:])
    json.dump(dict(hot=nodes,all=allp),open('exp/tls_nodes.json','w'))
    vt_files(); [vt_fix(p) for p in [0,10,30,50]]
    tl=[(v,p,s) for v in ['none','hot5','all'] for p in [1,2] for s in SEEDS]
    res+=list(ex.map(job_tls,tl)); json.dump(res,open('exp/res_sens.json','w'),default=float); print('tls done',flush=True)
    av=[(p,pen,s) for p in [1,1.5,2] for pen in [0,10,30,50] for s in SEEDS]
    res+=list(ex.map(job_av,av)); json.dump(res,open('exp/res_all.json','w'),default=float); print('av done',flush=True)
