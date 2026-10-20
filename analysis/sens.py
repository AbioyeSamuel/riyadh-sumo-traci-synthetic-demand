import os, sys, subprocess, json
import sumo
H=sumo.SUMO_HOME; T=os.path.join(H,'tools'); S=os.path.join(H,'bin','sumo')
import xml.etree.ElementTree as ET
import numpy as np
os.chdir('/tmp/claude-0/work/paper')
def run(tag,p,ff,seed,end=3600):
    d='sens/'+tag
    subprocess.run([sys.executable,T+'/randomTrips.py','-n','osm.net.xml.gz','-o',d+'.trips.xml','-r',d+'.rou.xml','-e',str(end),'-p',str(p),'--fringe-factor',str(ff),'--seed',str(seed),'--validate'],check=True,capture_output=True)
    subprocess.run([S,'-c','osm.sumocfg','-r',d+'.rou.xml','--step-length','0.5','--lateral-resolution','0.1','--seed',str(seed),'--tripinfo-output',d+'.ti.xml','--summary-output',d+'.sum.xml','--no-step-log','true','--duration-log.statistics','false','--no-warnings','true'],check=True,capture_output=True)
    r=ET.parse(d+'.ti.xml').getroot().findall('tripinfo')
    g=lambda k:np.array([float(t.get(k)) for t in r])
    s=ET.parse(d+'.sum.xml').getroot().findall('step')
    mx=max(int(x.get('running')) for x in s)
    return dict(tag=tag,p=p,ff=ff,seed=seed,n=len(r),dur=g('duration').mean(),rl=g('routeLength').mean(),spd=(g('routeLength')/g('duration')).mean(),wait=g('waitingTime').mean(),tl=g('timeLoss').mean(),maxrun=mx,tele=sum(1 for t in r if t.get('arrivalLane')==''),end=float(s[-1].get('time')))
res=[]
for p in [1,2,3,5,10]: res.append(run(f'p{p}',p,10,42))
for ff in [1,5,10,20]: res.append(run(f'ff{ff}',2,ff,42))
for sd in range(1,11): res.append(run(f'seed{sd}',2,10,sd))
json.dump(res,open('sens/results.json','w'),indent=1)
for r in res: print(r)
