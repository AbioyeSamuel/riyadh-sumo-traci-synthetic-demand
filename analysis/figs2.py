import os, sys, json
import sumo
sys.path.append(sumo.SUMO_HOME+'/tools')
import sumolib, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
os.chdir('/tmp/claude-0/work/paper')
B,O,A,G,INK='#2a78d6','#eb6834','#1baf7a','#c9ced6','#2b2f36'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#8a909a','axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'figure.dpi':200,'savefig.bbox':'tight'})
net=sumolib.net.readNet('osm.net.xml.gz'); D=json.load(open('traci_derived.json'))
sl=pd.DataFrame(D['slow'],columns=['step','v','x','y','e'])
cnt=sl.e.value_counts().to_dict()
def draw(ax,xl=None,yl=None,mode='type'):
    segs,cols,ws=[],[],[]
    for e in net.getEdges():
        if not e.allows('passenger'): continue
        xs,ys=zip(*e.getShape()); segs.append(list(zip(xs,ys)))
        c=cnt.get(e.getID(),0)
        if mode=='slow':
            cols.append(plt.cm.YlOrRd(0.15+0.85*np.log1p(c)/np.log1p(2000))); ws.append(1.0+2.2*np.log1p(c)/np.log1p(2000))
        else:
            cols.append(O if e.getType()=='highway.primary' else (A if e.getType()=='highway.unclassified' else B)); ws.append(2.4 if e.getType()=='highway.primary' else 0.9)
    ax.add_collection(LineCollection(segs,colors=cols,linewidths=ws,capstyle='round'))
    ax.set_aspect('equal')
    if xl: ax.set_xlim(*xl); ax.set_ylim(*yl)
    else: ax.autoscale()
    ax.set_xlabel('x (m)'); ax.set_ylabel('y (m)')
for mode,name in [('type','f1_network'),('slow','f5_slowmap')]:
    fig,ax=plt.subplots(1,2,figsize=(7.4,5.2),gridspec_kw=dict(width_ratios=[1,1.5]))
    draw(ax[0],mode=mode); ax[0].set_xlim(-300,6900); ax[0].set_ylim(-300,11900); ax[0].set_title('(a) Full extract',loc='left',fontsize=9)
    draw(ax[1],(3800,6900),(-300,2700),mode=mode); ax[1].set_title('(b) Southeast detail (residential grid)',loc='left',fontsize=9)
    if mode=='type':
        from matplotlib.lines import Line2D
        ax[1].legend([Line2D([0],[0],color=O,lw=2.4),Line2D([0],[0],color=B,lw=1),Line2D([0],[0],color=A,lw=1.4)],['Primary','Residential','Unclassified'],frameon=False,fontsize=7.5,loc='upper left')
    else:
        sm=plt.cm.ScalarMappable(cmap='YlOrRd',norm=matplotlib.colors.Normalize(0,np.log1p(2000))); 
        cb=fig.colorbar(sm,ax=ax[1],shrink=.6); cb.set_ticks(np.log1p([0,10,100,1000])); cb.set_ticklabels(['0','10','100','1000']); cb.set_label('Slow samples per edge (<2 m/s)')
    fig.tight_layout(); fig.savefig(f'fig/{name}.png'); plt.close()
print(sl.e.str.startswith(':').mean(), len(sl))
top=sl.e.value_counts().head(6)
for e,c in top.items():
    if e.startswith(':'): print(e,c,'internal'); continue
    ed=net.getEdge(e); print(e,c,ed.getType(),ed.getName(),round(ed.getLength()),ed.getLaneNumber(),ed.getSpeed())
