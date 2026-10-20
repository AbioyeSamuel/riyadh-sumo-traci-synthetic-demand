import sys; sys.path.insert(0,'/tmp/claude-0/work')
from lib import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sumolib; sys.path.append(H28+'/tools')
B,O,A,G,INK,P='#2a78d6','#eb6834','#1baf7a','#c9ced6','#2b2f36','#7a5cc7'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#8a909a','axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'figure.dpi':200,'savefig.bbox':'tight'})
TC=2.262
def ci(x): x=np.asarray(x,float); return TC*x.std(ddof=1)/math.sqrt(len(x))
def last_tele(tag):
    st=ET.parse(f'exp/{tag}.sum.xml').getroot().findall('step'); return int(st[-1].get('teleports')),float(st[-1].get('time'))
R=pd.DataFrame(json.load(open('exp/res_all.json'))); S=R[R.kind=='sens']; T=R[R.kind=='tls']; V=R[R.kind=='av']
OUT={}
# gridlock flags
S=S.copy(); S['tele']=[last_tele(f"p{int(p) if p==int(p) else p}_s{s}")[0] if ff==10 and True else np.nan for p,ff,s in zip(S.p,S.ff,S.seed)]
S['endt']=[last_tele(f"p{int(p) if p==int(p) else p}_s{s}")[1] for p,ff,s in zip(S.p,S.ff,S.seed)] if False else np.nan
# --- F9 sensitivity 10 seeds
Ps=S[(S.ff==10)&(S.p!=2.0)|((S.ff==10)&(S.p==2.0))]
ps=sorted(Ps.p.unique())
fig,ax=plt.subplots(1,3,figsize=(8.4,2.8))
for a,(c,yl,col) in zip(ax,[('dur','Mean travel time (s)',B),('wait','Mean waiting time (s)',O),('tl','Mean time loss (s)',A)]):
    xs=np.arange(len(ps))
    for i,p in enumerate(ps):
        v=Ps[Ps.p==p][c].values; a.scatter(np.full(len(v),i)+np.random.RandomState(1).uniform(-.12,.12,len(v)),v,s=7,color=col,alpha=.35,lw=0)
        a.errorbar(i,v.mean(),yerr=ci(v),fmt='o',color=INK,ms=4,capsize=3,lw=1.2)
    a.set_yscale('log'); a.set_xticks(xs); a.set_xticklabels([f'{p:g}' for p in ps]); a.set_xlabel('Insertion period p (s/veh)'); a.set_ylabel(yl+' (log scale)')
fig.tight_layout(); fig.savefig('fig/f9_sens10.png'); plt.close()
# p=1 per-seed occupancy
fig,ax=plt.subplots(1,2,figsize=(7.6,2.8),gridspec_kw=dict(width_ratios=[1.4,1]))
fin=[]
for s in range(1,11):
    sm=pd.DataFrame([x.attrib for x in ET.parse(f'exp/p1_s{s}.sum.xml').getroot().findall('step')]).astype(float)
    tele=int(sm.teleports.iloc[-1]); fin.append((s,tele,sm.time.iloc[-1],sm.running.max()))
    ax[0].plot(sm.time.iloc[::10],sm.running.iloc[::10],color=O if tele>0 else B,lw=1,alpha=.9)
ax[0].set_xlabel('Simulation time (s)'); ax[0].set_ylabel('Vehicles in network'); ax[0].set_title('p = 1 s, ten seeds',loc='left',fontsize=9)
ax[0].text(.02,.97,'blue: no teleports; orange: jam with teleports',transform=ax[0].transAxes,ha='left',va='top',fontsize=7.5,color=INK)
fd=pd.DataFrame(fin,columns=['seed','tele','end','peak']); fd=fd.sort_values('end')
ax[1].barh(range(10),fd.end/60,color=[O if t>0 else B for t in fd.tele]); ax[1].set_yticks(range(10)); ax[1].set_yticklabels([f's{s}' for s in fd.seed]); ax[1].set_xlabel('Time to clear network (min)'); ax[1].axvline(60,color='#8a909a',lw=.8,ls='--')
fig.tight_layout(); fig.savefig('fig/f10_gridlock.png'); plt.close(); fd.to_csv('exp/p1_gridlock.csv',index=False); print(fd)
# --- F11 fringe
Fs=S[(S.p==2.0)]; ffs=sorted(Fs.ff.unique())
fig,ax=plt.subplots(1,3,figsize=(8.4,2.7))
for a,(c,yl,col) in zip(ax,[('rl','Mean route length (m)',B),('dur','Mean travel time (s)',O),('wait','Mean waiting time (s)',A)]):
    m=[Fs[Fs.ff==f][c].mean() for f in ffs]; e=[ci(Fs[Fs.ff==f][c]) for f in ffs]
    a.errorbar(range(len(ffs)),m,yerr=e,fmt='-o',color=col,ms=5,capsize=3,lw=1.4); a.set_xticks(range(len(ffs))); a.set_xticklabels([f'{f:g}' for f in ffs]); a.set_xlabel('Fringe factor'); a.set_ylabel(yl)
fig.tight_layout(); fig.savefig('fig/f11_fringe10.png'); plt.close()
# --- F12 signals
fig,ax=plt.subplots(1,3,figsize=(8.4,2.8)); vars_=['none','hot5','all']; lab={'none':'No signals','hot5':'5 hotspot\njunctions','all':'61 junctions'}
for a,(c,yl) in zip(ax,[('dur','Mean travel time (s)'),('wait','Mean waiting time (s)'),('tl','Mean time loss (s)')]):
    for j,(p,col) in enumerate([(2,B),(1,O)]):
        m=[T[(T['var']==v)&(T.p==p)][c].mean() for v in vars_]; e=[ci(T[(T['var']==v)&(T.p==p)][c]) for v in vars_]
        a.errorbar(np.arange(3)+(j-.5)*.12,m,yerr=e,fmt='o-',color=col,ms=5,capsize=3,lw=1.2,label=f'p = {p} s')
    a.set_xticks(range(3)); a.set_xticklabels([lab[v] for v in vars_],fontsize=7.5); a.set_ylabel(yl)
ax[0].legend(frameon=False,fontsize=7.5)
fig.tight_layout(); fig.savefig('fig/f12_signals.png'); plt.close()
# --- F13 AV
fig,ax=plt.subplots(1,3,figsize=(8.4,2.8))
for a,(c,yl) in zip(ax,[('tl','Mean time loss (s)'),('dur','Mean travel time (s)'),('co2_g_km','CO2 (g/km, indicative)')]):
    for p,col in [(1.5,O),(2,B)]:
        m=[V[(V.p==p)&(V.pen==x)][c].mean() for x in [0,10,30,50]]; e=[ci(V[(V.p==p)&(V.pen==x)][c]) for x in [0,10,30,50]]
        a.errorbar([0,10,30,50],m,yerr=e,fmt='-o',color=col,ms=5,capsize=3,lw=1.3,label=f'p = {p:g} s')
    a.set_xlabel('AV share (%)'); a.set_ylabel(yl); a.set_xticks([0,10,30,50])
ax[0].legend(frameon=False,fontsize=7.5); fig.tight_layout(); fig.savefig('fig/f13_av.png'); plt.close()
# --- F18 connectivity
net=sumolib.net.readNet('osm.net.xml.gz'); import networkx as nx
E=[e for e in net.getEdges() if e.allows('passenger')]; G=nx.DiGraph()
for e in E:
    G.add_node(e.getID())
    for o in e.getOutgoing():
        if o.allows('passenger'): G.add_edge(e.getID(),o.getID())
sc=sorted(nx.strongly_connected_components(G),key=len,reverse=True); comp={}
for i,c in enumerate(sc):
    for x in c: comp[x]=i
fig,axs=plt.subplots(1,2,figsize=(7.4,5.2),gridspec_kw=dict(width_ratios=[1,1.5]))
from matplotlib.collections import LineCollection
cols={0:B,1:A}; 
for a,(xl,yl) in zip(axs,[((-300,6900),(-300,11900)),((3800,6900),(-300,2700))]):
    for e in E:
        xs,ys=zip(*e.getShape()); i=comp[e.getID()]; c=cols.get(i,O if e.getID()=='158959584' else '#8a909a'); w=2.2 if e.getType()=='highway.primary' else .9
        a.plot(xs,ys,color=c,lw=w,solid_capstyle='round')
    a.set_xlim(*xl); a.set_ylim(*yl); a.set_aspect('equal'); a.set_xlabel('x (m)'); a.set_ylabel('y (m)')
from matplotlib.lines import Line2D
axs[1].legend([Line2D([0],[0],color=B,lw=1.5),Line2D([0],[0],color=A,lw=1.5),Line2D([0],[0],color='#8a909a',lw=2),Line2D([0],[0],color=O,lw=2)],['Component 1 (120 edges)','Component 2 (103 edges)','Other fragments (incl. one-way primary chain)','Isolated 13.5 km edge'],frameon=False,fontsize=7.2,loc='upper left')
axs[0].set_title('(a) Full extract',loc='left',fontsize=9); axs[1].set_title('(b) Southeast detail',loc='left',fontsize=9)
fig.tight_layout(); fig.savefig('fig/f18_components.png'); plt.close()
# summary tables
tab=lambda df,g,c:df.groupby(g)[c].agg(['mean','std',ci]).round(2)
S.to_csv('exp/S.csv',index=False)
print(tab(S[S.ff==10],'p',['dur','wait','tl','spd','maxrun']).to_string())
print(V.groupby(['p','pen'])[['tl','dur','co2_g_km']].mean().round(2))
