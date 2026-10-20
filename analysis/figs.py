import os, sys, json, collections
import sumo
sys.path.append(sumo.SUMO_HOME+'/tools')
import sumolib, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
os.chdir('/tmp/claude-0/work/paper')
B,O,A,G,INK='#2a78d6','#eb6834','#1baf7a','#c9ced6','#2b2f36'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#8a909a','axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'figure.dpi':200,'savefig.bbox':'tight'})
net=sumolib.net.readNet('osm.net.xml.gz')
D=json.load(open('traci_derived.json'))
# Fig1 network map
fig,ax=plt.subplots(figsize=(6.2,5.4))
sty={'highway.primary':(O,2.4,'Primary (Al Janadiriyah Rd)'),'highway.residential':(B,0.9,'Residential'),'highway.unclassified':(A,1.2,'Unclassified'),'highway.service':('#9aa1ad',0.6,'Service (no passenger access)'),'highway.footway':('#d5d9e0',0.4,'Footway (no passenger access)')}
seen=set()
for e in sorted(net.getEdges(),key=lambda e:sty.get(e.getType(),(0,0))[1]):
    c,w,l=sty.get(e.getType(),('k',.5,e.getType()))
    xs,ys=zip(*e.getShape()); ax.plot(xs,ys,color=c,lw=w,solid_capstyle='round',label=None if l in seen else l); seen.add(l)
ax.set_aspect('equal'); ax.set_xlabel('x (m, UTM-projected network coordinates)'); ax.set_ylabel('y (m)')
h,l=ax.get_legend_handles_labels(); order=[l.index(k) for k in ['Primary (Al Janadiriyah Rd)','Residential','Unclassified','Service (no passenger access)','Footway (no passenger access)'] if k in l]
ax.legend([h[i] for i in order],[l[i] for i in order],frameon=False,loc='upper left',fontsize=7.5)
fig.savefig('fig/f1_network.png'); plt.close()
# tripinfo
ti=pd.DataFrame([t.attrib for t in ET.parse('base_tripinfo.xml').getroot().findall('tripinfo')])
for c in ['depart','arrival','duration','routeLength','waitingTime','timeLoss','departDelay','waitingCount','stopTime']: ti[c]=ti[c].astype(float)
ti['speed']=ti.routeLength/ti.duration
# Fig2 demand profile & running vehicles
sm=pd.DataFrame([s.attrib for s in ET.parse('base_summary.xml').getroot().findall('step')]).astype(float)
fig,ax=plt.subplots(1,2,figsize=(7,2.9))
b=np.arange(0,3601,300); ax[0].hist(ti.depart,bins=b,color=B,edgecolor='white',lw=1.5); ax[0].set_xlabel('Departure time (s)'); ax[0].set_ylabel('Vehicles per 5 min'); ax[0].set_title('Demand profile',loc='left',fontsize=9)
ax[1].plot(sm.time,sm.running,color=O,lw=1.2); ax[1].set_xlabel('Simulation time (s)'); ax[1].set_ylabel('Vehicles in network'); ax[1].set_title('Network occupancy',loc='left',fontsize=9)
fig.tight_layout(); fig.savefig('fig/f2_demand.png'); plt.close()
# Fig3 distributions
fig,ax=plt.subplots(1,4,figsize=(8,2.6))
for a,(c,xl) in zip(ax,[('routeLength','Route length (m)'),('duration','Travel time (s)'),('timeLoss','Time loss (s)'),('speed','Mean trip speed (m/s)')]):
    a.hist(ti[c],bins=30,color=B,edgecolor='white',lw=.6); a.axvline(ti[c].median(),color=O,lw=1.4); a.set_xlabel(xl); a.set_yticks([])
    a.text(.97,.95,f'median {ti[c].median():.1f}',transform=a.transAxes,ha='right',va='top',fontsize=7,color=INK)
ax[0].set_ylabel('Vehicles'); ax[0].set_yticks(a.get_yticks()[:0]); fig.tight_layout(); fig.savefig('fig/f3_dist.png'); plt.close()
# Fig4 TraCI speed distribution
sp=pd.read_csv('traci_speed_position_log.csv')
fig,ax=plt.subplots(figsize=(4.6,2.9))
ax.hist(sp.speed_mps,bins=60,color=B,edgecolor='white',lw=.4); ax.axvline(2.0,color=O,lw=1.4); ax.set_xlabel('Instantaneous speed (m/s), 0.5 s samples'); ax.set_ylabel('Vehicle-samples')
ax.text(2.4,ax.get_ylim()[1]*.92,f'slow-speed threshold 2 m/s\n{(sp.speed_mps<2).mean()*100:.1f}% of samples below',fontsize=7.5,color=INK,va='top')
fig.savefig('fig/f4_speed.png'); plt.close()
# Fig5 slow-speed event map
sl=pd.DataFrame(D['slow'],columns=['step','v','x','y','e'])
fig,ax=plt.subplots(figsize=(6.2,5.0))
for e in net.getEdges():
    if e.allows('passenger'):
        xs,ys=zip(*e.getShape()); ax.plot(xs,ys,color=G,lw=.7)
hb=ax.hexbin(sl.x,sl.y,gridsize=45,cmap='Blues',mincnt=1,linewidths=0); cb=fig.colorbar(hb,ax=ax,shrink=.7); cb.set_label('Slow-speed samples (<2 m/s)')
ax.set_aspect('equal'); ax.set_xlabel('x (m)'); ax.set_ylabel('y (m)'); fig.savefig('fig/f5_slowmap.png'); plt.close()
# Fig6 fundamental diagram
fd=pd.DataFrame(D['fd'],columns=['e','b','k','q','v']); fd=fd[fd.k>0]
fig,ax=plt.subplots(1,2,figsize=(7,2.9))
ax[0].scatter(fd.k,fd.q,s=5,color=B,alpha=.35,lw=0); ax[0].set_xlabel('Density (veh/km/lane)'); ax[0].set_ylabel('Flow (veh/h/lane)'); ax[0].set_title('Flow–density (Edie, 300 s, per edge)',loc='left',fontsize=8.5)
ax[1].scatter(fd.k,fd.v*3.6,s=5,color=O,alpha=.35,lw=0); ax[1].set_xlabel('Density (veh/km/lane)'); ax[1].set_ylabel('Space-mean speed (km/h)'); ax[1].set_title('Speed–density',loc='left',fontsize=8.5)
fig.tight_layout(); fig.savefig('fig/f6_fd.png'); plt.close()
print('fd n',len(fd),'max k',fd.k.max(),'max q',fd.q.max())
# Fig7 sensitivity
R=pd.DataFrame(json.load(open('sens/results.json')))
P=R[R.tag.str.startswith('p')&(R.ff==10)&(R.seed==42)].sort_values('p')
fig,ax=plt.subplots(1,3,figsize=(8,2.6))
for a,(c,yl,col) in zip(ax,[('dur','Mean travel time (s)',B),('wait','Mean waiting time (s)',O),('spd','Mean trip speed (m/s)',A)]):
    a.plot(P.p,P[c],'-o',color=col,lw=1.5,ms=5,mec='white'); a.set_xlabel('Insertion period p (s/veh)'); a.set_ylabel(yl); a.set_xticks(P.p)
fig.tight_layout(); fig.savefig('fig/f7_sens_p.png'); plt.close()
# Fig8 seed ensemble + fringe
S=R[R.tag.str.startswith('seed')]; F=R[R.tag.str.startswith('ff')].sort_values('ff')
fig,ax=plt.subplots(1,2,figsize=(7,2.8))
ax[0].plot(F.ff,F.rl,'-o',color=B,ms=5,mec='white'); ax[0].set_xlabel('Fringe factor'); ax[0].set_ylabel('Mean route length (m)'); ax[0].set_xscale('log'); ax[0].set_xticks(F.ff); ax[0].set_xticklabels(F.ff)
ax[1].boxplot([S.dur,S.tl,S.wait],tick_labels=['Travel\ntime (s)','Time\nloss (s)','Waiting\ntime (s)'],widths=.5,medianprops=dict(color=O),boxprops=dict(color=B),whiskerprops=dict(color=B),capprops=dict(color=B))
ax[1].set_title('10-seed ensemble (p = 2 s)',loc='left',fontsize=8.5)
fig.tight_layout(); fig.savefig('fig/f8_ens.png'); plt.close()
# tables
q=lambda s:[s.mean(),s.std(),s.min(),s.quantile(.5),s.quantile(.95),s.max()]
T=pd.DataFrame({k:q(ti[k]) for k in ['routeLength','duration','timeLoss','waitingTime','speed']},index=['mean','sd','min','median','p95','max']).T
T.to_csv('tab_trip.csv'); print(T.round(2))
S2=S[['dur','rl','spd','wait','tl','maxrun']].agg(['mean','std','min','max']).T; S2.to_csv('tab_seed.csv'); print(S2.round(3))
print('slow share',(sp.speed_mps<2).mean(), 'veh with any wait>0',(ti.waitingTime>0).mean(), 'p95 tl',ti.timeLoss.quantile(.95), 'n slow edges', sl.e.nunique())
print(sl.e.value_counts().head(5))
print('corr rl-dur',np.corrcoef(ti.routeLength,ti.duration)[0,1])
print(R[['tag','dur','wait','tl','spd','maxrun']].round(2).to_string())
