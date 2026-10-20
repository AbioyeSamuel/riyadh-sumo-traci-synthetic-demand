import sys; sys.path.insert(0,'/tmp/claude-0/work')
from lib import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
B,O,A,G,INK='#2a78d6','#eb6834','#1baf7a','#c9ced6','#2b2f36'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#8a909a','axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'figure.dpi':200,'savefig.bbox':'tight'})
exec(open('/tmp/claude-0/work/exp2.py').read().split("def run_e4")[0].split("def profile")[1].join(["def profile",""]) if False else "")
def read_counts(f):
    d={}
    for iv in ET.parse(f).getroot().findall('interval'):
        b=float(iv.get('begin'))
        for ed in iv.findall('edge'): d[(ed.get('id'),b)]=float(ed.get('entered'))
    return d
def geh(m,c): return 0 if m+c==0 else math.sqrt(2*(m-c)**2/(m+c))
# F14 time-varying
b=pd.read_csv('exp/e4_bins.csv'); r=pd.read_csv('exp/e4_run.csv')
fig,ax=plt.subplots(1,3,figsize=(8.6,2.8))
g=b.groupby('bin'); x=np.arange(16)*15
ax[0].bar(x,g.n.mean()*4,width=12,color=B); ax[0].set_xlabel('Departure time (min)'); ax[0].set_ylabel('Demand (veh/h equivalent)')
for a,(c,col,yl) in zip(ax[1:2],[('dur',O,'Mean travel time (s)')]):
    m=g[c].mean(); s=g[c].std(); a.plot(x,m,'-o',color=col,ms=4,lw=1.4); a.fill_between(x,m-s,m+s,color=col,alpha=.18,lw=0); a.set_xlabel('Departure time (min)'); a.set_ylabel(yl)
m=g.tl.mean(); s=g.tl.std(); ax[2].plot(x,m,'-o',color=A,ms=4,lw=1.4); ax[2].fill_between(x,m-s,m+s,color=A,alpha=.18,lw=0); ax[2].set_xlabel('Departure time (min)'); ax[2].set_ylabel('Mean time loss (s)')
fig.tight_layout(); fig.savefig('fig/f14_profile.png'); plt.close()
print('peak vs off',b[b.bin.between(4,7)][['dur','wait','tl']].mean().round(2).to_dict(),b[b.bin.isin([0,1,2,3,12,13,14,15])][['dur','wait','tl']].mean().round(2).to_dict())
# F15 calibration twin
d=json.load(open('exp/e5.json')); rows=pd.DataFrame(d['rows']); print({k:v for k,v in d.items() if k!='rows'})
tr=read_counts('exp/truth.edge.xml'); eds=sorted({k[0] for k,v in tr.items() if v>0})
def pts(sc,edges):
    m=[];c=[]
    for e in edges:
        for b_ in (0.0,3600.0):
            mv=sc.get((e,b_),0); cv=tr.get((e,b_),0)
            if mv+cv>0: m.append(mv); c.append(cv)
    return np.array(m),np.array(c)
uc=read_counts('exp/unc.edge.xml'); mu,cu=pts(uc,eds); gu=np.array([geh(a,b_) for a,b_ in zip(mu,cu)])
unc=dict(geh_lt5=float((gu<5).mean()),geh_mean=float(gu.mean()),r=float(np.corrcoef(mu,cu)[0,1]),n=len(gu))
print('unc',unc); json.dump(unc,open('exp/e5_unc2.json','w'))
fig,ax=plt.subplots(1,3,figsize=(8.8,2.9))
fr=sorted(rows.frac.unique()); 
TC=pd.DataFrame(json.load(open('exp/e5_tc.json')))
for i,f in enumerate(fr):
    v=rows[rows.frac==f].val_geh_lt5.values*100; ax[0].scatter(np.full(len(v),i-.2)+np.linspace(-.08,.08,len(v)),v,s=14,color=B,alpha=.55,lw=0); ax[0].plot([i-.32,i-.08],[v.mean()]*2,color=INK,lw=1.8)
    if len(TC):
        w=TC[TC.frac==f].val_geh_lt5.values*100; ax[0].scatter(np.full(len(w),i+.2)+np.linspace(-.08,.08,len(w)),w,s=14,color=A,alpha=.7,lw=0); ax[0].plot([i+.08,i+.32],[w.mean()]*2,color=INK,lw=1.8)
from matplotlib.lines import Line2D
ax[0].legend([Line2D([0],[0],marker='o',color='w',markerfacecolor=B,ms=5),Line2D([0],[0],marker='o',color='w',markerfacecolor=A,ms=5)],['Counts only','Counts + total demand'],frameon=False,fontsize=7,loc='lower right')
ax[0].axhline(unc['geh_lt5']*100,color=O,lw=1.3); ax[0].axhline(85,color='#8a909a',lw=.9,ls='--')
ax[0].set_xticks(range(len(fr))); ax[0].set_xticklabels([f'{int(f*100)}%\n({int(rows[rows.frac==f].n_sensors.mean())})' for f in fr],fontsize=8); ax[0].set_xlabel('Counting stations (share of edges)'); ax[0].set_ylabel('Held-out edge-hours with GEH < 5 (%)')
ax[0].text(-.45,unc['geh_lt5']*100+2,'uncalibrated',ha='left',fontsize=7.5,color=O); ax[0].text(-.45,87,'85% criterion',ha='left',fontsize=7.5,color='#6b7280'); ax[0].set_ylim(0,100)
bf=0.25; tag=f'cal_{int(bf*100)}_0'; sc=read_counts(f'exp/{tag}.edge.xml'); mc,cc=pts(sc,eds)
for a,(m,c,col,t) in zip(ax[1:],[(mu,cu,O,'Uncalibrated'),(mc,cc,B,'Counts-only calibration, 25% stations')]):
    a.scatter(c,m,s=7,color=col,alpha=.45,lw=0); lim=max(c.max(),m.max())*1.05; a.plot([0,lim],[0,lim],color='#8a909a',lw=.8); a.set_xlim(0,lim); a.set_ylim(0,lim); a.set_xlabel('"Observed" hourly count'); a.set_ylabel('Simulated hourly count'); a.set_title(t+f' (r = {np.corrcoef(m,c)[0,1]:.2f})',loc='left',fontsize=8.5)
fig.tight_layout(); fig.savefig('fig/f15_calib.png'); plt.close()
# F16 arterial FD
e=pd.read_csv('exp/e7.csv'); e=e[e.t<5400]; e['k']=e.dens/2; e['q']=e.dens*e.speed*3.6/2
fig,ax=plt.subplots(1,2,figsize=(7.2,2.9))
for ed,col,lab in [('158959584',B,'Isolated 13.5 km edge'),('158959688#2',O,'Connected chain, edge #2')]:
    s=e[e.edge==ed]; ax[0].plot(s.k,s.q,'o',color=col,ms=4,alpha=.8,label=lab); ax[1].plot(s.k,s.speed*3.6,'o',color=col,ms=4,alpha=.8)
ax[0].set_xlabel('Density (veh/km/lane)'); ax[0].set_ylabel('Flow (veh/h/lane)'); ax[1].set_xlabel('Density (veh/km/lane)'); ax[1].set_ylabel('Space-mean speed (km/h)'); ax[0].legend(frameon=False,fontsize=7.5)
fig.tight_layout(); fig.savefig('fig/f16_arterial.png'); plt.close()
print(e.groupby('edge')[['k','q']].max().round(1), e.groupby('edge').speed.min()*3.6)
# F17 versions
v=pd.read_csv('exp/e6.csv'); w=v.pivot_table(index=['p','seed'],columns='ver',values='dur').reset_index()
fig,ax=plt.subplots(1,2,figsize=(7.2,2.9))
q=w[w.p==2]; ax[0].scatter(q['1.28.0'],q['1.20.0'],s=18,color=B); lim=[90,98]; ax[0].plot(lim,lim,color='#8a909a',lw=.8); ax[0].set_xlim(lim); ax[0].set_ylim(lim); ax[0].set_xlabel('Mean travel time, SUMO 1.28.0 (s)'); ax[0].set_ylabel('Mean travel time, SUMO 1.20.0 (s)'); ax[0].set_title('p = 2 s, ten seeds',loc='left',fontsize=8.5)
q=w[w.p==1]; ax[1].scatter(q['1.28.0'],q['1.20.0'],s=18,color=O); lim=[0,800]; ax[1].plot(lim,lim,color='#8a909a',lw=.8); ax[1].set_xlabel('Mean travel time, SUMO 1.28.0 (s)'); ax[1].set_ylabel('Mean travel time, SUMO 1.20.0 (s)'); ax[1].set_title('p = 1 s, five seeds',loc='left',fontsize=8.5)
fig.tight_layout(); fig.savefig('fig/f17_versions.png'); plt.close()
print(rows.groupby('frac')[['n_sensors','n_veh','tt','fit_geh_lt5','val_geh_lt5','val_r','val_geh_mean']].mean().round(3))
