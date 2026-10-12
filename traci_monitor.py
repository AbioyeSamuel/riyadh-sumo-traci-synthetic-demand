# Step 1: Add modules to provide access to specific libraries and functions
import os   # Module provides functions to handle file paths, directories, environment variables
import sys  # Module provides access to Python-specific system parameters and functions
import csv  # Module to log simulation data to a CSV file for later analysis

# Step 2: Establish path to SUMO (SUMO_HOME)
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Step 3: Add Traci module to provide access to specific libraries and functions
import traci

# Step 4: Define Sumo configuration
Sumo_config = [
    'sumo-gui',
    '-c', r'C:\Users\olaol\Documents\SIMULATION\OSM\OSM_Riyadh_20260911\osm.sumocfg',
    '--step-length', '0.5',
    '--delay', '100',
    '--lateral-resolution', '0.1'
]

# Step 5: Open connection between SUMO and Traci
traci.start(Sumo_config)

# Step 6: Define Variables
log_rows = []          # will hold [step, veh_id, speed, x, y] for every vehicle at every step
step_count = 0
SLOW_SPEED_THRESHOLD = 2.0  # m/s — used in Step 7 to flag near-stopped vehicles (basic live monitoring)

# Step 7: Define Functions
def log_all_vehicles(step_count):
    """
    Reads speed and position for every vehicle currently in the network
    and appends it to log_rows. Also prints a live alert if any vehicle
    is moving slower than SLOW_SPEED_THRESHOLD (simple congestion flag).
    """
    vehicle_ids = traci.vehicle.getIDList()
    for veh_id in vehicle_ids:
        speed = traci.vehicle.getSpeed(veh_id)
        position = traci.vehicle.getPosition(veh_id)  # (x, y) in network coordinates
        log_rows.append([step_count, veh_id, speed, position[0], position[1]])

        if speed < SLOW_SPEED_THRESHOLD:
            print(f"[step {step_count}] Vehicle {veh_id} slow: {speed:.2f} m/s at {position}")

# Step 8: Take simulation steps until there are no more vehicles in the network
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()  # Move simulation forward 1 step
    step_count += 1
    log_all_vehicles(step_count)

# Step 9: Close connection between SUMO and Traci
traci.close()

# Save the collected log to CSV after the connection closes
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traci_speed_position_log.csv')
with open(output_path, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['step', 'vehicle_id', 'speed_mps', 'x', 'y'])
    writer.writerows(log_rows)

print(f"Log saved to: {output_path}")