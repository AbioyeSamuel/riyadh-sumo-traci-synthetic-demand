import os, sys, csv, collections, json
import sumo
H=sumo.SUMO_HOME; sys.path.append(H+'/tools')
import traci, sumolib
os.chdir('/tmp/claude-0/work/paper')
net=sumolib.net.readNet('osm.net.xml.gz')
traci.start([H+'/bin/sumo','-c','osm.sumocfg','--step-length','0.5','--lateral-resolution','0.1','--seed','42','--no-step-log','true','--duration-log.statistics','false','--no-warnings','true'])
rows=[]; step=0; prev={}
BIN=300; L={e.getID():e.getLength() for e in net.getEdges()}; NL={e.getID():len(e.getLanes()) for e in net.getEdges()}
tt=collections.defaultdict(float); dd=collections.defaultdict(float)
slow=[]
while traci.simulation.getMinExpectedNumber()>0:
    traci.simulationStep(); step+=1
    t=traci.simulation.getTime()
    for v in traci.vehicle.getIDList():
        s=traci.vehicle.getSpeed(v); x,y=traci.vehicle.getPosition(v); e=traci.vehicle.getRoadID(v)
        rows.append((step,v,round(s,3),round(x,2),round(y,2)))
        if e in L:
            b=int(t//BIN); tt[(e,b)]+=0.5; dd[(e,b)]+=s*0.5
        if s<2.0: slow.append((step,v,x,y,e))
traci.close()
with open('traci_speed_position_log.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['step','vehicle_id','speed_mps','x','y']); w.writerows(rows)
fd=[]
for (e,b),T in tt.items():
    if L[e]<30: continue
    k=T/(L[e]*BIN)*1000/NL[e]; q=dd[(e,b)]/(L[e]*BIN)*3600/NL[e]
    fd.append((e,b,k,q,dd[(e,b)]/T))
json.dump(dict(fd=fd,slow=slow,steps=step),open('traci_derived.json','w'))
print(step,len(rows),len(slow),len(fd))
