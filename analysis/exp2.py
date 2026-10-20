import sys; sys.path.insert(0,'/tmp/claude-0/work')
from lib import *
import random, re
from concurrent.futures import ProcessPoolExecutor
def profile(tag,ps,seed,ff=10,extra=()):
    veh=[]
    for h,p in enumerate(ps):
        r=gen(f'{tag}_h{h}',p,ff,seed*100+h,end=3600*(h+1),begin=3600*h,prefix=f'h{h}_',extra=extra)
        root=ET.parse(r).getroot()
        for v in root.findall('vehicle'): veh.append(v)
    veh.sort(key=lambda v:float(v.get('depart')))
    out=f'exp/{tag}.rou.xml'
    with open(out,'w') as f:
        f.write('<routes>\n')
        for v in veh: f.write(ET.tostring(v,encoding='unicode'))
        f.write('</routes>\n')
    return out
def counts_xml(edgedata_file,edges,path,period=3600):
    root=ET.parse(edgedata_file).getroot(); out=['<meandata>']
    for iv in root.findall('interval'):
        b,e=float(iv.get('begin')),float(iv.get('end'))
        if b>=7200: continue
        out.append(f'<interval begin="{b}" end="{e}">')
        for ed in iv.findall('edge'):
            if ed.get('id') in edges: out.append(f'<edge id="{ed.get("id")}" entered="{ed.get("entered")}"/>')
        out.append('</interval>')
    out.append('</meandata>'); open(path,'w').write('\n'.join(out))
def read_counts(f):
    d={}
    for iv in ET.parse(f).getroot().findall('interval'):
        b=float(iv.get('begin'))
        for ed in iv.findall('edge'): d[(ed.get('id'),b)]=float(ed.get('entered'))
    return d
def geh(m,c): return 0 if m+c==0 else math.sqrt(2*(m-c)**2/(m+c))
def eadd(tag,period=3600):
    f=f'exp/{tag}.edge.add.xml'; open(f,'w').write(f'<additional><edgeData id="e" period="{period}" file="{tag}.edge.xml" excludeEmpty="true"/></additional>'); return f
def run_e4():
    res=[];ts=[]
    for s in range(1,6):
        rou=profile(f'prof_s{s}',[4,1.5,2.5,5],s)
        d=sim(f'prof_s{s}',rou,s); df=ti(d); df['bin']=(df.depart//900).astype(int); df['seed']=s
        res.append(df.groupby(['seed','bin']).agg(n=('dur','size'),dur=('dur','mean'),wait=('wait','mean'),tl=('tl','mean')).reset_index())
        sm=pd.DataFrame([x.attrib for x in ET.parse(d+'.sum.xml').getroot().findall('step')]).astype(float); sm['seed']=s; ts.append(sm[['time','running','seed']].iloc[::10])
        print('e4',s,flush=True)
    pd.concat(res).to_csv('exp/e4_bins.csv',index=False); pd.concat(ts).to_csv('exp/e4_run.csv',index=False)
def od_trips(tag,n,t0,t1,seed,edges,hot_src=(),hot_dst=(),share=0.0):
    rg=random.Random(seed); lines=['<routes>']
    ts=sorted(rg.uniform(t0,t1) for _ in range(n))
    for k,t in enumerate(ts):
        o=rg.choice(list(hot_src)) if hot_src and rg.random()<share else rg.choice(edges)
        d=rg.choice(list(hot_dst)) if hot_dst and rg.random()<share else rg.choice(edges)
        while d==o: d=rg.choice(edges)
        lines.append(f'<trip id="{tag}{k}" depart="{t:.2f}" from="{o}" to="{d}" departLane="best" departSpeed="max"/>')
    lines.append('</routes>'); tf=f'exp/{tag}.trips.xml'; open(tf,'w').write('\n'.join(lines))
    out=f'exp/{tag}.rou.xml'
    subprocess.run([H28+'/bin/duarouter','-n','osm.net.xml.gz','--route-files',tf,'-o',out,'--ignore-errors','true','--no-warnings','true'],check=True,capture_output=True)
    r=ET.parse(out).getroot(); veh=r.findall('vehicle')
    return out
def run_e5():
    import sumolib; sys.path.append(H28+'/tools')
    sc=json.load(open('/tmp/claude-0/work/scc_edges.json')); edges=sorted(e for e in sc if not e.startswith(':'))
    rg=random.Random(11); hs=rg.sample(edges,12); hd=rg.sample(edges,8)
    rows=[]
    t1=od_trips('truth_a',1200,0,3600,101,edges,hs,hd,0.6); t2=od_trips('truth_b',2400,3600,7200,102,edges,hs,hd,0.6)
    veh=ET.parse(t1).getroot().findall('vehicle')+ET.parse(t2).getroot().findall('vehicle'); veh.sort(key=lambda v:float(v.get('depart')))
    open('exp/truth.rou.xml','w').write('<routes>\n'+''.join(ET.tostring(v,encoding='unicode') for v in veh)+'</routes>\n')
    d=sim('truth','exp/truth.rou.xml',101,add=eadd('truth')); tr=read_counts('exp/truth.edge.xml'); tdf=ti(d); print('truth veh',len(tdf),tdf.dur.mean(),flush=True)
    pool=od_trips('pool',9000,0,3600,77,edges)
    unc_a=od_trips('unc_a',1200,0,3600,201,edges); unc_b=od_trips('unc_b',2400,3600,7200,202,edges)
    uveh=ET.parse(unc_a).getroot().findall('vehicle')+ET.parse(unc_b).getroot().findall('vehicle'); uveh.sort(key=lambda v:float(v.get('depart')))
    open('exp/unc.rou.xml','w').write('<routes>\n'+''.join(ET.tostring(v,encoding='unicode') for v in uveh)+'</routes>\n')
    d=sim('unc','exp/unc.rou.xml',101,add=eadd('unc')); uc=read_counts('exp/unc.edge.xml'); udf=ti(d)
    cnt_edges=sorted({k[0] for k,v in tr.items() if v>0}); print('count edges',len(cnt_edges),flush=True)
    def evalr(sim_c,eds):
        g=[];m=[];c=[]
        for e in eds:
            for b in (0.0,3600.0):
                mv=sim_c.get((e,b),0); cv=tr.get((e,b),0)
                if mv+cv>0: g.append(geh(mv,cv)); m.append(mv); c.append(cv)
        g=np.array(g); r=np.corrcoef(m,c)[0,1] if len(g)>2 else float('nan')
        return dict(n=len(g),geh_lt5=float((g<5).mean()),geh_mean=float(g.mean()),r=float(r),rmse=float(np.sqrt(np.mean((np.array(m)-np.array(c))**2))))
    allr={'truth_mean_tt':float(tdf.dur.mean()),'truth_n':len(tdf),'unc_mean_tt':float(udf.dur.mean()),'unc_n':len(udf)}
    allr['unc_all']=evalr(uc,cnt_edges)
    rng=random.Random(5)
    for frac in [0.05,0.10,0.25,0.50]:
        for draw in range(5):
            sens=set(rng.sample(cnt_edges,max(2,int(round(frac*len(cnt_edges)))))); held=[e for e in cnt_edges if e not in sens]
            cf=f'exp/cnt_{int(frac*100)}_{draw}.xml'; counts_xml('exp/truth.edge.xml',sens,cf)
            out=f'exp/cal_{int(frac*100)}_{draw}.rou.xml'
            r=subprocess.run([sys.executable,H28+'/tools/routeSampler.py','-r',pool,'-d',cf,'--edgedata-attribute','entered','-o',out,'--optimize','full','--prefix','c','--seed',str(draw+1)],capture_output=True,text=True)
            if r.returncode!=0 or not os.path.exists(out): print('RS fail',r.stderr[-400:]); continue
            tag=f'cal_{int(frac*100)}_{draw}'; d=sim(tag,out,101,add=eadd(tag)); sc=read_counts(f'exp/{tag}.edge.xml'); cdf=ti(d)
            fit=evalr(sc,sorted(sens)); val=evalr(sc,held)
            rows.append(dict(frac=frac,draw=draw,n_sensors=len(sens),n_veh=len(cdf),tt=float(cdf.dur.mean()),wait=float(cdf.wait.mean()),**{'fit_'+k:v for k,v in fit.items()},**{'val_'+k:v for k,v in val.items()}))
            print('e5',frac,draw,rows[-1]['val_geh_lt5'],flush=True)
    allr['rows']=rows; json.dump(allr,open('exp/e5.json','w'),default=float)
def run_e6():
    rows=[]
    for p,seeds in [(2,range(1,11)),(1,range(1,6))]:
        for s in seeds:
            rou=f'exp/p{p}_s{s}.rou.xml'
            for ver,H in [('1.28.0',H28),('1.20.0',H120)]:
                d=sim(f'v{ver}_p{p}_s{s}',rou,s,H=H); rows.append(agg(ti(d),ver=ver,p=p,seed=s))
    pd.DataFrame(rows).to_csv('exp/e6.csv',index=False); print('e6 done',flush=True)
def run_e7():
    stages=list(range(500,4501,500)); T=600
    rts='<routes>\n<route id="lone" edges="158959584"/>\n<route id="chain" edges="158959688#0 158959688#1 158959688#2 158959688#3 158959688#4"/>\n'
    for i,q in enumerate(stages):
        for r in ['lone','chain']:
            rts+=f'<flow id="{r}_{i}" route="{r}" begin="{i*T}" end="{(i+1)*T}" vehsPerHour="{q}" departLane="free" departSpeed="max"/>\n'
    rts+='</routes>'; open('exp/art.rou.xml','w').write(rts)
    d=sim('art','exp/art.rou.xml',1,add=eadd('art',period=300),end=len(stages)*T+300,lat='0')
    rows=[]
    for iv in ET.parse('exp/art.edge.xml').getroot().findall('interval'):
        b=float(iv.get('begin'))
        for ed in iv.findall('edge'):
            if ed.get('id') in ('158959584','158959688#2','158959688#0'):
                rows.append(dict(t=b,edge=ed.get('id'),dens=float(ed.get('density')),speed=float(ed.get('speed')),entered=float(ed.get('entered')),left=float(ed.get('left')) if ed.get('left') else np.nan))
    pd.DataFrame(rows).to_csv('exp/e7.csv',index=False); df=ti(d); print('e7 veh',len(df),df.dur.mean(),flush=True)
if __name__=='__main__':
    which=sys.argv[1]; {'e4':run_e4,'e5':run_e5,'e6':run_e6,'e7':run_e7}[which]()
