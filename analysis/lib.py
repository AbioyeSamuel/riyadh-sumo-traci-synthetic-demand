import os, sys, subprocess, json, glob, math, collections
import xml.etree.ElementTree as ET
import numpy as np, pandas as pd
import sumo
H28=sumo.SUMO_HOME; H120='/tmp/claude-0/work/sumo120/lib/python3.13/site-packages/sumo'
W='/tmp/claude-0/work/paper'; os.chdir(W)
def gen(tag,p,ff,seed,end=3600,begin=0,net='osm.net.xml.gz',prefix='',extra=()):
    d='exp/'+tag
    subprocess.run([sys.executable,H28+'/tools/randomTrips.py','-n',net,'-o',d+'.trips.xml','-r',d+'.rou.xml','-b',str(begin),'-e',str(end),'-p',str(p),'--fringe-factor',str(ff),'--seed',str(seed),'--validate','--prefix',prefix,*extra],check=True,capture_output=True)
    return d+'.rou.xml'
def sim(tag,rou,seed,net='osm.net.xml.gz',add=None,H=H28,emis=False,end=None,extra=(),lat='0.1'):
    d='exp/'+tag
    c=[H+'/bin/sumo','-n',net,'-r',rou,'--step-length','0.5','--lateral-resolution',lat,'--seed',str(seed),'--tripinfo-output',d+'.ti.xml','--summary-output',d+'.sum.xml','--no-step-log','true','--duration-log.statistics','false','--no-warnings','true','--ignore-route-errors','true','--tls.actuated.jam-threshold','30']
    if add: c+=['-a',add]
    if emis: c+=['--device.emissions.probability','1']
    if end: c+=['-e',str(end)]
    c+=list(extra)
    r=subprocess.run(c,capture_output=True,text=True)
    if r.returncode!=0: raise RuntimeError(r.stderr[-500:])
    return d
def ti(d):
    rows=[]
    for t in ET.parse(d+'.ti.xml').getroot().findall('tripinfo'):
        a=dict(t.attrib); e=t.find('emissions')
        o=dict(id=a['id'],depart=float(a['depart']),dur=float(a['duration']),rl=float(a['routeLength']),wait=float(a['waitingTime']),tl=float(a['timeLoss']),stops=int(a.get('waitingCount',0)),vtype=a.get('vType',''))
        if e is not None: o['co2']=float(e.get('CO2_abs')); o['fuel']=float(e.get('fuel_abs',0))
        rows.append(o)
    return pd.DataFrame(rows)
def agg(df,**kw):
    o=dict(n=len(df),dur=df.dur.mean(),rl=df.rl.mean(),spd=(df.rl/df.dur.clip(lower=.5)).mean(),wait=df.wait.mean(),tl=df.tl.mean(),stops=df.stops.mean(),wait_share=(df.wait>0).mean())
    if 'co2' in df: o.update(co2_g_km=df.co2.sum()/1000/(df.rl.sum()/1000), co2_veh=df.co2.mean()/1000)
    o.update(kw); return o
def summ(d):
    s=ET.parse(d+'.sum.xml').getroot().findall('step'); return max(int(x.get('running')) for x in s)
