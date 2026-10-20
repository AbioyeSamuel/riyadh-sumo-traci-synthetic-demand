import sys; sys.path.insert(0,'/tmp/claude-0/work')
exec(open('/tmp/claude-0/work/exp2.py').read().split("if __name__")[0])
tr=read_counts('exp/truth.edge.xml'); cnt_edges=sorted({k[0] for k,v in tr.items() if v>0})
def evalr(sim_c,eds):
    g=[];m=[];c=[]
    for e in eds:
        for b in (0.0,3600.0):
            mv=sim_c.get((e,b),0); cv=tr.get((e,b),0)
            if mv+cv>0: g.append(geh(mv,cv)); m.append(mv); c.append(cv)
    g=np.array(g); r=np.corrcoef(m,c)[0,1] if len(g)>2 else float('nan')
    return dict(n=len(g),geh_lt5=float((g<5).mean()),geh_mean=float(g.mean()),r=float(r))
rng=random.Random(5); rows=[]
for frac in [0.05,0.10,0.25,0.50]:
    for draw in range(5):
        sens=set(rng.sample(cnt_edges,max(2,int(round(frac*len(cnt_edges)))))); held=[e for e in cnt_edges if e not in sens]
        cf=f'exp/cnt_{int(frac*100)}_{draw}.xml'; counts_xml('exp/truth.edge.xml',sens,cf)
        out=f'exp/calt_{int(frac*100)}_{draw}.rou.xml'
        r=subprocess.run([sys.executable,H28+'/tools/routeSampler.py','-r','exp/pool.rou.xml','-d',cf,'--edgedata-attribute','entered','-o',out,'--optimize','full','--prefix','c','--seed',str(draw+1),'--total-count','1200,2400'],capture_output=True,text=True)
        if r.returncode!=0 or not os.path.exists(out): print('RS fail',r.stderr[-300:]); continue
        tag=f'calt_{int(frac*100)}_{draw}'; d=sim(tag,out,101,add=eadd(tag)); sc=read_counts(f'exp/{tag}.edge.xml'); cdf=ti(d)
        fit=evalr(sc,sorted(sens)); val=evalr(sc,held)
        rows.append(dict(frac=frac,draw=draw,n_sensors=len(sens),n_veh=len(cdf),tt=float(cdf.dur.mean()),**{'fit_'+k:v for k,v in fit.items()},**{'val_'+k:v for k,v in val.items()}))
        print('tc',frac,draw,rows[-1]['n_veh'],rows[-1]['val_geh_lt5'],flush=True)
json.dump(rows,open('exp/e5_tc.json','w'),default=float)
